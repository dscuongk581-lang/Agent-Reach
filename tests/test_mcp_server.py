"""Security boundaries for the optional Agent Reach MCP server."""

import asyncio
from types import SimpleNamespace

import agent_reach.integrations.mcp_server as mcp_server


class _FakeServer:
    def __init__(self, name):
        self.name = name
        self.list_tools_handler = None
        self.call_tool_handler = None

    def list_tools(self):
        def register(handler):
            self.list_tools_handler = handler
            return handler

        return register

    def call_tool(self):
        def register(handler):
            self.call_tool_handler = handler
            return handler

        return register


def _install_fake_mcp(monkeypatch):
    monkeypatch.setattr(mcp_server, "HAS_MCP", True)
    monkeypatch.setattr(mcp_server, "Server", _FakeServer, raising=False)
    monkeypatch.setattr(
        mcp_server,
        "Tool",
        lambda **kwargs: SimpleNamespace(**kwargs),
        raising=False,
    )
    monkeypatch.setattr(
        mcp_server,
        "TextContent",
        lambda **kwargs: SimpleNamespace(**kwargs),
        raising=False,
    )


def test_mcp_status_uses_read_only_config(monkeypatch):
    _install_fake_mcp(monkeypatch)
    created_configs = []

    class _RecordingConfig:
        def __init__(self, *, read_only=False):
            self.read_only = read_only
            created_configs.append(self)

    class _AgentReach:
        def __init__(self, config):
            self.config = config

        def doctor_report(self):
            return "ok"

    monkeypatch.setattr(mcp_server, "Config", _RecordingConfig)
    monkeypatch.setattr(mcp_server, "AgentReach", _AgentReach)

    server = mcp_server.create_server()
    result = asyncio.run(server.call_tool_handler("get_status", {}))

    assert len(created_configs) == 1
    assert created_configs[0].read_only is True
    assert result[0].text == "ok"


def test_mcp_status_exception_credentials_are_scrubbed(monkeypatch):
    _install_fake_mcp(monkeypatch)

    class _Config:
        def __init__(self, *, read_only=False):
            self.read_only = read_only

    class _ExplodingAgentReach:
        def __init__(self, config):
            self.config = config

        def doctor_report(self):
            raise RuntimeError(
                "request https://alice:password@example.test/data"
                "?token=top-secret failed"
            )

    monkeypatch.setattr(mcp_server, "Config", _Config)
    monkeypatch.setattr(mcp_server, "AgentReach", _ExplodingAgentReach)

    server = mcp_server.create_server()
    result = asyncio.run(server.call_tool_handler("get_status", {}))
    text = result[0].text

    assert "alice" not in text
    assert "password" not in text
    assert "top-secret" not in text
    assert "https://***@example.test/data?token=***" in text


def test_mcp_exposes_osge_discovery_tools(monkeypatch):
    _install_fake_mcp(monkeypatch)

    class _Config:
        def __init__(self, *, read_only=False):
            self.read_only = read_only

    class _AgentReach:
        def __init__(self, config):
            self.config = config

        def doctor_report(self):
            return "ok"

    monkeypatch.setattr(mcp_server, "Config", _Config)
    monkeypatch.setattr(mcp_server, "AgentReach", _AgentReach)

    server = mcp_server.create_server()
    tools = asyncio.run(server.list_tools_handler())
    names = {tool.name for tool in tools}

    assert {"get_status", "get_osge_status", "resolve_capability"} <= names


def test_mcp_resolve_capability_uses_read_only_config(monkeypatch):
    _install_fake_mcp(monkeypatch)
    seen = {}

    class _Config:
        def __init__(self, *, read_only=False):
            self.read_only = read_only

    class _AgentReach:
        def __init__(self, config):
            self.config = config

        def doctor_report(self):
            return "ok"

    def _resolve(capability, config):
        seen["capability"] = capability
        seen["read_only"] = config.read_only
        return {"selected": {"channel": "web"}, "trust_score": None}

    monkeypatch.setattr(mcp_server, "Config", _Config)
    monkeypatch.setattr(mcp_server, "AgentReach", _AgentReach)
    monkeypatch.setattr(mcp_server, "resolve_capability", _resolve)

    server = mcp_server.create_server()
    result = asyncio.run(
        server.call_tool_handler("resolve_capability", {"capability": "read"})
    )

    assert seen == {"capability": "read", "read_only": True}
    assert '"trust_score": null' in result[0].text
