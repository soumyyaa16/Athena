def reconcile_values(value_a, source_a, value_b, source_b, field_name, tolerance_pct=5.0):
    """
    Compares two values for the same field from different sources.
    Returns the primary value, plus a note if there's a significant discrepancy.

    This is used when we have overlapping data (e.g. market cap from both
    FMP and yfinance) and want to flag disagreements rather than silently
    picking one and hiding the conflict.
    """
    if value_a is None and value_b is None:
        return None, {"field": field_name, "status": "both_missing"}

    if value_a is None:
        return value_b, {"field": field_name, "status": "used_secondary", "source_used": source_b}

    if value_b is None:
        return value_a, {"field": field_name, "status": "used_primary", "source_used": source_a}

    if value_a == 0 and value_b == 0:
        return value_a, {"field": field_name, "status": "agree", "source_used": source_a}

    if value_a == 0 or value_b == 0:
        return value_a, {"field": field_name, "status": "discrepancy_zero", "source_used": source_a,
                          "primary_value": value_a, "secondary_value": value_b}

    pct_diff = abs(value_a - value_b) / max(abs(value_a), abs(value_b)) * 100

    if pct_diff <= tolerance_pct:
        return value_a, {"field": field_name, "status": "agree", "source_used": source_a, "pct_diff": round(pct_diff, 2)}
    else:
        return value_a, {
            "field": field_name,
            "status": "discrepancy",
            "source_used": source_a,
            "primary_value": value_a,
            "secondary_value": value_b,
            "primary_source": source_a,
            "secondary_source": source_b,
            "pct_diff": round(pct_diff, 2)
        }


def reconcile_company_profile(fmp_data, yfinance_data):
    """
    Reconciles overlapping fields between FMP profile and yfinance info.
    Returns the reconciled profile dict plus a reconciliation log.
    """
    log = []
    reconciled = dict(fmp_data) if fmp_data else {}

    if yfinance_data:
        fmp_market_cap = fmp_data.get("market_cap") if fmp_data else None
        yf_market_cap = yfinance_data.get("marketCap")

        value, note = reconcile_values(
            fmp_market_cap, "FMP", yf_market_cap, "yfinance", "market_cap"
        )
        reconciled["market_cap"] = value
        log.append(note)

    return reconciled, log