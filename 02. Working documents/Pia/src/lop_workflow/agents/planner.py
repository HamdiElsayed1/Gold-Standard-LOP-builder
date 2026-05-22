from __future__ import annotations

from dataclasses import dataclass

from lop_workflow.models.brief import LOPCategory, ScaffoldingOut
from lop_workflow.models.brief import OpenQuestion
from lop_workflow.models.problem import ProblemStatement
from lop_workflow.models.section import LOPDocument, SectionId, SectionSpec, ToCEntry
from lop_workflow.orchestrator.state import OrchestratorState


@dataclass
class PlanInput:
    problem: ProblemStatement
    lop_category: LOPCategory | None


@dataclass
class PlanOutput:
    scaffolding: ScaffoldingOut
    lop: LOPDocument | None = None


def build_default_toc() -> list[ToCEntry]:
    """Default spine per lop-builder-workflow.mdc."""
    pairs: list[tuple[SectionId, str]] = [
        (SectionId.CONTEXT, "Context and objectives"),
        (SectionId.WHY_MCKINSEY, "Why McKinsey?"),
        (SectionId.TIMELINE_TEAM, "Timeline and team"),
        (SectionId.TEAM, "Team"),
        (SectionId.CREDENTIALS, "Credentials"),
        (SectionId.MARKET, "Market trends"),
        (SectionId.APPROACH, "Approach"),
        (SectionId.FEES, "Fees"),
        (SectionId.APPENDIX, "Appendix"),
        (SectionId.REFERENCES, "References"),
        (SectionId.TEAM_CVS, "Team CVs"),
    ]
    return [ToCEntry(order=i, section_id=sid, title=title) for i, (sid, title) in enumerate(pairs)]


def default_planner(_inp: PlanInput) -> ScaffoldingOut:
    qs = [OpenQuestion(id="timeline", question="What is the key decision or signing timeline?", blocking=True)]
    return ScaffoldingOut(questions_for_user=qs, toc=build_default_toc(), lop_category=_inp.lop_category)


def to_lop_document(st: OrchestratorState, s: ScaffoldingOut) -> LOPDocument:
    assert st.brief
    specs = [SectionSpec(section_id=t.section_id, title=t.title) for t in s.toc]
    return LOPDocument(
        run_id=st.run_id,
        project_name=st.brief.project_name,
        section_specs=specs,
        style_guide={"tone": "client-ready"},
    )
