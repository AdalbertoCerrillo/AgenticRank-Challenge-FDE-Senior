"""Route a classified ticket to the right queue.

STATUS: not implemented. Nothing is wired up yet.
"""

from .ticketing_api import push_ticket  # noqa: F401  (available for when this is built)


def route_ticket(ticket: dict, classification: dict) -> None:
    """Send a ticket to the appropriate queue based on its classification."""
    # TODO: decide the target queue from the classification and push the ticket
    # via ticketing_api.push_ticket(ticket, queue). Urgent tickets must never
    # end up in the general queue.
    return None
