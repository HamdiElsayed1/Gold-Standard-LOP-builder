"""
Production-oriented `AgentContext`: Background Material corpus + optional OpenAI
for workplan and section drafts; falls back to `NoOpAgents` where LLM is off.
"""

from __future__ import annotations

import os
from pathlib import Path

from lop_workflow.agents.llm_client import corpus_excerpt_for_section, llm_draft_section_markdown
from lop_workflow.corpus.background_material import load_background_sources
from lop_workflow.models.section import LOPDocument, SectionId
from lop_workflow.models.source import SourceRef
from lop_workflow.orchestrator.graph import NoOpAgents
from lop_workflow.orchestrator.state import OrchestratorState
from lop_workflow.workspace_paths import background_material_dir, background_material_extracted_dir


class PipelineAgentContext:
    """Delegates to `NoOpAgents` except `run_research`, `synthesize_workplan`, and `write_all_sections`."""

    def __init__(
        self,
        *,
        background_material_root: Path | None = None,
        extracted_dir: Path | None = None,
        use_llm: bool | None = None,
        jasper_prompts_root: str = "",
    ) -> None:
        self._inner = NoOpAgents()
        self.background_material_root = background_material_root
        self.extracted_dir = extracted_dir
        if use_llm is None:
            use_llm = bool(os.environ.get("OPENAI_API_KEY"))
        self.use_llm = use_llm
        self.jasper_prompts_root = jasper_prompts_root

    def synthesize_workplan(self, st: OrchestratorState) -> None:
        if self.use_llm and st.brief:
            from lop_workflow.agents.llm_client import llm_synthesize_problem

            prob = llm_synthesize_problem(st.brief)
            if prob is not None:
                st.problem = prob
                return
        self._inner.synthesize_workplan(st)

    def run_research(self, st: OrchestratorState) -> list[SourceRef]:
        root = self.background_material_root or background_material_dir()
        ext = self.extracted_dir if self.extracted_dir is not None else background_material_extracted_dir()
        st.research_corpus = load_background_sources(root, extracted_dir=ext)
        return st.research_corpus

    def build_scaffolding(self, st: OrchestratorState):
        return self._inner.build_scaffolding(st)

    def identify_agents(self, st: OrchestratorState) -> list[str]:
        return self._inner.identify_agents(st)

    def build_section_spec(self, st: OrchestratorState) -> LOPDocument:
        return self._inner.build_section_spec(st)

    def write_all_sections(self, st: OrchestratorState) -> LOPDocument:
        if not self.use_llm:
            return self._inner.write_all_sections(st)
        from lop_workflow.agents.writers import placehold_section
        from lop_workflow.models.section import SectionContent

        if st.lop is None:
            st.lop = LOPDocument(run_id=st.run_id, project_name=st.brief.project_name if st.brief else "")
        if st.brief is None:
            return st.lop

        corpus_list = list(st.research_corpus or [])
        brief_excerpt = (
            f"Project: {st.brief.project_name}\nClient: {st.brief.client_name}\n"
            f"Problem: {st.problem.statement if st.problem else ''}\n"
            f"LoP category: {st.brief.lop_category.value if st.brief.lop_category else 'unknown'}\n"
        )
        if st.meta.get("revision_feedback"):
            brief_excerpt += f"\nPartner revision notes:\n{st.meta['revision_feedback']}"

        category = st.brief.lop_category

        for spec in st.lop.section_specs:
            corpus_excerpt = corpus_excerpt_for_section(spec.section_id, corpus_list)
            body = llm_draft_section_markdown(
                section_id=spec.section_id,
                section_title=spec.title,
                brief_excerpt=brief_excerpt[:4000],
                corpus_excerpt=corpus_excerpt[:14000],
                lop_category=category,
                prompts_root=self.jasper_prompts_root,
            )
            if body:
                srcs = corpus_list[:5] if corpus_list else []
                sc = SectionContent(
                    section_id=spec.section_id,
                    outline_bullets=[f"Draft: {spec.title}"],
                    body_markdown=body,
                    sources=srcs,
                    confidence=0.78 if srcs else 0.55,
                    extra=_fees_extra_if_needed(spec.section_id),
                )
            else:
                sc = placehold_section(spec, st)
            st.lop.sections = [x for x in st.lop.sections if x.section_id != sc.section_id]
            st.lop.sections.append(sc)
        return st.lop

    def compose(self, st: OrchestratorState) -> LOPDocument:
        return self._inner.compose(st)

    def lop_coach(self, st: OrchestratorState) -> None:
        return self._inner.lop_coach(st)

    def do_export(self, st: OrchestratorState, out_dir: str) -> list[str]:
        return self._inner.do_export(st, out_dir)


def _fees_extra_if_needed(section_id: SectionId) -> dict:
    if section_id != SectionId.FEES:
        return {}
    return {
        "fees_table": {
            "headers": ["Line item", "Unit", "Amount (indicative)", "Notes / citation"],
            "rows": [
                ["Program management", "month", "TBD", "Confirm with BD/partner"],
                ["Workstreams", "month", "TBD", "Scope-dependent"],
            ],
        }
    }
