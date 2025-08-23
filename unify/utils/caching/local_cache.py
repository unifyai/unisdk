"""
Local file-based cache implementation.

This cache stores data in a local JSON file and provides fast in-memory access.
"""

import json
import os
import threading
import warnings
from typing import Any, Dict, List, Optional

from unify.utils.caching.base_cache import BaseCache

from .ndsjson_cache_utils import _load_ndjson_cache, _write_to_ndjson_cache


class LocalCache(BaseCache):
    """Local file-based cache implementation."""

    _cache: Optional[Dict[str, Any]] = None
    _cache_dir: str = os.environ.get("UNIFY_CACHE_DIR", os.getcwd())
    _cache_lock: threading.Lock = threading.Lock()
    _cache_filename: str = ".cache.ndjson"
    _enabled: bool = False

    @classmethod
    def set_cache_name(cls, name: str) -> None:
        """Set the cache filename and reset the in-memory cache."""
        cls._cache_filename = name
        cls._cache = None  # Force reload on next access

    @classmethod
    def get_cache_name(cls) -> str:
        """Get the current cache filename."""
        return cls._cache_filename

    @classmethod
    def get_cache_filepath(cls, name: str = None) -> str:
        """Get the full filepath for the cache file."""
        if name is None:
            name = cls.get_cache_name()
        return os.path.join(cls._cache_dir, name)

    @classmethod
    def is_enabled(cls) -> bool:
        """Check if the cache is enabled."""
        return cls._enabled

    @classmethod
    def store_entry(
        cls,
        *,
        key: str,
        value: Any,
        res_types: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Store a key-value pair in the cache."""
        cls._cache[key] = {"value": value, "res_types": res_types}
        with open(cls.get_cache_filepath(), "a") as f:
            _write_to_ndjson_cache(f, key, value, res_types)

    @classmethod
    def initialize_cache(cls, name: str = None) -> None:
        """Initialize or load the cache from disk."""
        cache_filepath = cls.get_cache_filepath(name)

        if cls._cache is None:
            try:
                if not os.path.exists(cache_filepath):
                    with open(cache_filepath, "w") as f:
                        f.write("")

                with open(cache_filepath, "r") as f:
                    cls._cache = _load_ndjson_cache(f)
            except IOError:
                # File does not exist or can't be read, reinitialize
                warnings.warn(
                    f"Cache file {cache_filepath} can't be read, reinitializing",
                )
                cls._cache = {}
                with open(cache_filepath, "w") as f:
                    f.write("")

    @classmethod
    def list_keys(cls) -> List[str]:
        return list(cls._cache.keys())

    @classmethod
    def retrieve_entry(cls, key: str) -> tuple[Optional[Any], Optional[Dict[str, Any]]]:
        """
        Retrieve a value from the cache.

        Returns:
            Tuple of (value, type_registry) or (None, None) if not found
        """
        if cls._cache is None:
            return None, None

        value = cls._cache.get(key)
        if value is None:
            return None, None

        deserialized_value = json.loads(value["value"])
        return deserialized_value, value["res_types"]

    @classmethod
    def has_key(cls, key: str) -> bool:
        """Check if a key exists in the cache."""
        return cls._cache is not None and key in cls._cache

    @classmethod
    def remove_entry(cls, key: str) -> None:
        """Remove an entry and its res_types from the cache."""
        if cls._cache is not None:
            item = cls._cache.pop(key, None)
            if item is not None:
                with open(cls.get_cache_filepath(), "w") as f:
                    for key, value in cls._cache.items():
                        _write_to_ndjson_cache(
                            f,
                            key,
                            value["value"],
                            value["res_types"],
                        )
