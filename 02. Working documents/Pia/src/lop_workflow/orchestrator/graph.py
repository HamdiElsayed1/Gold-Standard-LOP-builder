from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Protocol
from uuid import uuid4

from lop_workflow.models import LOPCategory, LOPDocument
from lop_workflow.models.brief import Brief, ScaffoldingOut, VoiceIngestionMeta
from lop_workflow.models.section import SectionId, ToCEntry
from lop_workflow.models.source import SourceRef
from lop_workflow.orchestrator.state import HumanCheckpoint, OrchestratorState, Phase
from lop_workflow.observability.audit import EventKind, AuditLogger, get_audit_logger, phase_timer
from lop_workflow.observability.audit import emit_eval_metrics


def _ts() -> str:
    return datetime.now(timezone.utc).isoformat()


class AgentContext(Protocol):
    """Injects real LLM + retrieval; `NoOpAgents` is the offline stub pipeline."""

    def synthesize_workplan(self, st: OrchestratorState) -> None: ...
    def run_research(self, st: OrchestratorState) -> list[SourceRef]: ...
    def build_scaffolding(self, st: OrchestratorState) -> ScaffoldingOut: ...
    def identify_agents(self, st: OrchestratorState) -> list[str]: ...
    def build_section_spec(self, st: OrchestratorState) -> LOPDocument: ...
    def write_all_sections(self, st: OrchestratorState) -> LOPDocument: ...
    def compose(self, st: OrchestratorState) -> LOPDocument: ...
    def lop_coach(self, st: OrchestratorState) -> None: ...
    def do_export(self, st: OrchestratorState, out_dir: str) -> list[str]: ...


@dataclass
class WorkflowResult:
    state: OrchestratorState
    exported_paths: list[str] = field(default_factory=list)
    log_path: str | None = None


@dataclass
class NoOpAgents:
    """Default offline pipeline: rule-based stub content for local testing."""

    def synthesize_workplan(self, st: OrchestratorState) -> None:  # noqa: D102
        from lop_workflow.models.problem import ProblemStatement
        from lop_workflow.models.brief import LOPCategory

        b = st.brief
        if b is None:
            return
        st.problem = ProblemStatement(
            statement=f"Help {b.client_name or 'the client'} meet stated objectives in {b.project_name or 'this engagement'}.",
            lop_category=b.lop_category or LOPCategory.EXPLORATORY,
        )

    def run_research(self, st: OrchestratorState) -> list[SourceRef]:  # noqa: D102
        st.research_corpus = [
            SourceRef(
                source_id="demo-1",
                source_type="internal_lop",
                title="Best practice snippet (demo)",
                snippet="Reusable structure for LOPs.",
            )
        ]
        return st.research_corpus

    def build_scaffolding(self, st: OrchestratorState) -> ScaffoldingOut:  # noqa: D102
        from lop_workflow.models.brief import LOPCategory, OpenQuestion
        from lop_workflow.models.section import ToCEntry

        order = 0
        toc: list[ToCEntry] = []
        for sid, ttitle in [
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
        ]:
            toc.append(ToCEntry(order=order, section_id=sid, title=ttitle))
            order += 1
        if st.brief and st.brief.lop_category is None:
            st.brief.lop_category = st.problem.lop_category if st.problem and st.problem.lop_category else LOPCategory.NON_COMPETITIVE
        questions = [OpenQuestion(id="q1", question="Key decision timeline?", blocking=True)]
        return ScaffoldingOut(questions_for_user=questions, toc=toc, lop_category=st.brief.lop_category if st.brief else None)

    def identify_agents(self, st: OrchestratorState) -> list[str]:  # noqa: D102
        n = len(st.scaffolding.toc) if st.scaffolding else 0
        return ["ingestion", "research", "planner", f"writer_pool:{n}", "lop_coach"]

    def build_section_spec(self, st: OrchestratorState) -> LOPDocument:  # noqa: D102
        from lop_workflow.models.section import LOPDocument, SectionSpec

        if st.brief is None or st.scaffolding is None:
            return LOPDocument(run_id=st.run_id, project_name="")
        specs: list[SectionSpec] = []
        for t in st.scaffolding.toc:
            specs.append(SectionSpec(section_id=t.section_id, title=t.title, dependencies=[]))
        st.lop = LOPDocument(
            run_id=st.run_id,
            project_name=st.brief.project_name,
            section_specs=specs,
            style_guide={"tone": "client-ready", "voice": "we"},
        )
        return st.lop

    def write_all_sections(self, st: OrchestratorState) -> LOPDocument:  # noqa: D102
        from lop_workflow.models.section import LOPDocument
        from lop_workflow.agents.writers import placehold_section

        if st.lop is None:
            st.lop = LOPDocument(run_id=st.run_id, project_name=st.brief.project_name if st.brief else "")
        if st.brief is None:
            return st.lop
        for spec in st.lop.section_specs:
            sc = placehold_section(spec, st)
            st.lop.sections = [x for x in st.lop.sections if x.section_id != sc.section_id]
            st.lop.sections.append(sc)
        return st.lop

    def compose(self, st: OrchestratorState) -> LOPDocument:  # noqa: D102
        from lop_workflow.models.section import LOPDocument
        from lop_workflow.agents.composer import harmonize
        h = harmonize(st)
        st.lop = h
        return st.lop if h is not None else LOPDocument(run_id=st.run_id, project_name="")

    def lop_coach(self, st: OrchestratorState) -> None:  # noqa: D102
        from lop_workflow.agents import coach
        coach.run_lop_coach_state(st)
        st.meta["coach_pass"] = (st.coach_report.overall_ok if st.coach_report else None)

    def do_export(self, st: OrchestratorState, out_dir: str) -> list[str]:  # noqa: D102
        from lop_workflow.export.html_export import write_html
        from lop_workflow.export.ppt_export import write_pptx
        from lop_workflow.export.excel_export import write_fees_excel
        if st.lop is None:
            return []
        paths: list[str] = []
        paths.append(write_html(st, out_dir))
        paths.append(write_pptx(st, out_dir))
        paths.append(write_fees_excel(st, out_dir))
        st.meta["export_type"] = "html,pptx,xlsx"
        return paths


@dataclass
class LopWorkflow:
    """
    Maps canvas: Workplan → information gathering → agents → divide work
    → work on elements → review, with three human gates.
    """

    agents: AgentContext = field(default_factory=NoOpAgents)
    audit_path: str | None = None
    out_dir: str = ".lop_out"

    def _log(self) -> AuditLogger:
        return get_audit_logger(self.audit_path)

    def new_run(
        self,
        *,
        run_id: str | None = None,
        project_name: str = "",
        client_name: str = "",
        voice_transcript: str = "",
    ) -> OrchestratorState:
        rid = run_id or str(uuid4())
        voice = VoiceIngestionMeta.from_transcript(voice_transcript) if voice_transcript else None
        b = Brief(run_id=rid, project_name=project_name, client_name=client_name, voice=voice)
        st = OrchestratorState(
            run_id=rid,
            phase=Phase.HUMAN_INTAKE,
            brief=b,
            pending_checkpoint=HumanCheckpoint.INTAKE,
        )
        self._log().emit(_ts(), EventKind.RUN_START, st.run_id, f"Intake ready: {client_name or project_name}", None)
        return st

    def resolve_intake(self, st: OrchestratorState, *, lop_category: LOPCategory | None = None) -> OrchestratorState:
        st.pending_checkpoint = None
        if lop_category and st.brief:
            st.brief.lop_category = lop_category
        st.phase = Phase.WORKPLAN
        self._log().emit(_ts(), EventKind.CHECKPOINT, st.run_id, "intake_approved", {"next": Phase.WORKPLAN.value})
        return st

    def resolve_post_toc(self, st: OrchestratorState) -> OrchestratorState:
        st.pending_checkpoint = None
        st.phase = Phase.WRITE_ELEMENTS
        st.meta["human_rounds"] = st.meta.get("human_rounds", 0) + 1
        self._log().emit(_ts(), EventKind.CHECKPOINT, st.run_id, "post_toc_approved", None)
        return st

    def resolve_pre_final(self, st: OrchestratorState) -> OrchestratorState:
        st.pending_checkpoint = None
        st.phase = Phase.EXPORT
        st.meta["human_rounds"] = st.meta.get("human_rounds", 0) + 1
        self._log().emit(_ts(), EventKind.CHECKPOINT, st.run_id, "pre_final_approved", None)
        return st

    def resolve_pre_final_send_back(self, st: OrchestratorState, *, feedback: str) -> OrchestratorState:
        """Partner sends draft back for another writer pass (coach-driven revision loop)."""
        st.pending_checkpoint = None
        st.phase = Phase.WRITE_ELEMENTS
        st.meta["revision_feedback"] = feedback
        st.meta["human_rounds"] = st.meta.get("human_rounds", 0) + 1
        self._log().emit(
            _ts(),
            EventKind.CHECKPOINT,
            st.run_id,
            "pre_final_send_back",
            {"feedback_preview": feedback[:500]},
        )
        return st

    def advance(self, st: OrchestratorState) -> OrchestratorState:
        return self._advance(st)

    def _advance(self, st: OrchestratorState) -> OrchestratorState:
        alog = self._log()
        p = st.phase
        if p == Phase.DONE:
            return st
        with phase_timer(alog, st, p):
            if p == Phase.INIT:
                st.phase = Phase.WORKPLAN
            elif p == Phase.HUMAN_INTAKE and st.pending_checkpoint:
                return st
            elif p == Phase.WORKPLAN:
                self.agents.synthesize_workplan(st)
                st.phase = Phase.INFO_GATHER
            elif p == Phase.INFO_GATHER:
                st.research_corpus = self.agents.run_research(st)
                st.phase = Phase.AGENT_BOOTSTRAP
            elif p == Phase.AGENT_BOOTSTRAP:
                st.meta["agent_roles"] = self.agents.identify_agents(st)
                st.phase = Phase.DIVIDE_WORK
            elif p == Phase.DIVIDE_WORK:
                st.scaffolding = self.agents.build_scaffolding(st)
                st.lop = self.agents.build_section_spec(st)
                st.phase = Phase.HUMAN_POST_TOC
                st.pending_checkpoint = HumanCheckpoint.POST_TOC
            elif p == Phase.HUMAN_POST_TOC and st.pending_checkpoint:
                return st
            elif p == Phase.WRITE_ELEMENTS:
                self.agents.write_all_sections(st)
                st.phase = Phase.COMPOSE
            elif p == Phase.COMPOSE:
                self.agents.compose(st)
                st.phase = Phase.LOP_COACH
            elif p == Phase.LOP_COACH:
                self.agents.lop_coach(st)
                st.phase = Phase.HUMAN_PRE_FINAL
                st.pending_checkpoint = HumanCheckpoint.PRE_FINAL
            elif p == Phase.HUMAN_PRE_FINAL and st.pending_checkpoint:
                return st
            elif p == Phase.EXPORT:
                paths = self.agents.do_export(st, self.out_dir)
                alog.emit(_ts(), EventKind.EXPORT, st.run_id, "export_complete", {"paths": paths})
                emit_eval_metrics(alog, st, paths_count=len(paths))
                st.meta["export_paths"] = paths
                st.phase = Phase.DONE
                alog.emit(_ts(), EventKind.DONE, st.run_id, "run_complete", None)
            else:
                st.last_error = f"unhandled_phase:{p}"
        return st


def run_to_done_with_auto_approves(
    *,
    out_dir: str | None = None,
    lop_category: LOPCategory | None = None,
    use_pipeline_agents: bool = True,
) -> tuple[OrchestratorState, list[str]]:
    """
    Exercises the full state machine: resolves post-ToC and pre-final immediately.
    Intake is pre-resolved with `resolve_intake` (first gate is cleared before the loop).

    When ``out_dir`` is omitted, exports go to ``Fleur/exports`` under the workspace
    (see ``workspace_paths.lop_exports_dir``). Set ``use_pipeline_agents=False`` to
    keep the offline ``NoOpAgents`` demo (no Background Material scan).
    """
    from lop_workflow.workspace_paths import ensure_workspace_directories, lop_exports_dir

    if out_dir is None:
        ensure_workspace_directories()
        out_dir = str(lop_exports_dir())

    agents = None
    if use_pipeline_agents:
        from lop_workflow.agents.pipeline_agents import PipelineAgentContext

        agents = PipelineAgentContext()

    w = LopWorkflow(agents=agents or NoOpAgents(), audit_path=None, out_dir=out_dir)
    st = w.new_run(
        project_name="Demo LOP",
        client_name="Demo client",
        voice_transcript="Client needs digital transformation. Key deadline Q3.",
    )
    st = w.resolve_intake(st, lop_category=lop_category or LOPCategory.NON_COMPETITIVE)
    for _ in range(64):
        st = w.advance(st)
        if st.phase == Phase.DONE:
            break
        if st.pending_checkpoint == HumanCheckpoint.POST_TOC:
            st = w.resolve_post_toc(st)
        elif st.pending_checkpoint == HumanCheckpoint.PRE_FINAL:
            st = w.resolve_pre_final(st)
    paths: list[str] = list(st.meta.get("export_paths", []))
    return st, paths