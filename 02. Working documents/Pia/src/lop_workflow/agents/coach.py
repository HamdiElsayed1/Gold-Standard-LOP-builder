from __future__ import annotations

from lop_workflow.gold_patterns.loader import get_section_pattern
from lop_workflow.models.brief import Brief, LOPCategory
from lop_workflow.models.coach import (
    IssueSeverity,
    LOPCoachIssue,
    LOPCoachReport,
    SectionScore,
)
from lop_workflow.models.facts import FactsRegistry
from lop_workflow.models.section import LOPDocument, SectionContent, SectionId
from lop_workflow.models.source import SourceRef
from lop_workflow.orchestrator.state import OrchestratorState


def _background_for_state(st: OrchestratorState) -> list[SourceRef]:
    """Merge info-gathering retrieval and brief RFP/tender chunks (dedup by source_id)."""
    out: list[SourceRef] = []
    seen: set[str] = set()
    for src in st.research_corpus or []:
        if src.source_id not in seen:
            seen.add(src.source_id)
            out.append(src)
    if st.brief:
        for src in st.brief.rfp_tender_references or []:
            if src.source_id not in seen:
                seen.add(src.source_id)
                out.append(src)
    return out


def _uncited_forbidden(body: str) -> bool:
    b = body.lower()
    for bad in ("guaranteed", "unlimited liability", "will save"):
        if bad in b and "[citation" not in body.lower() and "http" not in b:
            return True
    return False


def _score_section(s: SectionContent) -> SectionScore:
    if s.body_markdown.strip() and s.confidence >= 0.5 and not _uncited_forbidden(s.body_markdown):
        return SectionScore(section_id=s.section_id, score=0.9, pass_gate=True)
    return SectionScore(section_id=s.section_id, score=0.3, pass_gate=False)


def _sev_letter(sev: IssueSeverity) -> str:
    if sev == IssueSeverity.BLOCK:
        return "H"
    if sev == IssueSeverity.WARN:
        return "M"
    return "L"


def _build_issue_table(issues: list[LOPCoachIssue]) -> str:
    lines = [
        "| Chapter | Severity (H/M/L) | Issue | Suggested fix type |",
        "| --- | --- | --- | --- |",
    ]
    for i in issues:
        chap = i.section_id.value if i.section_id else "(global)"
        fix = "get source" if "source" in i.message.lower() or "cite" in i.message.lower() else "TBD"
        if i.code.startswith("F"):
            fix = "get source"
        if "TBD" in i.message:
            fix = "TBD"
        if "cut" in i.message.lower():
            fix = "cut"
        lines.append(f"| {chap} | {_sev_letter(i.severity)} | {i.message.replace('|', '/')} | {fix} |")
    return "\n".join(lines)


def _gold_pattern_issues(
    section: SectionContent,
    *,
    category: LOPCategory | None,
) -> list[LOPCoachIssue]:
    pattern = get_section_pattern(section.section_id, category)
    out: list[LOPCoachIssue] = []
    body = section.body_markdown.strip()
    bl = body.lower()

    if pattern.must_have_evidence and len(body) < 120:
        out.append(
            LOPCoachIssue(
                code="GP001",
                message="Section body is thin vs gold-pattern evidence gates — expand or mark explicit TBDs.",
                severity=IssueSeverity.WARN,
                section_id=section.section_id,
            )
        )

    for gate in pattern.must_have_evidence:
        g = gate.lower()
        if "fee" in g and section.section_id == SectionId.FEES:
            if "tbd" not in bl and "workshop" not in bl and not any(c.isdigit() for c in body):
                out.append(
                    LOPCoachIssue(
                        code="GP002",
                        message="Fees: gold pattern expects TBD/structure or sourced numbers — clarify commercial posture.",
                        severity=IssueSeverity.WARN,
                        section_id=section.section_id,
                    )
                )
        if section.section_id == SectionId.WHY_MCKINSEY and (
            "why" in g or "proof" in g or "manifest" in g
        ):
            if "evidence required" not in bl and "manifest" not in bl and "`" not in body:
                out.append(
                    LOPCoachIssue(
                        code="GP003",
                        message="Why McKinsey: tie proof bullets to manifest rows or flag `evidence required`.",
                        severity=IssueSeverity.WARN,
                        section_id=section.section_id,
                    )
                )
                break

    if category == LOPCategory.COMPETITIVE and section.section_id == SectionId.WHY_MCKINSEY:
        if "differentiat" not in bl and "distinct" not in bl:
            out.append(
                LOPCoachIssue(
                    code="GP004",
                    message="Competitive LoP: strengthen explicit differentiators (evidence-bound).",
                    severity=IssueSeverity.WARN,
                    section_id=section.section_id,
                )
            )

    return out


def _rubric_dimensions(
    *,
    report: LOPCoachReport,
    brief: Brief | None,
    lop: LOPDocument,
) -> dict[str, str]:
    blocks = sum(1 for i in report.issues if i.severity == IssueSeverity.BLOCK)
    warns = sum(1 for i in report.issues if i.severity == IssueSeverity.WARN)
    avg_score = (
        sum(s.score for s in report.section_scores) / len(report.section_scores)
        if report.section_scores
        else 0.0
    )

    gate = "green" if blocks == 0 and report.overall_ok else "amber" if blocks == 0 else "red"

    # RFP fit
    rfp_fit = gate
    if brief and brief.rfp_tender_references:
        ctx = next((s for s in lop.sections if s.section_id == SectionId.CONTEXT), None)
        if ctx and len(ctx.body_markdown.strip()) < 200:
            rfp_fit = "amber"

    # Fees
    fees_sec = next((s for s in lop.sections if s.section_id == SectionId.FEES), None)
    fee_clarity = "review"
    if fees_sec:
        fl = fees_sec.body_markdown.lower()
        if "tbd" in fl or fees_sec.extra.get("fees_table"):
            fee_clarity = "green"
        elif blocks == 0:
            fee_clarity = "amber"

    # Appendix
    app = next((s for s in lop.sections if s.section_id == SectionId.APPENDIX), None)
    appendix = "green"
    if app and len(app.body_markdown.strip()) < 80:
        appendix = "amber"

    gp_warns = sum(1 for i in report.issues if i.code.startswith("GP"))
    if gp_warns == 0:
        gold_pattern_fit = "green"
    elif gp_warns <= 2:
        gold_pattern_fit = "amber"
    else:
        gold_pattern_fit = "red"

    narrative_flow = "green" if avg_score >= 0.85 else "amber"

    return {
        "rubric_rfp_fit": rfp_fit,
        "rubric_narrative_flow": narrative_flow,
        "rubric_fee_clarity": fee_clarity,
        "rubric_appendix_completeness": appendix,
        "rubric_gold_pattern_fit": gold_pattern_fit,
        "rubric_avg_section_score": str(round(avg_score, 3)),
        "rubric_blocking_issues": str(blocks),
        "rubric_warnings": str(warns),
    }


def evaluate_lop_coach(
    lop: LOPDocument,
    facts: FactsRegistry,
    *,
    background: list[SourceRef] | None = None,
    brief: Brief | None = None,
    lop_category: LOPCategory | None = None,
) -> LOPCoachReport:
    bg = list(background) if background else []
    bg_ids = {x.source_id for x in bg}
    issues: list[LOPCoachIssue] = []

    cat = lop_category or (brief.lop_category if brief else None)

    for s in lop.sections:
        optional_src = {
            SectionId.APPENDIX,
            SectionId.REFERENCES,
            SectionId.TEAM_CVS,
        }
        if not s.sources and s.section_id not in optional_src:
            src_msg = "Section has no supporting sources; add citations in appendix or inline."
            if bg_ids:
                src_msg = (
                    f"Section has no supporting sources; {len(bg)} background source(s) "
                    "from the run (research + RFP/tender) are available to cite."
                )
            issues.append(
                LOPCoachIssue(
                    code="SRC001",
                    message=src_msg,
                    severity=IssueSeverity.WARN,
                    section_id=s.section_id,
                )
            )
        elif bg_ids and s.sources and s.section_id not in (SectionId.APPENDIX,):
            if not any(sx.source_id in bg_ids for sx in s.sources):
                issues.append(
                    LOPCoachIssue(
                        code="BG001",
                        message="Section does not reference any of the run background materials (research/RFP). Consider tying the narrative to those sources.",
                        severity=IssueSeverity.WARN,
                        section_id=s.section_id,
                    )
                )
        if s.confidence < 0.5:
            issues.append(
                LOPCoachIssue(
                    code="Q002",
                    message="Low model confidence; verify with human.",
                    severity=IssueSeverity.BLOCK,
                    section_id=s.section_id,
                )
            )

        issues.extend(_gold_pattern_issues(s, category=cat))

    for f in facts.entries:
        if not f.citations and f.claim:
            issues.append(
                LOPCoachIssue(
                    code="F001",
                    message=f"Fact '{f.key}' is uncited.",
                    severity=IssueSeverity.BLOCK,
                    fact_key=f.key,
                )
            )

    scores = [_score_section(s) for s in lop.sections]
    overall = all(s.pass_gate for s in scores) and not any(i.severity == IssueSeverity.BLOCK for i in issues)
    base = "LOP Coach pass (rules)" if overall else "LOP Coach: fix blocking issues."
    if bg:
        base = f"{base} Evaluated against {len(bg)} background source(s) from the run."

    table_md = _build_issue_table(issues)

    report = LOPCoachReport(
        issues=issues,
        section_scores=scores,
        overall_ok=overall,
        summary=base,
        background_materials=bg,
        issue_table_markdown=table_md,
        rubric_dimensions={},
    )
    report.rubric_dimensions = _rubric_dimensions(report=report, brief=brief, lop=lop)
    return report


def _eval_rubric_scores(report: LOPCoachReport) -> dict[str, object]:
    """Legacy flat meta keys + new rubric_dimensions."""
    base = dict(report.rubric_dimensions)
    base["rubric_issue_table_rows"] = len(report.issues)
    return base


def run_lop_coach_state(st: OrchestratorState) -> LOPCoachReport:
    if st.lop is None:
        st.coach_report = LOPCoachReport(overall_ok=False, summary="No LOP document to review.")
        return st.coach_report
    r = evaluate_lop_coach(
        st.lop,
        st.facts,
        background=_background_for_state(st),
        brief=st.brief,
        lop_category=st.brief.lop_category if st.brief else None,
    )
    st.coach_report = r
    st.meta["eval_rubric_scores"] = _eval_rubric_scores(r)
    st.meta["coach_issue_table_md"] = r.issue_table_markdown
    for s in st.lop.sections:
        from datetime import datetime, timezone

        s.last_review = datetime.now(timezone.utc).isoformat()
    st.meta["coach"] = r.model_dump()
    return r


def run_lop_coach(st: OrchestratorState) -> None:
    run_lop_coach_state(st)
