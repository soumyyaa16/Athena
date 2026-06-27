import os
import requests
import yfinance as yf
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

NEWS_API_KEY = os.getenv("NEWS_API_KEY")
FMP_API_KEY = os.getenv("FMP_API_KEY")


def fetch_company_profile(ticker):
    """Fetch company profile from FMP. Returns (data, success, error)."""
    try:
        url = f"https://financialmodelingprep.com/stable/profile?symbol={ticker}&apikey={FMP_API_KEY}"
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if not data:
            return None, False, "Empty response from FMP"
        company = data[0]
        profile = {
            "name": company.get("companyName"),
            "sector": company.get("sector"),
            "industry": company.get("industry"),
            "ceo": company.get("ceo"),
            "employees": company.get("fullTimeEmployees"),
            "description": company.get("description"),
            "market_cap": company.get("marketCap"),
            "exchange": company.get("exchange")
        }
        return profile, True, None
    except Exception as e:
        return None, False, str(e)

def fetch_financial_statements(ticker):
    """Fetch financial statements from yfinance, keeping 2 periods for YoY comparison."""
    try:
        stock = yf.Ticker(ticker)

        income_stmt = stock.income_stmt
        balance_sheet = stock.balance_sheet
        cash_flow = stock.cashflow

        if income_stmt is None or income_stmt.empty:
            return None, False, "No income statement data available"

        def clean_dict(d):
            return {str(k): (float(v) if v is not None and str(v) != 'nan' else None) for k, v in d.items()}

        def get_period(df, index):
            if df is None or df.empty or index >= df.shape[1]:
                return {}
            return clean_dict(df.iloc[:, index].to_dict())

        statements = {
            "income_statement": {
                "current_period": get_period(income_stmt, 0),
                "prior_period": get_period(income_stmt, 1)
            },
            "balance_sheet": {
                "current_period": get_period(balance_sheet, 0),
                "prior_period": get_period(balance_sheet, 1)
            },
            "cash_flow": {
                "current_period": get_period(cash_flow, 0),
                "prior_period": get_period(cash_flow, 1)
            }
        }

        return statements, True, None
    except Exception as e:
        return None, False, str(e)


def fetch_news(ticker, company_name=None, page_size=10):
    """Fetch recent news from NewsAPI. Returns (data, success, error)."""
    try:
        query = f'"{company_name}"' if company_name else ticker
        url = (
            f"https://newsapi.org/v2/everything?q={query}"
            f"&searchIn=title"
            f"&apiKey={NEWS_API_KEY}&pageSize={page_size}"
            f"&sortBy=publishedAt&language=en"
        )
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        articles = []
        seen_titles = set()
        for article in data.get("articles", []):
            title = article.get("title")
            if title in seen_titles:
                continue
            seen_titles.add(title)
            articles.append({
                "title": title,
                "source": article.get("source", {}).get("name"),
                "published_at": article.get("publishedAt"),
                "url": article.get("url")
            })
        return articles, True, None
    except Exception as e:
        return None, False, str(e)


def run_market_intelligence(ticker):
    """
    Main entry point for the Market Intelligence Agent.
    Returns a structured JSON object matching market_intelligence_schema.json
    """
    ticker = ticker.upper().strip()
    errors = []

    profile, profile_ok, profile_err = fetch_company_profile(ticker)
    if not profile_ok:
        errors.append(f"Profile fetch failed: {profile_err}")
        profile = {}

    company_name = profile.get("name") if profile else None

    financials, financials_ok, financials_err = fetch_financial_statements(ticker)
    if not financials_ok:
        errors.append(f"Financials fetch failed: {financials_err}")
        financials = {"income_statement": {}, "balance_sheet": {}, "cash_flow": {}}

    news, news_ok, news_err = fetch_news(ticker, company_name)
    if not news_ok:
        errors.append(f"News fetch failed: {news_err}")
        news = []

    result = {
        "agent": "market_intelligence",
        "ticker": ticker,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "company_profile": profile,
        "financial_statements": financials,
        "news": news,
        "sources": {
            "profile_source": "FMP",
            "financials_source": "yfinance",
            "news_source": "NewsAPI"
        },
        "data_quality": {
            "profile_fetched": profile_ok,
            "financials_fetched": financials_ok,
            "news_fetched": news_ok,
            "errors": errors
        }
    }

    return result


if __name__ == "__main__":
    import json
    result = run_market_intelligence("AAPL")
    print(json.dumps(result, indent=2, default=str))