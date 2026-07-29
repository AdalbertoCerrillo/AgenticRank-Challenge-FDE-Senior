"""Classify a support ticket by category and urgency.

STATUS: placeholder. Right now this returns "general / normal" for every ticket
regardless of content. Making this actually work is the job.
"""


def classify_ticket(ticket: dict) -> dict:
    """Return a classification for a single ticket.

    Expected shape: {"category": <str>, "urgency": <str>}.
    """
    # TODO: call an LLM to classify the ticket by category and urgency.
    # The tickets are raw (see data/tickets.json): some have missing fields,
    # HTML/signature noise in the body, and a few are not in English.
    return {"category": "general", "urgency": "normal"}
