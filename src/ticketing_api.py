"""Mock of Meridian's ticketing API.

Stands in for the real service so you don't need any credentials or network
access. Pushing a ticket appends a record to routed.json in the repo root.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

ROUTED_PATH = Path(__file__).resolve().parent.parent / "routed.json"

# The queues the real ticketing system accepts. Anything else is rejected.
VALID_QUEUES = {"urgent", "billing", "accounts", "orders", "general"}


def push_ticket(ticket: dict, queue: str) -> dict:
    """Push a ticket to a queue. Raises ValueError on an unknown queue."""
    if queue not in VALID_QUEUES:
        raise ValueError(
            f"unknown queue {queue!r}; expected one of {sorted(VALID_QUEUES)}"
        )

    record = {
        "ticket_id": ticket.get("id"),
        "queue": queue,
        "pushed_at": datetime.now(timezone.utc).isoformat(),
    }

    routed = []
    if ROUTED_PATH.exists():
        with open(ROUTED_PATH, encoding="utf-8") as f:
            routed = json.load(f)
    routed.append(record)
    with open(ROUTED_PATH, "w", encoding="utf-8") as f:
        json.dump(routed, f, indent=2)

    return record
