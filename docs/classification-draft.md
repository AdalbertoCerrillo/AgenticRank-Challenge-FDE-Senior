# Ticket classification rules and labels (validated)

> Status: **validated.** Labelled from `data/tickets.json` (53 records,
> 50 unique tickets). This is the reference ("golden") set
> used to check the LLM classifier.

## Urgency rule

**Urgent** if any of these apply:

1. **Money at risk.** The customer lost money or was charged wrongly (double charge,
   overcharge, refund well past its promised date), or the company is losing revenue
   (store down, customers can't pay or check out).
2. **Product failure on delivery.** The item is missing, broken, damaged, or wrong.
3. **Security or fraud.** Account takeover, orders the customer didn't place, risk to
   saved cards.
4. **Business risk.** A threat to leave or cancel a contract, or repeated unanswered
   follow-ups (escalation).

**Normal**: logins and password resets with no sign of compromise, how-to and
pre-sale questions, order changes, tracking, coupons and points, invoices,
feedback.

Money-adjacent questions where nothing has gone wrong yet (a coupon not applying,
loyalty points, gift cards, invoices, cancelling a subscription) stay **normal**. See
open question Q1.

## Categories

The README asks for category and urgency. The ticketing API (`src/ticketing_api.py`)
**only accepts the queues `urgent`, `billing`, `accounts`, `orders` and `general`.**
So the proposed category set matches the queues:

| Category   | Covers |
|------------|--------|
| `billing`  | charges, refunds, promos and coupons, invoices, subscriptions, gift cards, points |
| `accounts` | login, password, email change, account security and fraud |
| `orders`   | tracking, delivery, changes and cancellations, missing, damaged or wrong items, exchanges |
| `general`  | product and pre-sale questions, technical or site issues, feedback, anything else |

Recommendation: **don't add categories for now.** Any extra category (such as `technical`
or `retention`) would still have to go to one of these five queues. If you want them
for reporting, they could be a secondary tag. See Q3.

## Labels

Routing rule: urgent goes to the `urgent` queue. Everything else goes to its category queue.
⚑ = borderline case, decided as shown.

| ID | Subject (short) | Category | Urgency | Why / note |
|----|-----------------|----------|---------|------------|
| T-1001 | Reset password link expired | accounts | normal | Routine login |
| T-1002 | Store down during sale | general | **urgent** | Revenue loss, threatens to leave. Merged with its `reopened` follow-up (2 contacts) |
| T-1003 | Order 2 days late | orders | normal | ⚑ Late but not lost yet |
| T-1004 | (no subject) change account email | accounts | normal | Missing subject |
| T-1005 | Refund status (1 week) | billing | normal | ⚑ Money, but still a routine status check within the normal window |
| T-1006 | No puedo iniciar sesión (ES) | accounts | normal | ⚑ Locked out 2 days, no sign of compromise |
| T-1007 | Leather or vegan? | general | normal | Product question |
| T-1008 | Cancel order before it ships | orders | normal | ⚑ Time-sensitive |
| T-1009 | STUDENT10 code invalid | billing | normal | Merged: 2 identical records |
| T-1010 | Update shipping address | orders | normal | ⚑ Time-sensitive |
| T-1011 | Unsubscribe newsletter | general | normal | Missing customer_id |
| T-1012 | Pedido llegó dañado (ES) | orders | **urgent** | Broken product |
| T-1013 | Double charged, overdraft | billing | **urgent** | Wrongly charged |
| T-1014 | Where's tracking number | orders | normal | How-to |
| T-1015 | Item missing from delivery | orders | **urgent** | Missing product. Merged with its `reopened` follow-up (2 contacts) |
| T-1016 | Someone logged into my account | accounts | **urgent** | Account takeover, saved cards at risk |
| T-1017 | "Re: Re: Fwd: order" (empty body) | general | **urgent** | **needs_review**: no content to judge (Q4) |
| T-1018 | Gift wrapping? | general | normal | Pre-sale |
| T-1019 | Não consigo finalizar a compra (PT) | general | **urgent** | ⚑ Can't pay. May be the same outage as T-1021 |
| T-1020 | Loyalty points missing | billing | normal | |
| T-1021 | None of my customers can pay | general | **urgent** | Checkout down for a whole shop (same customer as T-1002) |
| T-1022 | (no subject) return policy | general | normal | Missing subject and customer_id |
| T-1023 | Wrong item received | orders | **urgent** | ⚑ Fulfilment error. Calm tone, but same class as missing or damaged |
| T-1024 | Delay delivery | orders | normal | |
| T-1025 | Fraud orders on my account | accounts | **urgent** | Fraud |
| T-1026 | Ship to Canada? | general | normal | Pre-sale |
| T-1027 | Cambiar dirección (ES) | orders | normal | ⚑ Time-sensitive |
| T-1028 | App crashes on orders tab | general | normal | ⚑ Bug, but it doesn't block purchases |
| T-1029 | VAT invoice | billing | normal | |
| T-1030 | SUMMER20 expired early | billing | normal | ⚑ Money-adjacent |
| T-1031 | Size exchange | orders | normal | |
| T-1032 | Payment failed but charged twice | billing | **urgent** | Possible double charge |
| T-1033 | (no subject) nice packaging | general | normal | Feedback |
| T-1034 | Refund 3 weeks late, 2nd ask | billing | **urgent** | Overdue refund, repeat contact |
| T-1035 | Cancelar assinatura (PT) | billing | normal | ⚑ Wants it done before the next charge |
| T-1036 | Backpack recommendation | general | normal | Pre-sale |
| T-1037 | Account locked (forgot password) | accounts | normal | Says it's not a security issue |
| T-1038 | Bulk order, 200 units | general | normal | ⚑ Sales opportunity with a deadline, not a support emergency |
| T-1039 | Damaged on arrival (soaked) | orders | **urgent** | Ruined product. Missing customer_id |
| T-1040 | Redeem gift card | billing | normal | How-to |
| T-1041 | Cancelling our contract | general | **urgent** | Formal churn notice. Highest business risk |
| T-1042 | Me cobraron dos veces (ES) | billing | **urgent** | Double charge |
| T-1043 | Change account email | accounts | normal | |
| T-1044 | Processing for 5 days | orders | normal | ⚑ Customer is worried. Could be stuck |
| T-1045 | Warranty question | general | normal | |
| T-1046 | Promo price not honored ($10) | billing | **urgent** | ⚑ Overcharged, though the amount is small |
| T-1047 | Add to cart does nothing | general | **urgent** | ⚑ Blocks purchases (likely affects every customer on that page) |
| T-1048 | ¿Descuento estudiantes? (ES) | general | normal | Pre-sale |
| T-1049 | Charged $18 more than cart | billing | **urgent** | Overcharged |
| T-1050 | Thanks to Marco | general | normal | Feedback |

**Totals (50 unique):** 18 urgent (including 1 needs_review) and 32 normal. By category:
general 18, orders 12, billing 13, accounts 7.

## Data issues noticed

- **Duplicates.** T-1009 appears twice (identical). T-1002 and T-1015 each have a second,
  `reopened` record. See the merge rule below.

## Merge rule for duplicates (decided)

Records on the same topic are **merged into one ticket**. They are not handled as
separate tickets, and none are discarded.

- **When to merge:** records with the same ticket `id`. That is the export
  double-counting a reopened ticket.
- **How to merge:**
  - **Body:** all distinct messages kept in time order, as one thread. Identical
    copies are collapsed, so no information is lost.
  - **Subject:** the original. **created_at:** the earliest. **status:** the latest
    (for example `reopened`).
  - **Contact count:** the number of distinct messages. A reopen or repeat contact is
    an escalation signal.
  - **Urgency:** the highest urgency of any part. A merged ticket is never less
    urgent than its most urgent message.
- **Classify after merging,** so the classifier sees the whole conversation.

| Merged ticket | Records | Result |
|---------------|---------|--------|
| T-1002 | original + `reopened` follow-up ("STILL down, evaluating other providers") | 1 ticket, 2 contacts, **urgent** |
| T-1015 | original + `reopened` follow-up ("no one got back to me") | 1 ticket, 2 contacts, **urgent** |
| T-1009 | 2 identical copies | 1 ticket, 1 contact, normal |

**Related, not merged:** T-1021 ("none of my customers can pay") is from the
same customer as T-1002 (C-8890, store down during sale). It has a different ID,
but it is probably the same incident. Decision: **don't auto-merge across different
IDs.** Both stay urgent. Linking related tickets is deferred (see HANDOFF.md). See Q6.
- **Missing fields.** Null subjects (T-1004, T-1022, T-1033), null customer_id (T-1011,
  T-1022, T-1039), and an empty body (T-1017).
- **Noise.** HTML in T-1002, quoted email headers in T-1008, signatures ("Sent from my
  iPhone").
- **Languages.** Spanish: T-1006, T-1012, T-1027, T-1042, T-1048. Portuguese: T-1019,
  T-1035. Two of these are urgent, so the classifier must handle them.

## Decisions (validated)

- **Q1. Money involved:** urgent means the customer was charged wrongly or revenue is
  being lost. Money questions where nothing has gone wrong yet stay normal.
- **Q2. Urgent volume:** urgency stays binary (urgent/normal). Ranking inside the
  urgent queue is deferred.
- **Q3. Categories:** the 4 that match the ticketing queues. No extra tags.
- **Q4. Unclear tickets:** marked `needs_review` and routed to the **urgent** queue.
  This applies to ambiguous content, empty forwards, and classifier errors. We accept
  some false alarms so an urgent ticket never lands in a normal queue.
- **Q5. Borderline rows:** labelled as in the table.
- **Q6. Merging across IDs:** only same-ID records and replies (same customer, same
  subject) are merged. T-1002 and T-1021 stay separate tickets, both urgent.
