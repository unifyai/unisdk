"""
Remote cache implementation using the logging system.

This cache stores data remotely using the Unify logging infrastructure.
"""

import json
from typing import Any, Dict, List, Optional

from unify.utils.caching.base_cache import BaseCache


class RemoteCache(BaseCache):
    """Remote cache implementation using the logging system."""

    _remote_context = "UNIFY_CACHE"

    @staticmethod
    def _build_filter_expression(cache_key: str) -> str:
        """Build a filter expression for querying logs."""
        return f"key == {json.dumps(cache_key)}"

    @classmethod
    def set_cache_name(cls, name: str) -> None:
        """Set the remote context name for the cache."""
        cls._remote_context = name

    @classmethod
    def get_cache_name(cls) -> str:
        """Get the current remote context name."""
        return cls._remote_context

    @classmethod
    def store_entry(
        cls,
        *,
        key: str,
        value: Any,
        res_types: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Store a key-value pair in the remote cache."""
        from unify import delete_logs, get_logs, log

        # Remove existing entries with the same key
        existing_logs = get_logs(
            context=cls._remote_context,
            filter=cls._build_filter_expression(key),
            return_ids_only=True,
        )

        if existing_logs:
            delete_logs(logs=existing_logs, context=cls._remote_context)

        # Create new log entry
        entries = {"value": value}
        if res_types:
            entries["res_types"] = json.dumps(res_types)
        log(key=key, context=cls._remote_context, **entries)

    @classmethod
    def write(cls, filename: str = None) -> None:
        """No-op for remote cache - data is persisted immediately."""

    @classmethod
    def initialize_cache(cls, name: str = None) -> None:
        """Ensure the remote context exists."""
        from unify import create_context, get_contexts

        if cls._remote_context not in get_contexts():
            create_context(cls._remote_context)

    @classmethod
    def list_keys(cls) -> List[str]:
        """Get a list of all cache keys from the remote context."""
        from unify import get_logs

        logs = get_logs(context=cls._remote_context)
        return [log.entries["key"] for log in logs]

    @classmethod
    def retrieve_entry(cls, key: str) -> tuple[Optional[Any], Optional[Dict[str, Any]]]:
        """
        Retrieve a value from the remote cache.

        Returns:
            Tuple of (value, res_types) or (None, None) if not found
        """
        from unify import get_logs

        logs = get_logs(
            context=cls._remote_context,
            filter=cls._build_filter_expression(key),
        )

        if not logs:
            return None, None

        entry = logs[0].entries
        value = json.loads(entry["value"])
        res_types = None

        if "res_types" in entry:
            res_types = json.loads(entry["res_types"])

        return value, res_types

    @classmethod
    def has_key(cls, key: str) -> bool:
        """Check if a key exists in the remote cache."""
        from unify import get_logs

        logs = get_logs(
            context=cls._remote_context,
            filter=cls._build_filter_expression(key),
            return_ids_only=True,
        )
        return len(logs) > 0

    @classmethod
    def remove_entry(cls, key: str) -> None:
        """Remove an entry from the remote cache."""
        from unify import delete_logs, get_logs

        logs = get_logs(
            context=cls._remote_context,
            filter=cls._build_filter_expression(key),
            return_ids_only=True,
        )
        if logs:
            delete_logs(context=cls._remote_context, logs=logs)
