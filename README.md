# Meridian Triage

Internal tool that automatically classifies incoming support tickets by category
and urgency and routes each one to the right queue, so nothing urgent gets buried
in the general pile.

## Getting started

```bash
pip install -r requirements.txt
cp .env.example .env   # add your LLM API key
python main.py
```

## What it does

- Classifies each ticket by category (billing, accounts, orders, ...) and urgency.
- Routes urgent tickets to the urgent queue automatically.
- Reads tickets from `data/tickets.json`.

## Notes

- The team exported a fresh batch of tickets to `data/tickets.json`.
- The customer conversation that kicked this off is in `docs/client-thread.md`.
