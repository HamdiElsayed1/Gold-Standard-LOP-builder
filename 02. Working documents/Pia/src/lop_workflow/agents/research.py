"""
Research agent: RAG + web + MVI / external policy boundary.

- Every retrieved item MUST include `SourceRef` with snippet for citation.
- MVI: only `allowed_source_types` from policy; block others with explicit reason in output.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from lop_workflow.models.brief import LOPCategory
from lop_workflow.models.source import SourceRef
from lop_workflow.orchestrator.state import OrchestratorState


@dataclass
class ResearchPolicy:
    allow_web: bool = True
    allow_mvi: bool = False
    # Source types the pipeline may attach (internal corpora, tenders, web, mvi, …)
    allowed_source_types: frozenset[str] = field(
        default_factory=lambda: frozenset({"tender", "internal_lop", "cst_context", "web"})
    )
    mvi_safety_note: str = "MVI connections disabled until approved connector is configured."


@dataclass
class ResearchInput:
    query: str
    lop_category: LOPCategory | None
    run_id: str
    prior_sources: list[SourceRef] = field(default_factory=list)
    policy: ResearchPolicy = field(default_factory=ResearchPolicy)


@dataclass
class ResearchOutput:
    hits: list[SourceRef]
    blocked_attempts: list[dict] = field(default_factory=list)  # e.g. {"type":"mvi", "reason":...}
    require_citation: bool = True  # wire writers + coach to enforce


def _stub_hits(ri: ResearchInput) -> list[SourceRef]:
    base = list(ri.prior_sources)
    if ri.lop_category:
        base.append(
            SourceRef(
                source_id="cat-match",
                source_type="internal_lop",
                title=f"LOP example ({ri.lop_category.value})",
                snippet=f"Category: {ri.lop_category.value}. {ri.query[:500]}",
            )
        )
    if ri.policy.allow_web and "web" in ri.policy.allowed_source_types:
        base.append(
            SourceRef(
                source_id="web-1",
                source_type="web",
                title="Market search (demo)",
                snippet="Replace with real web tool output; keep citation.",
            )
        )
    if ri.policy.allow_mvi and "mvi" in ri.policy.allowed_source_types:
        base.append(SourceRef(source_id="mvi-1", source_type="mvi", title="MVI", snippet="…"))
    return base


def run_research(ri: ResearchInput) -> ResearchOutput:
    """
    I/O spec for the Research agent. Stub returns `SourceRef` with snippets for RAG.
    """
    blocked: list[dict] = []
    if "mvi" in ri.policy.allowed_source_types and not ri.policy.allow_mvi:
        # Policy contradiction: allow_mvi false wins
        blocked.append({"type": "mvi", "reason": "allow_mvi is false"})
    hits = _stub_hits(ri)
    filtered: list[SourceRef] = []
    for h in hits:
        if h.source_type not in ri.policy.allowed_source_types:
            blocked.append({"type": h.source_type, "reason": "not in policy"})
            continue
        filtered.append(h)
    if ri.policy.allow_mvi is False:
        # Document policy echo for observability
        pass
    return ResearchOutput(
        hits=filtered,
        blocked_attempts=blocked,
    )


def research_from_state(st: OrchestratorState) -> list[SourceRef]:
    b = st.brief
    q = ((b.voice.raw_transcript if b and b.voice else "") or (b.project_name if b else "") or "LOP")
    prior = b.rfp_tender_references if b else []
    out = run_research(
        ResearchInput(
            query=q,
            lop_category=b.lop_category if b else None,
            run_id=st.run_id,
            prior_sources=prior,
        )
    )
    st.meta["research_blocked"] = out.blocked_attempts
    return out.hits
