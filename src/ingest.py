"""Load raw support tickets from the exported JSON file.

This is the one finished piece of the tool. It returns the tickets exactly as
they were exported — no cleaning, no dedup, no normalization.
"""

import json
from pathlib import Path

DEFAULT_PATH = Path(__file__).resolve().parent.parent / "data" / "tickets.json"


def load_tickets(path: str | Path = DEFAULT_PATH) -> list[dict]:
    """Read the exported tickets and return them as a list of dicts."""
    with open(path, encoding="utf-8") as f:
        tickets = json.load(f)
    if not isinstance(tickets, list):
        raise ValueError("tickets.json should contain a JSON array of tickets")
    return tickets
