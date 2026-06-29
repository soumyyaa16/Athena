import os
import json
from datetime import datetime, timezone
from google import genai
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY)


def score_profitability(metrics):
    """0-100 score based on ROE, ROIC, net margin."""
    roe = metrics.get("roe")
    roic = metrics.get("roic")
    net_margin = metrics.get("net_margin")

    if roe is None or roic is None or net_margin is None:
        return None

    # Simple bucketed scoring against common institutional benchmarks
    roe_score = min(100, max(0, roe * 100))  # ROE of 1.0 (100%) = max score
    roic_score = min(100, max(0, roic * 150))  # ROIC of ~0.67 = max score
    margin_score = min(100, max(0, net_margin * 400))  # 25% net margin = max score

    return round((roe_score + roic_score + margin_score) / 3, 1)


def score_financial_health(metrics):
    """0-100 score based on current ratio and debt/equity."""
    current_ratio = metrics.get("current_ratio")
    debt_to_equity = metrics.get("debt_to_equity")

    if current_ratio is None or debt_to_equity is None:
        return None

    # Current ratio: 2.0 is ideal (100), below 1.0 starts penalizing heavily
    if current_ratio >= 2.0:
        liquidity_score = 100
    elif current_ratio >= 1.0:
        liquidity_score = 60 + (current_ratio - 1.0) * 40
    else:
        liquidity_score = current_ratio * 60

    # Debt/Equity: lower is better, 0 = 100, 2.0+ = 0
    leverage_score = max(0, 100 - (debt_to_equity * 50))

    return round((liquidity_score + leverage_score) / 2, 1)


def score_growth(metrics):
    """0-100 score based on revenue growth."""
    revenue_growth = metrics.get("revenue_growth")
    if revenue_growth is None:
        return None

    # 15%+ growth = max score, negative growth = low score
    score = min(100, max(0, (revenue_growth + 0.05) * 500))
    return round(score, 1)


def score_risk(risk_intelligence_output):
    """0-100 score where higher = lower risk (more favorable)."""
    risk_level = risk_intelligence_output.get("overall_risk_level")
    mapping = {"low": 90, "moderate": 65, "elevated": 35}
    return mapping.get(risk_level, 50)


def calculate_committee_score(financial_analysis_output, risk_intelligence_output):
    """Computes the weighted overall score and per-dimension breakdown."""
    metrics = financial_analysis_output.get("metrics", {})

    profitability = score_profitability(metrics)
    financial_health = score_financial_health(metrics)
    growth = score_growth(metrics)
    risk = score_risk(risk_intelligence_output)

    weights = {
        "profitability": 0.30,
        "financial_health": 0.25,
        "growth": 0.20,
        "risk": 0.25
    }

    scores = {
        "profitability": profitability,
        "financial_health": financial_health,
        "growth": growth,
        "risk": risk
    }

    valid_scores = {k: v for k, v in scores.items() if v is not None}
    if not valid_scores:
        return None, scores, weights

    total_weight = sum(weights[k] for k in valid_scores)
    overall_score = sum(valid_scores[k] * weights[k] for k in valid_scores) / total_weight
    overall_score = round(overall_score, 1)

    return overall_score, scores, weights


def classify_score(overall_score):
    """Maps numeric score to a qualitative band. No buy/sell/hold language."""
    if overall_score is None:
        return "insufficient_data"
    if overall_score >= 75:
        return "strong_fundamentals"
    elif overall_score >= 55:
        return "stable_fundamentals"
    elif overall_score >= 35:
        return "mixed_fundamentals"
    else:
        return "weak_fundamentals"


def build_committee_prompt(ticker, company_name, overall_score, dimension_scores,
                             weights, classification, risk_flags, synthesis_text):
    prompt = f"""You are summarizing the output of a multi-agent investment research system for {company_name} ({ticker}).

You will be given a computed score (already calculated deterministically, NOT by you) and supporting context.

STRICT RULES:
1. Do NOT issue a buy/sell/hold recommendation. This system does not make investment decisions - it informs a human analyst's review.
2. Do NOT change, second-guess, or recalculate the scores provided. Treat them as fixed facts.
3. Your job is ONLY to explain WHY the score is what it is, in plain English, using the data given.
4. Be balanced - mention both strengths and concerns.
5. End with 1-2 sentences listing specific questions a human analyst should investigate further.

COMPUTED OVERALL SCORE: {overall_score} / 100 ({classification})

DIMENSION BREAKDOWN (with weights):
- Profitability ({weights['profitability']*100:.0f}% weight): {dimension_scores['profitability']}
- Financial Health ({weights['financial_health']*100:.0f}% weight): {dimension_scores['financial_health']}
- Growth ({weights['growth']*100:.0f}% weight): {dimension_scores['growth']}
- Risk ({weights['risk']*100:.0f}% weight): {dimension_scores['risk']}

RISK FLAGS IDENTIFIED:
{json.dumps(risk_flags, indent=2)}

PRIOR RESEARCH SYNTHESIS:
{synthesis_text}

TASK:
Write a concise (150-200 word) committee summary explaining this score, written as if briefing a human investment analyst who will make the final call. End with specific follow-up questions for the analyst."""

    return prompt


def run_investment_committee(financial_analysis_output, risk_intelligence_output,
                                research_synthesis_output, market_intelligence_output):
    """
    Main entry point for the Investment Committee Agent.
    Computes a deterministic weighted score, then uses LLM ONLY to explain
    the score in plain English. The LLM cannot alter or override the score.
    """
    ticker = financial_analysis_output.get("ticker", "UNKNOWN")
    company_name = market_intelligence_output.get("company_profile", {}).get("name", ticker)
    risk_flags = risk_intelligence_output.get("risk_flags", [])
    synthesis_text = research_synthesis_output.get("synthesis", "")

    overall_score, dimension_scores, weights = calculate_committee_score(
        financial_analysis_output, risk_intelligence_output
    )
    classification = classify_score(overall_score)

    errors = []
    committee_summary = None

    if overall_score is not None:
        try:
            prompt = build_committee_prompt(
                ticker, company_name, overall_score, dimension_scores,
                weights, classification, risk_flags, synthesis_text
            )
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            committee_summary = response.text
        except Exception as e:
            errors.append(f"LLM summary generation failed: {str(e)}")
    else:
        errors.append("Insufficient data to calculate overall score")

    result = {
        "agent": "investment_committee",
        "ticker": ticker,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "overall_score": overall_score,
        "classification": classification,
        "dimension_scores": dimension_scores,
        "weights": weights,
        "committee_summary": committee_summary,
        "requires_human_approval": True,
        "method": "weighted_deterministic_scoring_with_llm_explanation",
        "data_quality": {
            "score_calculated": overall_score is not None,
            "errors": errors
        }
    }

    return result


if __name__ == "__main__":
    import sys
    sys.path.append(".")
    from agents.market_intelligence import run_market_intelligence
    from agents.financial_analysis import run_financial_analysis
    from agents.risk_intelligence import run_risk_intelligence
    from agents.research_synthesis import run_research_synthesis

    mi_output = run_market_intelligence("AAPL")
    fa_output = run_financial_analysis(mi_output)
    risk_output = run_risk_intelligence(fa_output, mi_output)
    synthesis_output = run_research_synthesis(fa_output, risk_output, mi_output)
    committee_output = run_investment_committee(fa_output, risk_output, synthesis_output, mi_output)

    print(json.dumps(committee_output, indent=2, default=str))