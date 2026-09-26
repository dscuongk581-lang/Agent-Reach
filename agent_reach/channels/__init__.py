# -*- coding: utf-8 -*-
"""Lazy channel registry.

Importing :mod:`agent_reach.channels` must stay cheap. Individual platform
modules are loaded only when their channel is requested; the full doctor path
still materializes every registered channel through :func:`get_all_channels`.

Module-level lazy class exports preserve compatibility with imports such as
`from agent_reach.channels import GitHubChannel`.
"""

from __future__ import annotations

from collections.abc import Iterator, Sequence
from importlib import import_module
from typing import Dict, Optional

from .base import Channel

# Stable doctor/display order. Tuple entries are:
# (channel name, module name, class name)
_CHANNEL_SPECS = (
    ("github", "github", "GitHubChannel"),
    ("twitter", "twitter", "TwitterChannel"),
    ("youtube", "youtube", "YouTubeChannel"),
    ("reddit", "reddit", "RedditChannel"),
    ("facebook", "facebook", "FacebookChannel"),
    ("instagram", "instagram", "InstagramChannel"),
    ("bilibili", "bilibili", "BilibiliChannel"),
    ("xiaohongshu", "xiaohongshu", "XiaoHongShuChannel"),
    ("linkedin", "linkedin", "LinkedInChannel"),
    ("boss", "boss", "BossChannel"),
    ("xiaoyuzhou", "xiaoyuzhou", "XiaoyuzhouChannel"),
    ("v2ex", "v2ex", "V2EXChannel"),
    ("xueqiu", "xueqiu", "XueqiuChannel"),
    ("rss", "rss", "RSSChannel"),
    ("exa_search", "exa_search", "ExaSearchChannel"),
    ("web", "web", "WebChannel"),
)

_BY_NAME = {name: (module, class_name) for name, module, class_name in _CHANNEL_SPECS}
_BY_CLASS = {class_name: (name, module) for name, module, class_name in _CHANNEL_SPECS}
_INSTANCES: Dict[str, Channel] = {}


def _load_class(module_name: str, class_name: str):
    module = import_module(f"{__name__}.{module_name}")
    return getattr(module, class_name)


def get_channel(name: str) -> Optional[Channel]:
    """Get one channel, importing only that platform module on first use."""
    spec = _BY_NAME.get(name)
    if spec is None:
        return None

    cached = _INSTANCES.get(name)
    if cached is not None:
        return cached

    module_name, class_name = spec
    channel_class = _load_class(module_name, class_name)
    instance = channel_class()
    _INSTANCES[name] = instance
    return instance


def get_all_channels() -> list[Channel]:
    """Get all registered channels in the historical doctor/display order."""
    return [get_channel(name) for name, _, _ in _CHANNEL_SPECS]  # type: ignore[list-item]


class _LazyChannelSequence(Sequence[Channel]):
    """Read-only compatibility view for the historical ALL_CHANNELS export."""

    def __len__(self) -> int:
        return len(_CHANNEL_SPECS)

    def __iter__(self) -> Iterator[Channel]:
        return iter(get_all_channels())

    def __getitem__(self, index):
        if isinstance(index, slice):
            names = [name for name, _, _ in _CHANNEL_SPECS][index]
            return [get_channel(name) for name in names]
        name = _CHANNEL_SPECS[index][0]
        channel = get_channel(name)
        assert channel is not None
        return channel

    def __repr__(self) -> str:
        return repr(get_all_channels())


ALL_CHANNELS: Sequence[Channel] = _LazyChannelSequence()


def __getattr__(name: str):
    """Lazily preserve exported channel classes without eager imports."""
    spec = _BY_CLASS.get(name)
    if spec is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    _, module_name = spec
    _, _, class_name = next(item for item in _CHANNEL_SPECS if item[2] == name)
    value = _load_class(module_name, class_name)
    globals()[name] = value
    return value


def __dir__():
    return sorted(set(globals()) | set(_BY_CLASS))


__all__ = [
    "Channel",
    "ALL_CHANNELS",
    "get_channel",
    "get_all_channels",
    *sorted(_BY_CLASS),
]
