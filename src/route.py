"""Route a classified ticket to the right queue.

Urgent and needs-review tickets always go to the urgent queue; everything else
goes to its category queue. Urgent tickets never end up in the general queue.
"""

from .ticketing_api import push_ticket


def queue_for(classification: dict) -> str:
    """Pick the target queue for a classification."""
    if classification.get("needs_review") or classification.get("urgency") == "urgent":
        return "urgent"
    return classification["category"]


def route_ticket(ticket: dict, classification: dict) -> dict:
    """Send a ticket to the appropriate queue based on its classification."""
    return push_ticket(ticket, queue_for(classification))
