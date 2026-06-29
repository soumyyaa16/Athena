import time
import functools


def with_retry(max_attempts=3, base_delay=2, backoff_factor=2):
    """
    Decorator that retries a function on failure with exponential backoff.
    Use this on any function that calls an external API (FMP, NewsAPI, Gemini, yfinance).

    Example:
        @with_retry(max_attempts=3, base_delay=2)
        def fetch_something():
            ...
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_attempts:
                        delay = base_delay * (backoff_factor ** (attempt - 1))
                        time.sleep(delay)
                    else:
                        raise last_exception
        return wrapper
    return decorator


class DataSourceUnavailable(Exception):
    """Raised when a data source fails after all retries, and no fallback exists."""
    pass


def fetch_with_fallback(primary_fn, fallback_fn=None, source_name="unknown"):
    """
    Tries primary_fn first. If it fails, tries fallback_fn if provided.
    Returns (data, source_used, success, error_message).

    Example:
        data, source, ok, err = fetch_with_fallback(
            primary_fn=lambda: fetch_from_fmp(ticker),
            fallback_fn=lambda: fetch_from_yfinance(ticker),
            source_name="company_profile"
        )
    """
    try:
        result = primary_fn()
        return result, "primary", True, None
    except Exception as primary_error:
        if fallback_fn is not None:
            try:
                result = fallback_fn()
                return result, "fallback", True, f"Primary source failed ({source_name}): {str(primary_error)}, used fallback"
            except Exception as fallback_error:
                return None, None, False, f"Both primary and fallback failed for {source_name}. Primary: {str(primary_error)} | Fallback: {str(fallback_error)}"
        else:
            return None, None, False, f"Primary source failed for {source_name} with no fallback available: {str(primary_error)}"