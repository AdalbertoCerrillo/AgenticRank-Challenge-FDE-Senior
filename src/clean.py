"""Clean raw tickets before classification.

- Strips HTML, email signatures, sign-offs and quoted reply/forward text from bodies.
- Merges duplicate records (same ticket id, or a reply from the same customer on
  the same subject) into one ticket, keeping every distinct message.
"""

import html
import re

_BLOCK_END = re.compile(r"<br\s*/?>|</(?:div|p|li|tr|h[1-6])\s*>", re.IGNORECASE)
_TAG = re.compile(r"<[^>]+>")

_FORWARD_MARKER = re.compile(
    r"^\s*(?:-{2,}\s*(?:original message|forwarded message)\s*-{2,}|begin forwarded message:)\s*$",
    re.IGNORECASE,
)
_HEADER_LINE = re.compile(r"^\s*(?:from|sent|to|cc|subject|date)\s*:", re.IGNORECASE)
_REPLY_INTRO = re.compile(r"^\s*(?:on|el|em)\s.+(?:wrote|escribió|escreveu):\s*$", re.IGNORECASE)
_SENT_FROM = re.compile(r"^\s*(?:sent from|enviado desde|enviado do)\s", re.IGNORECASE)
_SIGN_OFF = re.compile(
    r"^\s*(?:thanks|thank you|thx|regards|best(?: regards)?|cheers|"
    r"saludos|un saludo|gracias|atentamente|obrigad[oa]|atenciosamente|abraços?)[\s,.!]*$",
    re.IGNORECASE,
)
_NAME_LINE = re.compile(r"^\s*[^\W\d_][\w.'-]*(?:\s+[^\W\d_][\w.'-]*){0,2}\s*$")

_SUBJECT_PREFIX = re.compile(r"^\s*(?:(?:re|fwd?|fw|rv|enc|tr)\s*:\s*)+", re.IGNORECASE)


def _strip_html(text: str) -> str:
    text = _BLOCK_END.sub("\n", text)
    text = _TAG.sub("", text)
    return html.unescape(text).replace("\xa0", " ")


def _strip_forward(lines: list[str]) -> list[str]:
    """Cut quoted original messages; for a pure forward, keep its content only."""
    for i, line in enumerate(lines):
        if not _FORWARD_MARKER.match(line):
            continue
        if any(l.strip() for l in lines[:i]):
            return lines[:i]
        rest = lines[i + 1 :]
        while rest and (_HEADER_LINE.match(rest[0]) or not rest[0].strip()):
            rest = rest[1:]
        return rest
    return lines


def _strip_signature(lines: list[str]) -> list[str]:
    for i, line in enumerate(lines):
        if line.strip() == "--":
            lines = lines[:i]
            break
    lines = [l for l in lines if not _SENT_FROM.match(l)]

    while lines and not lines[-1].strip():
        lines.pop()
    if lines and _SIGN_OFF.match(lines[-1]):
        lines.pop()
    elif len(lines) >= 2 and _NAME_LINE.match(lines[-1]) and _SIGN_OFF.match(lines[-2]):
        del lines[-2:]
    return lines


def clean_body(raw: str | None) -> str:
    """Return the customer's own words: no HTML, signature or quoted text."""
    if not raw:
        return ""
    lines = [l.rstrip() for l in _strip_html(raw).splitlines()]
    lines = _strip_forward(lines)
    lines = [l for l in lines if not l.lstrip().startswith(">") and not _REPLY_INTRO.match(l)]
    lines = _strip_signature(lines)
    text = "\n".join(lines)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def clean_subject(subject: str | None) -> str | None:
    """Drop Re:/Fwd: style prefixes. Returns None for a missing or empty subject."""
    if subject is None:
        return None
    return _SUBJECT_PREFIX.sub("", subject).strip() or None


def _is_reply(subject: str | None) -> bool:
    return bool(subject and _SUBJECT_PREFIX.match(subject))


def _merge_group(records: list[dict], merged_ids: list[str]) -> dict:
    records = sorted(records, key=lambda r: r.get("created_at") or "")
    merged = dict(records[0])
    for record in records[1:]:
        for key, value in record.items():
            if merged.get(key) is None and value is not None:
                merged[key] = value

    messages, seen = [], set()
    for record in records:
        body = record.get("body") or ""
        if body in seen:
            continue
        seen.add(body)
        messages.append({"created_at": record.get("created_at"), "status": record.get("status"), "body": body})
    if len(messages) > 1:
        messages = [m for m in messages if m["body"]]

    merged["subject"] = clean_subject(next((r["subject"] for r in records if r.get("subject")), None))
    merged["status"] = records[-1].get("status") or merged.get("status")
    merged["messages"] = messages
    merged["body"] = "\n\n".join(m["body"] for m in messages if m["body"])
    merged["contact_count"] = len(messages)
    merged["merged_ids"] = merged_ids
    return merged


def merge_duplicates(tickets: list[dict]) -> list[dict]:
    """Fold duplicate records into one ticket each, without discarding any message.

    Records merge when they share an id, or when a reply (Re:/Fwd: subject) from a
    known customer matches the subject of that customer's earlier ticket.
    """
    groups: dict[str, list[dict]] = {}
    merged_ids: dict[str, list[str]] = {}
    by_customer_subject: dict[tuple[str, str], str] = {}

    for record in sorted(tickets, key=lambda r: r.get("created_at") or ""):
        ticket_id = record.get("id")
        subject = clean_subject(record.get("subject"))
        customer = record.get("customer_id")
        target = ticket_id

        if ticket_id not in groups and _is_reply(record.get("subject")) and customer and subject:
            original = by_customer_subject.get((customer, subject.lower()))
            if original:
                target = original
                merged_ids[original].append(ticket_id)

        if target not in groups:
            groups[target] = []
            merged_ids[target] = []
            if customer and subject:
                by_customer_subject.setdefault((customer, subject.lower()), target)
        groups[target].append(record)

    return [_merge_group(records, merged_ids[tid]) for tid, records in groups.items()]


def clean_tickets(tickets: list[dict]) -> list[dict]:
    """Clean every body, then merge duplicates. Input records are not modified."""
    cleaned = [{**t, "body": clean_body(t.get("body"))} for t in tickets]
    return merge_duplicates(cleaned)
