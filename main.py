"""Entry point: load tickets, classify each, route each, print a summary.

Tickets are cleaned and merged first (src.clean), classified by the LLM
(src.classify), then pushed to the mock ticketing API (writes routed.json).
"""

from collections import Counter

from src.ingest import load_tickets
from src.clean import clean_tickets
from src.classify import classify_ticket
from src.route import route_ticket


def main() -> None:
    raw = load_tickets()
    tickets = clean_tickets(raw)
    print(f"Loaded {len(raw)} records -> {len(tickets)} tickets after cleaning and merging\n")

    queues = Counter()
    for ticket in tickets:
        classification = classify_ticket(ticket)
        record = route_ticket(ticket, classification)
        queues[record["queue"]] += 1
        subject = ticket.get("subject") or "(no subject)"
        review = "REVIEW" if classification["needs_review"] else ""
        print(
            f"{ticket.get('id', '?'):>8}  "
            f"{classification['category']:>10} / {classification['urgency']:<8} {review:<6} "
            f"-> {record['queue']:<8}  {subject[:50]}"
        )

    print("\nRouted: " +", ".join(f"{q}={n}" for q, n in sorted(queues.items())))


if __name__ == "__main__":
    main()
