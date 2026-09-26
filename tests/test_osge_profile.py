# -*- coding: utf-8 -*-

import pytest

import agent_reach.osge as osge


class StubConfig:
    pass


class StubChannel:
    def __init__(self, name, status="ok", backend="stub"):
        self.name = name
        self.status = status
        self.backends = [backend]
        self.active_backend = None

    def check(self, config):
        self.active_backend = self.backends[0] if self.status in {"ok", "warn"} else None
        return self.status, f"{self.name} status"


def test_core_profile_is_small_and_explicit():
    assert osge.CORE_CHANNEL_NAMES == (
        "web",
        "exa_search",
        "github",
        "youtube",
        "twitter",
        "reddit",
        "rss",
    )


def test_resolve_prefers_ok_and_hands_off_to_osge(monkeypatch):
    channels = {
        "twitter": StubChannel("twitter", status="off"),
        "reddit": StubChannel("reddit", status="ok", backend="rdt"),
    }
    monkeypatch.setattr(osge, "get_channel", channels.get)

    result = osge.resolve_capability("social", config=StubConfig())

    assert result["selected"]["channel"] == "reddit"
    assert result["selected"]["active_backend"] == "rdt"
    assert result["next_stage"] == "osge-filter"
    assert result["trust_owner"] == "OSGE"
    assert result["trust_score"] is None


def test_resolve_uses_warn_as_degraded_candidate(monkeypatch):
    monkeypatch.setattr(
        osge,
        "get_channel",
        lambda name: StubChannel(name, status="warn", backend="candidate"),
    )
    result = osge.resolve_capability("search", config=StubConfig())
    assert result["selected"]["status"] == "warn"
    assert result["next_stage"] == "osge-filter"


def test_unknown_capability_fails_closed():
    with pytest.raises(ValueError):
        osge.resolve_capability("buy-coffee", config=StubConfig())
