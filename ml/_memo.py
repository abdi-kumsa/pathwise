"""
Request-path memoisation for the Ethiopia forecast functions.

Every Model 1/2/3 widget re-runs the same per-series fits (152 enrollment
series, 224 employment series, 112 vacancy series). One page view could call
`forecast_unconstrained` three or four times through different paths, and
`forecast_employment` alone takes ~6 s. Results only change when the parquets
change, so they are cached for TTL_SECONDS, matching the dataset reader cache
in backend/services/_datasets.py.

Two properties matter more than the hit rate:

* Callers receive a copy. Many call sites add columns to the frame they get
  back; without a copy one request would corrupt the next request's input.
* Concurrent misses on the same key compute once. Without the per-key lock,
  N simultaneous cold requests run N identical fits that fight over the GIL,
  which is why latency grew roughly tenfold with three users.

Calls with an unhashable argument (e.g. a scenario passing its own DataFrame)
bypass the cache entirely.

TTL is longer than the 5-minute dataset cache because the inputs only change
when a parquet is replaced, which is followed by a restart or clear(). It is
a ceiling on staleness, not a freshness requirement.
"""
from __future__ import annotations

import copy
import functools
import threading
import time

import pandas as pd

TTL_SECONDS = 1800

_store: dict = {}
_locks: dict = {}
_locks_guard = threading.Lock()


def _copy(value):
    if isinstance(value, pd.DataFrame):
        return value.copy(deep=True)
    if isinstance(value, (dict, list, tuple)):
        return copy.deepcopy(value)
    return value


def _lock_for(key) -> threading.Lock:
    with _locks_guard:
        lock = _locks.get(key)
        if lock is None:
            lock = _locks[key] = threading.Lock()
        return lock


def memo(fn):
    """Cache `fn` for TTL_SECONDS keyed on its arguments; return copies."""
    prefix = (fn.__module__, fn.__qualname__)

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        key = (*prefix, args, tuple(sorted(kwargs.items())))
        try:
            hash(key)
        except TypeError:
            return fn(*args, **kwargs)

        entry = _store.get(key)
        if entry and (time.monotonic() - entry[0]) < TTL_SECONDS:
            return _copy(entry[1])

        with _lock_for(key):
            # Another thread may have filled it while this one waited.
            entry = _store.get(key)
            if entry and (time.monotonic() - entry[0]) < TTL_SECONDS:
                return _copy(entry[1])
            result = fn(*args, **kwargs)
            _store[key] = (time.monotonic(), result)
            return _copy(result)

    wrapper.uncached = fn
    return wrapper


def clear() -> None:
    """Drop every cached result. Call after a retrain or a data refresh."""
    _store.clear()
