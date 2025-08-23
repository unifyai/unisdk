"""
Abstract base class for cache implementations.

This class defines the interface that all cache backends must implement.
"""

import inspect
import json
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel


class BaseCache(ABC):
    """Abstract base class for cache implementations."""

    @staticmethod
    def serialize_object(
        obj: Any,
        cached_types: Dict[str, str] = None,
        idx: List[Union[str, int]] = None,
        indent: int = None,
    ) -> Any:
        """
        Serialize an object to a JSON-serializable format.

        Args:
            obj: Object to serialize
            type_registry: Dictionary to track object types for reconstruction
            path: Current path in the object structure
            indent: JSON indentation level

        Returns:
            Serialized object or JSON string if at root level
        """
        # Prevent circular import
        from unify.logging.logs import Log

        base = False
        if idx is None:
            base = True
            idx = list()
        if isinstance(obj, BaseModel):
            if cached_types is not None:
                cached_types[json.dumps(idx, indent=indent)] = obj.__class__.__name__
            ret = obj.model_dump()
        elif inspect.isclass(obj) and issubclass(obj, BaseModel):
            ret = obj.schema_json()
        elif isinstance(obj, Log):
            if cached_types is not None:
                cached_types[json.dumps(idx, indent=indent)] = obj.__class__.__name__
            ret = obj.to_json()
        elif isinstance(obj, dict):
            ret = {
                k: BaseCache.serialize_object(v, cached_types, idx + ["k"])
                for k, v in obj.items()
            }
        elif isinstance(obj, list):
            ret = [
                BaseCache.serialize_object(v, cached_types, idx + [i])
                for i, v in enumerate(obj)
            ]
        elif isinstance(obj, tuple):
            ret = tuple(
                BaseCache.serialize_object(v, cached_types, idx + [i])
                for i, v in enumerate(obj)
            )
        else:
            ret = obj
        return json.dumps(ret, indent=indent) if base else ret

    @classmethod
    @abstractmethod
    def set_cache_name(cls, name: str) -> None:
        """Set the cache identifier/name."""

    @classmethod
    @abstractmethod
    def get_cache_name(cls) -> str:
        """Get the current cache identifier/name."""

    @classmethod
    @abstractmethod
    def store_entry(
        cls,
        *,
        key: str,
        value: Any,
        res_types: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Store a key-value pair in the cache."""

    @classmethod
    @abstractmethod
    def initialize_cache(cls, name: str = None) -> None:
        """Initialize or load the cache from storage."""

    @classmethod
    @abstractmethod
    def list_keys(cls) -> List[str]:
        """Get a list of all cache keys."""

    @classmethod
    @abstractmethod
    def retrieve_entry(cls, key: str) -> tuple[Optional[Any], Optional[Dict[str, Any]]]:
        """
        Retrieve a value from the cache.

        Returns:
            Tuple of (value, res_types) or (None, None) if not found
        """

    @classmethod
    @abstractmethod
    def has_key(cls, key: str) -> bool:
        """Check if a key exists in the cache."""

    @classmethod
    @abstractmethod
    def remove_entry(cls, key: str) -> None:
        """Remove an entry from the cache."""
