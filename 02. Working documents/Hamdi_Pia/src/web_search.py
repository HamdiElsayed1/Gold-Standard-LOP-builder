"""
Web search wrapper around OpenAI's Responses API + built-in `web_search` tool.

Reuses the OpenAI client from `orchestrator` so the McKinsey AI gateway
(`OPENAI_BASE_URL`) and key from `.env` are picked up automatically.

Public surface:
  * call_with_web_search(...) -> (parsed_json, url_citations)
  * WebSearchUnavailable                — raised when the gateway/SDK does
                                          not support the Responses API or
                                          the web_search tool. Call-sites
                                          can catch this and fall back to
                                          the chat.completions path.

This module is intentionally narrow. It does not load agent specs (the
caller does that via `orchestrator.load_agent_spec`) and it does not pick a
fallback path (the caller decides). It just runs one Responses call with
web_search enabled and returns a parsed JSON dict plus the URL annotations.
"""

from __future__ import annotations

import json
import re
from typing import Any

from orchestrator import MODEL, _get_client


class WebSearchUnavailable(RuntimeError):
    """Raised when the Responses API or `web_search` tool is not usable."""


# Mode → (search_context_size, max_tool_calls).
# Quick: tight budget, ~30s. Deep: high context, 1–3 minutes typical.
_MODE_CONFIG: dict[str, tuple[str, int]] = {
    "quick": ("low", 3),
    "deep": ("high", 10),
}


# Keys we expect on the final ContextDoc payload. Used to score candidate
# JSON objects when the model emits multiple (e.g. per-search status objects
# concatenated with the real answer).
_CONTEXT_DOC_KEYS: frozenset[str] = frozenset(
    {
        "client_profile",
        "market_trends",
        "competitive_landscape",
        "relevant_challenges",
        "citations",
        "evidence_gaps",
        "knowledge_cutoff_note",
        # Context v3 dimensions — included in scoring so the extractor
        # picks the right object even when the model emits multiple.
        "recent_signals",
        "regulatory_environment",
        "chapter_takeaways",
    }
)


def _iter_top_level_json_objects(text: str):
    """
    Walk `text` and yield every balanced top-level `{...}` substring.
    Handles strings (including escaped quotes) so braces inside JSON
    string values do not unbalance the scan.
    """
    depth = 0
    start = -1
    in_string = False
    escape = False
    for i, ch in enumerate(text):
        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
            continue
        if ch == '"':
            in_string = True
            continue
        if ch == "{":
            if depth == 0:
                start = i
            depth += 1
        elif ch == "}":
            if depth == 0:
                continue
            depth -= 1
            if depth == 0 and start >= 0:
                yield text[start : i + 1]
                start = -1


def _extract_json(text: str) -> dict:
    """
    Pull the final ContextDoc-shaped JSON object out of an assistant
    message. The model running with the web_search tool sometimes emits
    one or more small status objects (e.g. {"search_query": "...",
    "search_count": 1}) before the real answer, so we cannot just take
    the first `{...}`.

    Strategy:
      1. Direct parse if the whole stripped text is a single object.
      2. ```json``` fenced block.
      3. Walk every top-level balanced `{...}` substring and pick the
         candidate with the most ContextDoc-shaped keys; on ties, the
         LAST candidate wins (the real answer is emitted last).
      4. Fall back to a greedy `{.*}` regex parse.
      5. Otherwise raise WebSearchUnavailable with a 500-char preview.
    """
    stripped = text.strip()
    if stripped.startswith("{") and stripped.endswith("}"):
        try:
            return json.loads(stripped)
        except json.JSONDecodeError:
            pass

    fence = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
    if fence:
        try:
            return json.loads(fence.group(1))
        except json.JSONDecodeError:
            pass

    best_candidate: dict | None = None
    best_score: int = -1
    for chunk in _iter_top_level_json_objects(text):
        try:
            parsed = json.loads(chunk)
        except json.JSONDecodeError:
            continue
        if not isinstance(parsed, dict):
            continue
        score = len(_CONTEXT_DOC_KEYS.intersection(parsed.keys()))
        # `>=` so the LAST candidate wins on ties — the final answer is
        # always the last object the model emits.
        if score >= best_score:
            best_score = score
            best_candidate = parsed

    if best_candidate is not None:
        return best_candidate

    brace = re.search(r"\{.*\}", text, re.DOTALL)
    if brace:
        try:
            return json.loads(brace.group(0))
        except json.JSONDecodeError:
            pass

    raise WebSearchUnavailable(
        f"Web search returned text that was not valid JSON. "
        f"First 500 chars:\n{text[:500]}"
    )


def _collect_text_and_citations(response: Any) -> tuple[str, list[dict]]:
    """
    Walk `response.output` to find the final assistant message, concatenate
    its text parts, and collect any `url_citation` annotations.
    """
    output_items = getattr(response, "output", None) or []

    final_text_parts: list[str] = []
    url_citations: list[dict] = []

    for item in output_items:
        # Final assistant message has type == "message" and role == "assistant".
        if getattr(item, "type", None) != "message":
            continue
        if getattr(item, "role", None) != "assistant":
            continue

        for content in getattr(item, "content", None) or []:
            content_type = getattr(content, "type", None)
            if content_type not in ("output_text", "text"):
                continue

            text_value = getattr(content, "text", "") or ""
            final_text_parts.append(text_value)

            for ann in getattr(content, "annotations", None) or []:
                if getattr(ann, "type", None) != "url_citation":
                    continue
                url_citations.append(
                    {
                        "url": getattr(ann, "url", "") or "",
                        "title": getattr(ann, "title", "") or "",
                        "start_index": getattr(ann, "start_index", 0) or 0,
                        "end_index": getattr(ann, "end_index", 0) or 0,
                    }
                )

    final_text = "".join(final_text_parts).strip()

    # Some SDK versions also expose `output_text` as a convenience attr.
    if not final_text:
        convenience = getattr(response, "output_text", "") or ""
        final_text = convenience.strip()

    return final_text, url_citations


def call_with_web_search(
    system_prompt: str,
    user_message: str,
    output_schema: dict,
    mode: str,
    model: str | None = None,
) -> tuple[dict, list[dict]]:
    """
    Run one Responses API call with the built-in `web_search` tool enabled.

    Parameters
    ----------
    system_prompt : str
        The agent's full system prompt (already extracted from the spec).
    user_message : str
        The user turn — should already include the intake package, the
        user's additional context, and an explicit Quick/Deep instruction.
    output_schema : dict
        The JSON object the agent must return. Used to build the schema
        instruction appended to the system prompt (matches the pattern in
        `orchestrator.run_agent`).
    mode : str
        Either "quick" or "deep".
    model : str | None
        Optional override for the OpenAI model identifier. When None,
        falls back to `orchestrator.MODEL` (the `OPENAI_MODEL` env var).

    Returns
    -------
    (parsed_json, url_citations)
        `parsed_json` is the agent's JSON response as a dict.
        `url_citations` is a list of dicts with keys
        `url`, `title`, `start_index`, `end_index` — one per `url_citation`
        annotation on the final message.

    Raises
    ------
    ValueError
        If `mode` is not "quick" or "deep".
    WebSearchUnavailable
        If the Responses API or `web_search` tool is not supported by the
        gateway, or if the response cannot be parsed as JSON.
    """
    if mode not in _MODE_CONFIG:
        raise ValueError(
            f"Unknown web search mode: {mode!r}. Expected 'quick' or 'deep'."
        )

    context_size, max_tool_calls = _MODE_CONFIG[mode]

    schema_instruction = (
        "\n\n---\n"
        "OUTPUT CONTRACT — read carefully:\n"
        "Return EXACTLY ONE JSON object — your final answer — and nothing else. "
        "Do NOT emit intermediate status objects describing your tool use "
        "(e.g. {\"search_query\": ...}, {\"search_count\": ...}, "
        "{\"step\": ...}). The web_search tool already records its own calls; "
        "list the queries you ran inside the FINAL object's "
        "`searches_performed` array, not as separate emissions. "
        "Do NOT include text, commentary, or markdown outside the JSON. "
        "Your single response object must match this structure exactly:\n"
        f"```json\n{json.dumps(output_schema, indent=2)}\n```"
    )

    # NOTE: we deliberately do NOT pass `text={"format": {"type": "json_object"}}`.
    # OpenAI rejects the combination of `web_search` + the older `json_object`
    # JSON mode with `400 - Web Search cannot be used with JSON mode`. The
    # cookbook pattern is to rely on the system prompt's OUTPUT CONTRACT and
    # the robust `_extract_json` extractor. If we ever want stricter typing,
    # swap to `json_schema` (Structured Outputs) — it IS compatible with
    # web_search but requires a real JSON Schema for the ContextDoc, which we
    # do not yet generate.
    try:
        response = _get_client().responses.create(
            model=model or MODEL,
            input=[
                {"role": "system", "content": system_prompt + schema_instruction},
                {"role": "user", "content": user_message},
            ],
            tools=[
                {
                    "type": "web_search",
                    "search_context_size": context_size,
                }
            ],
            tool_choice="auto",
            max_tool_calls=max_tool_calls,
        )
    except Exception as exc:
        # Any failure on this path — gateway does not forward Responses,
        # tool not supported, auth scope mismatch, etc — is treated as
        # "web search unavailable" so the call-site can fall back.
        raise WebSearchUnavailable(
            f"Responses API + web_search call failed: {exc}"
        ) from exc

    final_text, url_citations = _collect_text_and_citations(response)

    if not final_text:
        raise WebSearchUnavailable(
            "Responses API returned an empty assistant message."
        )

    parsed = _extract_json(final_text)
    return parsed, url_citations
