"""
LoP Builder — Phase 1 Streamlit Application

Run from the src/ directory:
    pip install -r requirements.txt
    cp .env.example .env          # then add your OPENAI_API_KEY
    streamlit run app.py
"""

import json
import os
import sys
import traceback
from datetime import datetime
from io import BytesIO
from pathlib import Path

import streamlit as st
from docx import Document as DocxDocument
from dotenv import load_dotenv

# ─── PATH + ENV ───────────────────────────────────────────────────────────────
sys.path.insert(0, str(Path(__file__).parent))


def _find_working_documents_dir() -> Path | None:
    """Walk upward until we find the folder named '02. Working documents'."""
    here = Path(__file__).resolve()
    for parent in [here, *here.parents]:
        if parent.name == "02. Working documents":
            return parent
    return None


def _resolve_user_folder() -> Path | None:
    """Resolve the current user's folder under 02. Working documents."""
    working_docs = _find_working_documents_dir()
    if working_docs is None or not working_docs.exists():
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
        # e.g., Alexander_Veldhuijzen -> Alexander
        if "_" in cleaned:
            hints.append(cleaned.split("_", 1)[0])

    # De-duplicate while preserving order
    deduped_hints = list(dict.fromkeys(hints))

    subdirs = [d for d in working_docs.iterdir() if d.is_dir()]
    by_lower = {d.name.lower(): d for d in subdirs}
    for hint in deduped_hints:
        direct = by_lower.get(hint.lower())
        if direct:
            return direct
        # Fallback prefix match for usernames that include suffixes.
        for d in subdirs:
            d_lower = d.name.lower()
            h_lower = hint.lower()
            if d_lower.startswith(h_lower) or h_lower.startswith(d_lower):
                return d
    return None


def _load_user_env() -> Path | None:
    """Load API keys from the user's own folder."""
    user_folder = _resolve_user_folder()
    if not user_folder:
        return None

    for name in ("api-keys.env", ".env"):
        env_path = user_folder / name
        if env_path.exists():
            load_dotenv(env_path, override=True)
            return env_path
    return None


_ENV_SOURCE = _load_user_env()

from mock_answers import generate_mock_answers
from orchestrator import run_agent
from run_logger import (
    get_run_logger,
    log_agent_result,
    log_agent_start,
    log_event,
    log_gate_event,
    log_session_start,
)
from schemas import (
    Answer,
    AnswerList,
    ContextDoc,
    DotDashDoc,
    DotDashSlide,
    IntakePackage,
    LopEvalReport,
    Question,
    QuestionList,
    SynthesisDoc,
    ValidationReport,
)

# ─── PAGE CONFIG ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="LoP Builder — Phase 1",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── SESSION STATE INIT ───────────────────────────────────────────────────────
_DEFAULTS: dict = {
    "processed_docs": [],
    "upload_done": False,
    "intake_package": None,
    "intake_done": False,
    "context_doc": None,
    "context_done": False,
    "synthesis_doc": None,
    "synthesis_done": False,
    "gate_a_done": False,
    "answer_list": None,
    "answers_generated": False,
    "answers_done": False,
    "validation_report": None,
    "validation_done": False,
    "gate_b_done": False,
    "dotdash_doc": None,
    "dotdash_done": False,
    "gate_c_done": False,
}
for _k, _v in _DEFAULTS.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v

ss = st.session_state

# Assign a unique run ID to this session (persists across Streamlit reruns)
if "run_id" not in ss:
    ss.run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_session_start(ss.run_id)

_, _log_path = get_run_logger(ss.run_id)

# ─── STEP DEFINITIONS ────────────────────────────────────────────────────────
_STEPS = [
    ("upload_done",     "Upload Documents"),
    ("intake_done",     "Intake Agent"),
    ("context_done",    "Context Agent"),
    ("synthesis_done",  "Synthesis Agent"),
    ("gate_a_done",     "Gate A — Approve Questions"),
    ("answers_done",    "Mock Answers"),
    ("validation_done", "Validation Agent"),
    ("gate_b_done",     "Gate B — Approve to Dot-Dash"),
    ("dotdash_done",    "Dot-Dash Agent"),
    ("gate_c_done",     "Gate C — Approve Dot-Dash"),
]

# ─── HELPERS ─────────────────────────────────────────────────────────────────

def _quality_badge(quality: str) -> None:
    if quality == "complete":
        st.success("complete")
    elif quality == "partial":
        st.warning("partial")
    else:
        st.error("missing")


def _completeness_badge(completeness: str) -> None:
    if completeness == "complete":
        st.success("complete")
    elif completeness == "partial":
        st.warning("partial")
    else:
        st.error("missing")


def _infer_direct_input_type(text: str) -> str:
    """Infer direct-input document type from common cue words."""
    t = text.lower()
    if any(token in t for token in ("best practice", "winning lop", "proposal example", "past proposal")):
        return "Best Practice LoP"
    if any(token in t for token in ("rfi", "request for information")):
        return "RFI"
    if any(token in t for token in ("rfp", "request for proposal", "scope of work", "sow")):
        return "RFP"
    return "RFP"


def _format_dotdash_for_eval(dd: DotDashDoc) -> str:
    """Serialize dot-dash storyline for Gold Standard evaluation."""
    chunks: list[str] = [
        "## Dot-dash storyline (primary LoP spine)",
        "",
        "### Storyline summary",
        dd.storyline_summary.strip(),
        "",
        "### Slide-by-slide",
        "",
    ]
    for slide in dd.slides:
        chunks.append(f"#### {slide.chapter} _(confidence: {slide.confidence})_")
        chunks.append(slide.headline.strip())
        for pt in slide.supporting_points:
            chunks.append(f"- {pt}")
        if slide.notes:
            chunks.append(f"_Notes:_ {slide.notes}")
        chunks.append("")
    if dd.open_risks:
        chunks.append("### Open risks flagged in dot-dash")
        for r in dd.open_risks:
            chunks.append(f"- {r}")
        chunks.append("")
    return "\n".join(chunks).strip()


def _assemble_pipeline_eval_document() -> tuple[str | None, str]:
    """
    Concatenate pipeline artefacts into one evaluation payload.

    Returns (document_or_none, hint_for_ui).
    """
    has_syn = bool(ss.get("synthesis_done") and ss.get("synthesis_doc"))
    has_dd = bool(ss.get("dotdash_done") and ss.get("dotdash_doc"))
    if not has_syn and not has_dd:
        return (
            None,
            "Run **Pipeline** through at least **Synthesis** (ideally **Dot-Dash**) "
            "before evaluating.",
        )

    lines: list[str] = [
        "# Letter of Proposal — assembled from LoP Builder pipeline output",
        "",
        "_Auto-built from this session: intake, context, synthesis, validation "
        "(if available), and dot-dash (if available). Not a client PDF export._",
        "",
    ]

    if ss.get("intake_package"):
        ip = ss.intake_package
        lines.extend(
            [
                "## Intake package",
                f"- **Client:** {ip.client_name}",
                f"- **Industry:** {ip.industry}",
                f"- **Geography:** {ip.geography}",
                f"- **Problem area:** {ip.problem_area}",
                "",
            ]
        )
        if ip.gap_list:
            lines.append("### Gap list (excerpt)")
            for g in ip.gap_list[:15]:
                lines.append(f"- {g}")
            if len(ip.gap_list) > 15:
                lines.append(f"- _(…{len(ip.gap_list) - 15} more gaps omitted)_")
            lines.append("")

    if ss.get("context_doc"):
        ctx = ss.context_doc
        lines.extend(
            [
                "## Context agent _(model knowledge — validate before client use)_",
                "### Client profile",
                ctx.client_profile.strip(),
                "",
                "### Market trends",
                ctx.market_trends.strip(),
                "",
                "### Competitive landscape",
                ctx.competitive_landscape.strip(),
                "",
            ]
        )

    if ss.get("synthesis_doc"):
        syn = ss.synthesis_doc
        lines.extend(
            [
                "## Synthesis",
                "### Brief summary",
                syn.brief_summary.strip(),
                "",
                "### Problem statement",
                syn.problem_statement.strip(),
                "",
                "### Win themes",
                *[f"- {w}" for w in syn.win_themes],
                "",
            ]
        )

    if ss.get("answers_done") and ss.get("answer_list") and ss.get("synthesis_doc"):
        lines.append("## Partner answers (mock or confirmed)")
        q_map = {q.id: q for q in ss.synthesis_doc.question_list.questions}
        for ans in ss.answer_list.answers:
            q = q_map.get(ans.question_id)
            ch = f"{q.chapter}" if q else "?"
            qt = q.question if q else ""
            excerpt = ans.answer_text.strip()
            if len(excerpt) > 1200:
                excerpt = excerpt[:1200] + "…"
            lines.append(f"- **{ans.question_id}** ({ch})  ")
            lines.append(f"  _Question:_ {qt}")
            lines.append(f"  _Answer:_ {excerpt}")
            lines.append("")

    if ss.get("validation_done") and ss.get("validation_report"):
        vr = ss.validation_report
        lines.extend(
            [
                "## Validation snapshot",
                f"- **Readiness score:** {vr.readiness_score}/100",
                f"- **Overall readiness:** {vr.overall_readiness}",
                f"- **Can proceed to dot-dash:** {vr.can_proceed_to_dot_dash}",
                f"- **Recommendation:** {vr.recommendation.strip()}",
                "",
            ]
        )
        if vr.dot_dash_blockers:
            lines.append("### Dot-dash blockers / risks")
            for b in vr.dot_dash_blockers:
                lines.append(f"- {b}")
            lines.append("")

    if ss.get("dotdash_done") and ss.get("dotdash_doc"):
        lines.append(_format_dotdash_for_eval(ss.dotdash_doc))
        hint = (
            "Evaluation uses **full pipeline assembly**, including **dot-dash** "
            "(slide spine)."
        )
    else:
        lines.append(
            "## Dot-dash storyline\n\n"
            "_Not generated in this session yet — scores reflect upstream "
            "artefacts only (no slide spine)._"
        )
        hint = (
            "Evaluation uses pipeline outputs **without dot-dash** "
            "(complete Dot-Dash in Pipeline for slide-level review)."
        )

    return "\n".join(lines).strip(), hint


def _best_practice_reference_text() -> str | None:
    """Plain-text excerpts from uploaded Best Practice LoP inputs (TXT/DOCX only)."""
    docs = ss.get("processed_docs") or []
    chunks: list[str] = []
    for d in docs:
        if d.get("doc_type") != "Best Practice LoP":
            continue
        txt = (d.get("text") or "").strip()
        if not txt:
            continue
        fn = d.get("filename", "unknown")
        chunks.append(f"### {fn}\n\n{txt}")
    if not chunks:
        return None
    return "\n\n---\n\n".join(chunks)


def _show_agent_error(agent_label: str, exc: Exception) -> None:
    """Render actionable agent errors, especially for network/API failures."""
    err_text = str(exc).strip() or exc.__class__.__name__
    cause = exc.__cause__ or exc.__context__
    cause_chain: list[str] = []
    while cause:
        cause_chain.append(f"{cause.__class__.__name__}: {cause}")
        cause = cause.__cause__ or cause.__context__
    cause_text = " -> ".join(cause_chain)

    st.error(f"{agent_label} failed: {err_text}")
    if cause_text:
        st.caption(f"Underlying cause: {cause_text}")

    combined = f"{err_text} {cause_text}".lower()
    if any(
        token in combined
        for token in ("connection error", "proxy", "timeout", "timed out", "dns", "ssl")
    ):
        env_hint = str(_ENV_SOURCE) if _ENV_SOURCE else "02. Working documents/<YourName>/api-keys.env"
        st.info(
            "Connection troubleshooting:\n"
            "- Confirm VPN / corporate network is active.\n"
            f"- Check `{env_hint}` has valid `OPENAI_BASE_URL`, `OPENAI_API_KEY`, and `OPENAI_MODEL`.\n"
            "- Refresh `OPENAI_API_KEY` if your JWT is older than ~24h.\n"
            "- Run `python test_api.py` from `Hamdi/src` to verify connectivity."
        )


def _reset_from(step: str) -> None:
    """Clear state for `step` and all downstream steps."""
    _order = [
        "intake", "context", "synthesis", "gate_a",
        "answers", "validation", "gate_b", "dotdash", "gate_c",
    ]
    if step not in _order:
        return
    idx = _order.index(step)

    # Flags
    for s in _order[idx:]:
        ss[f"{s}_done"] = False

    # Data blobs per step
    _data: dict[str, list] = {
        "intake":     ["intake_package"],
        "context":    ["context_doc"],
        "synthesis":  ["synthesis_doc"],
        "gate_a":     [],
        "answers":    ["answer_list"],
        "validation": ["validation_report"],
        "gate_b":     [],
        "dotdash":    ["dotdash_doc"],
        "gate_c":     [],
    }
    for s in _order[idx:]:
        for field in _data.get(s, []):
            ss[field] = None
    if "answers" in _order[idx:]:
        ss.answers_generated = False

    # Clear Gate A question edits when synthesis is reset
    if idx <= _order.index("synthesis"):
        for key in [k for k in ss.keys() if k.startswith("q_edit_")]:
            del ss[key]

    # Clear Gate C dot-dash edits when dot-dash is reset
    if idx <= _order.index("dotdash"):
        for key in [
            k for k in ss.keys()
            if k.startswith("dd_headline_")
            or k.startswith("dd_dashes_")
            or k.startswith("dd_notes_")
        ]:
            del ss[key]


# ─── SIDEBAR ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("LoP Builder")
    st.caption("Phase 1 — Intake → Synthesis → Gate A → Mocks → Validation → Gate B → Dot-Dash → Gate C")
    st.divider()

    for _flag, _label in _STEPS:
        if ss.get(_flag):
            st.success(_label)
        else:
            st.text(_label)

    st.divider()
    st.markdown("**Evals**")
    st.caption("Assess a drafted LoP against the Gold Standard rubric.")
    app_section = st.radio(
        "View",
        ["Pipeline", "Evals"],
        key="lop_sidebar_view",
        label_visibility="collapsed",
    )
    if app_section == "Evals":
        st.selectbox(
            "Evaluation agent",
            ["Gold Standard LoP Quality"],
            key="lop_eval_agent_choice",
            help="Runs on the assembled Pipeline output from this session.",
        )

    st.divider()
    st.caption(f"Model: {os.environ.get('OPENAI_MODEL', 'gpt-4o')}")
    st.caption(f"Run: {ss.run_id}")
    st.caption(
        "Env: "
        + (str(_ENV_SOURCE) if _ENV_SOURCE else "No user API key file found")
    )
    if _log_path.exists():
        st.caption(f"Log: runs/{_log_path.name}")

    if st.button("Start Over", use_container_width=True):
        log_event(ss.run_id, "SESSION ended by user (Start Over)")
        for _k in list(ss.keys()):
            del ss[_k]
        st.rerun()

# ─── HEADER (pipeline only; Evals uses its own header below) ────────────────

if not os.environ.get("OPENAI_API_KEY"):
    expected_path = "02. Working documents/<YourName>/api-keys.env"
    if _ENV_SOURCE is not None:
        expected_path = str(_ENV_SOURCE)
    st.error(
        "**OPENAI_API_KEY not set.**  \n"
        "This app expects API keys in your personal folder under "
        f"`{expected_path}`.  \n"
        "Add your key there and restart: `streamlit run app.py`"
    )
    st.stop()

# Resolve sidebar mode (same key as sidebar radio)
_app_section = ss.get("lop_sidebar_view", "Pipeline")

# ─── EVALS (Gold Standard LoP Quality) ───────────────────────────────────────
if _app_section == "Evals":
    st.title("Evals — Gold Standard LoP Quality")
    st.caption(
        "Runs on the **assembled output of this session’s Pipeline** "
        "(intake → context → synthesis → answers → validation → dot-dash). "
        "Advisory only — confirm client facts against your Y-manifest sources."
    )

    assembled, bundle_hint = _assemble_pipeline_eval_document()
    st.info(bundle_hint)

    ref_txt = _best_practice_reference_text()
    if ref_txt:
        st.success(
            "LLM-as-judge: **Best Practice LoP** text from Step 0 is included as the "
            "**gold reference** for this evaluation."
        )
    elif ss.get("upload_done"):
        st.caption(
            "**Gold reference (optional):** upload and tag a **Best Practice LoP** "
            "(TXT or DOCX) in Step 0 to enable automatic reference comparison."
        )

    if assembled:
        with st.expander("Preview pipeline bundle sent to evaluator", expanded=False):
            st.markdown(assembled)

    st.text_area(
        "Optional notes for the evaluator",
        height=100,
        key="lop_eval_extra_notes",
        placeholder=(
            "Anything to stress for the reviewer (e.g., pending partner edits, "
            "sections intentionally thin)."
        ),
        help="Appended after the auto-assembled pipeline output when you click Run.",
    )

    if assembled is None:
        st.warning(
            "No pipeline output to evaluate yet. Open **Pipeline**, run through "
            "at least **Synthesis** (ideally **Dot-Dash**), then return here."
        )

    col_run, col_disc = st.columns([1, 2])
    with col_run:
        run_eval = st.button(
            "Run evaluation",
            type="primary",
            key="lop_eval_run",
            disabled=assembled is None,
        )
    with col_disc:
        if st.button("Discard last report", key="lop_eval_discard"):
            ss.lop_eval_report = None
            st.rerun()

    if run_eval:
        body_base = assembled
        if body_base is None:
            st.warning("Nothing to evaluate — complete Pipeline steps first.")
        else:
            extra = (ss.get("lop_eval_extra_notes") or "").strip()
            body = body_base
            if extra:
                body += (
                    "\n\n---\n\n## Reviewer-supplied notes\n\n"
                    f"{extra}\n"
                )
            ref_anchor = _best_practice_reference_text()
            eval_msg_parts = [
                "Evaluate per your system instructions.",
                "",
                "--- RESPONSE TO EVALUATE (ASSEMBLED PIPELINE OUTPUT) ---",
                "",
                body,
                "",
                "--- REFERENCE (GOLD / BEST-PRACTICE ANCHOR) ---",
                "",
            ]
            if ref_anchor:
                eval_msg_parts.append(ref_anchor)
            else:
                eval_msg_parts.append(
                    "(None supplied — no extractable Best Practice LoP text in this "
                    "session. Set reference_judgement.reference_provided to false.)"
                )
            eval_message = "\n".join(eval_msg_parts)
            with st.spinner(
                "Gold Standard evaluation running — reviewing 10 core elements "
                "and best-practice markers (30–90 seconds)..."
            ):
                try:
                    log_agent_start(
                        ss.run_id,
                        "lop-quality-eval-agent",
                        f"{len(body)} chars bundle; ref={'yes' if ref_anchor else 'no'}",
                    )
                    result = run_agent(
                        "lop-quality-eval-agent",
                        user_message=eval_message,
                        files=None,
                        use_extended_thinking=True,
                    )
                    log_agent_result(ss.run_id, "lop-quality-eval-agent", result)
                    ss.lop_eval_report = LopEvalReport.model_validate(result)
                    st.rerun()
                except Exception as exc:
                    traceback.print_exc()
                    log_event(ss.run_id, f"[LOP QUALITY EVAL] ERROR: {exc}")
                    _show_agent_error("LoP Quality Evaluation", exc)

    if ss.get("lop_eval_report"):
        rep: LopEvalReport = ss.lop_eval_report
        st.divider()
        st.subheader("1. Executive summary & overall verdict")
        m1, m2 = st.columns(2)
        m1.metric("Overall score", f"{rep.overall_score} / 10")
        m2.metric("Verdict", rep.verdict)
        st.markdown(rep.high_level_feedback)

        st.subheader("Reference comparison (LLM-as-judge)")
        rj = rep.reference_judgement
        if not rj.reference_provided:
            st.caption(rj.reasoning or "No gold reference was used for this run.")
        elif rj.score == 1:
            st.success(f"**PASS (1)** — {rj.reasoning}")
        elif rj.score == 0:
            st.error(f"**FAIL (0)** — {rj.reasoning}")
        else:
            st.warning(rj.reasoning or "Reference provided but score unset.")

        st.subheader("2. The 10 elements breakdown")
        for el in rep.elements_breakdown:
            status = el.status.lower()
            if status == "strong":
                st.success(f"**{el.element_name}** — {el.status}")
            elif status == "missing":
                st.error(f"**{el.element_name}** — {el.status}")
            else:
                st.warning(f"**{el.element_name}** — {el.status}")
            st.markdown(f"*Feedback:* {el.feedback}")

        st.subheader("3. Best practices assessment")
        st.markdown(f"**Storyline:** {rep.storyline}")
        st.markdown(f"**Client-centricity:** {rep.client_centricity}")
        st.markdown(f"**Brevity:** {rep.brevity}")
        st.markdown(f"**The magic moment:** {rep.magic_moment}")

        st.subheader("4. Top 3 action items")
        for i, item in enumerate(rep.top_action_items, start=1):
            st.markdown(f"{i}. {item}")

    st.stop()

st.title("LoP Builder — Phase 1")
st.caption(
    "Upload  →  Intake  →  Context  →  Synthesis  →  Gate A  →  "
    "Mock Answers  →  Validation  →  Gate B  →  Dot-Dash  →  Gate C"
)

_done_count = sum(ss.get(f, False) for f, _ in _STEPS)
st.progress(_done_count / len(_STEPS))
st.divider()


# ─────────────────────────────────────────────────────────────────────────────
# STEP 0 — UPLOAD DOCUMENTS
# ─────────────────────────────────────────────────────────────────────────────
st.subheader("Step 0 — Upload Documents or Enter Text")

if ss.upload_done:
    with st.expander(
        f"Uploaded — {len(ss.processed_docs)} document(s) confirmed", expanded=False
    ):
        for d in ss.processed_docs:
            st.caption(f"{d['filename']}  [{d['doc_type']}]")
        if st.button("Change uploads (resets all downstream steps)"):
            ss.upload_done = False
            ss.processed_docs = []
            _reset_from("intake")
            st.rerun()
else:
    st.info(
        "Upload your RFP / RFI documents and any best-practice LoP reference files, "
        "or paste relevant content directly below. Tag each input with its type, then "
        "click **Confirm Inputs**."
    )

    uploaded = st.file_uploader(
        "Select files (PDF, DOCX, or TXT — multiple files allowed)",
        accept_multiple_files=True,
        type=["pdf", "docx", "txt"],
    )

    if uploaded:
        st.markdown("**Tag each document:**")
        hdr = st.columns([5, 2])
        hdr[0].markdown("Filename")
        hdr[1].markdown("Type")
        for f in uploaded:
            row = st.columns([5, 2])
            row[0].write(f.name)
            row[1].selectbox(
                "type",
                ["RFP", "RFI", "Best Practice LoP"],
                key=f"tag_{f.name}",
                label_visibility="collapsed",
            )

    st.markdown("**Or enter relevant information directly:**")
    direct_title = st.text_input(
        "Direct input title (optional)",
        value="Direct Input Notes",
        help="Used as the filename label for this text input.",
    )
    direct_text = st.text_area(
        "Direct input text",
        height=180,
        placeholder="Paste key client context, notes, or other relevant content here.",
    )
    if direct_text.strip():
        st.caption(f"Inferred input type: {_infer_direct_input_type(direct_text)}")

    has_uploaded = bool(uploaded)
    has_direct_text = bool(direct_text.strip())

    if has_uploaded or has_direct_text:
        if st.button("Confirm Inputs", type="primary"):
            docs: list[dict] = []

            if uploaded:
                for f in uploaded:
                    doc_type = ss.get(f"tag_{f.name}", "RFP")
                    raw = f.getvalue()

                    if f.name.lower().endswith(".pdf"):
                        docs.append(
                            {
                                "filename": f.name,
                                "doc_type": doc_type,
                                "is_pdf": True,
                                "bytes": raw,
                                "text": "",
                            }
                        )
                    elif f.name.lower().endswith(".docx"):
                        docx_doc = DocxDocument(BytesIO(raw))
                        text = "\n\n".join(
                            p.text for p in docx_doc.paragraphs if p.text.strip()
                        )
                        docs.append(
                            {
                                "filename": f.name,
                                "doc_type": doc_type,
                                "is_pdf": False,
                                "bytes": b"",
                                "text": text,
                            }
                        )
                    else:  # .txt
                        docs.append(
                            {
                                "filename": f.name,
                                "doc_type": doc_type,
                                "is_pdf": False,
                                "bytes": b"",
                                "text": raw.decode("utf-8", errors="replace"),
                            }
                        )

            if has_direct_text:
                inferred_type = _infer_direct_input_type(direct_text)
                docs.append(
                    {
                        "filename": (direct_title.strip() or "Direct Input Notes") + ".txt",
                        "doc_type": inferred_type,
                        "is_pdf": False,
                        "bytes": b"",
                        "text": direct_text.strip(),
                    }
                )

            ss.processed_docs = docs
            ss.upload_done = True
            log_event(
                ss.run_id,
                f"[UPLOAD] {len(docs)} input document(s) confirmed: "
                + ", ".join(f"{d['filename']} [{d['doc_type']}]" for d in docs),
            )
            st.rerun()
    else:
        st.caption("Upload at least one file or enter text above to continue.")

st.divider()


# ─────────────────────────────────────────────────────────────────────────────
# STEP 1 — INTAKE AGENT
# ─────────────────────────────────────────────────────────────────────────────
if not ss.upload_done:
    st.text("Step 1 — Intake Agent  [complete upload first]")
    st.divider()
else:
    st.subheader("Step 1 — Intake Agent")

    if ss.intake_done and ss.intake_package:
        pkg: IntakePackage = ss.intake_package
        with st.expander(
            f"Done — {pkg.client_name}  |  {pkg.industry}  |  {len(pkg.gap_list)} gaps found",
            expanded=False,
        ):
            c1, c2 = st.columns(2)
            c1.metric("Client", pkg.client_name)
            c1.metric("Industry", pkg.industry)
            c2.metric("Geography", pkg.geography)
            c2.metric("Gaps", len(pkg.gap_list))

            st.markdown("**Chapter coverage:**")
            for b in pkg.chapter_buckets:
                row = st.columns([5, 1])
                row[0].markdown(f"**{b.chapter}**  — {b.notes}" if b.notes else f"**{b.chapter}**")
                with row[1]:
                    _quality_badge(b.quality)

            if pkg.gap_list:
                st.markdown("**Gap list:**")
                for g in pkg.gap_list:
                    st.markdown(f"- {g}")

            if pkg.key_facts:
                st.markdown("**Key facts:**")
                for kf in pkg.key_facts:
                    st.markdown(f"- {kf}")

        if st.button("Re-run Intake Agent", key="rerun_intake"):
            _reset_from("intake")
            st.rerun()
    else:
        st.write(
            "The Intake Agent reads your documents, classifies content by "
            "LoP chapter, extracts key facts and RFP requirements, and "
            "produces an explicit gap list."
        )
        if st.button("Run Intake Agent", type="primary", key="run_intake"):
            with st.spinner(
                "Intake Agent running — classifying documents and identifying gaps "
                "(may take 30–90 seconds)..."
            ):
                try:
                    doc_summary = ", ".join(
                        f"{d['filename']} [{d['doc_type']}]"
                        for d in ss.processed_docs
                    )
                    log_agent_start(ss.run_id, "intake-agent", doc_summary)
                    result = run_agent(
                        "intake-agent",
                        user_message=(
                            "Analyse the provided documents and produce a structured "
                            "intake package. Each document is labelled with its type "
                            "(RFP, RFI, or Best Practice LoP). Classify content across "
                            "all nine LoP chapters and identify every gap."
                        ),
                        files=ss.processed_docs,
                        use_extended_thinking=True,
                    )
                    log_agent_result(ss.run_id, "intake-agent", result)
                    ss.intake_package = IntakePackage.model_validate(result)
                    ss.intake_done = True
                    st.rerun()
                except Exception as exc:
                    traceback.print_exc()
                    log_event(ss.run_id, f"[INTAKE AGENT] ERROR: {exc}")
                    _show_agent_error("Intake Agent", exc)

    st.divider()


# ─────────────────────────────────────────────────────────────────────────────
# STEP 2 — CONTEXT AGENT
# ─────────────────────────────────────────────────────────────────────────────
if not ss.intake_done:
    st.text("Step 2 — Context Agent  [complete intake first]")
    st.divider()
else:
    st.subheader("Step 2 — Context Agent")

    if ss.context_done and ss.context_doc:
        ctx: ContextDoc = ss.context_doc
        with st.expander("Done — context document ready", expanded=False):
            st.markdown("**Client profile**")
            st.markdown(ctx.client_profile)
            st.markdown("**Market trends**")
            st.markdown(ctx.market_trends)
            st.markdown("**Competitive landscape**")
            st.markdown(ctx.competitive_landscape)
            if ctx.evidence_gaps:
                st.warning(
                    "Evidence gaps — validate before using in LoP:  \n"
                    + "\n".join(f"- {g}" for g in ctx.evidence_gaps)
                )
            st.info(f"Knowledge note: {ctx.knowledge_cutoff_note}")

        if st.button("Re-run Context Agent", key="rerun_context"):
            _reset_from("context")
            st.rerun()
    else:
        st.write(
            "The Context Agent uses the model's training knowledge to build a "
            "company profile and market picture. All output is clearly labelled "
            "as model knowledge — validate before using as evidence in the LoP."
        )
        if st.button("Run Context Agent", type="primary", key="run_context"):
            with st.spinner(
                "Context Agent running — building company and market context "
                "(30–90 seconds)..."
            ):
                try:
                    pkg = ss.intake_package
                    log_agent_start(
                        ss.run_id, "context-agent",
                        f"{pkg.client_name} | {pkg.industry} | {pkg.geography}",
                    )
                    intake_dict = pkg.model_dump()
                    result = run_agent(
                        "context-agent",
                        user_message=(
                            "Build a context document for this LoP pursuit.\n\n"
                            f"Intake Package:\n{json.dumps(intake_dict, indent=2)}"
                        ),
                        files=None,
                        use_extended_thinking=True,
                    )
                    log_agent_result(ss.run_id, "context-agent", result)
                    ss.context_doc = ContextDoc.model_validate(result)
                    ss.context_done = True
                    st.rerun()
                except Exception as exc:
                    traceback.print_exc()
                    log_event(ss.run_id, f"[CONTEXT AGENT] ERROR: {exc}")
                    _show_agent_error("Context Agent", exc)

    st.divider()


# ─────────────────────────────────────────────────────────────────────────────
# STEP 3 — SYNTHESIS AGENT
# ─────────────────────────────────────────────────────────────────────────────
if not ss.context_done:
    st.text("Step 3 — Synthesis Agent  [complete context first]")
    st.divider()
else:
    st.subheader("Step 3 — Synthesis Agent")

    if ss.synthesis_done and ss.synthesis_doc:
        syn: SynthesisDoc = ss.synthesis_doc
        with st.expander("Done — synthesis ready for Gate A review", expanded=False):
            st.markdown("**Problem statement**")
            st.info(syn.problem_statement)
            st.markdown("**Win themes**")
            for wt in syn.win_themes:
                st.markdown(f"- {wt}")
            st.caption(
                f"Question list: {len(syn.question_list.questions)} questions generated"
            )
    else:
        st.write(
            "The Synthesis Agent merges the intake package and context document "
            "into a synthesis brief, a problem statement, win themes, and a "
            "partner question list. The output goes to Gate A for review."
        )
        if st.button("Run Synthesis Agent", type="primary", key="run_synthesis"):
            with st.spinner(
                "Synthesis Agent running — producing brief and question list "
                "(30–90 seconds)..."
            ):
                try:
                    log_agent_start(ss.run_id, "synthesis-agent")
                    intake_dict = ss.intake_package.model_dump()
                    context_dict = ss.context_doc.model_dump()
                    result = run_agent(
                        "synthesis-agent",
                        user_message=(
                            "Produce a synthesis brief, problem statement, win themes, "
                            "and partner question list.\n\n"
                            f"Intake Package:\n{json.dumps(intake_dict, indent=2)}\n\n"
                            f"Context Document:\n{json.dumps(context_dict, indent=2)}"
                        ),
                        files=None,
                        use_extended_thinking=True,
                    )
                    log_agent_result(ss.run_id, "synthesis-agent", result)
                    ss.synthesis_doc = SynthesisDoc.model_validate(result)
                    ss.synthesis_done = True
                    st.rerun()
                except Exception as exc:
                    traceback.print_exc()
                    log_event(ss.run_id, f"[SYNTHESIS AGENT] ERROR: {exc}")
                    _show_agent_error("Synthesis Agent", exc)

    st.divider()


# ─────────────────────────────────────────────────────────────────────────────
# GATE A — REVIEW AND APPROVE QUESTION LIST
# ─────────────────────────────────────────────────────────────────────────────
if not ss.synthesis_done:
    st.text("Gate A — Review Question List  [complete synthesis first]")
    st.divider()
else:
    st.subheader("Gate A — Review and Approve Question List")

    if ss.gate_a_done:
        q_count = len(ss.synthesis_doc.question_list.questions)
        with st.expander(f"Approved — {q_count} questions confirmed", expanded=False):
            for q in ss.synthesis_doc.question_list.questions:
                st.markdown(f"**{q.id}** ({q.chapter})  \n{q.question}")
        if st.button("Re-open Gate A", key="reopen_gate_a"):
            ss.gate_a_done = False
            _reset_from("answers")
            st.rerun()
    else:
        syn = ss.synthesis_doc

        # Synthesis overview
        with st.expander("Synthesis brief", expanded=False):
            st.markdown(syn.brief_summary)

        st.markdown("**Problem statement**")
        st.info(syn.problem_statement)

        st.markdown("**Win themes**")
        for wt in syn.win_themes:
            st.markdown(f"- {wt}")

        st.divider()
        st.markdown(
            "**Question list** — edit question text inline, then Approve or use "
            "Iterate to re-run synthesis with notes."
        )
        st.caption(
            "Tip: edit any question text directly in the box below. "
            "Changes are saved when you click Approve."
        )

        for i, q in enumerate(syn.question_list.questions):
            c_label, c_field = st.columns([2, 5])
            c_label.markdown(f"**{q.id}**  \n{q.chapter}")
            c_label.caption(f"Type: {q.expected_answer_type}")
            c_field.text_area(
                f"q_{i}",
                value=ss.get(f"q_edit_{i}", q.question),
                key=f"q_edit_{i}",
                height=80,
                label_visibility="collapsed",
            )
            c_field.caption(f"Why asked: {q.why_asked}")

        st.markdown("---")
        col_approve, col_iter = st.columns([1, 2])

        with col_approve:
            if st.button("Approve Question List", type="primary", key="approve_gate_a"):
                updated_qs = [
                    Question(
                        id=q.id,
                        chapter=q.chapter,
                        question=ss.get(f"q_edit_{i}", q.question),
                        why_asked=q.why_asked,
                        expected_answer_type=q.expected_answer_type,
                    )
                    for i, q in enumerate(syn.question_list.questions)
                ]
                syn.question_list = QuestionList(questions=updated_qs)
                ss.synthesis_doc = syn
                ss.gate_a_done = True
                log_gate_event(
                    ss.run_id, "gate-a", "APPROVED",
                    f"{len(updated_qs)} question(s) confirmed",
                )
                _reset_from("answers")
                st.rerun()

        with col_iter:
            with st.expander("Iterate synthesis with notes"):
                notes = st.text_area(
                    "Describe what to change (e.g. 'Add a question on budget; "
                    "remove Q9 as it overlaps with Q3')",
                    key="gate_a_notes",
                    height=90,
                )
                if st.button("Re-run Synthesis with These Notes", key="rerun_synthesis"):
                    if notes.strip():
                        with st.spinner("Re-running Synthesis Agent..."):
                            try:
                                log_gate_event(
                                    ss.run_id, "gate-a", "ITERATE",
                                    f"notes: {notes[:120]}",
                                )
                                log_agent_start(ss.run_id, "synthesis-agent", "re-run with user notes")
                                intake_dict = ss.intake_package.model_dump()
                                context_dict = ss.context_doc.model_dump()

                                # Capture any inline edits the user made to question text
                                # so the agent revises against the user's current draft,
                                # not the original model output.
                                edited_questions = [
                                    Question(
                                        id=q.id,
                                        chapter=q.chapter,
                                        question=ss.get(f"q_edit_{i}", q.question),
                                        why_asked=q.why_asked,
                                        expected_answer_type=q.expected_answer_type,
                                    )
                                    for i, q in enumerate(
                                        ss.synthesis_doc.question_list.questions
                                    )
                                ]
                                current_draft = SynthesisDoc(
                                    brief_summary=ss.synthesis_doc.brief_summary,
                                    problem_statement=ss.synthesis_doc.problem_statement,
                                    win_themes=ss.synthesis_doc.win_themes,
                                    question_list=QuestionList(questions=edited_questions),
                                )
                                draft_dict = current_draft.model_dump()

                                result = run_agent(
                                    "synthesis-agent",
                                    user_message=(
                                        "**REVISION MODE.** You are revising an existing "
                                        "synthesis based on explicit user feedback from the "
                                        "Gate A reviewer. The user has reviewed the previous "
                                        "draft and given you specific changes to apply. Your "
                                        "output MUST visibly reflect their feedback — if they "
                                        "asked you to remove a question, that question must "
                                        "not appear; if they asked you to add a question, a "
                                        "new question must appear; if they asked you to "
                                        "reword something, the rewording must be applied. "
                                        "Do NOT return a near-identical question list.\n\n"
                                        f"Intake Package:\n"
                                        f"{json.dumps(intake_dict, indent=2)}\n\n"
                                        f"Context Document:\n"
                                        f"{json.dumps(context_dict, indent=2)}\n\n"
                                        f"Current synthesis draft (with any inline question "
                                        f"edits already applied by the user):\n"
                                        f"{json.dumps(draft_dict, indent=2)}\n\n"
                                        f"User feedback to apply:\n{notes.strip()}\n\n"
                                        "Return the FULL revised synthesis (brief, problem "
                                        "statement, win themes, and complete question list). "
                                        "Preserve any of the user's inline question edits "
                                        "unless their feedback explicitly contradicts them."
                                    ),
                                    files=None,
                                    use_extended_thinking=True,
                                )
                                log_agent_result(ss.run_id, "synthesis-agent", result)
                                ss.synthesis_doc = SynthesisDoc.model_validate(result)
                                for _k in [k for k in ss.keys() if k.startswith("q_edit_")]:
                                    del ss[_k]
                                _reset_from("answers")
                                st.rerun()
                            except Exception as exc:
                                traceback.print_exc()
                                log_event(ss.run_id, f"[SYNTHESIS AGENT] RE-RUN ERROR: {exc}")
                                _show_agent_error("Re-synthesis", exc)
                    else:
                        st.warning("Add notes before re-running.")

    st.divider()


# ─────────────────────────────────────────────────────────────────────────────
# STEP 4 — MOCK PARTNER ANSWERS
# ─────────────────────────────────────────────────────────────────────────────
if not ss.gate_a_done:
    st.text("Step 4 — Mock Partner Answers  [approve Gate A first]")
    st.divider()
else:
    st.subheader("Step 4 — Mock Partner Answers")
    st.caption(
        "Mock Partner Agent — generated placeholder answers for each question. "
        "Edit any answer before running validation — answers deliberately vary "
        "in quality to give the Validation Agent something meaningful to audit."
    )

    if not ss.answers_generated:
        if st.button("Generate Mock Answers", type="primary", key="gen_answers"):
            with st.spinner("Mock Partner Agent running — generating partner answers..."):
                try:
                    n_q = len(ss.synthesis_doc.question_list.questions)
                    log_agent_start(
                        ss.run_id, "mock-partner-agent",
                        f"{n_q} question(s) to answer",
                    )
                    ss.answer_list = generate_mock_answers(
                        ss.synthesis_doc.question_list
                    )
                    ss.answers_generated = True
                    log_agent_result(
                        ss.run_id, "mock-partner-agent",
                        ss.answer_list.model_dump(),
                    )
                    st.rerun()
                except Exception as exc:
                    traceback.print_exc()
                    log_event(ss.run_id, f"[MOCK PARTNER AGENT] ERROR: {exc}")
                    _show_agent_error("Mock answer generation", exc)
    else:
        q_map = {q.id: q for q in ss.synthesis_doc.question_list.questions}

        for answer in ss.answer_list.answers:
            q = q_map.get(answer.question_id)
            hdr = (
                f"**{answer.question_id}** — {q.chapter}"
                if q
                else f"**{answer.question_id}**"
            )
            st.markdown(hdr)
            if q:
                st.caption(q.question)
            st.text_area(
                f"ans_{answer.question_id}",
                value=ss.get(f"answer_edit_{answer.question_id}", answer.answer_text),
                key=f"answer_edit_{answer.question_id}",
                height=90,
                label_visibility="collapsed",
            )

        col_confirm, col_regen = st.columns([2, 2])

        with col_confirm:
            if not ss.answers_done:
                if st.button("Confirm Answers", type="primary", key="confirm_answers"):
                    updated = [
                        Answer(
                            question_id=a.question_id,
                            answer_text=ss.get(
                                f"answer_edit_{a.question_id}", a.answer_text
                            ),
                        )
                        for a in ss.answer_list.answers
                    ]
                    ss.answer_list = AnswerList(answers=updated)
                    ss.answers_done = True
                    ss.validation_done = False
                    ss.validation_report = None
                    st.rerun()
            else:
                st.success("Answers confirmed.")
                if st.button("Edit answers again", key="re_edit_answers"):
                    ss.answers_done = False
                    ss.validation_done = False
                    ss.validation_report = None
                    st.rerun()

        with col_regen:
            if st.button("Regenerate mock answers", key="regen_answers"):
                with st.spinner("Regenerating..."):
                    try:
                        ss.answer_list = generate_mock_answers(
                            ss.synthesis_doc.question_list
                        )
                        ss.answers_done = False
                        ss.validation_done = False
                        ss.validation_report = None
                        # Clear old answer edits
                        for _k in [k for k in ss.keys() if k.startswith("answer_edit_")]:
                            del ss[_k]
                        st.rerun()
                    except Exception as exc:
                        _show_agent_error("Regeneration", exc)

    st.divider()


# ─────────────────────────────────────────────────────────────────────────────
# STEP 5 — VALIDATION AGENT
# ─────────────────────────────────────────────────────────────────────────────
if not ss.answers_done:
    st.text("Step 5 — Validation Agent  [confirm answers first]")
else:
    st.subheader("Step 5 — Validation Agent")

    if ss.validation_done and ss.validation_report:
        report: ValidationReport = ss.validation_report

        # Overall metrics row
        m1, m2, m3 = st.columns([1, 1, 4])
        m1.metric("Readiness score", f"{report.readiness_score}/100")
        with m2:
            st.markdown("**Status**")
            if report.overall_readiness == "ready":
                st.success(report.overall_readiness)
            elif report.overall_readiness == "conditional":
                st.warning(report.overall_readiness)
            else:
                st.error(report.overall_readiness)
        m3.info(report.recommendation)

        st.progress(report.readiness_score / 100)
        st.markdown("---")

        # Per-question verdicts
        st.markdown("**Per-question verdicts:**")
        for v in report.verdicts:
            v_cols = st.columns([5, 1])
            with v_cols[0]:
                st.markdown(f"**{v.question_id}** — {v.question_text}")
                st.caption(
                    f"Answer: {v.answer_text[:200]}"
                    + ("..." if len(v.answer_text) > 200 else "")
                )
                st.caption(v.assessment)
                if v.follow_up:
                    st.caption(f"Follow-up needed: {v.follow_up}")
            with v_cols[1]:
                _completeness_badge(v.completeness)

        st.markdown("---")
        # Dot-dash readiness verdict
        rc1, rc2 = st.columns([1, 4])
        with rc1:
            st.markdown("**Dot-dash readiness**")
            if report.can_proceed_to_dot_dash:
                st.success("can proceed")
            else:
                st.error("not yet")
        with rc2:
            if report.dot_dash_blockers:
                label = (
                    "Blockers — must close before dot-dash:"
                    if not report.can_proceed_to_dot_dash
                    else "Material risks — dot-dash will mark these as placeholder/partial:"
                )
                st.markdown(f"**{label}**")
                for b in report.dot_dash_blockers:
                    st.markdown(f"- {b}")
            else:
                st.caption("No material blockers or risks flagged.")

        # Follow-up questions
        if report.follow_up_questions:
            st.markdown("---")
            st.markdown(
                f"**Follow-up questions for the partner — "
                f"{len(report.follow_up_questions)} proposed:**"
            )
            for fq in report.follow_up_questions:
                st.markdown(f"**{fq.id}** ({fq.chapter})  \n{fq.question}")
                st.caption(f"Why asked: {fq.why_asked}")

        # Residual gaps
        if report.residual_gaps:
            st.markdown("---")
            st.markdown("**Residual gaps:**")
            for g in report.residual_gaps:
                st.markdown(f"- {g}")

        if st.button("Re-run Validation Agent", key="rerun_validation"):
            _reset_from("validation")
            st.rerun()

    else:
        st.write(
            "The Validation Agent audits each answer for completeness, "
            "proposes follow-up questions for the residual gaps, and gives "
            "an explicit go/no-go verdict on whether enough input exists "
            "to produce a credible dot-dash storyline."
        )
        if st.button("Run Validation Agent", type="primary", key="run_validation"):
            with st.spinner(
                "Validation Agent running — auditing answer completeness "
                "(30–90 seconds)..."
            ):
                try:
                    log_agent_start(
                        ss.run_id, "validation-agent",
                        f"{len(ss.answer_list.answers)} answer(s) to audit",
                    )
                    qs_dict = ss.synthesis_doc.question_list.model_dump()
                    ans_dict = ss.answer_list.model_dump()
                    result = run_agent(
                        "validation-agent",
                        user_message=(
                            "Audit the partner answers against the question list "
                            "and produce a completeness report.\n\n"
                            f"Question List:\n{json.dumps(qs_dict, indent=2)}\n\n"
                            f"Answer List:\n{json.dumps(ans_dict, indent=2)}"
                        ),
                        files=None,
                        use_extended_thinking=True,
                    )
                    log_agent_result(ss.run_id, "validation-agent", result)
                    ss.validation_report = ValidationReport.model_validate(result)
                    ss.validation_done = True
                    st.rerun()
                except Exception as exc:
                    traceback.print_exc()
                    log_event(ss.run_id, f"[VALIDATION AGENT] ERROR: {exc}")
                    _show_agent_error("Validation Agent", exc)

    st.divider()


# ─────────────────────────────────────────────────────────────────────────────
# GATE B — APPROVE TO PROCEED TO DOT-DASH (or loop back with follow-ups)
# ─────────────────────────────────────────────────────────────────────────────
if not ss.validation_done:
    st.text("Gate B — Approve to Dot-Dash  [complete validation first]")
    st.divider()
else:
    st.subheader("Gate B — Approve to Dot-Dash")

    report: ValidationReport = ss.validation_report

    if ss.gate_b_done:
        with st.expander(
            f"Approved — proceeding to dot-dash with "
            f"readiness_score={report.readiness_score}/100",
            expanded=False,
        ):
            if report.dot_dash_blockers:
                st.markdown("**Risks carried into dot-dash:**")
                for b in report.dot_dash_blockers:
                    st.markdown(f"- {b}")
        if st.button("Re-open Gate B", key="reopen_gate_b"):
            ss.gate_b_done = False
            _reset_from("dotdash")
            st.rerun()
    else:
        # Surface the verdict explicitly at the gate
        if report.can_proceed_to_dot_dash:
            st.success(
                "Validation says: proceed to dot-dash. "
                "Any flagged risks will be carried as `partial` or `placeholder` slides."
            )
        else:
            st.error(
                "Validation says: do NOT proceed yet — at least one critical chapter "
                "is blocked. Recommended: append the proposed follow-up questions to "
                "the question list and re-run mock answers + validation."
            )

        st.markdown("**Recommendation from validation agent:**")
        st.info(report.recommendation)

        st.markdown("---")
        st.markdown(
            "**Two paths from here.** Pick one. (You can override the validation "
            "verdict if you want to push on, but the affected slides will be "
            "marked as placeholders.)"
        )

        col_loop, col_proceed = st.columns([1, 1])

        # ── Path 1: Loop back with follow-ups ──
        with col_loop:
            st.markdown("**Loop back — add follow-ups to question list**")
            n_fu = len(report.follow_up_questions or [])
            if n_fu == 0:
                st.caption("No follow-up questions proposed — nothing to loop back with.")
            else:
                st.caption(
                    f"This will append {n_fu} follow-up question(s) to the question "
                    f"list, clear the current answers and validation, and send you "
                    f"back to Step 4 (Mock Answers) so the partner can answer the "
                    f"follow-ups before re-running validation."
                )
                if st.button(
                    f"Append {n_fu} follow-up(s) and re-run mocks",
                    key="loopback_followups",
                ):
                    syn = ss.synthesis_doc
                    existing_qs = list(syn.question_list.questions)
                    # Re-id follow-ups so they continue Q-numbering after existing
                    next_idx = len(existing_qs) + 1
                    appended = []
                    for fq in report.follow_up_questions:
                        appended.append(
                            Question(
                                id=f"Q{next_idx}",
                                chapter=fq.chapter,
                                question=fq.question,
                                why_asked=fq.why_asked
                                + " (follow-up from validation)",
                                expected_answer_type=fq.expected_answer_type,
                            )
                        )
                        next_idx += 1
                    syn.question_list = QuestionList(
                        questions=existing_qs + appended
                    )
                    ss.synthesis_doc = syn
                    log_gate_event(
                        ss.run_id, "gate-b", "LOOPBACK",
                        f"appended {n_fu} follow-up question(s) — "
                        f"total now {len(syn.question_list.questions)}",
                    )
                    # Reset everything from answers onward; keep gate_a approved
                    _reset_from("answers")
                    ss.gate_a_done = True
                    st.rerun()

        # ── Path 2: Proceed to dot-dash ──
        with col_proceed:
            st.markdown("**Proceed — send current state to Dot-Dash Agent**")
            st.caption(
                "Use this when validation says proceed, OR when you want to draft "
                "a placeholder dot-dash now and close the gaps later."
            )
            override = False
            if not report.can_proceed_to_dot_dash:
                override = st.checkbox(
                    "I understand validation says NOT to proceed, and I want to "
                    "draft a placeholder dot-dash anyway.",
                    key="gate_b_override",
                )
            can_press = report.can_proceed_to_dot_dash or override
            if st.button(
                "Approve & proceed to Dot-Dash",
                type="primary",
                disabled=not can_press,
                key="approve_gate_b",
            ):
                ss.gate_b_done = True
                log_gate_event(
                    ss.run_id, "gate-b", "APPROVED",
                    "proceed to dot-dash"
                    + (" (with override)" if override else ""),
                )
                _reset_from("dotdash")
                st.rerun()

    st.divider()


# ─────────────────────────────────────────────────────────────────────────────
# STEP 6 — DOT-DASH AGENT
# ─────────────────────────────────────────────────────────────────────────────
if not ss.gate_b_done:
    st.text("Step 6 — Dot-Dash Agent  [approve Gate B first]")
    st.divider()
else:
    st.subheader("Step 6 — Dot-Dash Agent")

    if ss.dotdash_done and ss.dotdash_doc:
        dd: DotDashDoc = ss.dotdash_doc
        with st.expander(
            f"Done — {len(dd.slides)} slide(s) drafted", expanded=False
        ):
            st.markdown("**Storyline summary**")
            st.info(dd.storyline_summary)
            for s in dd.slides:
                st.markdown(f"**{s.chapter}**  \n{s.headline}")
                for p in s.supporting_points:
                    st.markdown(f"  - {p}")
                if s.notes:
                    st.caption(f"Notes: {s.notes}")
        if st.button("Re-run Dot-Dash Agent", key="rerun_dotdash"):
            _reset_from("dotdash")
            st.rerun()
    else:
        st.write(
            "The Dot-Dash Agent produces the LoP storyline — one slide per "
            "chapter, each with a headline ('dot') and 3–5 supporting "
            "points ('dashes'). The output is reviewed and iterated at Gate C."
        )
        if st.button("Run Dot-Dash Agent", type="primary", key="run_dotdash"):
            with st.spinner(
                "Dot-Dash Agent running — drafting LoP storyline (30–90 seconds)..."
            ):
                try:
                    log_agent_start(ss.run_id, "dot-dash-agent")
                    intake_dict = ss.intake_package.model_dump()
                    context_dict = ss.context_doc.model_dump()
                    syn_dict = ss.synthesis_doc.model_dump()
                    ans_dict = ss.answer_list.model_dump()
                    val_dict = ss.validation_report.model_dump()
                    result = run_agent(
                        "dot-dash-agent",
                        user_message=(
                            "Produce the LoP storyline as a chapter-by-chapter "
                            "dot-dash. Use the validation report to set slide "
                            "confidence honestly — flag placeholder content "
                            "rather than fabricating.\n\n"
                            f"Intake Package:\n{json.dumps(intake_dict, indent=2)}\n\n"
                            f"Context Document:\n{json.dumps(context_dict, indent=2)}\n\n"
                            f"Synthesis Document:\n{json.dumps(syn_dict, indent=2)}\n\n"
                            f"Answer List:\n{json.dumps(ans_dict, indent=2)}\n\n"
                            f"Validation Report:\n{json.dumps(val_dict, indent=2)}"
                        ),
                        files=None,
                        use_extended_thinking=True,
                    )
                    log_agent_result(ss.run_id, "dot-dash-agent", result)
                    ss.dotdash_doc = DotDashDoc.model_validate(result)
                    ss.dotdash_done = True
                    st.rerun()
                except Exception as exc:
                    traceback.print_exc()
                    log_event(ss.run_id, f"[DOT-DASH AGENT] ERROR: {exc}")
                    _show_agent_error("Dot-Dash Agent", exc)

    st.divider()


# ─────────────────────────────────────────────────────────────────────────────
# GATE C — REVIEW AND ITERATE DOT-DASH
# ─────────────────────────────────────────────────────────────────────────────
if not ss.dotdash_done:
    st.text("Gate C — Review Dot-Dash  [complete dot-dash agent first]")
    st.divider()
else:
    st.subheader("Gate C — Review and Iterate Dot-Dash")

    if ss.gate_c_done:
        dd = ss.dotdash_doc
        with st.expander(
            f"Approved — final dot-dash locked ({len(dd.slides)} slide(s))",
            expanded=False,
        ):
            st.markdown("**Storyline summary**")
            st.info(dd.storyline_summary)
            for s in dd.slides:
                st.markdown(f"**{s.chapter}** [{s.confidence}]  \n{s.headline}")
                for p in s.supporting_points:
                    st.markdown(f"  - {p}")
                if s.notes:
                    st.caption(f"Notes: {s.notes}")
        if st.button("Re-open Gate C", key="reopen_gate_c"):
            ss.gate_c_done = False
            st.rerun()
    else:
        dd = ss.dotdash_doc

        st.markdown("**Storyline summary**")
        st.info(dd.storyline_summary)

        if dd.open_risks:
            st.markdown("**Open risks flagged by the agent:**")
            for r in dd.open_risks:
                st.markdown(f"- {r}")

        st.markdown("---")
        st.markdown(
            "**Slides** — edit headline, supporting points (one per line), "
            "and notes inline. Edits are saved when you click Approve."
        )

        for i, s in enumerate(dd.slides):
            st.markdown(f"**Slide {i + 1} — {s.chapter}**")
            st.caption(f"Confidence: {s.confidence}")

            st.text_input(
                f"Headline ({s.chapter})",
                value=ss.get(f"dd_headline_{i}", s.headline),
                key=f"dd_headline_{i}",
            )
            st.text_area(
                f"Supporting points — one per line ({s.chapter})",
                value=ss.get(
                    f"dd_dashes_{i}",
                    "\n".join(s.supporting_points),
                ),
                key=f"dd_dashes_{i}",
                height=120,
            )
            st.text_input(
                f"Notes ({s.chapter})",
                value=ss.get(f"dd_notes_{i}", s.notes or ""),
                key=f"dd_notes_{i}",
            )
            st.markdown("---")

        col_approve_c, col_iter_c = st.columns([1, 2])

        with col_approve_c:
            if st.button("Approve Dot-Dash", type="primary", key="approve_gate_c"):
                updated_slides = []
                for i, s in enumerate(dd.slides):
                    new_dashes = [
                        line.strip().lstrip("-").strip()
                        for line in ss.get(
                            f"dd_dashes_{i}", "\n".join(s.supporting_points)
                        ).split("\n")
                        if line.strip()
                    ]
                    updated_slides.append(
                        DotDashSlide(
                            chapter=s.chapter,
                            headline=ss.get(f"dd_headline_{i}", s.headline),
                            supporting_points=new_dashes,
                            confidence=s.confidence,
                            notes=ss.get(f"dd_notes_{i}", s.notes or ""),
                        )
                    )
                ss.dotdash_doc = DotDashDoc(
                    storyline_summary=dd.storyline_summary,
                    slides=updated_slides,
                    open_risks=dd.open_risks,
                )
                ss.gate_c_done = True
                log_gate_event(
                    ss.run_id, "gate-c", "APPROVED",
                    f"{len(updated_slides)} slide(s) confirmed",
                )
                st.rerun()

        with col_iter_c:
            with st.expander("Iterate dot-dash with notes"):
                dd_notes = st.text_area(
                    "Describe what to change (e.g. 'Sharpen the Why McKinsey "
                    "headline; the Approach slide is too generic — add a dash on "
                    "the integrated bench point')",
                    key="gate_c_notes",
                    height=100,
                )
                if st.button(
                    "Re-run Dot-Dash with These Notes", key="rerun_dotdash_notes"
                ):
                    if dd_notes.strip():
                        with st.spinner("Re-running Dot-Dash Agent..."):
                            try:
                                log_gate_event(
                                    ss.run_id, "gate-c", "ITERATE",
                                    f"notes: {dd_notes[:120]}",
                                )
                                log_agent_start(
                                    ss.run_id, "dot-dash-agent",
                                    "re-run with user notes",
                                )

                                # Capture inline edits before sending to agent
                                edited_slides = []
                                for i, s in enumerate(dd.slides):
                                    new_dashes = [
                                        line.strip().lstrip("-").strip()
                                        for line in ss.get(
                                            f"dd_dashes_{i}",
                                            "\n".join(s.supporting_points),
                                        ).split("\n")
                                        if line.strip()
                                    ]
                                    edited_slides.append(
                                        DotDashSlide(
                                            chapter=s.chapter,
                                            headline=ss.get(
                                                f"dd_headline_{i}", s.headline
                                            ),
                                            supporting_points=new_dashes,
                                            confidence=s.confidence,
                                            notes=ss.get(
                                                f"dd_notes_{i}", s.notes or ""
                                            ),
                                        )
                                    )
                                current_draft = DotDashDoc(
                                    storyline_summary=dd.storyline_summary,
                                    slides=edited_slides,
                                    open_risks=dd.open_risks,
                                )
                                draft_dict = current_draft.model_dump()

                                intake_dict = ss.intake_package.model_dump()
                                context_dict = ss.context_doc.model_dump()
                                syn_dict = ss.synthesis_doc.model_dump()
                                ans_dict = ss.answer_list.model_dump()
                                val_dict = ss.validation_report.model_dump()

                                result = run_agent(
                                    "dot-dash-agent",
                                    user_message=(
                                        "**REVISION MODE.** You are revising an "
                                        "existing dot-dash based on explicit user "
                                        "feedback from the Gate C reviewer. The "
                                        "user has reviewed the current draft and "
                                        "given you specific changes to apply. Your "
                                        "output MUST visibly reflect their feedback "
                                        "— do NOT return a near-identical "
                                        "dot-dash. Preserve any inline edits the "
                                        "user already applied unless their feedback "
                                        "explicitly contradicts them.\n\n"
                                        f"Intake Package:\n"
                                        f"{json.dumps(intake_dict, indent=2)}\n\n"
                                        f"Context Document:\n"
                                        f"{json.dumps(context_dict, indent=2)}\n\n"
                                        f"Synthesis Document:\n"
                                        f"{json.dumps(syn_dict, indent=2)}\n\n"
                                        f"Answer List:\n"
                                        f"{json.dumps(ans_dict, indent=2)}\n\n"
                                        f"Validation Report:\n"
                                        f"{json.dumps(val_dict, indent=2)}\n\n"
                                        f"Current dot-dash draft (with any inline "
                                        f"edits already applied by the user):\n"
                                        f"{json.dumps(draft_dict, indent=2)}\n\n"
                                        f"User feedback to apply:\n"
                                        f"{dd_notes.strip()}\n\n"
                                        "Return the FULL revised dot-dash "
                                        "(storyline_summary, all nine slides in "
                                        "canonical order, and open_risks)."
                                    ),
                                    files=None,
                                    use_extended_thinking=True,
                                )
                                log_agent_result(
                                    ss.run_id, "dot-dash-agent", result
                                )
                                ss.dotdash_doc = DotDashDoc.model_validate(result)
                                # Clear inline edit keys so the new draft is shown
                                for _k in [
                                    k for k in ss.keys()
                                    if k.startswith("dd_headline_")
                                    or k.startswith("dd_dashes_")
                                    or k.startswith("dd_notes_")
                                ]:
                                    del ss[_k]
                                st.rerun()
                            except Exception as exc:
                                traceback.print_exc()
                                log_event(
                                    ss.run_id,
                                    f"[DOT-DASH AGENT] RE-RUN ERROR: {exc}",
                                )
                                _show_agent_error("Re-run", exc)
                    else:
                        st.warning("Add notes before re-running.")

    st.divider()
