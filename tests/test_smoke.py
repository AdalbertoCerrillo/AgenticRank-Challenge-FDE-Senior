"""Smoke test for the data loader. Nothing about classification quality —
that's for you to build and verify."""

from src.ingest import load_tickets


def test_load_tickets_returns_nonempty_list():
    tickets = load_tickets()
    assert isinstance(tickets, list)
    assert len(tickets) > 0
