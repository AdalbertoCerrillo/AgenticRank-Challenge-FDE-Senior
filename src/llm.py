"""Connection to Claude on Amazon Bedrock.

Configuration comes from the repo-root .env (loaded by absolute path, so it works
regardless of the directory main.py is launched from) or the shell environment,
which takes precedence:

    AWS_PROFILE       AWS profile with Bedrock access (credentials in ~/.aws)
    AWS_REGION        Bedrock region
    BEDROCK_MODEL_ID  Bedrock model / inference profile id
"""

import json
import os
from functools import lru_cache
from pathlib import Path

import anthropic
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")


def model_id() -> str:
    return os.environ["BEDROCK_MODEL_ID"]


@lru_cache(maxsize=1)
def get_client() -> anthropic.AnthropicBedrock:
    """Shared Bedrock client (thread-safe, reused across calls)."""
    return anthropic.AnthropicBedrock(
        aws_profile=os.getenv("AWS_PROFILE") or None,
        aws_region=os.environ["AWS_REGION"],
    )


def ask(prompt: str, system: str | None = None, max_tokens: int = 1024) -> str:
    """Send one user message and return the model's text reply."""
    kwargs = {"system": system} if system else {}
    response = get_client().messages.create(
        model=model_id(),
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
        **kwargs,
    )
    return "".join(b.text for b in response.content if b.type == "text")


def ask_json(prompt: str, schema: dict, system: str | None = None, max_tokens: int = 1024) -> dict:
    """Send one user message and return the reply parsed against a JSON schema.

    Raises RuntimeError if the model refuses or the reply is cut off.
    """
    kwargs = {"system": system} if system else {}
    response = get_client().messages.create(
        model=model_id(),
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
        output_config={"format": {"type": "json_schema", "schema": schema}},
        **kwargs,
    )
    if response.stop_reason in ("refusal", "max_tokens"):
        raise RuntimeError(f"model stopped with {response.stop_reason}")
    text = next(b.text for b in response.content if b.type == "text")
    return json.loads(text)
