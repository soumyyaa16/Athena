import os
import json
from datetime import datetime, timezone
from google import genai
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY)


def build_synthesis_prompt(ticker, company_name, metrics, risk_flags, news_articles):
    """
    Builds a strict, evidence-bounded prompt. The LLM is given ONLY this
    structured data and instructed not to introduce outside facts or numbers.
    """
    news_titles = [article.get("title") for article in news_articles[:7]]

    prompt = f"""You are an equity research analyst assistant. You will be given structured financial data, risk flags, and recent news headlines for {company_name} ({ticker}).

STRICT RULES:
1. Use ONLY the data provided below. Do not introduce any numbers, facts, or events not present in this data.
2. If you are uncertain or the data is insufficient for a conclusion, say so explicitly.
3. Do not give a buy/sell/hold recommendation. That is not your role.
4. Every claim you make must be traceable to the data below.

FINANCIAL METRICS:
{json.dumps(metrics, indent=2)}

RISK FLAGS:
{json.dumps(risk_flags, indent=2)}

RECENT NEWS HEADLINES:
{json.dumps(news_titles, indent=2)}

TASK:
Produce a structured analysis with exactly these three sections:

CATALYSTS: (2-4 bullet points on what could drive the business forward, based only on the data above)
OPPORTUNITIES: (2-4 bullet points on areas of strength visible in the data above)
THREATS: (2-4 bullet points on risks or concerns, prioritizing the risk flags provided)

Respond in plain text with clear section headers. Do not add any other commentary."""

    return prompt


def run_research_synthesis(financial_analysis_output, risk_intelligence_output, market_intelligence_output):
    """
    Main entry point for the Research Synthesis Agent.
    Synthesizes structured data into catalysts/opportunities/threats using Gemini.
    LLM has no access to raw APIs - only the structured data passed in below.
    """
    ticker = financial_analysis_output.get("ticker", "UNKNOWN")
    company_name = market_intelligence_output.get("company_profile", {}).get("name", ticker)
    metrics = financial_analysis_output.get("metrics", {})
    risk_flags = risk_intelligence_output.get("risk_flags", [])
    news_articles = market_intelligence_output.get("news", [])

    errors = []
    synthesis_text = None

    try:
        prompt = build_synthesis_prompt(ticker, company_name, metrics, risk_flags, news_articles)
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        synthesis_text = response.text
    except Exception as e:
        errors.append(f"LLM synthesis failed: {str(e)}")
        synthesis_text = None

    result = {
        "agent": "research_synthesis",
        "ticker": ticker,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "synthesis": synthesis_text,
        "inputs_used": {
            "metrics_provided": list(metrics.keys()),
            "risk_flags_provided": len(risk_flags),
            "news_headlines_provided": min(len(news_articles), 7)
        },
        "method": "llm_synthesis_constrained",
        "data_quality": {
            "synthesis_generated": synthesis_text is not None,
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

    mi_output = run_market_intelligence("AAPL")
    fa_output = run_financial_analysis(mi_output)
    risk_output = run_risk_intelligence(fa_output, mi_output)
    synthesis_output = run_research_synthesis(fa_output, risk_output, mi_output)

    print(json.dumps(synthesis_output, indent=2, default=str))