from datetime import datetime, timezone


def safe_divide(numerator, denominator):
    """Returns None if division isn't possible, instead of crashing."""
    if numerator is None or denominator is None or denominator == 0:
        return None
    return numerator / denominator


def calculate_ratios(market_intelligence_output):
    """
    Takes the full output of the Market Intelligence Agent and computes
    financial ratios. Pure calculation, no AI involved.
    """
    errors = []
    statements = market_intelligence_output.get("financial_statements", {})

    income_curr = statements.get("income_statement", {}).get("current_period", {})
    income_prior = statements.get("income_statement", {}).get("prior_period", {})
    balance_curr = statements.get("balance_sheet", {}).get("current_period", {})
    balance_prior = statements.get("balance_sheet", {}).get("prior_period", {})
    cash_curr = statements.get("cash_flow", {}).get("current_period", {})

    if not income_curr:
        errors.append("No current period income statement data available")
    if not balance_curr:
        errors.append("No current period balance sheet data available")

    # --- Pull raw values ---
    net_income = income_curr.get("Net Income")
    total_revenue = income_curr.get("Total Revenue")
    gross_profit = income_curr.get("Gross Profit")
    operating_income = income_curr.get("Operating Income")
    prior_revenue = income_prior.get("Total Revenue")

    stockholders_equity = balance_curr.get("Stockholders Equity")
    total_debt = balance_curr.get("Total Debt")
    current_assets = balance_curr.get("Current Assets")
    current_liabilities = balance_curr.get("Current Liabilities")
    total_assets = balance_curr.get("Total Assets")
    invested_capital = balance_curr.get("Invested Capital")

    operating_cash_flow = cash_curr.get("Operating Cash Flow")
    capex = cash_curr.get("Capital Expenditure")
    ebit = income_curr.get("EBIT")
    tax_rate = income_curr.get("Tax Rate For Calcs")

    # --- Calculate ratios ---
    metrics = {}

    # Profitability
    metrics["roe"] = safe_divide(net_income, stockholders_equity)
    metrics["gross_margin"] = safe_divide(gross_profit, total_revenue)
    metrics["operating_margin"] = safe_divide(operating_income, total_revenue)
    metrics["net_margin"] = safe_divide(net_income, total_revenue)

    # ROIC = NOPAT / Invested Capital, where NOPAT = EBIT * (1 - tax rate)
    if ebit is not None and tax_rate is not None:
        nopat = ebit * (1 - tax_rate)
        metrics["roic"] = safe_divide(nopat, invested_capital)
    else:
        metrics["roic"] = None
        errors.append("Could not calculate ROIC - missing EBIT or tax rate")

    # Liquidity
    metrics["current_ratio"] = safe_divide(current_assets, current_liabilities)

    # Leverage
    metrics["debt_to_equity"] = safe_divide(total_debt, stockholders_equity)

    # Growth
    metrics["revenue_growth"] = safe_divide(
        (total_revenue - prior_revenue) if total_revenue and prior_revenue else None,
        prior_revenue
    )

    # Cash flow
    if operating_cash_flow is not None and capex is not None:
        metrics["free_cash_flow"] = operating_cash_flow + capex  # capex is already negative
    else:
        metrics["free_cash_flow"] = None
        errors.append("Could not calculate Free Cash Flow - missing operating cash flow or capex")

    # Check for any None values and log them
    for key, value in metrics.items():
        if value is None and f"Could not calculate {key}" not in str(errors):
            errors.append(f"Metric '{key}' could not be calculated - missing source data")

    return metrics, errors


def run_financial_analysis(market_intelligence_output):
    """
    Main entry point for the Financial Analysis Agent.
    Takes Market Intelligence Agent's output, returns structured ratio analysis.
    """
    ticker = market_intelligence_output.get("ticker", "UNKNOWN")
    metrics, errors = calculate_ratios(market_intelligence_output)

    result = {
        "agent": "financial_analysis",
        "ticker": ticker,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "metrics": metrics,
        "method": "deterministic_calculation",
        "data_quality": {
            "calculation_complete": len(errors) == 0,
            "errors": errors
        }
    }

    return result


if __name__ == "__main__":
    import json
    import sys
    sys.path.append(".")
    from agents.market_intelligence import run_market_intelligence

    mi_output = run_market_intelligence("AAPL")
    fa_output = run_financial_analysis(mi_output)
    print(json.dumps(fa_output, indent=2, default=str))