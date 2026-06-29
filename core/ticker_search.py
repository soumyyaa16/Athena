import yfinance as yf


PREFERRED_EXCHANGES = {"NMS", "NYQ", "NGM", "PCX"}  # NASDAQ, NYSE variants


def search_ticker(query, max_results=6):
    """
    Takes a company name or ticker string, returns a list of matching
    equity results sorted by relevance (US exchanges first).
    """
    query = query.strip()
    if not query:
        return []

    try:
        result = yf.Search(query, max_results=10)
        quotes = result.quotes
    except Exception as e:
        return []

    equities = [q for q in quotes if q.get("quoteType") == "EQUITY"]

    preferred = [q for q in equities if q.get("exchange") in PREFERRED_EXCHANGES]
    others = [q for q in equities if q.get("exchange") not in PREFERRED_EXCHANGES]
    sorted_results = preferred + others

    output = []
    for q in sorted_results[:max_results]:
        output.append({
            "symbol": q.get("symbol"),
            "name": q.get("longname") or q.get("shortname"),
            "exchange": q.get("exchDisp"),
            "sector": q.get("sectorDisp", "")
        })

    return output


if __name__ == "__main__":
    import json
    tests = ["Apple", "Tesla", "MSFT", "nvidia", "reliance"]
    for t in tests:
        print(f"\nQuery: {t}")
        print(json.dumps(search_ticker(t), indent=2))