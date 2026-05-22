"""
Run logger — writes a compact per-session log to Hamdi/runs/.

Design principles:
  - One log file per Streamlit session, named by timestamp.
  - Only key sentences are written — no full JSON dumps.
  - Each agent has a dedicated formatter that picks the 3-5 most informative fields.
  - The log is intended to be readable by a human in ~30 seconds per run.

Log location: Hamdi/runs/YYYYMMDD_HHMMSS_lop_run.log
"""

import logging
from pathlib import Path

_RUNS_DIR = Path(__file__).parent.parent / "runs"

# Maps run_id → (Logger, Path); avoids duplicate handlers across Streamlit reruns
_REGISTRY: dict[str, tuple[logging.Logger, Path]] = {}


# ─── INITIALISATION ───────────────────────────────────────────────────────────

def get_run_logger(run_id: str) -> tuple[logging.Logger, Path]:
    """
    Return (logger, log_file_path) for this run_id.
    Creates the file and attaches a handler on first call; reuses on reruns.
    """
    if run_id in _REGISTRY:
        return _REGISTRY[run_id]

    _RUNS_DIR.mkdir(parents=True, exist_ok=True)
    log_file = _RUNS_DIR / f"{run_id}_lop_run.log"

    logger = logging.getLogger(f"lop_{run_id}")
    logger.setLevel(logging.INFO)
    logger.propagate = False  # don't send to root logger

    if not logger.handlers:
        fh = logging.FileHandler(log_file, encoding="utf-8")
        fh.setFormatter(
            logging.Formatter("%(asctime)s  %(message)s", datefmt="%H:%M:%S")
        )
        logger.addHandler(fh)

    _REGISTRY[run_id] = (logger, log_file)
    return logger, log_file


# ─── PUBLIC HELPERS ───────────────────────────────────────────────────────────

def log_event(run_id: str, message: str) -> None:
    logger, _ = get_run_logger(run_id)
    logger.info(message)


def log_session_start(run_id: str) -> None:
    log_event(run_id, "=" * 60)
    log_event(run_id, f"LoP Builder — Phase 1 — Run ID: {run_id}")
    log_event(run_id, "=" * 60)


def log_agent_start(run_id: str, agent_name: str, context: str = "") -> None:
    label = agent_name.upper().replace("-", " ")
    msg = f"[{label}] Starting"
    if context:
        msg += f" — {context}"
    log_event(run_id, msg)


def log_agent_result(run_id: str, agent_name: str, result: dict) -> None:
    """
    Extract and log only the key facts from an agent result dict.
    Full JSON is never written; only human-readable summary sentences.
    """
    _FORMATTERS = {
        "intake-agent":           _fmt_intake,
        "context-agent":          _fmt_context,
        "synthesis-agent":        _fmt_synthesis,
        "mock-partner-agent":     _fmt_mock_partner,
        "voice-splitter-agent":   _fmt_voice_splitter,
        "voice-structurer-agent": _fmt_voice_structurer,
        "validation-agent":       _fmt_validation,
        "dot-dash-agent":         _fmt_dot_dash,
    }
    fn = _FORMATTERS.get(agent_name)
    if fn:
        fn(run_id, result)
    else:
        log_event(run_id, f"[{agent_name.upper()}] Completed (no formatter)")


def log_gate_event(run_id: str, gate: str, action: str, note: str = "") -> None:
    msg = f"[{gate.upper()}] {action}"
    if note:
        msg += f" — {note}"
    log_event(run_id, msg)


# ─── PER-AGENT FORMATTERS ─────────────────────────────────────────────────────

def _fmt_intake(run_id: str, r: dict) -> None:
    log_event(
        run_id,
        f"[INTAKE] Client identified: {r.get('client_name', '?')}  |  "
        f"Industry: {r.get('industry', '?')}  |  "
        f"Geography: {r.get('geography', '?')}",
    )
    log_event(run_id, f"[INTAKE] Problem area: {r.get('problem_area', '?')}")

    log_event(
        run_id,
        f"[INTAKE] Pursuit type: {r.get('pursuit_type', 'unclear')}  |  "
        f"Competitive: {r.get('competitive_status', 'unclear')}",
    )

    competitors = r.get("competitor_firms", []) or []
    if competitors:
        log_event(
            run_id,
            f"[INTAKE] Competitors named: {', '.join(competitors)}",
        )

    gold_mode = r.get("gold_standard_mode", "none")
    if gold_mode and gold_mode != "none":
        gold_text = (
            r.get("gold_standard_guidance", "")
            if gold_mode == "guidance"
            else r.get("gold_standard_synthesis", "")
        )
        snippet = (gold_text or "").strip()[:140]
        log_event(run_id, f"[INTAKE] Gold standard handling: {gold_mode}")
        if snippet:
            log_event(
                run_id,
                f"[INTAKE]     {snippet}"
                + ("..." if len(gold_text or "") > 140 else ""),
            )

    rfi_signals = r.get("rfi_signals", []) or []
    if rfi_signals:
        log_event(run_id, f"[INTAKE] {len(rfi_signals)} RFI signal(s):")
        for s in rfi_signals[:3]:
            log_event(run_id, f"[INTAKE]     signal: {s[:140]}")
        if len(rfi_signals) > 3:
            log_event(run_id, f"[INTAKE]     ... and {len(rfi_signals) - 3} more")

    buckets = r.get("chapter_buckets", [])
    q_counts: dict[str, int] = {"complete": 0, "partial": 0, "missing": 0}
    for b in buckets:
        key = b.get("quality", "missing")
        q_counts[key] = q_counts.get(key, 0) + 1

    log_event(
        run_id,
        f"[INTAKE] Chapter coverage — "
        f"complete: {q_counts['complete']}  "
        f"partial: {q_counts['partial']}  "
        f"missing: {q_counts['missing']}",
    )

    gaps = r.get("gap_list", [])
    log_event(run_id, f"[INTAKE] {len(gaps)} gap(s) identified")
    for g in gaps[:5]:
        log_event(run_id, f"[INTAKE]     gap: {g}")
    if len(gaps) > 5:
        log_event(run_id, f"[INTAKE]     ... and {len(gaps) - 5} more gap(s)")

    rfp_reqs = r.get("rfp_requirements", [])
    log_event(run_id, f"[INTAKE] {len(rfp_reqs)} explicit RFP requirement(s) extracted")


def _fmt_context(run_id: str, r: dict) -> None:
    profile_len = len(r.get("client_profile", ""))
    log_event(run_id, f"[CONTEXT] Client profile built — {profile_len} chars")

    search_mode = r.get("search_mode", "model_knowledge_fallback")
    log_event(run_id, f"[CONTEXT] Search mode: {search_mode}")

    extra_ctx = (r.get("additional_context_used", "") or "").strip()
    if extra_ctx:
        log_event(
            run_id,
            f"[CONTEXT] Additional context provided: {len(extra_ctx)} chars",
        )

    citations = r.get("citations", []) or []
    web_citations = [
        c for c in citations
        if isinstance(c, dict) and c.get("kind") == "web"
    ]
    model_citations = [
        c for c in citations
        if isinstance(c, dict) and c.get("kind") != "web"
    ]
    log_event(
        run_id,
        f"[CONTEXT] {len(citations)} citation(s) — "
        f"web: {len(web_citations)}, model knowledge: {len(model_citations)}",
    )
    for c in web_citations[:5]:
        label = (c.get("title") or "").strip() or (c.get("url") or "")[:90]
        log_event(run_id, f"[CONTEXT]     source: {label[:120]}")
    if len(web_citations) > 5:
        log_event(
            run_id,
            f"[CONTEXT]     ... and {len(web_citations) - 5} more web source(s)",
        )

    searches = r.get("searches_performed", []) or []
    if searches:
        log_event(run_id, f"[CONTEXT] {len(searches)} search query(ies) reported")

    ev_gaps = r.get("evidence_gaps", [])
    log_event(run_id, f"[CONTEXT] {len(ev_gaps)} topic(s) flagged for human validation:")
    for g in ev_gaps[:4]:
        log_event(run_id, f"[CONTEXT]     verify: {g}")

    # ── v3 dimensions ──
    recent = r.get("recent_signals", []) or []
    if recent:
        log_event(run_id, f"[CONTEXT] {len(recent)} recent signal(s):")
        for s in recent[:5]:
            if not isinstance(s, dict):
                continue
            cat = (s.get("category") or "").strip() or "?"
            head = (s.get("headline") or "").strip()
            log_event(run_id, f"[CONTEXT]     {cat}: {head[:120]}")
        if len(recent) > 5:
            log_event(
                run_id,
                f"[CONTEXT]     ... and {len(recent) - 5} more signal(s)",
            )

    reg = r.get("regulatory_environment", []) or []
    if reg:
        log_event(run_id, f"[CONTEXT] {len(reg)} regulatory item(s):")
        for it in reg[:5]:
            if not isinstance(it, dict):
                continue
            topic = (it.get("topic") or "").strip()
            log_event(run_id, f"[CONTEXT]     {topic[:120]}")
        if len(reg) > 5:
            log_event(
                run_id,
                f"[CONTEXT]     ... and {len(reg) - 5} more regulatory item(s)",
            )

    ct = r.get("chapter_takeaways", {}) or {}
    if isinstance(ct, dict):
        populated = sum(
            1
            for v in ct.values()
            if isinstance(v, str) and v.strip()
        )
        log_event(
            run_id,
            f"[CONTEXT] {populated}/5 chapter takeaway(s) populated",
        )

    note = r.get("knowledge_cutoff_note", "")
    if note:
        snippet = note[:140] + ("..." if len(note) > 140 else "")
        log_event(run_id, f"[CONTEXT] Knowledge note: {snippet}")


def _fmt_synthesis(run_id: str, r: dict) -> None:
    ps = r.get("problem_statement", "")
    snippet = ps[:220] + ("..." if len(ps) > 220 else "")
    log_event(run_id, f"[SYNTHESIS] Problem statement: {snippet}")

    themes = r.get("win_themes", [])
    log_event(run_id, f"[SYNTHESIS] {len(themes)} win theme(s):")
    for t in themes:
        log_event(run_id, f"[SYNTHESIS]     theme: {t[:130]}{'...' if len(t) > 130 else ''}")

    ql = r.get("question_list", [])
    if isinstance(ql, dict):
        questions = ql.get("questions", [])
    elif isinstance(ql, list):
        questions = ql
    else:
        questions = []
    log_event(run_id, f"[SYNTHESIS] {len(questions)} question(s) in partner question list:")
    for q in questions:
        if not isinstance(q, dict):
            continue
        log_event(
            run_id,
            f"[SYNTHESIS]     {q.get('id', '?')} ({q.get('chapter', '?')}): "
            f"{q.get('question', '')[:110]}",
        )


def _fmt_mock_partner(run_id: str, r: dict) -> None:
    answers = r.get("answers", [])
    log_event(run_id, f"[MOCK PARTNER] {len(answers)} answer(s) generated")
    for a in answers:
        snippet = (a.get("answer_text") or "")[:110]
        log_event(
            run_id,
            f"[MOCK PARTNER]     {a.get('question_id', '?')}: {snippet}"
            + ("..." if len(a.get("answer_text") or "") > 110 else ""),
        )


def _fmt_voice_splitter(run_id: str, r: dict) -> None:
    answers = r.get("answers", []) or []
    blanks = sum(1 for a in answers if not (a.get("answer_text") or "").strip())
    log_event(
        run_id,
        f"[VOICE SPLITTER] {len(answers)} answer(s) routed from transcript "
        f"({blanks} not addressed by partner)",
    )
    for a in answers:
        text = (a.get("answer_text") or "").strip()
        qid = a.get("question_id", "?")
        if not text:
            log_event(run_id, f"[VOICE SPLITTER]     {qid}: (not addressed)")
        else:
            snippet = text[:110]
            log_event(
                run_id,
                f"[VOICE SPLITTER]     {qid}: {snippet}"
                + ("..." if len(text) > 110 else ""),
            )


def _fmt_voice_structurer(run_id: str, r: dict) -> None:
    perspective = r.get("lop_perspective") or {}
    if not isinstance(perspective, dict):
        perspective = {}

    situation = (perspective.get("client_situation") or "").strip()
    if situation:
        snippet = situation[:140]
        log_event(
            run_id,
            f"[VOICE STRUCTURER] Client situation: {snippet}"
            + ("..." if len(situation) > 140 else ""),
        )

    win_themes = perspective.get("win_themes") or []
    win_themes = [str(t).strip() for t in win_themes if str(t).strip()]
    log_event(run_id, f"[VOICE STRUCTURER] Win themes: {len(win_themes)}")
    for t in win_themes[:3]:
        log_event(run_id, f"[VOICE STRUCTURER]     - {t[:140]}")

    open_questions = perspective.get("open_questions") or []
    open_questions = [str(q).strip() for q in open_questions if str(q).strip()]
    log_event(
        run_id,
        f"[VOICE STRUCTURER] Open questions raised by partner: "
        f"{len(open_questions)}",
    )
    for q in open_questions[:3]:
        log_event(run_id, f"[VOICE STRUCTURER]     - {q[:140]}")

    chapter_signals = r.get("chapter_signals") or []
    chapters_with_signal = [
        (entry.get("chapter") or "").strip()
        for entry in chapter_signals
        if isinstance(entry, dict)
        and (entry.get("chapter") or "").strip()
        and (entry.get("signal") or "").strip()
    ]
    log_event(
        run_id,
        f"[VOICE STRUCTURER] Chapters with partner signal: "
        f"{len(chapters_with_signal)} "
        f"({', '.join(chapters_with_signal) if chapters_with_signal else 'none'})",
    )


def _fmt_validation(run_id: str, r: dict) -> None:
    log_event(
        run_id,
        f"[VALIDATION] Overall readiness: {r.get('overall_readiness', '?').upper()}  |  "
        f"Score: {r.get('readiness_score', '?')}/100",
    )

    verdicts = r.get("verdicts", [])
    vc: dict[str, int] = {"complete": 0, "partial": 0, "missing": 0}
    for v in verdicts:
        c = v.get("completeness", "missing")
        vc[c] = vc.get(c, 0) + 1
    log_event(
        run_id,
        f"[VALIDATION] Answer verdicts — "
        f"complete: {vc['complete']}  partial: {vc['partial']}  missing: {vc['missing']}",
    )

    # Log only the non-complete verdicts (the interesting ones)
    for v in verdicts:
        if v.get("completeness") in ("partial", "missing"):
            log_event(
                run_id,
                f"[VALIDATION]     {v.get('question_id', '?')} [{v.get('completeness', '?')}]: "
                f"{v.get('assessment', '')[:120]}",
            )
            if v.get("follow_up"):
                log_event(
                    run_id,
                    f"[VALIDATION]         follow-up needed: {v.get('follow_up', '')[:110]}",
                )

    gaps = r.get("residual_gaps", [])
    log_event(run_id, f"[VALIDATION] {len(gaps)} residual gap(s):")
    for g in gaps:
        log_event(run_id, f"[VALIDATION]     gap: {g}")

    # Dot-dash readiness verdict
    can_proceed = r.get("can_proceed_to_dot_dash")
    if can_proceed is True:
        verdict = "CAN PROCEED to dot-dash"
    elif can_proceed is False:
        verdict = "CANNOT PROCEED to dot-dash yet"
    else:
        verdict = "verdict not provided"
    log_event(run_id, f"[VALIDATION] Dot-dash readiness: {verdict}")
    blockers = r.get("dot_dash_blockers", []) or []
    if blockers:
        log_event(
            run_id,
            f"[VALIDATION] {len(blockers)} dot-dash blocker(s)/risk(s):",
        )
        for b in blockers:
            log_event(run_id, f"[VALIDATION]     blocker/risk: {b}")

    # Follow-up questions for Gate B
    fu_qs = r.get("follow_up_questions", []) or []
    log_event(
        run_id,
        f"[VALIDATION] {len(fu_qs)} follow-up question(s) proposed for partner:",
    )
    for fq in fu_qs:
        if not isinstance(fq, dict):
            continue
        log_event(
            run_id,
            f"[VALIDATION]     {fq.get('id', '?')} ({fq.get('chapter', '?')}): "
            f"{(fq.get('question') or '')[:110]}",
        )

    rec = r.get("recommendation", "")
    if rec:
        snippet = rec[:270] + ("..." if len(rec) > 270 else "")
        log_event(run_id, f"[VALIDATION] Recommendation: {snippet}")


def _fmt_dot_dash(run_id: str, r: dict) -> None:
    summary = r.get("storyline_summary", "")
    if summary:
        snippet = summary[:240] + ("..." if len(summary) > 240 else "")
        log_event(run_id, f"[DOT-DASH] Storyline: {snippet}")

    slides = r.get("slides", []) or []
    conf_counts: dict[str, int] = {"complete": 0, "partial": 0, "placeholder": 0}
    for s in slides:
        if isinstance(s, dict):
            c = s.get("confidence", "complete")
            conf_counts[c] = conf_counts.get(c, 0) + 1
    log_event(
        run_id,
        f"[DOT-DASH] {len(slides)} slide(s) drafted — "
        f"complete: {conf_counts['complete']}  "
        f"partial: {conf_counts['partial']}  "
        f"placeholder: {conf_counts['placeholder']}",
    )

    for s in slides:
        if not isinstance(s, dict):
            continue
        chapter = s.get("chapter", "?")
        confidence = s.get("confidence", "complete")
        headline = (s.get("headline") or "")[:120]
        log_event(
            run_id,
            f"[DOT-DASH]     {chapter} [{confidence}]: {headline}"
            + ("..." if len(s.get("headline") or "") > 120 else ""),
        )

    risks = r.get("open_risks", []) or []
    if risks:
        log_event(run_id, f"[DOT-DASH] {len(risks)} open risk(s):")
        for risk in risks:
            log_event(run_id, f"[DOT-DASH]     risk: {risk}")
