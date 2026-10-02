"""Tests for ticket cleaning: HTML, signatures, quoted replies, and merging
duplicate records into one ticket."""

from src.clean import clean_body, clean_subject, clean_tickets, merge_duplicates
from src.ingest import load_tickets


def _ticket(**fields):
    base = {
        "id": "T-1",
        "subject": "Help",
        "body": "text",
        "customer_id": "C-1",
        "customer_email": "a@example.com",
        "created_at": "2026-06-14T08:00:00Z",
        "channel": "email",
        "status": "open",
    }
    base.update(fields)
    return base


# --- HTML -------------------------------------------------------------------


def test_html_tags_and_entities_are_removed_keeping_paragraphs():
    raw = "<div>Store is down.</div><div>&nbsp;</div><div>Fix it NOW.</div>"
    assert clean_body(raw) == "Store is down.\n\nFix it NOW."


def test_html_entities_are_decoded():
    assert clean_body("<p>Tom &amp; Jerry&#39;s order</p>") == "Tom & Jerry's order"


# --- Signatures -------------------------------------------------------------


def test_dash_dash_signature_block_is_removed():
    raw = "Can you send a new link?\n\n--\nSent from my iPhone"
    assert clean_body(raw) == "Can you send a new link?"


def test_html_dash_dash_signature_is_removed():
    raw = '<div dir="ltr">How do I swap it?</div><div dir="ltr"><br></div><div dir="ltr">-- <br>Jamie</div>'
    assert clean_body(raw) == "How do I swap it?"


def test_sent_from_device_line_is_removed():
    raw = "<div>Box arrived soaked. Order #49022.</div><div><br></div><div>Sent from Mail for Windows</div>"
    assert clean_body(raw) == "Box arrived soaked. Order #49022."


def test_sign_off_with_name_is_removed():
    assert clean_body("When should I expect it?\n\nThanks,\nGreg") == "When should I expect it?"


def test_non_english_sign_off_is_removed():
    raw = "¿Cómo procedo para un reemplazo?\n\nSaludos,\nCarlos"
    assert clean_body(raw) == "¿Cómo procedo para un reemplazo?"


def test_thanks_inside_a_sentence_line_is_kept():
    raw = "Please update the address. Thanks!"
    assert clean_body(raw) == "Please update the address. Thanks!"


# --- Quoted replies / forwards ----------------------------------------------


def test_quoted_reply_text_is_removed():
    raw = "The store is STILL down.\n\n> On Jun 14 you wrote:\n> This is the third time I am writing..."
    assert clean_body(raw) == "The store is STILL down."


def test_original_message_below_new_text_is_removed():
    raw = "Any update?\n\n-----Original Message-----\nFrom: x@example.com\nSubject: Hi\n\nOld text"
    assert clean_body(raw) == "Any update?"


def test_pure_forward_keeps_forwarded_content_without_headers():
    raw = (
        "-----Original Message-----\nFrom: sam@example.com\nSent: Saturday\n"
        "To: support\nSubject: Cancel my order please\n\n"
        "I ordered the wrong size, order #49001. Please cancel it before it ships."
    )
    assert clean_body(raw) == "I ordered the wrong size, order #49001. Please cancel it before it ships."


def test_missing_body_becomes_empty_string():
    assert clean_body(None) == ""


def test_reply_and_forward_prefixes_are_stripped_from_subject():
    assert clean_subject("Re: Re: Fwd: order") == "order"
    assert clean_subject("RE: STORE IS DOWN") == "STORE IS DOWN"
    assert clean_subject(None) is None


# --- Merging duplicates -----------------------------------------------------


def test_identical_duplicates_merge_into_one_ticket_with_one_message():
    a = _ticket(body="Code invalid")
    merged = merge_duplicates([a, dict(a)])
    assert len(merged) == 1
    assert merged[0]["contact_count"] == 1


def test_reopened_record_merges_keeping_both_messages_in_time_order():
    original = _ticket(subject="Item missing", body="Jacket missing.", created_at="2026-06-14T08:00:00Z")
    follow_up = _ticket(
        subject="RE: Item missing - still not resolved",
        body="Still missing.",
        created_at="2026-06-16T08:00:00Z",
        status="reopened",
    )
    [merged] = merge_duplicates([follow_up, original])

    assert merged["subject"] == "Item missing"
    assert merged["created_at"] == "2026-06-14T08:00:00Z"
    assert merged["status"] == "reopened"
    assert merged["contact_count"] == 2
    assert [m["body"] for m in merged["messages"]] == ["Jacket missing.", "Still missing."]
    assert merged["body"] == "Jacket missing.\n\nStill missing."


def test_merge_fills_missing_fields_from_other_records():
    a = _ticket(customer_id=None, created_at="2026-06-14T08:00:00Z")
    b = _ticket(customer_id="C-9", created_at="2026-06-15T08:00:00Z", body="more")
    [merged] = merge_duplicates([a, b])
    assert merged["customer_id"] == "C-9"


def test_reply_with_new_id_merges_into_customers_original_ticket():
    original = _ticket(id="T-1", subject="Order late", customer_id="C-5")
    reply = _ticket(
        id="T-2", subject="Re: Order late", customer_id="C-5",
        body="Any news?", created_at="2026-06-15T08:00:00Z",
    )
    merged = merge_duplicates([original, reply])
    assert len(merged) == 1
    assert merged[0]["id"] == "T-1"
    assert merged[0]["merged_ids"] == ["T-2"]
    assert merged[0]["contact_count"] == 2


def test_same_subject_from_different_customer_is_not_merged():
    a = _ticket(id="T-1", subject="Order late", customer_id="C-5")
    b = _ticket(id="T-2", subject="Re: Order late", customer_id="C-6")
    assert len(merge_duplicates([a, b])) == 2


def test_reply_without_original_stays_its_own_ticket():
    [t] = merge_duplicates([_ticket(id="T-1017", subject="Re: Re: Fwd: order", body="")])
    assert t["id"] == "T-1017"
    assert t["subject"] == "order"


# --- Real export ------------------------------------------------------------


def test_real_export_cleans_to_50_unique_tickets_with_no_noise():
    tickets = clean_tickets(load_tickets())

    ids = [t["id"] for t in tickets]
    assert len(ids) == len(set(ids)) == 50
    for t in tickets:
        assert "<" not in t["body"] and "&nbsp;" not in t["body"]
        assert "Sent from" not in t["body"]
        assert "\n>" not in t["body"] and not t["body"].startswith(">")

    by_id = {t["id"]: t for t in tickets}
    assert by_id["T-1002"]["contact_count"] == 2
    assert by_id["T-1015"]["contact_count"] == 2
    assert by_id["T-1009"]["contact_count"] == 1
