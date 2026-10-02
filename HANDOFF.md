# Handoff

## The need

Dana's non-negotiable: an urgent ticket must never sit in the general pile again. I
built for that and nothing else. Marcus's extras (auto-replies, summaries,
sentiment, translation, dashboard) are listed under deferred, with reasons.

## What I shipped

Running `python main.py` loads tickets, cleans them, classifies them and routes them.

1. **Cleaning** (`src/clean.py`)
   - Removes HTML, email signatures, sign-offs and quoted reply or forward text. This works in English, Spanish and Portuguese.
   - **Duplicates are merged, never discarded.** Records with the same ticket ID, and replies from the same customer on the same subject, become one ticket. Every distinct message is kept in time order, and the ticket records how many times the customer wrote in. Repeat contact counts as an urgency signal.
   - Result: the 53 exported records become **50 tickets**. T-1002 and T-1015 were reopened and now carry both messages.
2. **Classification** (`src/classify.py`, Claude on Amazon Bedrock)
   - Each ticket gets a **category** that matches the ticketing queues (`billing`, `accounts`, `orders`, `general`) and an **urgency** (`urgent`/`normal`).
   - **Urgent** means:
     - money at risk: the customer was charged wrongly, or the business is losing revenue;
     - a product that is missing, broken, damaged or wrong;
     - security or fraud;
     - business risk, such as a churn threat or repeated unanswered follow-ups.
   - Logins, how-to questions, pre-sale questions, order changes and feedback are normal.
   - The rules were validated against a hand-labelled reference set: `docs/classification-draft.md`.
3. **Safety fallback: when in doubt, it goes to urgent.** A ticket is marked **needs review** and sent to the **urgent** queue when:
   - the model can't tell with confidence what the customer needs;
   - the ticket has no content, for example an empty forward;
   - the API call fails, the model refuses, or its answer is invalid.

   We accept some false alarms so that an urgent ticket never lands in a normal queue.
4. **Routing** (`src/route.py`): urgent and needs-review tickets go to `urgent`. Everything else goes to its category queue, through the mock ticketing API.

**Results on the current export:** 18 tickets went to urgent, including 1 needs-review (T-1017, an empty forward). The other 32 went to their category queues. All 17 tickets labelled urgent in the reference set were routed to urgent. Spanish and Portuguese tickets are classified directly, without translation. One category differs from the reference: T-1040 (redeeming a gift card) came out as `general` instead of `billing`. It is a normal ticket either way.

**Tests:** 36 passing (`pytest`). They cover cleaning, merging, every fallback path and routing. The classifier tests use a fake LLM, so they run offline.

## What I deferred (and why)

- **Auto-drafted replies.** Dana flagged refunds and legal wording as risky to send without human review. That needs a human-approval design, not a quick add-on.
- **Thread summaries, sentiment, language detection and translation.** None of these is needed to get urgent tickets out of the general pile. The classifier already reads Spanish and Portuguese directly.
- **Dashboard.** A QBR nice-to-have. The run output already gives a per-queue summary.
- **Ranking inside the urgent queue.** Urgency is binary for now. With 36% of tickets urgent, store-down, fraud and churn tickets (T-1002, T-1021, T-1016, T-1025, T-1041) should eventually be sorted to the top.
- **Linking related tickets across IDs.** T-1021 is probably the same outage as T-1002 (same customer), but tickets with different IDs are not merged automatically. Both are already urgent.

## What I'd do next

1. **Make classifier errors visible.** If Bedrock is down, every ticket currently goes to urgent as needs-review. That is safe, but it happens silently. A run should report the error count and alert on it.
2. **Automated accuracy check.** Turn the validated labels into a test that runs the real classifier and fails on any urgent ticket routed to a normal queue. Run it whenever the prompt or model changes.

3. **Watch the needs-review rate.** If it climbs, the urgent queue becomes noisy. Review those tickets weekly and tune the rules.
