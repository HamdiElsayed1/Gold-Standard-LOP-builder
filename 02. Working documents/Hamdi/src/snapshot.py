"""
Run-snapshot serialization for the LoP Builder.

A snapshot is a self-contained JSON document holding every artefact a
Streamlit run produced — intake package, context, synthesis, partner
answers, validation, dot-dash, BA support pack, rendered slide deck,
plus the three Evals reports. Uploading a snapshot back into the app
restores the session state so every step's existing "Done" view
renders without re-running any agents.

Design notes:
  - Pure logic, no Streamlit imports — the sidebar UI in `app.py`
    handles file I/O and `st.rerun()`. This module is unit-testable.
  - Pydantic v2 round-trip: `.model_dump()` to write, `.model_validate()`
    to read. Mirrors the orchestrator's existing JSON contract.
  - Raw upload bytes (PDFs / DOCX / PPTX in `processed_docs[*].bytes`)
    are intentionally dropped — see `_strip_doc_bytes`. The Step 0
    Done view only needs filename + tag, and re-running upstream
    agents on a restored session falls back to the extracted text.
  - Widget-internal state (`q_edit_*`, `dd_headline_*`,
    `voice_recording_*`, etc.) is not persisted. Gate edits and voice
    memos are intentionally fresh after a load.
  - `SCHEMA_VERSION` is checked on load; bumping it is a one-line
    change when the snapshot shape ever needs to evolve.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from schemas import (
    AnswerList,
    BASupportPack,
    ClientEvaluationReport,
    ContextDoc,
    DotDashDoc,
    IntakePackage,
    LopEvalReport,
    LossAnalysisReport,
    SlideDeck,
    SynthesisDoc,
    ValidationReport,
)


SCHEMA_VERSION = 1


# Pipeline artefacts: each entry maps a session-state key to the
# Pydantic model used to validate it on restore. `build_snapshot` walks
# this list when serializing; `apply_snapshot` walks it on the way back.
_ARTEFACTS: list[tuple[str, type]] = [
    ("intake_package",     IntakePackage),
    ("context_doc",        ContextDoc),
    ("synthesis_doc",      SynthesisDoc),
    ("answer_list",        AnswerList),
    ("validation_report",  ValidationReport),
    ("dotdash_doc",        DotDashDoc),
    ("ba_support_pack",    BASupportPack),
    ("slide_deck",         SlideDeck),
    ("client_eval_report", ClientEvaluationReport),
    ("loss_eval_report",   LossAnalysisReport),
    ("lop_eval_report",    LopEvalReport),
]

# Boolean step-completion flags surfaced in the sidebar progress.
# Restoring these makes every step render its Done view.
_DONE_FLAGS: list[str] = [
    "upload_done",
    "intake_done",
    "context_done",
    "synthesis_done",
    "gate_a_done",
    "answers_done",
    "validation_done",
    "gate_b_done",
    "dotdash_done",
    "gate_c_done",
    "ba_support_done",
    "slides_done",
    "client_eval_done",
    "loss_eval_done",
]

# Loose metadata — plain strings / scalars that the Done views read
# directly. `lop_sidebar_view` is intentionally excluded so loading a
# snapshot does not yank the user out of whatever view they are in.
_METADATA_KEYS: list[str] = [
    "voice_transcript",
    "answers_source",
    "answers_generated",
    "step0_partner_text",
    "step0_partner_text_title",
    "step0_structured_memo",
    "step0_structured_memo_done",
    "client_style_summary",
    "slide_format_mode",
    "loss_eval_competitor_override",
    "lop_eval_extra_notes",
]


# ─── PIPELINE CUTOFF SUPPORT ──────────────────────────────────────────
#
# The sidebar "Save until: <step>" selector lets the partner ship a
# partial snapshot that includes only steps up to and including the
# chosen cutoff. Everything downstream is emitted as `None` / `False` /
# `""` so the loaded session presents as a clean intermediate
# checkpoint. The Evals reviewers are not part of this linear order —
# they ride on a separate `include_evals` toggle.

# Ordered list of linear-pipeline done flags. Mirrors `_STEPS` in
# `app.py`; if a step is added there, add it here too.
_PIPELINE_ORDER: list[str] = [
    "upload_done",
    "intake_done",
    "context_done",
    "synthesis_done",
    "gate_a_done",
    "answers_done",
    "validation_done",
    "gate_b_done",
    "dotdash_done",
    "gate_c_done",
    "ba_support_done",
    "slides_done",
]

# Evals reviewers — independently gated by `include_evals`.
_EVALS_FLAGS: set[str] = {"client_eval_done", "loss_eval_done"}
_EVALS_ARTEFACTS: set[str] = {
    "client_eval_report",
    "loss_eval_report",
    "lop_eval_report",
}
_EVALS_METADATA: set[str] = {
    "loss_eval_competitor_override",
    "lop_eval_extra_notes",
}

# Step ownership — for each pipeline done flag, which artefact keys
# and metadata keys belong to that step. `build_snapshot` zeroes out
# everything whose owning step falls outside the cutoff.
_STEP_OWNERSHIP: dict[str, dict[str, list[str]]] = {
    "upload_done":     {
        "artefacts": [],
        "metadata":  [
            "step0_partner_text",
            "step0_partner_text_title",
            "step0_structured_memo",
            "step0_structured_memo_done",
        ],
    },
    "intake_done":     {"artefacts": ["intake_package"],    "metadata": []},
    "context_done":    {"artefacts": ["context_doc"],       "metadata": []},
    "synthesis_done":  {"artefacts": ["synthesis_doc"],     "metadata": []},
    "gate_a_done":     {"artefacts": [],                    "metadata": []},
    "answers_done":    {
        "artefacts": ["answer_list"],
        "metadata":  ["voice_transcript", "answers_source", "answers_generated"],
    },
    "validation_done": {"artefacts": ["validation_report"], "metadata": []},
    "gate_b_done":     {"artefacts": [],                    "metadata": []},
    "dotdash_done":    {"artefacts": ["dotdash_doc"],       "metadata": []},
    "gate_c_done":     {"artefacts": [],                    "metadata": []},
    "ba_support_done": {"artefacts": ["ba_support_pack"],   "metadata": []},
    "slides_done":     {
        "artefacts": ["slide_deck"],
        "metadata":  ["slide_format_mode", "client_style_summary"],
    },
}


def latest_completed_step(ss) -> str:
    """Return the last `True` flag in `_PIPELINE_ORDER`.

    Falls back to the first pipeline step (`upload_done`) when nothing
    is done yet, so the sidebar selectbox always has a sensible
    default index.
    """
    latest = _PIPELINE_ORDER[0]
    for flag in _PIPELINE_ORDER:
        if ss.get(flag):
            latest = flag
    return latest


def _allowed_pipeline_flags(cutoff_step: str | None) -> set[str]:
    """Return the set of pipeline flags up to and including `cutoff_step`.

    `cutoff_step=None` means "save everything" — every flag in
    `_PIPELINE_ORDER` is allowed. An unknown cutoff_step falls back to
    "everything" so a stale UI selection never silently truncates more
    than the user expected.
    """
    if not cutoff_step or cutoff_step not in _PIPELINE_ORDER:
        return set(_PIPELINE_ORDER)
    idx = _PIPELINE_ORDER.index(cutoff_step)
    return set(_PIPELINE_ORDER[: idx + 1])


def _owning_step(key: str) -> str | None:
    """Return the pipeline-flag that owns `key` (artefact or metadata).

    Returns `None` for Evals artefacts/metadata (they are not in the
    linear pipeline order) and for unknown keys.
    """
    for flag, owned in _STEP_OWNERSHIP.items():
        if key in owned["artefacts"] or key in owned["metadata"]:
            return flag
    return None


_UNSAFE_FILENAME_CHARS = '<>:"/\\|?*'


def sanitize_snapshot_filename(name: str, fallback: str) -> str:
    """Coerce user-supplied filename into something safe for download.

    - Trims whitespace; empty input falls back to `fallback`.
    - Replaces filesystem-unsafe chars with `_`.
    - Appends `.json` when the caller forgot it.
    """
    cleaned = (name or "").strip()
    if not cleaned:
        cleaned = fallback
    for ch in _UNSAFE_FILENAME_CHARS:
        cleaned = cleaned.replace(ch, "_")
    if not cleaned.lower().endswith(".json"):
        cleaned += ".json"
    return cleaned


def _strip_doc_bytes(doc: dict) -> dict:
    """Return a copy of a `processed_docs` entry with raw bytes removed.

    Keeps the fields the rest of the app actually consults after Step 0
    is confirmed: filename, doc_type, is_pdf, extracted text. The
    `bytes` field is replaced with an empty-bytes marker so any later
    code that inspects it sees a consistent shape.
    """
    return {
        "filename": doc.get("filename", ""),
        "doc_type": doc.get("doc_type", ""),
        "is_pdf":   bool(doc.get("is_pdf", False)),
        "text":     doc.get("text", "") or "",
        "bytes":    b"",  # intentionally dropped; see module docstring
    }


def build_snapshot(
    ss,
    cutoff_step: str | None = None,
    include_evals: bool = True,
) -> dict[str, Any]:
    """Serialize the live session state into a JSON-safe dict.

    Parameters
    ----------
    ss
        Live `st.session_state` (or any mapping-like).
    cutoff_step
        A pipeline flag from `_PIPELINE_ORDER` (e.g. `"synthesis_done"`).
        Only steps up to and including this flag are serialized;
        downstream artefacts / flags / metadata are emitted as `None` /
        `False` / `""`. `None` (the default) means "save everything".
    include_evals
        When `False`, the Evals reviewer reports + done flags +
        Evals-only metadata are omitted regardless of cutoff. When
        `True`, they are included if present in `ss`.

    Pydantic artefacts are dumped via `.model_dump()`; `processed_docs`
    keeps metadata + extracted text but drops raw bytes.
    """
    allowed = _allowed_pipeline_flags(cutoff_step)

    # Artefacts — gated by their owning step (or by include_evals for
    # Evals reports).
    pipeline: dict[str, Any] = {}
    for key, _model in _ARTEFACTS:
        if key in _EVALS_ARTEFACTS:
            if not include_evals:
                pipeline[key] = None
                continue
        else:
            owner = _owning_step(key)
            if owner is not None and owner not in allowed:
                pipeline[key] = None
                continue

        obj = ss.get(key)
        if obj is None:
            pipeline[key] = None
            continue
        try:
            pipeline[key] = obj.model_dump(mode="json")
        except AttributeError:
            # Defensive: object that isn't a Pydantic model. Skip.
            pipeline[key] = None

    # Done flags — pipeline flags gated by cutoff, Evals flags gated by
    # `include_evals`.
    done_flags: dict[str, bool] = {}
    for flag in _DONE_FLAGS:
        if flag in _EVALS_FLAGS:
            done_flags[flag] = bool(include_evals and ss.get(flag, False))
        elif flag in allowed:
            done_flags[flag] = bool(ss.get(flag, False))
        else:
            done_flags[flag] = False

    # Loose metadata — same gating rules. Evals-only metadata follows
    # `include_evals`; everything else follows its owning step.
    metadata: dict[str, Any] = {}
    for key in _METADATA_KEYS:
        if key in _EVALS_METADATA:
            metadata[key] = ss.get(key) if include_evals else _empty_like(ss.get(key))
            continue
        owner = _owning_step(key)
        if owner is not None and owner not in allowed:
            metadata[key] = _empty_like(ss.get(key))
        else:
            metadata[key] = ss.get(key)

    # `processed_docs` belongs to Step 0 (Upload Documents). Drop it
    # entirely when Step 0 is outside the cutoff.
    if "upload_done" in allowed:
        uploads = [
            _strip_doc_bytes(d) for d in (ss.get("processed_docs") or [])
        ]
        for u in uploads:
            u["bytes"] = ""
    else:
        uploads = []

    return {
        "schema_version": SCHEMA_VERSION,
        "saved_at":       datetime.utcnow().isoformat() + "Z",
        "run_id":         ss.get("run_id", ""),
        "cutoff_step":    cutoff_step or "",
        "include_evals":  bool(include_evals),
        "done_flags":     done_flags,
        "pipeline":       pipeline,
        "uploads":        uploads,
        "metadata":       metadata,
    }


def _empty_like(value: Any) -> Any:
    """Return a 'cleared' value of the same general shape as `value`.

    Used when zeroing out metadata that falls outside the cutoff so the
    JSON snapshot keeps consistent types (e.g. `""` for strings,
    `False` for bools, `[]` for lists, `None` otherwise).
    """
    if isinstance(value, str):
        return ""
    if isinstance(value, bool):
        return False
    if isinstance(value, list):
        return []
    if isinstance(value, dict):
        return {}
    return None


def apply_snapshot(snapshot: dict[str, Any], ss) -> tuple[bool, str]:
    """Restore session state from a snapshot dict.

    Returns `(ok, message)` so the caller can render a Streamlit toast
    or error. Validates `schema_version` before touching state; on
    mismatch, leaves the session untouched and returns a clear error.

    Per-artefact rehydration is wrapped in try/except so one bad block
    (e.g. an older shape that no longer validates) does not abort the
    entire restore — it is reported in the returned message and skipped.
    """
    if not isinstance(snapshot, dict):
        return False, "Snapshot is not a JSON object."

    version = snapshot.get("schema_version")
    if version != SCHEMA_VERSION:
        return (
            False,
            f"Snapshot schema version mismatch: got {version!r}, "
            f"expected {SCHEMA_VERSION}. Refusing to load.",
        )

    pipeline = snapshot.get("pipeline") or {}
    done_flags = snapshot.get("done_flags") or {}
    metadata = snapshot.get("metadata") or {}
    uploads = snapshot.get("uploads") or []

    skipped: list[str] = []

    for key, model in _ARTEFACTS:
        raw = pipeline.get(key)
        if raw is None:
            ss[key] = None
            continue
        try:
            ss[key] = model.model_validate(raw)
        except Exception as exc:
            ss[key] = None
            skipped.append(f"{key} ({type(exc).__name__})")

    for flag in _DONE_FLAGS:
        ss[flag] = bool(done_flags.get(flag, False))

    for key in _METADATA_KEYS:
        if key in metadata:
            ss[key] = metadata[key]

    # `processed_docs` — restore filename / tag / text and a sentinel
    # bytes placeholder. The Step 0 Done view only renders filename +
    # tag, so this is enough for the UI to look correct.
    restored_docs: list[dict] = []
    for d in uploads:
        restored_docs.append(
            {
                "filename": d.get("filename", ""),
                "doc_type": d.get("doc_type", ""),
                "is_pdf":   bool(d.get("is_pdf", False)),
                "text":     d.get("text", "") or "",
                "bytes":    b"",  # raw bytes intentionally not persisted
            }
        )
    ss["processed_docs"] = restored_docs

    # Reset transient widget-internal state that does not survive a
    # restore: gate edits, voice-memo widgets, dot-dash chapter edits.
    # Any value left over from the current session would confuse the
    # newly-restored model artefacts.
    _purge_widget_keys(ss)

    msg_parts: list[str] = [
        f"Snapshot loaded (saved {snapshot.get('saved_at', 'unknown')}, "
        f"original run {snapshot.get('run_id', 'unknown')})."
    ]
    if skipped:
        msg_parts.append(
            "Some blocks could not be validated and were skipped: "
            + ", ".join(skipped)
        )
    return True, " ".join(msg_parts)


def _purge_widget_keys(ss) -> None:
    """Drop widget-internal session keys so a restored run starts clean.

    The pipeline's gate-edit widgets, voice-recording widgets, inline
    dot-dash edits, and the sidebar snapshot controls all live under
    predictable key prefixes. They are repopulated by their owning
    widgets on the next render — and we want them re-initialized
    against the freshly restored session, not against the previous
    one. In particular, the `snapshot_*` keys (cutoff selector,
    include-Evals checkbox, custom filename) should reset to
    sensible defaults derived from the new state.
    """
    prefixes = (
        "q_edit_",
        "dd_headline_",
        "dd_dash_",
        "voice_recording_",
        "voice_upload_",
        "answer_edit_",
        "snapshot_",
    )
    for key in [k for k in list(ss.keys()) if k.startswith(prefixes)]:
        del ss[key]
