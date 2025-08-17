"""
Local file-based cache implementation.

This cache stores data in a local JSON file and provides fast in-memory access.
"""

import json
import os
import threading
from typing import Any, Dict, List, Optional

from unify.utils.caching.base_cache import BaseCache


class LocalCache(BaseCache):
    """Local file-based cache implementation."""

    _cache: Optional[Dict[str, Any]] = None
    _cache_dir: str = os.environ.get("UNIFY_CACHE_DIR", os.getcwd())
    _cache_lock: threading.Lock = threading.Lock()
    _cache_filename: str = ".cache.json"
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
        if res_types:
            cls._cache[f"{key}_res_types"] = res_types
        cls._cache[key] = value
        cls.write()

    @classmethod
    def write(cls, filename: str = None) -> None:
        """Write the cache to disk."""
        cache_filepath = cls.get_cache_filepath(filename)
        with open(cache_filepath, "w") as outfile:
            json.dump(cls._cache, outfile, indent=2)

    @classmethod
    def initialize_cache(cls, name: str = None) -> None:
        """Initialize or load the cache from disk."""
        cache_filepath = cls.get_cache_filepath(name)

        if cls._cache is None:
            # Create cache file if it doesn't exist
            if not os.path.exists(cache_filepath):
                with open(cache_filepath, "w") as outfile:
                    json.dump({}, outfile)
                cls._cache = {}
                return

            # Load existing cache
            try:
                with open(cache_filepath, "r") as infile:
                    content = infile.read().strip()
                    if not content:
                        # File is empty, initialize with empty dict
                        cls._cache = {}
                    else:
                        # Parse the JSON content
                        cls._cache = json.loads(content)
            except (json.JSONDecodeError, IOError):
                # File contains invalid JSON or can't be read, reinitialize
                cls._cache = {}

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

        deserialized_value = json.loads(value)
        res_types = cls._cache.get(f"{key}_res_types")
        return deserialized_value, res_types

    @classmethod
    def has_key(cls, key: str) -> bool:
        """Check if a key exists in the cache."""
        return cls._cache is not None and key in cls._cache

    @classmethod
    def remove_entry(cls, key: str) -> None:
        """Remove an entry and its res_types from the cache."""
        if cls._cache is not None:
            del cls._cache[key]
            del cls._cache[f"{key}_res_types"]
            cls.write()
