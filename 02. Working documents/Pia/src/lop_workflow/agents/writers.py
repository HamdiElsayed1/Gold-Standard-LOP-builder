from __future__ import annotations

from lop_workflow.gold_patterns.loader import get_section_pattern
from lop_workflow.models.section import SectionContent, SectionSpec, SectionId
from lop_workflow.models.facts import FactEntry, FactsRegistry
from lop_workflow.models.source import Citation, SourceRef
from lop_workflow.orchestrator.state import OrchestratorState


def placehold_section(spec: SectionSpec, st: OrchestratorState) -> SectionContent:
    """
    Offline-friendly section body using gold-pattern scaffold (no LLM).
    Links claims to `FactsRegistry` when possible.
    """
    ctx = f"{st.brief.client_name or 'The client'}" if st.brief else "The client"
    cat = st.brief.lop_category if st.brief else None
    pattern = get_section_pattern(spec.section_id, cat)

    srcs: list[SourceRef] = list(getattr(st, "research_corpus", []) or [])[:3]
    freg = st.facts
    fee_fact: FactEntry | None = next((e for e in freg.entries if e.key == "fee_placeholder"), None)
    if not fee_fact and spec.section_id == SectionId.FEES:
        src = srcs[0] if srcs else SourceRef(source_id="cst-confirm", source_type="cst_context", title="CST", snippet="To be confirmed in workshop")
        fee_fact = FactEntry(
            key="fee_placeholder",
            claim="Indicative fee model TBD; confirm in workshop.",
            citations=[Citation(key="c-fee-1", text="Pending CST confirmation", source_refs=[src])],
            used_in_sections=[str(spec.section_id.value)],
        )
        freg.entries.append(fee_fact)

    bullets: list[str] = []
    if pattern.win_logic:
        bullets.extend(pattern.win_logic[:3])
    else:
        bullets.extend([f"Structure aligned to: {spec.title}", f"Client context: {ctx}"])
    rev = st.meta.get("revision_feedback")
    if rev:
        bullets.insert(0, f"Partner revision: {str(rev)[:400]}")

    lines: list[str] = [f"## {spec.title}", ""]
    lines.append(f"*Draft scaffold for **{ctx}** — fill from manifest-approved sources only.*")
    lines.append("")
    if pattern.structure_hints:
        lines.append("### Suggested structure")
        lines.extend(f"- {h}" for h in pattern.structure_hints)
        lines.append("")
    if pattern.must_have_evidence:
        lines.append("### Evidence / gates")
        lines.extend(f"- `{m}`" for m in pattern.must_have_evidence)
        lines.append("")
    lines.append("### Narrative")
    lines.append(
        f"Develop this section using only Step 0 manifest sources. "
        f"See gold-pattern traceability in internal catalog for `{spec.section_id.value}`."
    )

    extra: dict = {}
    if spec.section_id == SectionId.FEES:
        extra["fees_table"] = {
            "headers": ["Line item", "Unit", "Amount (indicative)", "Notes / citation"],
            "rows": [
                ["Program management", "month", "TBD", "Partner / BD approval"],
                ["Workstreams", "month", "TBD", "Scope-dependent"],
            ],
        }

    return SectionContent(
        section_id=spec.section_id,
        outline_bullets=bullets[:8],
        body_markdown="\n".join(lines),
        sources=srcs,
        confidence=0.62 if not srcs else 0.72,
        extra=extra,
    )


def run_parallel_drafts(st: OrchestratorState) -> list[SectionContent]:
    if st.lop is None or not st.lop.section_specs:
        return []
    return [placehold_section(sp, st) for sp in st.lop.section_specs]
