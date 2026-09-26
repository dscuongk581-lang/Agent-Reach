# -*- coding: utf-8 -*-
"""Agent Reach MCP server.

The legacy get_status tool remains available. OSGE adds two thin discovery
tools so agents can resolve acquisition capabilities without making Agent Reach
a second execution or trust engine.
"""

import asyncio
import json
import sys

from agent_reach.config import Config
from agent_reach.core import AgentReach
from agent_reach.osge import get_osge_status, resolve_capability
from agent_reach.utils.text import scrub_url_credentials

try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import TextContent, Tool

    HAS_MCP = True
except ImportError:
    HAS_MCP = False


def create_server():
    if not HAS_MCP:
        print(
            "MCP not installed. Install: python -m pip install "
            "'agent-reach[mcp] @ "
            "https://github.com/Panniantong/agent-reach/archive/main.zip'",
            file=sys.stderr,
        )
        sys.exit(1)

    server = Server("agent-reach")
    config = Config(read_only=True)
    eyes = AgentReach(config)

    @server.list_tools()
    async def list_tools():
        return [
            Tool(
                name="get_status",
                description="Get legacy full Agent Reach doctor status.",
                inputSchema={"type": "object", "properties": {}},
            ),
            Tool(
                name="get_osge_status",
                description="Get health for the small OSGE acquisition profile.",
                inputSchema={"type": "object", "properties": {}},
            ),
            Tool(
                name="resolve_capability",
                description="Resolve a generic acquisition capability and hand off trust to OSGE.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "capability": {
                            "type": "string",
                            "description": "read, web, search, code, github, video, youtube, social, twitter, reddit, feeds, or rss",
                        }
                    },
                    "required": ["capability"],
                },
            ),
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict):
        try:
            if name == "get_status":
                result = eyes.doctor_report()
            elif name == "get_osge_status":
                result = get_osge_status(config)
            elif name == "resolve_capability":
                result = resolve_capability(str(arguments.get("capability", "")), config)
            else:
                result = f"Unknown tool: {name}"

            text = (
                json.dumps(result, ensure_ascii=False, indent=2)
                if isinstance(result, (dict, list))
                else str(result)
            )
            return [TextContent(type="text", text=text)]
        except Exception as exc:
            return [
                TextContent(
                    type="text",
                    text=f"Error: {scrub_url_credentials(exc)}",
                )
            ]

    return server


async def main():
    server = create_server()
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
