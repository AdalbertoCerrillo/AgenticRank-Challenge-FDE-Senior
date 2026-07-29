"""Entry point: load tickets, classify each, route each, print a summary.

Run it as-is and you'll see every ticket come back as "general / normal" —
classification and routing are still stubs.
"""

from src.ingest import load_tickets
from src.classify import classify_ticket
from src.route import route_ticket


def main() -> None:
    tickets = load_tickets()
    print(f"Loaded {len(tickets)} tickets\n")

    for ticket in tickets:
        classification = classify_ticket(ticket)
        route_ticket(ticket, classification)
        subject = ticket.get("subject") or "(no subject)"
        print(
            f"{ticket.get('id', '?'):>8}  "
            f"{classification['category']:>10} / {classification['urgency']:<8}  "
            f"{subject[:60]}"
        )


if __name__ == "__main__":
    main()
