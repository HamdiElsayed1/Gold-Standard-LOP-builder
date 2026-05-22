"""
Quick API connectivity test — works with both OpenAI and Anthropic gateway keys.
Run from the src/ directory:
    python test_api.py
"""

import os
from pathlib import Path

from env_bootstrap import load_app_env

load_app_env()

# ─── Detect which provider is configured ──────────────────────────────────────
openai_key  = os.environ.get("OPENAI_API_KEY")
openai_url  = os.environ.get("OPENAI_BASE_URL")
openai_model = os.environ.get("OPENAI_MODEL", "gpt-4o")

anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
anthropic_url = os.environ.get("ANTHROPIC_BASE_URL")
anthropic_model = os.environ.get("CLAUDE_MODEL", "claude-sonnet-4-5")

if openai_key:
    provider = "openai"
elif anthropic_key:
    provider = "anthropic"
else:
    print("ERROR: No API key found in .env (expected OPENAI_API_KEY or ANTHROPIC_API_KEY)")
    raise SystemExit(1)

print(f"Provider : {provider}")

# ─── OpenAI test ──────────────────────────────────────────────────────────────
if provider == "openai":
    from openai import OpenAI

    print(f"Base URL : {openai_url or '(default Anthropic endpoint)'}")
    print(f"Model    : {openai_model}")
    print(f"Key      : {openai_key[:30]}...  (truncated)")
    print()

    kwargs = {"api_key": openai_key}
    if openai_url:
        kwargs["base_url"] = openai_url

    client = OpenAI(**kwargs)

    print("Sending test message...")
    response = client.chat.completions.create(
        model=openai_model,
        max_completion_tokens=64,
        messages=[{"role": "user", "content": "Reply with exactly: API connection successful."}],
    )
    print(f"Response : {response.choices[0].message.content}")

# ─── Anthropic test ───────────────────────────────────────────────────────────
else:
    import anthropic

    print(f"Base URL : {anthropic_url or '(default Anthropic endpoint)'}")
    print(f"Model    : {anthropic_model}")
    print(f"Key      : {anthropic_key[:30]}...  (truncated)")
    print()

    kwargs = {"api_key": anthropic_key}
    if anthropic_url:
        kwargs["base_url"] = anthropic_url

    client = anthropic.Anthropic(**kwargs)

    print("Sending test message...")
    response = client.messages.create(
        model=anthropic_model,
        max_tokens=64,
        messages=[{"role": "user", "content": "Reply with exactly: API connection successful."}],
    )
    print(f"Response : {response.content[0].text}")

print("Test passed.")
