import functools
import os
import warnings
from dataclasses import dataclass


@dataclass
class CacheStats:
    hits: int = 0
    misses: int = 0
    reads: int = 0
    writes: int = 0

    def get_percentage_of_cache_hits(self) -> float:
        if self.reads == 0:
            return 0.0
        return self.hits / self.reads * 100

    def get_percentage_of_cache_misses(self) -> float:
        if self.reads == 0:
            return 0.0
        return self.misses / self.reads * 100

    def __repr__(self) -> str:
        return f"CacheStats(hits={self.hits} ({self.get_percentage_of_cache_hits():.1f}%), misses={self.misses} ({self.get_percentage_of_cache_misses():.1f}%), reads={self.reads}, writes={self.writes})"

    def __add__(self, other: "CacheStats") -> "CacheStats":
        return CacheStats(
            hits=self.hits + other.hits,
            misses=self.misses + other.misses,
            reads=self.reads + other.reads,
            writes=self.writes + other.writes,
        )


CURRENT_CACHE_STATS = CacheStats()


def _is_cache_benchmark_enabled() -> bool:
    return os.environ.get("UNIFY_CACHE_BENCHMARK", "false") == "true"


def get_cache_stats() -> CacheStats:
    if not _is_cache_benchmark_enabled():
        warnings.warn(
            "Cache benchmark is not enabled, set UNIFY_CACHE_BENCHMARK=true to enable it, must be set before importing unify.",
        )
    return CURRENT_CACHE_STATS


def reset_cache_stats() -> None:
    global CURRENT_CACHE_STATS
    CURRENT_CACHE_STATS = CacheStats()


def record_get_cache(fn):
    if not _is_cache_benchmark_enabled():
        return fn
    else:

        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            benchmark = get_cache_stats()
            benchmark.reads += 1
            ret = fn(*args, **kwargs)
            if ret is None:
                benchmark.misses += 1
            else:
                benchmark.hits += 1
            return ret

        return wrapper


def record_write_to_cache(fn):
    if not _is_cache_benchmark_enabled():
        return fn
    else:

        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            benchmark = get_cache_stats()
            benchmark.writes += 1
            return fn(*args, **kwargs)

        return wrapper
