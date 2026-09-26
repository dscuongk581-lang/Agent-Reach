# -*- coding: utf-8 -*-
"""OSGE acquisition profile for Agent Reach.

Resolve information-acquisition capabilities to healthy Agent Reach channels.
This module never scores trust. It only routes acquisition and describes the
handoff to OSGE's existing local MCP primitives.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from agent_reach.channels import get_channel
from agent_reach.config import Config
from agent_reach.osge_handoff import handoff_contract
from agent_reach.utils.text import scrub_url_credentials

OSGE_PROFILE = "osge-core-v1"

CORE_CHANNEL_NAMES: Tuple[str, ...] = (
    "web",
    "exa_search",
    "github",
    "youtube",
    "twitter",
    "reddit",
    "rss",
)

CAPABILITY_ROUTES: Dict[str, Tuple[str, ...]] = {
    "read": ("web",),
    "web": ("web",),
    "search": ("exa_search",),
    "code": ("github",),
    "github": ("github",),
    "video": ("youtube",),
    "youtube": ("youtube",),
    "social": ("twitter", "reddit"),
    "twitter": ("twitter",),
    "reddit": ("reddit",),
    "feeds": ("rss",),
    "rss": ("rss",),
}


def _probe_channel(name: str, config: Config) -> dict:
    """Probe one channel without leaking stale backend state or credentials."""
    channel = get_channel(name)
    if channel is None:
        return {
            "channel": name,
            "status": "off",
            "active_backend": None,
            "message": "channel not registered",
        }

    channel.active_backend = None
    try:
        status, message = channel.check(config)
        active = getattr(channel, "active_backend", None)
    except Exception as exc:
        status = "error"
        message = f"probe failed: {exc}"
        active = None

    return {
        "channel": name,
        "status": status,
        "active_backend": active,
        "message": scrub_url_credentials(str(message)),
    }


def get_osge_status(config: Optional[Config] = None) -> dict:
    """Return health for only the OSGE hot-path channels."""
    cfg = config or Config(read_only=True)
    channels: List[dict] = [_probe_channel(name, cfg) for name in CORE_CHANNEL_NAMES]
    return {
        "profile": OSGE_PROFILE,
        "channels": channels,
        "handoff": handoff_contract(),
    }


def resolve_capability(capability: str, config: Optional[Config] = None) -> dict:
    """Resolve a generic capability to the first usable acquisition channel."""
    key = capability.strip().lower()
    if key not in CAPABILITY_ROUTES:
        supported = ", ".join(sorted(CAPABILITY_ROUTES))
        raise ValueError(f"unsupported capability '{capability}'. supported: {supported}")

    cfg = config or Config(read_only=True)
    candidates = [_probe_channel(name, cfg) for name in CAPABILITY_ROUTES[key]]

    selected = next((item for item in candidates if item["status"] == "ok"), None)
    if selected is None:
        selected = next((item for item in candidates if item["status"] == "warn"), None)

    return {
        "profile": OSGE_PROFILE,
        "capability": key,
        "selected": selected,
        "candidates": candidates,
        "next_stage": "osge_filter" if selected else None,
        "handoff": handoff_contract(),
    }
