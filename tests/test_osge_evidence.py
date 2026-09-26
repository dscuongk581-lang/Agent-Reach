# -*- coding: utf-8 -*-

import pytest

from agent_reach.osge_evidence import (
    build_article_identity_input,
    build_score_lookup,
    build_vote_payload,
    evidence_signal_contract,
    valid_content_id,
)


CONTENT_ID = "sha256:a185493743179f6ff7aa48e8078156886441ff04f494c741446a2531ac05164d"


def test_contract_keeps_identity_and_voting_separate():
    contract = evidence_signal_contract()
    assert contract["schema"] == "osge.article.v1"
    assert contract["identity_authority"] == "evidence-signal hash"
    assert contract["automatic_identity"] is False
    assert contract["automatic_vote"] is False
    assert contract["requires_full_article"] is True
    assert contract["requires_independent_review_before_vote"] is True
    assert contract["insufficient_evidence"] == "abstain"


def test_article_identity_input_preserves_exact_text():
    title = "  Tiêu đề 😀  "
    body = "\nBody with spaces  \n"
    payload = build_article_identity_input(title=title, body=body)
    assert payload == {"title": title, "body": body}


def test_article_identity_input_rejects_non_utf8_surrogate():
    with pytest.raises(ValueError):
        build_article_identity_input(title="ok", body="bad\ud800")


def test_content_id_shape_is_strict():
    assert valid_content_id(CONTENT_ID)
    assert not valid_content_id(CONTENT_ID.upper())
    assert not valid_content_id("sha256:abc")
    assert not valid_content_id(None)


def test_score_lookup_is_only_a_request_shape():
    assert build_score_lookup(CONTENT_ID) == {
        "method": "GET",
        "path": f"/v1/scores/{CONTENT_ID}",
    }


def test_vote_payload_accepts_only_integer_zero_to_ten():
    assert build_vote_payload(CONTENT_ID, 0) == {
        "content_id": CONTENT_ID,
        "score": 0,
    }
    assert build_vote_payload(CONTENT_ID, 10)["score"] == 10

    for invalid in (-1, 11, 7.5, True, "7"):
        with pytest.raises(ValueError):
            build_vote_payload(CONTENT_ID, invalid)
