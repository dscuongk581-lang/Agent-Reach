# -*- coding: utf-8 -*-
"""Strict caller-side handoff helpers for the OSGE MCP v0.1 contract.

Agent Reach owns acquisition routing only. These helpers merely shape caller-
supplied evidence for OSGE's existing local FILTER/CANONICALIZE primitives.
They do not fetch, infer sponsorship, score trust, persist evidence, or contact
a network.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, Dict, List, Optional

OSGE_MCP_ADAPTER = "osge-mcp-v0.1"
OSGE_FILTER_TOOL = "osge_filter"
OSGE_CANONICALIZE_TOOL = "osge_canonicalize"
OSGE_MAX_ITEMS = 128

_STRING_LIMITS = {
    "id": 256,
    "url": 8192,
    "title": 2048,
    "text": 32768,
}
_ALLOWED_ITEM_FIELDS = ("id", "url", "title", "text", "sponsored")


def handoff_contract() -> dict:
    """Describe the fixed OSGE MCP v0.1 handoff without adding new tools."""
    return {
        "adapter": OSGE_MCP_ADAPTER,
        "filter_tool": OSGE_FILTER_TOOL,
        "canonicalize_tool": OSGE_CANONICALIZE_TOOL,
        "order": [OSGE_FILTER_TOOL, OSGE_CANONICALIZE_TOOL],
        "retrieval_owner": "caller",
        "trust_owner": "OSGE",
        "trust_score": None,
    }


def _require_bool(name: str, value: object) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{name} must be a boolean")
    return value


def _require_string(name: str, value: object, limit: int) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{name} must be a string")
    try:
        # Zod/JavaScript string max() uses UTF-16 code units, not Python code points.
        units = len(value.encode("utf-16-le")) // 2
    except UnicodeEncodeError as exc:
        raise ValueError(f"{name} must be valid Unicode") from exc
    if units > limit:
        raise ValueError(
            f"{name} exceeds OSGE MCP limit ({limit} UTF-16 code units)"
        )
    return value


def _validate_item(item: object, index: int) -> Dict[str, Any]:
    if not isinstance(item, Mapping):
        raise ValueError(f"items[{index}] must be an object")

    # OSGE MCP uses a strict schema. Upstream result objects are often richer,
    # so the handoff deliberately projects only the fields OSGE accepts.
    result: Dict[str, Any] = {}
    for field in _ALLOWED_ITEM_FIELDS:
        if field not in item:
            continue
        value = item[field]
        if field == "sponsored":
            result[field] = _require_bool(f"items[{index}].sponsored", value)
        else:
            result[field] = _require_string(
                f"items[{index}].{field}", value, _STRING_LIMITS[field]
            )
    return result


def build_filter_input(
    items: Sequence[Mapping[str, object]],
    *,
    remove_sponsored: bool = True,
    collapse_duplicates: bool = True,
) -> dict:
    """Build input for osge_filter from already-retrieved evidence.

    sponsored is copied only when the caller explicitly supplied a boolean.
    No prose analysis or sponsorship inference happens here.
    """
    if isinstance(items, (str, bytes, bytearray)) or not isinstance(items, Sequence):
        raise ValueError("items must be a sequence of evidence objects")
    if len(items) > OSGE_MAX_ITEMS:
        raise ValueError(f"items exceeds OSGE MCP limit ({OSGE_MAX_ITEMS})")

    return {
        "items": [_validate_item(item, i) for i, item in enumerate(items)],
        "remove_sponsored": _require_bool("remove_sponsored", remove_sponsored),
        "collapse_duplicates": _require_bool("collapse_duplicates", collapse_duplicates),
    }


def build_canonicalize_input(
    urls: Sequence[str],
    *,
    base_url: Optional[str] = None,
) -> dict:
    """Build input for osge_canonicalize without resolving or fetching URLs."""
    if isinstance(urls, (str, bytes, bytearray)) or not isinstance(urls, Sequence):
        raise ValueError("urls must be a sequence of strings")
    if len(urls) > OSGE_MAX_ITEMS:
        raise ValueError(f"urls exceeds OSGE MCP limit ({OSGE_MAX_ITEMS})")

    payload: Dict[str, object] = {
        "urls": [
            _require_string(f"urls[{i}]", value, _STRING_LIMITS["url"])
            for i, value in enumerate(urls)
        ]
    }
    if base_url is not None:
        payload["base_url"] = _require_string(
            "base_url", base_url, _STRING_LIMITS["url"]
        )
    return payload


def canonicalize_input_from_filter_output(output: Mapping[str, object]) -> dict:
    """Prepare CANONICALIZE input from the kept items of an OSGE FILTER result."""
    items = output.get("items")
    if not isinstance(items, list):
        raise ValueError("filter output must contain an items array")

    urls: List[str] = []
    for index, item in enumerate(items):
        if not isinstance(item, Mapping):
            raise ValueError(f"filter output items[{index}] must be an object")
        value = item.get("url")
        if value is not None:
            urls.append(_require_string(
                f"filter output items[{index}].url", value, _STRING_LIMITS["url"]
            ))
    return build_canonicalize_input(urls)
