"""
Deep Research smoke test — runs ONE simple, neutral Deep Research call to
confirm the model works end-to-end on the configured gateway, independent
of any pursuit content.

Use this when a real run inside the LoP Builder app comes back empty,
refused, or unavailable — to isolate whether the gateway / model is the
problem or the pursuit content / system prompt is the problem.

Run from the src/ directory:
    python test_deep_research.py
    python test_deep_research.py "EU battery storage market 2026"

Output:
    - status messages from call_deep_research's progress callback,
    - on success: report length, citation count, first 600 chars,
    - on failure: the DeepResearchUnavailable message (which will
      include the refusal text if the model refused),
    - a probe JSON is written under runs/deep_research_probes/ either way.
"""

from __future__ import annotations

import sys
from pathlib import Path

from dotenv import load_dotenv

# Match app.py's path / env setup so the OpenAI client picks up the
# McKinsey gateway base_url and the JWT key from src/.env.
_HERE = Path(__file__).parent
sys.path.insert(0, str(_HERE))
load_dotenv(_HERE / ".env")

from deep_research import DeepResearchUnavailable, call_deep_research  # noqa: E402


_DEFAULT_TOPIC = "European utility-scale battery storage market in 2026"

_NEUTRAL_SYSTEM_PROMPT = (
    "You are a research analyst. The user will name a public-interest "
    "research topic. Plan and run web searches autonomously, then write "
    "a concise (~600-900 word) sourced briefing covering: market size and "
    "growth, the three or four major trends, two or three named players "
    "and their public moves, and the regulatory environment. Cite every "
    "specific number, named company, and named regulation with a URL. "
    "Do not provide medical, legal, financial, or political advice. "
    "Stay strictly factual and source-grounded."
)


def _make_user_message(topic: str) -> str:
    return (
        f"Research topic: {topic}\n\n"
        "Produce the briefing as instructed in the system prompt. Run as "
        "many searches as you need, then write the final report."
    )


def main() -> int:
    topic = sys.argv[1] if len(sys.argv) > 1 else _DEFAULT_TOPIC

    print("=" * 70)
    print("Deep Research smoke test")
    print(f"Topic: {topic}")
    print("=" * 70)
    print()

    def _progress(msg: str) -> None:
        print(f"[deep-research] {msg}")

    try:
        report_text, url_citations = call_deep_research(
            system_prompt=_NEUTRAL_SYSTEM_PROMPT,
            user_message=_make_user_message(topic),
            progress_cb=_progress,
        )
    except DeepResearchUnavailable as exc:
        print()
        print("RESULT: Deep Research unavailable.")
        print(f"  reason: {exc}")
        print(
            "  → check the latest probe JSON under "
            "runs/deep_research_probes/ for full response shape."
        )
        return 1
    except Exception as exc:
        print()
        print(f"RESULT: unexpected error: {exc!r}")
        return 2

    print()
    print("=" * 70)
    print("RESULT: success")
    print(f"  report length:  {len(report_text)} chars")
    print(f"  url citations:  {len(url_citations)}")
    print("=" * 70)

    if url_citations:
        print()
        print("First few citations:")
        for c in url_citations[:5]:
            title = (c.get("title") or "(no title)")[:80]
            url = c.get("url") or ""
            print(f"  - {title} — {url}")

    print()
    print("First 600 chars of the report:")
    print("-" * 70)
    print(report_text[:600] + ("…" if len(report_text) > 600 else ""))
    print("-" * 70)

    return 0


if __name__ == "__main__":
    sys.exit(main())
