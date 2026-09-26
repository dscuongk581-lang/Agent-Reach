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

`agent_reach.osge_handoff` mirrors the public OSGE MCP v0.1 input limits exactly. String limits are measured as UTF-16 code units, matching TypeScript/Zod:

- at most 128 evidence items
- id: 256 UTF-16 code units
- URL: 8192 UTF-16 code units
- title: 2048 UTF-16 code units
- text: 32768 UTF-16 code units
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


## Optional Evidence Signal stage

Evidence Signal is deliberately separate from the OSGE MCP cleaning path.

After FILTER + CANONICALIZE, an enrolled research agent may create a content
identity only when it has a **fully extracted article**. A generic search result,
snippet, social post preview, or provider ranking record is not automatically an
Evidence Signal article.

Use `agent_reach.osge_evidence.build_article_identity_input(title=..., body=...)`
to preserve the exact extracted strings, then pass that JSON to the local
canonical command:

```text
evidence-signal hash
```

Agent Reach does not implement the hash algorithm itself. The Go command remains
the authority for `osge.article.v1`, preventing cross-language identity drift.

The same helper module can validate a returned content ID and build the strict
lookup/vote request shapes, but it never calls the score service and never
chooses a score. Voting requires independent evidence review; insufficient
evidence means abstain, not zero.

```text
clean evidence
   |
full article extraction only
   v
exact title + body
   |
evidence-signal hash
   v
content_id
   |
optional mean lookup
   |
independent review
   |
optional 0..10 vote
```
