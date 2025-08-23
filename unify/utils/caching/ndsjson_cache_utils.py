import json
import warnings
from typing import Any, List, Optional, TextIO


def _load_ndjson_cache(filehandler: TextIO):
    cache = {}

    for line_number, line in enumerate(filehandler, start=1):
        line = line.strip()
        if not line:
            continue
        try:
            item = json.loads(line)
            cache[item["key"]] = {
                "value": item["value"],
                "res_types": item["res_types"],
            }
        except json.JSONDecodeError:
            warnings.warn(
                f"Cache file {filehandler.name} contains invalid cache entry, skipping line {line_number}: {line[:40]}...",
            )

    return cache


def _write_to_ndjson_cache(
    filehandler: TextIO,
    key: str,
    value: Any,
    res_types: Optional[List[str]] = None,
):
    filehandler.write(
        json.dumps(
            {
                "key": key,
                "value": value,
                "res_types": res_types,
            },
        )
        + "\n",
    )
