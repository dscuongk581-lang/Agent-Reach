# Agent Reach × OSGE

This fork uses Agent Reach as a thin acquisition router in front of OSGE.

## Boundary

Internet -> Agent Reach -> OSGE -> Agent

Agent Reach answers where and how to acquire information. It must not decide
whether that information is trustworthy. OSGE owns filtering, normalization,
content identity, and trust scoring.

## OSGE core profile

The hot path intentionally contains only seven channels:

- Web
- Exa search
- GitHub
- YouTube
- Twitter/X
- Reddit
- RSS

All other upstream channels remain in the fork for compatibility and future use,
but they are outside the OSGE default path.

## Python API

Use agent_reach.osge.get_osge_status() to inspect the core profile and
agent_reach.osge.resolve_capability("search") to select an acquisition route.

A successful resolution contains next_stage = "osge-filter".
trust_score is always null by design.

## MCP contract

The MCP server exposes:

- get_osge_status: health of the seven OSGE core channels.
- resolve_capability: choose the current route for a generic capability.
- get_status: legacy full Agent Reach doctor status.

This lets Chief/Worker agents discover Internet capabilities without turning
Agent Reach into a second execution engine or a second trust engine.

## Fork policy

Keep upstream channel implementations whenever possible. OSGE-specific behavior
should stay in small integration files so upstream fixes remain easy to merge.
