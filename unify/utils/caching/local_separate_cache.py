import json
import os
from typing import Any, Dict, List, Optional

from unify.utils.caching.base_cache import BaseCache


class LocalSeparateCache(BaseCache):
    """Local cache with separate read and write storage for better performance."""

    _cache_read: Optional[Dict[str, Any]] = None
    _cache_write: Optional[Dict[str, Any]] = None
    _cache_dir: str = os.environ.get("UNIFY_CACHE_DIR", os.getcwd())
    _cache_name_read: str = ".cache.json"
    _cache_name_write: str = ".cache_write.json"
    _enabled: bool = False

    @classmethod
    def set_cache_name(cls, name: str) -> None:
        """Set the cache names and reset both caches."""
        cls._cache_name_read = f"{name}_read"
        cls._cache_name_write = f"{name}_write"
        cls._cache_read = None  # Force reload of read cache
        cls._cache_write = None  # Force reload of write cache

    @classmethod
    def get_cache_name(cls) -> str:
        """Get the current read cache name."""
        return cls._cache_name_read

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
        """Store a key-value pair in the write cache."""
        if res_types:
            cls._cache_write[f"{key}_res_types"] = res_types
        cls._cache_write[key] = value
        cls.write()

    @classmethod
    def write(cls, filename: str = None) -> None:
        """Write the write cache to disk."""
        if cls._cache_write is None:
            return

        cache_filepath = os.path.join(cls._cache_dir, cls._cache_name_write)
        with open(cache_filepath, "w") as outfile:
            json.dump(cls._cache_write, outfile, indent=2)

    @classmethod
    def initialize_cache(cls, name: str = None) -> None:
        """Initialize both read and write caches."""
        # Always initialize the write cache
        if cls._cache_write is None:
            cls._cache_write = {}
            write_filepath = os.path.join(cls._cache_dir, cls._cache_name_write)
            with open(write_filepath, "w") as outfile:
                json.dump({}, outfile)

        # Initialize the read cache
        if cls._cache_read is None:
            cls._cache_read = {}
            read_filepath = os.path.join(cls._cache_dir, cls._cache_name_read)

            try:
                if os.path.exists(read_filepath):
                    with open(read_filepath, "r") as infile:
                        content = infile.read().strip()
                        if content:
                            cls._cache_read = json.loads(content)
            except (json.JSONDecodeError, IOError):
                # File contains invalid JSON or can't be read, keep empty cache
                cls._cache_read = {}

    @classmethod
    def list_keys(cls) -> List[str]:
        return list(cls._cache_read.keys()) + list(cls._cache_write.keys())

    @classmethod
    def retrieve_entry(cls, key: str) -> tuple[Optional[Any], Optional[Dict[str, Any]]]:
        """
        Retrieve a value from the cache, checking write cache first.

        Returns:
            Tuple of (value, res_types) or (None, None) if not found
        """
        # First check the write cache
        if cls._cache_write and key in cls._cache_write:
            value = cls._cache_write[key]
            res_types = cls._cache_write.get(f"{key}_res_types")
            deserialized_value = json.loads(value)
            return deserialized_value, res_types

        # If not found in write cache, check the read cache
        if cls._cache_read and key in cls._cache_read:
            value = cls._cache_read[key]
            res_types = cls._cache_read.get(f"{key}_res_types")

            deserialized_value = json.loads(value)
            # Promote to write cache for faster future access
            cls.store_entry(
                key=key,
                value=cls.serialize_object(deserialized_value),
                res_types=res_types,
            )
            return deserialized_value, res_types

        return None, None

    @classmethod
    def has_key(cls, key: str) -> bool:
        """Check if a key exists in either cache."""
        return (cls._cache_write is not None and key in cls._cache_write) or (
            cls._cache_read is not None and key in cls._cache_read
        )

    @classmethod
    def remove_entry(cls, key: str) -> None:
        """Remove an entry from both caches."""
        if cls._cache_write:
            cls._cache_write.pop(key, None)
            cls._cache_write.pop(f"{key}_res_types", None)
        if cls._cache_read:
            cls._cache_read.pop(key, None)
            cls._cache_read.pop(f"{key}_res_types", None)
        cls.write()
