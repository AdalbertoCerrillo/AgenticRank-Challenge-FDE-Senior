"""Tests for classification fallbacks and routing. The LLM is replaced by a fake
so these run offline; what's tested is our handling of its answers."""

import json

import pytest

from src import route, ticketing_api
from src.classify import classify_ticket


def _ticket(**fields):
    base = {"id": "T-1", "subject": "Double charged", "body": "Charged twice for #1.", "contact_count": 1}
    base.update(fields)
    return base


def _llm_returning(answer):
    calls = []

    def fake(system, prompt):
        calls.append(prompt)
        if isinstance(answer, Exception):
            raise answer
        return answer

    fake.calls = calls
    return fake


def _answer(**fields):
    base = {"category": "billing", "urgency": "urgent", "needs_review": False, "reason": "double charge"}
    base.update(fields)
    return base


def test_clear_answer_is_returned_as_is():
    result = classify_ticket(_ticket(), llm=_llm_returning(_answer(urgency="normal")))
    assert result == _answer(urgency="normal")


def test_ambiguous_ticket_is_forced_to_urgent_for_review():
    result = classify_ticket(_ticket(), llm=_llm_returning(_answer(urgency="normal", needs_review=True)))
    assert result["needs_review"] is True
    assert result["urgency"] == "urgent"
    assert result["category"] == "billing"


def test_llm_error_falls_back_to_urgent_review():
    result = classify_ticket(_ticket(), llm=_llm_returning(RuntimeError("bedrock down")))
    assert result["needs_review"] is True
    assert result["urgency"] == "urgent"
    assert "bedrock down" in result["reason"]


@pytest.mark.parametrize(
    "bad",
    [
        _answer(category="shipping"),
        _answer(urgency="high"),
        {"category": "billing"},
        "not a dict",
    ],
)
def test_invalid_llm_answer_falls_back_to_urgent_review(bad):
    result = classify_ticket(_ticket(), llm=_llm_returning(bad))
    assert result["needs_review"] is True
    assert result["urgency"] == "urgent"


def test_forward_with_no_content_goes_to_review_without_calling_llm():
    llm = _llm_returning(_answer())
    result = classify_ticket(_ticket(subject="order", body=""), llm=llm)
    assert result["needs_review"] is True
    assert result["urgency"] == "urgent"
    assert llm.calls == []


def test_prompt_contains_whole_merged_thread_and_contact_count():
    llm = _llm_returning(_answer())
    classify_ticket(_ticket(body="First message.\n\nStill waiting.", contact_count=2), llm=llm)
    [prompt] = llm.calls
    assert "First message." in prompt and "Still waiting." in prompt
    assert "2" in prompt


# --- Routing ----------------------------------------------------------------


@pytest.mark.parametrize(
    "classification, queue",
    [
        ({"category": "billing", "urgency": "urgent", "needs_review": False}, "urgent"),
        ({"category": "orders", "urgency": "urgent", "needs_review": True}, "urgent"),
        ({"category": "accounts", "urgency": "normal", "needs_review": True}, "urgent"),
        ({"category": "billing", "urgency": "normal", "needs_review": False}, "billing"),
        ({"category": "general", "urgency": "normal", "needs_review": False}, "general"),
    ],
)
def test_queue_selection(classification, queue):
    assert route.queue_for(classification) == queue


def test_route_ticket_pushes_to_ticketing_api(tmp_path, monkeypatch):
    routed = tmp_path / "routed.json"
    monkeypatch.setattr(ticketing_api, "ROUTED_PATH", routed)

    route.route_ticket({"id": "T-9"}, {"category": "orders", "urgency": "urgent", "needs_review": False})

    [record] = json.loads(routed.read_text())
    assert record["ticket_id"] == "T-9" and record["queue"] == "urgent"
