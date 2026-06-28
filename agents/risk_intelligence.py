from datetime import datetime, timezone


def assess_liquidity_risk(metrics):
    current_ratio = metrics.get("current_ratio")
    if current_ratio is None:
        return None
    if current_ratio < 1.0:
        severity = "high" if current_ratio < 0.8 else "moderate"
        return {
            "risk_type": "liquidity_risk",
            "severity": severity,
            "evidence": f"Current Ratio is {round(current_ratio, 2)}, below the 1.0 threshold, meaning current liabilities exceed current assets.",
            "metric": "current_ratio",
            "value": current_ratio
        }
    return None


def assess_leverage_risk(metrics):
    debt_to_equity = metrics.get("debt_to_equity")
    if debt_to_equity is None:
        return None
    if debt_to_equity > 1.5:
        severity = "high" if debt_to_equity > 2.5 else "moderate"
        return {
            "risk_type": "leverage_risk",
            "severity": severity,
            "evidence": f"Debt-to-Equity ratio is {round(debt_to_equity, 2)}, above the 1.5 threshold, indicating elevated reliance on debt financing.",
            "metric": "debt_to_equity",
            "value": debt_to_equity
        }
    return None


def assess_profitability_risk(metrics):
    net_margin = metrics.get("net_margin")
    if net_margin is None:
        return None
    if net_margin < 0.10:
        severity = "high" if net_margin < 0 else "moderate"
        return {
            "risk_type": "profitability_risk",
            "severity": severity,
            "evidence": f"Net margin is {round(net_margin * 100, 2)}%, below the 10% threshold considered healthy for most industries.",
            "metric": "net_margin",
            "value": net_margin
        }
    return None


def assess_growth_risk(metrics):
    revenue_growth = metrics.get("revenue_growth")
    if revenue_growth is None:
        return None
    if revenue_growth < 0:
        return {
            "risk_type": "growth_risk",
            "severity": "high",
            "evidence": f"Revenue growth is {round(revenue_growth * 100, 2)}%, indicating year-over-year revenue contraction.",
            "metric": "revenue_growth",
            "value": revenue_growth
        }
    return None


def assess_cash_flow_risk(metrics):
    fcf = metrics.get("free_cash_flow")
    if fcf is None:
        return None
    if fcf < 0:
        return {
            "risk_type": "cash_flow_risk",
            "severity": "high",
            "evidence": f"Free Cash Flow is negative (${fcf:,.0f}), indicating the company is burning cash after capital expenditures.",
            "metric": "free_cash_flow",
            "value": fcf
        }
    return None


def assess_news_signal(news_articles):
    """
    Secondary, lightweight signal only - counts negative keywords in headlines.
    This does NOT drive severity on its own; it's flagged separately as a
    qualitative note, never a quantitative risk score.
    """
    negative_keywords = ["lawsuit", "investigation", "decline", "falling", "drop",
                          "cut", "downgrade", "recall", "scandal", "fraud", "fine", "probe"]
    flagged_articles = []
    for article in news_articles:
        title_lower = article.get("title", "").lower()
        if any(keyword in title_lower for keyword in negative_keywords):
            flagged_articles.append(article.get("title"))

    if flagged_articles:
        return {
            "risk_type": "news_signal",
            "severity": "informational",
            "evidence": f"{len(flagged_articles)} recent headline(s) contain cautionary language.",
            "flagged_headlines": flagged_articles,
            "note": "This is a secondary qualitative signal, not a quantitative risk score."
        }
    return None


def run_risk_intelligence(financial_analysis_output, market_intelligence_output):
    """
    Main entry point for the Risk Intelligence Agent.
    Takes outputs from Financial Analysis and Market Intelligence agents.
    Pure rule-based logic - no LLM involved in flag generation.
    """
    ticker = financial_analysis_output.get("ticker", "UNKNOWN")
    metrics = financial_analysis_output.get("metrics", {})
    news = market_intelligence_output.get("news", [])

    risk_flags = []

    checks = [
        assess_liquidity_risk(metrics),
        assess_leverage_risk(metrics),
        assess_profitability_risk(metrics),
        assess_growth_risk(metrics),
        assess_cash_flow_risk(metrics),
        assess_news_signal(news)
    ]

    for flag in checks:
        if flag is not None:
            risk_flags.append(flag)

    high_severity_count = sum(1 for f in risk_flags if f.get("severity") == "high")
    moderate_severity_count = sum(1 for f in risk_flags if f.get("severity") == "moderate")

    if high_severity_count > 0:
        overall_risk_level = "elevated"
    elif moderate_severity_count > 0:
        overall_risk_level = "moderate"
    else:
        overall_risk_level = "low"

    result = {
        "agent": "risk_intelligence",
        "ticker": ticker,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "overall_risk_level": overall_risk_level,
        "risk_flags": risk_flags,
        "method": "rule_based_thresholds",
        "data_quality": {
            "flags_generated": len(risk_flags),
            "errors": []
        }
    }

    return result


if __name__ == "__main__":
    import json
    import sys
    sys.path.append(".")
    from agents.market_intelligence import run_market_intelligence
    from agents.financial_analysis import run_financial_analysis

    mi_output = run_market_intelligence("AAPL")
    fa_output = run_financial_analysis(mi_output)
    risk_output = run_risk_intelligence(fa_output, mi_output)
    print(json.dumps(risk_output, indent=2, default=str))