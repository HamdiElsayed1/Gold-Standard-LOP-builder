"""
Quick API connectivity test — works with both OpenAI and Anthropic gateway keys.
Run from the src/ directory:
    python test_api.py
"""

import os
from pathlib import Path
from dotenv import load_dotenv
import httpx


def _resolve_user_folder() -> Path | None:
    """Resolve the current user's folder under 02. Working documents."""
    workspace_root = Path(__file__).resolve().parents[3]
    working_docs = workspace_root / "02. Working documents"
    if not working_docs.exists():
        return None

    hints: list[str] = []
    for raw in (
        os.environ.get("LOP_USER_FOLDER"),
        os.environ.get("LOP_USER"),
        os.environ.get("USERNAME"),
        os.environ.get("USER"),
        Path.home().name,
    ):
        if not raw:
            continue
        cleaned = raw.strip()
        if not cleaned:
            continue
        hints.append(cleaned)
        if "_" in cleaned:
            hints.append(cleaned.split("_", 1)[0])

    deduped_hints = list(dict.fromkeys(hints))
    subdirs = [d for d in working_docs.iterdir() if d.is_dir()]
    by_lower = {d.name.lower(): d for d in subdirs}

    for hint in deduped_hints:
        direct = by_lower.get(hint.lower())
        if direct:
            return direct
        for d in subdirs:
            d_lower = d.name.lower()
            h_lower = hint.lower()
            if d_lower.startswith(h_lower) or h_lower.startswith(d_lower):
                return d
    return None


def _load_user_env() -> Path | None:
    user_folder = _resolve_user_folder()
    if not user_folder:
        return None
    for name in ("api-keys.env", ".env"):
        env_path = user_folder / name
        if env_path.exists():
            load_dotenv(env_path, override=True)
            return env_path
    return None


ENV_SOURCE = _load_user_env()

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
    expected = "02. Working documents/<YourName>/api-keys.env"
    if ENV_SOURCE:
        expected = str(ENV_SOURCE)
    print(
        "ERROR: No API key found "
        "(expected OPENAI_API_KEY or ANTHROPIC_API_KEY).\n"
        f"Checked user env source: {expected}"
    )
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

    prefer_system_proxy = os.environ.get("LOP_USE_SYSTEM_PROXY", "").lower() in {
        "1", "true", "yes",
    }

    print("Sending test message...")
    response = None
    last_exc: Exception | None = None
    for mode in (prefer_system_proxy, not prefer_system_proxy):
        try:
            test_kwargs = dict(kwargs)
            test_kwargs["http_client"] = httpx.Client(trust_env=mode, timeout=120.0)
            client = OpenAI(**test_kwargs)
            response = client.chat.completions.create(
                model=openai_model,
                max_completion_tokens=64,
                messages=[{"role": "user", "content": "Reply with exactly: API connection successful."}],
            )
            print(f"Network mode: {'system-proxy' if mode else 'direct'}")
            break
        except Exception as exc:
            last_exc = exc

    if response is None:
        raise RuntimeError("Connectivity test failed with proxy and direct network modes.") from last_exc

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
