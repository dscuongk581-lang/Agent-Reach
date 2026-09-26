# Agent Reach × OSGE

This fork uses Agent Reach as a thin acquisition router in front of OSGE.

## Boundary

```text
Internet
   |
Agent Reach        acquisition route only
   |
caller retrieves evidence
   |
OSGE MCP           FILTER -> CANONICALIZE
   |
clean evidence
   |
agent
```

Agent Reach answers where and how to acquire information. It does not decide
whether information is trustworthy and does not add a trust score.

OSGE MCP remains exactly the two primitives defined by OSGE Source of Truth:
`osge_filter` and `osge_canonicalize`. Trust/evidence scoring, when enabled in
the broader OSGE stack, is a separate Evidence Signal track and is not smuggled
into this MCP handoff.

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

## Handoff v0.1

`agent_reach.osge_handoff` mirrors the public OSGE MCP v0.1 input limits:

- at most 128 evidence items
- id: 256 characters
- URL: 8192 characters
- title: 2048 characters
- text: 32768 characters
- sponsored must be an explicit boolean supplied by the caller

The handoff projects richer upstream result objects onto only the fields accepted
by OSGE. It never infers sponsorship from prose and never truncates evidence
silently: an oversized/invalid value fails before the OSGE call.

Typical flow:

```python
from agent_reach.osge import resolve_capability
from agent_reach.osge_handoff import (
    build_filter_input,
    canonicalize_input_from_filter_output,
)

route = resolve_capability("search")
# The agent/caller executes route["selected"] upstream and retrieves evidence.

filter_args = build_filter_input(retrieved_items)
filtered = call_osge("osge_filter", filter_args)

canonicalize_args = canonicalize_input_from_filter_output(filtered)
canonicalized = call_osge("osge_canonicalize", canonicalize_args)
```

The helper only builds local payloads. It does not call OSGE, fetch a URL, store
evidence, or make a network request.

## MCP discovery contract

Agent Reach MCP exposes:

- `get_osge_status`: health of the seven acquisition channels
- `resolve_capability`: select the current upstream acquisition route
- `get_status`: legacy full Agent Reach doctor status

A successful `resolve_capability` response sets `next_stage` to
`osge_filter` and includes the fixed handoff order
`osge_filter -> osge_canonicalize`.

## Fork policy

Keep upstream channel implementations whenever possible. OSGE-specific behavior
stays in small integration files so upstream fixes remain easy to merge.
