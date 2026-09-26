# -*- coding: utf-8 -*-

import pytest

from agent_reach.osge_handoff import (
    OSGE_MAX_ITEMS,
    build_canonicalize_input,
    build_filter_input,
    canonicalize_input_from_filter_output,
    handoff_contract,
)


def test_contract_is_exactly_existing_osge_mcp_primitives():
    contract = handoff_contract()
    assert contract["order"] == ["osge_filter", "osge_canonicalize"]
    assert contract["retrieval_owner"] == "caller"
    assert contract["trust_score"] is None


def test_filter_input_projects_only_osge_fields_without_inference():
    payload = build_filter_input(
        [
            {
                "id": "one",
                "url": "https://example.com/a?utm_source=x",
                "title": "A",
                "text": "body",
                "provider": "exa",
            },
            {
                "id": "two",
                "url": "https://example.com/b",
                "title": "B",
                "sponsored": True,
                "ranking_score": 0.99,
            },
        ]
    )

    assert payload == {
        "items": [
            {
                "id": "one",
                "url": "https://example.com/a?utm_source=x",
                "title": "A",
                "text": "body",
            },
            {
                "id": "two",
                "url": "https://example.com/b",
                "title": "B",
                "sponsored": True,
            },
        ],
        "remove_sponsored": True,
        "collapse_duplicates": True,
    }
    assert "sponsored" not in payload["items"][0]


def test_filter_input_rejects_non_boolean_sponsored():
    with pytest.raises(ValueError):
        build_filter_input([{"text": "ad-like prose", "sponsored": "maybe"}])


def test_filter_input_rejects_oversized_evidence_instead_of_truncating():
    with pytest.raises(ValueError):
        build_filter_input([{"text": "x" * 32769}])


def test_filter_input_enforces_osge_item_limit():
    with pytest.raises(ValueError):
        build_filter_input([{}] * (OSGE_MAX_ITEMS + 1))


def test_canonicalize_input_is_local_payload_only():
    assert build_canonicalize_input(
        ["/docs?utm_source=x&a=1"],
        base_url="https://example.com/root",
    ) == {
        "urls": ["/docs?utm_source=x&a=1"],
        "base_url": "https://example.com/root",
    }


def test_canonicalize_input_can_follow_filter_output():
    payload = canonicalize_input_from_filter_output(
        {
            "items": [
                {"id": "one", "url": "https://example.com/a?utm_source=x"},
                {"id": "text-only", "text": "evidence"},
                {"id": "two", "url": "https://example.com/b"},
            ]
        }
    )
    assert payload == {
        "urls": [
            "https://example.com/a?utm_source=x",
            "https://example.com/b",
        ]
    }


def test_filter_input_matches_javascript_utf16_limits():
    # JavaScript/Zod counts astral emoji as two UTF-16 code units.
    payload = build_filter_input([{"id": "😀" * 128}])
    assert payload["items"][0]["id"] == "😀" * 128

    with pytest.raises(ValueError):
        build_filter_input([{"id": "😀" * 129}])
