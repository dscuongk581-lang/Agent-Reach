# -*- coding: utf-8 -*-
"""Caller-side helpers for the optional OSGE Evidence Signal pilot.

This module does not hash articles, call the score service, or submit votes.
The Go `evidence-signal` binary remains the identity and aggregation authority.
Helpers here only preserve exact caller-supplied strings and build strict,
reviewable request shapes for an enrolled agent host.
"""

from __future__ import annotations

import re
from typing import Any, Dict

OSGE_ARTICLE_SCHEMA = "osge.article.v1"
EVIDENCE_HASH_COMMAND = ("evidence-signal", "hash")
_CONTENT_ID_RE = re.compile(r"^sha256:[0-9a-f]{64}$")


def evidence_signal_contract() -> dict:
    """Describe the optional post-cleaning Evidence Signal boundary."""
    return {
        "schema": OSGE_ARTICLE_SCHEMA,
        "identity_authority": "evidence-signal hash",
        "hash_command": list(EVIDENCE_HASH_COMMAND),
        "automatic_identity": False,
        "automatic_vote": False,
        "requires_full_article": True,
        "requires_independent_review_before_vote": True,
        "insufficient_evidence": "abstain",
        "score_range": [0, 10],
    }


def _exact_utf8_string(name: str, value: object) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{name} must be a string")
    try:
        value.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise ValueError(f"{name} must be valid UTF-8 text") from exc
    return value


def build_article_identity_input(*, title: str, body: str) -> Dict[str, str]:
    """Build stdin JSON data for `evidence-signal hash`.

    The strings are returned byte-for-byte equivalent after UTF-8 encoding:
    no trim, lowercase, summary, URL canonicalization, or whitespace rewrite.
    Generic result snippets must not be passed here as an article body.
    """
    return {
        "title": _exact_utf8_string("title", title),
        "body": _exact_utf8_string("body", body),
    }


def valid_content_id(content_id: object) -> bool:
    """Return whether a value matches the public Evidence Signal ID shape."""
    return isinstance(content_id, str) and _CONTENT_ID_RE.fullmatch(content_id) is not None


def build_score_lookup(content_id: str) -> Dict[str, str]:
    """Build the local pilot lookup request without performing network I/O."""
    if not valid_content_id(content_id):
        raise ValueError("invalid Evidence Signal content_id")
    return {
        "method": "GET",
        "path": f"/v1/scores/{content_id}",
    }


def build_vote_payload(content_id: str, score: int) -> Dict[str, Any]:
    """Build a vote body after the enrolled agent has independently reviewed evidence.

    This function does not decide the score and does not send the vote.
    """
    if not valid_content_id(content_id):
        raise ValueError("invalid Evidence Signal content_id")
    if type(score) is not int or score < 0 or score > 10:
        raise ValueError("score must be an integer from 0 to 10")
    return {
        "content_id": content_id,
        "score": score,
    }
