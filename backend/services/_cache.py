"""
Shared TTL cache for the data services.

Promoted out of market_service.py, where this originally lived, so the five
services that read the same handful of CSV/parquet files share one
implementation rather than each defining their own copy.

Thread-safe enough for CPython: the GIL makes the dict get/set atomic, and a
duplicate concurrent computation is harmless (both callers produce the same
value; the later write wins).
"""
import functools
import time

TTL_SECONDS = 300   # 5 minutes

_cache: dict = {}


def ttl_cache(fn):
    """Cache a function's return value for TTL_SECONDS, then recompute.

    Keyed on (module, qualified name, args, sorted kwargs), so different
    arguments cache independently. Only use on functions whose arguments are
    hashable.

    The module must be part of the key. Several services deliberately expose the
    same function name — labour_market_service, education_service and
    mismatch_service all define get_overview() — and keying on the bare name
    alone made them collide in this shared dict, so whichever ran first served
    its result to all three.
    """
    cache_key_prefix = (fn.__module__, fn.__qualname__)

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        key = (*cache_key_prefix, args, tuple(sorted(kwargs.items())))
        entry = _cache.get(key)
        if entry and (time.monotonic() - entry[0]) < TTL_SECONDS:
            return entry[1]
        result = fn(*args, **kwargs)
        _cache[key] = (time.monotonic(), result)
        return result
    return wrapper


def clear() -> None:
    """Drop every cached entry, including the ML forecast memo. Used by tests
    and after a retrain."""
    _cache.clear()
    try:
        from ml._memo import clear as clear_ml_memo
        clear_ml_memo()
    except ImportError:
        pass
