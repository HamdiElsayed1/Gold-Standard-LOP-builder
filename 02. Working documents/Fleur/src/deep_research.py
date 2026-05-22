"""
Deep Research wrapper around OpenAI's Responses API + the
`o4-mini-deep-research` / `o3-deep-research` model family.

Reuses the OpenAI client from `orchestrator` so the McKinsey AI gateway
(`OPENAI_BASE_URL`) and key from `.env` are picked up automatically.

Public surface:
  * call_deep_research(...)            -> (report_text, url_citations)
  * DeepResearchUnavailable            -- raised when the gateway/SDK does
                                          not expose the deep research
                                          model, when the job fails, or
                                          when polling times out.

The Deep Research model is autonomous: given a system prompt and a user
message, it plans queries, calls `web_search_preview` repeatedly, and
synthesises a long-form report with inline URL citation annotations.
Jobs typically run 3-15 minutes; OpenAI recommends background mode plus
polling, which is what this module implements.

The OUTPUT IS PROSE — not JSON. Call-sites are expected to feed the
returned report and citation list into a structuring step (e.g. the
existing `context-agent` running through `chat.completions` JSON mode)
to coerce it into a `ContextDoc`.
"""

from __future__ import annotations

import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

from env_bootstrap import load_app_env

load_app_env()

from orchestrator import _get_client


# Probes go alongside the run logs so they are easy to find when diagnosing
# why a Deep Research call returned 0 URL citations etc.
_PROBE_DIR = Path(__file__).parent.parent / "runs" / "deep_research_probes"


class DeepResearchUnavailable(RuntimeError):
    """
    Raised when the Deep Research model is not usable on this run.

    Triggers include:
      * gateway does not expose the model / SDK rejects the call,
      * the background job ends in a non-success terminal state
        ("failed", "cancelled", "incomplete"),
      * the job exceeds `timeout_seconds` (the call-site should fall
        back to the enriched web_search path).
    """


# Default model. Swap to "o3-deep-research-2025-06-26" for maximum depth
# (slower, more expensive). Override via the DEEP_RESEARCH_MODEL env var.
_DEFAULT_DEEP_RESEARCH_MODEL = "o4-mini-deep-research-2025-06-26"

# Polling cadence. 10s is generous enough to avoid hammering the gateway
# while still feeling responsive when wired into a Streamlit spinner.
_POLL_INTERVAL_SECONDS = 10

# Hard ceiling: 25 minutes. Background-mode results are stored for ~10
# minutes after completion, so going much longer than this is risky.
_DEFAULT_TIMEOUT_SECONDS = 25 * 60


def _resolve_model(override: str | None = None) -> str:
    """
    Pick the Deep Research model for this call. Precedence:
      1. explicit `override` from the call-site (e.g. UI toggle), if set;
      2. `DEEP_RESEARCH_MODEL` env var;
      3. `_DEFAULT_DEEP_RESEARCH_MODEL`.
    """
    if override and override.strip():
        return override.strip()
    return os.environ.get("DEEP_RESEARCH_MODEL", _DEFAULT_DEEP_RESEARCH_MODEL)


def _emit(progress_cb: Callable[[str], None] | None, msg: str) -> None:
    if progress_cb is None:
        return
    try:
        progress_cb(msg)
    except Exception:
        # A callback failure must never break the research loop.
        pass


def _count_search_calls(response: Any) -> int:
    items = getattr(response, "output", None) or []
    return sum(1 for it in items if getattr(it, "type", None) == "web_search_call")


def _final_assistant_message(response: Any) -> Any:
    """
    Return the last item in `response.output` whose type is "message" and
    role is "assistant". Returns None if no such item exists.
    """
    items = getattr(response, "output", None) or []
    for item in reversed(items):
        if (
            getattr(item, "type", None) == "message"
            and getattr(item, "role", None) == "assistant"
        ):
            return item
    return None


def _to_plain(obj: Any, *, max_str_len: int = 400) -> Any:
    """
    Best-effort convert SDK models / arbitrary objects into JSON-serialisable
    primitives, capping long strings so probe files stay readable. Used
    exclusively by the diagnostic probe, never by the live research path.
    """
    try:
        if obj is None or isinstance(obj, (bool, int, float)):
            return obj
        if isinstance(obj, str):
            return obj if len(obj) <= max_str_len else obj[:max_str_len] + "…"
        # Pydantic v2 models from the OpenAI SDK.
        dump = getattr(obj, "model_dump", None)
        if callable(dump):
            return _to_plain(dump(), max_str_len=max_str_len)
        if isinstance(obj, dict):
            return {str(k): _to_plain(v, max_str_len=max_str_len) for k, v in obj.items()}
        if isinstance(obj, (list, tuple)):
            return [_to_plain(x, max_str_len=max_str_len) for x in obj]
        # Fallback: vars() for namespace-like objects.
        v = getattr(obj, "__dict__", None)
        if isinstance(v, dict):
            return _to_plain(v, max_str_len=max_str_len)
        return repr(obj)[:max_str_len]
    except Exception as exc:
        return f"<unserialisable: {exc!r}>"


def _probe_response_shape(response: Any) -> dict:
    """
    Inventory the response so we can see why URL citations may be empty.

    The probe answers:
      - Did `web_search_call` items survive in `response.output`?
      - What content parts are on the final assistant message, and what
        annotation types do they carry (if any)?
      - Are there annotations of unexpected types (e.g. `file_citation`,
        bare `{"type": "citation"}`, or no `type` field at all)?

    Best-effort. Any introspection failure is captured into the probe
    rather than raised — this must NEVER break the research call.
    """
    probe: dict[str, Any] = {
        "probed_at": datetime.now().isoformat(),
        "response_id": getattr(response, "id", None),
        "model": getattr(response, "model", None),
        "status": getattr(response, "status", None),
    }

    try:
        items = list(getattr(response, "output", None) or [])
        probe["output_item_count"] = len(items)

        type_counts: dict[str, int] = {}
        for it in items:
            t = getattr(it, "type", None) or "<no_type>"
            type_counts[t] = type_counts.get(t, 0) + 1
        probe["output_item_count_by_type"] = type_counts

        # ── Sample web_search_call items (queries + any embedded results) ──
        web_calls = [it for it in items if getattr(it, "type", None) == "web_search_call"]
        probe["web_search_call_count"] = len(web_calls)
        probe["web_search_call_samples"] = [
            _to_plain(it) for it in web_calls[:3]
        ]

        # ── Drill into the final assistant message ──
        final = _final_assistant_message(response)
        if final is None:
            probe["final_message"] = None
        else:
            content_parts = list(getattr(final, "content", None) or [])
            part_summaries: list[dict] = []
            total_url_citations = 0
            total_other_annotations = 0
            other_annotation_types: dict[str, int] = {}

            refusal_texts: list[str] = []

            for cp in content_parts:
                cp_type = getattr(cp, "type", None) or "<no_type>"
                text_value = getattr(cp, "text", "") or ""
                annotations = list(getattr(cp, "annotations", None) or [])
                ann_type_counts: dict[str, int] = {}
                ann_samples: list[Any] = []

                for ann in annotations:
                    a_type = getattr(ann, "type", None) or "<no_type>"
                    ann_type_counts[a_type] = ann_type_counts.get(a_type, 0) + 1
                    if a_type == "url_citation":
                        total_url_citations += 1
                    else:
                        total_other_annotations += 1
                        other_annotation_types[a_type] = (
                            other_annotation_types.get(a_type, 0) + 1
                        )
                    if len(ann_samples) < 3:
                        ann_samples.append(_to_plain(ann))

                # Capture refusal text when the content part is a refusal.
                # The refusal string is the only signal we get about WHY the
                # model declined to produce the final report.
                refusal_text = ""
                if cp_type == "refusal":
                    refusal_raw = getattr(cp, "refusal", "") or ""
                    if isinstance(refusal_raw, str):
                        refusal_text = refusal_raw
                    if refusal_text.strip():
                        refusal_texts.append(refusal_text.strip())

                # Also list ALL attribute names visible on the content part
                # (helps catch typos like `citations` vs `annotations`, or
                # gateway-renamed fields like `references`).
                attr_names: list[str] = []
                if hasattr(cp, "model_fields_set"):
                    try:
                        attr_names = sorted(cp.model_fields_set)
                    except Exception:
                        attr_names = []
                if not attr_names:
                    try:
                        attr_names = sorted(
                            n for n in dir(cp) if not n.startswith("_")
                        )[:40]
                    except Exception:
                        attr_names = []

                part_summary: dict[str, Any] = {
                    "type": cp_type,
                    "text_len": len(text_value),
                    "annotation_count": len(annotations),
                    "annotation_types": ann_type_counts,
                    "annotation_samples": ann_samples,
                    "visible_attributes": attr_names,
                }
                # Only include refusal text on refusal parts to keep the
                # probe compact when content is normal.
                if cp_type == "refusal":
                    part_summary["refusal_text"] = (
                        refusal_text[:1500]
                        + ("…" if len(refusal_text) > 1500 else "")
                    )

                part_summaries.append(part_summary)

            probe["final_message"] = {
                "id": getattr(final, "id", None),
                "role": getattr(final, "role", None),
                "status": getattr(final, "status", None),
                "content_part_count": len(content_parts),
                "content_parts": part_summaries,
                "totals": {
                    "url_citation_annotations": total_url_citations,
                    "other_annotations": total_other_annotations,
                    "other_annotation_types": other_annotation_types,
                    "refusal_count": len(refusal_texts),
                },
            }
            if refusal_texts:
                # Top-level convenience field so the refusal is the first
                # thing visible when opening the JSON.
                probe["refusal_texts"] = refusal_texts
    except Exception as exc:
        probe["probe_error"] = repr(exc)

    return probe


def _save_probe(probe: dict) -> Path | None:
    """
    Write the probe to `Hamdi/runs/deep_research_probes/<id>_<ts>.json`.
    Returns the path on success, or None on any failure (probing must
    never break the research path).
    """
    try:
        _PROBE_DIR.mkdir(parents=True, exist_ok=True)
        rid = probe.get("response_id") or "unknown"
        # Sanitize the response id for filesystem use.
        safe_rid = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in str(rid))
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = _PROBE_DIR / f"{ts}_{safe_rid[:60]}.json"
        path.write_text(json.dumps(probe, indent=2, default=str), encoding="utf-8")
        return path
    except Exception:
        return None


def _summarise_probe_for_log(probe: dict) -> str:
    """One-line human-readable summary for the run log / spinner."""
    final = probe.get("final_message") or {}
    totals = (final.get("totals") or {}) if isinstance(final, dict) else {}
    url_n = totals.get("url_citation_annotations", 0)
    other_n = totals.get("other_annotations", 0)
    other_types = totals.get("other_annotation_types", {}) or {}
    refusal_count = totals.get("refusal_count", 0)
    type_counts = probe.get("output_item_count_by_type", {}) or {}
    web_calls = probe.get("web_search_call_count", 0)
    cp_count = (
        final.get("content_part_count", 0) if isinstance(final, dict) else 0
    )

    other_types_str = (
        ", ".join(f"{k}:{v}" for k, v in other_types.items())
        if other_types
        else "none"
    )
    type_counts_str = ", ".join(
        f"{k}:{v}" for k, v in sorted(type_counts.items())
    ) or "none"

    # Make refusals the headline when present — they are the most common
    # reason Deep Research returns nothing useful and we want them
    # impossible to miss in the log.
    refusal_prefix = ""
    if refusal_count:
        first_refusal = ""
        for r in (probe.get("refusal_texts") or []):
            if isinstance(r, str) and r.strip():
                first_refusal = r.strip()
                break
        snippet = (first_refusal[:160] + "…") if len(first_refusal) > 160 else first_refusal
        refusal_prefix = f"REFUSAL ({refusal_count}) — \"{snippet}\" | "

    return (
        f"{refusal_prefix}Probe — output items[{type_counts_str}]; "
        f"web_search_calls={web_calls}; "
        f"final_msg content_parts={cp_count}; "
        f"url_citation annotations={url_n}; "
        f"other annotations={other_n} ({other_types_str})"
    )


def _extract_refusal_text(response: Any) -> str:
    """
    Return the refusal text from the final assistant message, or "" if no
    refusal is present. A `"refusal"` content part means the model
    completed the underlying searches/reasoning but declined to produce
    the final report — typically due to a content-policy hit.
    """
    final = _final_assistant_message(response)
    if final is None:
        return ""
    for content in getattr(final, "content", None) or []:
        if getattr(content, "type", None) == "refusal":
            text = getattr(content, "refusal", "") or ""
            if isinstance(text, str) and text.strip():
                return text.strip()
    return ""


def _extract_report_and_citations(response: Any) -> tuple[str, list[dict]]:
    """
    Walk the final assistant message: concatenate every text part and
    collect every `url_citation` annotation.
    """
    final = _final_assistant_message(response)
    if final is None:
        return "", []

    text_parts: list[str] = []
    citations: list[dict] = []

    for content in getattr(final, "content", None) or []:
        if getattr(content, "type", None) not in ("output_text", "text"):
            continue

        text_value = getattr(content, "text", "") or ""
        text_parts.append(text_value)

        for ann in getattr(content, "annotations", None) or []:
            if getattr(ann, "type", None) != "url_citation":
                continue
            citations.append(
                {
                    "url": getattr(ann, "url", "") or "",
                    "title": getattr(ann, "title", "") or "",
                    "start_index": getattr(ann, "start_index", 0) or 0,
                    "end_index": getattr(ann, "end_index", 0) or 0,
                }
            )

    return "".join(text_parts).strip(), citations


def call_deep_research(
    system_prompt: str,
    user_message: str,
    model: str | None = None,
    timeout_seconds: int = _DEFAULT_TIMEOUT_SECONDS,
    progress_cb: Callable[[str], None] | None = None,
) -> tuple[str, list[dict]]:
    """
    Run one Deep Research job and block until it terminates.

    Parameters
    ----------
    system_prompt : str
        The agent's full system prompt. It is sent as the `developer` role
        message, which is the convention for Deep Research models.
    user_message : str
        The user turn. Should already contain the intake package, any
        partner-supplied additional context, and an explicit research
        instruction. The model decides on its own which queries to run.
    model : str, optional
        Override the Deep Research model identifier for this call.
        When omitted, falls back to the `DEEP_RESEARCH_MODEL` env var,
        and finally to `_DEFAULT_DEEP_RESEARCH_MODEL`. Typical values:
        `"o4-mini-deep-research-2025-06-26"` (faster, lighter synthesis)
        or `"o3-deep-research-2025-06-26"` (slower, deeper synthesis).
    timeout_seconds : int
        Hard ceiling on polling. Defaults to 25 minutes; raise
        `DeepResearchUnavailable` on overrun.
    progress_cb : callable, optional
        Receives short status strings the call-site can surface to the
        user (e.g. an `st.empty()` placeholder inside a Streamlit
        spinner). Errors raised by the callback are silently swallowed.

    Returns
    -------
    (report_text, url_citations)
        `report_text` is the long-form research report, free prose with
        inline citation markers preserved.
        `url_citations` is a list of dicts with keys
        `url`, `title`, `start_index`, `end_index`.

    Raises
    ------
    DeepResearchUnavailable
        On any kickoff failure, non-success terminal status, or timeout.
    """
    client = _get_client()
    resolved_model = _resolve_model(model)

    _emit(progress_cb, f"Kicking off Deep Research job ({resolved_model})...")

    try:
        response = client.responses.create(
            model=resolved_model,
            background=True,
            input=[
                {
                    "role": "developer",
                    "content": [{"type": "input_text", "text": system_prompt}],
                },
                {
                    "role": "user",
                    "content": [{"type": "input_text", "text": user_message}],
                },
            ],
            reasoning={"summary": "auto"},
            tools=[{"type": "web_search_preview"}],
        )
    except Exception as exc:
        # Most likely the gateway does not expose the Deep Research model
        # or the SDK version does not understand `background=True`.
        raise DeepResearchUnavailable(
            f"Deep Research kickoff failed: {exc}"
        ) from exc

    response_id = getattr(response, "id", None)
    if not response_id:
        raise DeepResearchUnavailable(
            "Deep Research kickoff returned a response without an id."
        )

    started_at = time.monotonic()
    last_search_count = -1

    # Polling loop. The kickoff response may already include partial
    # output, so we re-check status before sleeping.
    while True:
        status = getattr(response, "status", None) or ""
        elapsed = int(time.monotonic() - started_at)
        searches = _count_search_calls(response)

        if searches != last_search_count:
            _emit(
                progress_cb,
                f"Deep Research running — status={status}, "
                f"searches={searches}, elapsed={elapsed}s",
            )
            last_search_count = searches

        if status == "completed":
            break

        if status in {"failed", "cancelled", "incomplete"}:
            err = getattr(response, "error", None)
            err_msg = getattr(err, "message", None) or str(err) if err else ""
            raise DeepResearchUnavailable(
                f"Deep Research job ended with status={status!r}"
                + (f": {err_msg}" if err_msg else "")
            )

        if elapsed > timeout_seconds:
            raise DeepResearchUnavailable(
                f"Deep Research polling exceeded {timeout_seconds}s "
                f"(last status: {status!r})."
            )

        time.sleep(_POLL_INTERVAL_SECONDS)

        try:
            response = client.responses.retrieve(response_id)
        except Exception as exc:
            raise DeepResearchUnavailable(
                f"Deep Research retrieve({response_id}) failed: {exc}"
            ) from exc

    # ── Diagnostic probe ─────────────────────────────────────────────────
    # Wrapped in try/except: probing must NEVER break the research path.
    try:
        probe = _probe_response_shape(response)
        probe_path = _save_probe(probe)
        summary = _summarise_probe_for_log(probe)
        if probe_path is not None:
            summary = f"{summary} | dump={probe_path.name}"
        _emit(progress_cb, summary)
    except Exception as exc:
        _emit(progress_cb, f"Probe failed: {exc!r}")

    # Detect refusal BEFORE the empty-text check so the error message
    # tells the user what actually happened rather than the generic
    # "empty or could not be parsed".
    refusal_text = _extract_refusal_text(response)
    if refusal_text:
        snippet = refusal_text if len(refusal_text) <= 400 else refusal_text[:400] + "…"
        raise DeepResearchUnavailable(
            f"Deep Research model refused to produce the final report: "
            f"\"{snippet}\""
        )

    report_text, url_citations = _extract_report_and_citations(response)

    if not report_text:
        raise DeepResearchUnavailable(
            "Deep Research job completed but the final assistant message "
            "was empty or could not be parsed."
        )

    elapsed_total = int(time.monotonic() - started_at)
    _emit(
        progress_cb,
        f"Deep Research complete — {len(url_citations)} citation(s), "
        f"~{len(report_text)} chars of report, total {elapsed_total}s.",
    )

    return report_text, url_citations
