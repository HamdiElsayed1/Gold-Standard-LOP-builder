from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field

from lop_workflow.models import (
    Brief,
    ConflictLog,
    FactsRegistry,
    LOPCoachReport,
    LOPDocument,
    ProblemStatement,
    ScaffoldingOut,
    SourceRef,
)


class Phase(StrEnum):
    """
    Maps to canvas: Workplan -> Information gathering -> Identifying agents
    -> Divide work -> Work on elements -> Review / iterate.
    """

    INIT = "init"
    HUMAN_INTAKE = "human_intake"  # checkpoint: confirm raw brief
    WORKPLAN = "workplan"  # problem statement from brief
    INFO_GATHER = "info_gather"  # research + RAG
    AGENT_BOOTSTRAP = "agent_bootstrap"  # choose writer roles / tools
    DIVIDE_WORK = "divide_work"  # section specs + ToC
    HUMAN_POST_TOC = "human_post_toc"  # checkpoint: answer clarifying Qs, approve ToC
    WRITE_ELEMENTS = "write_elements"  # parallel section drafting
    COMPOSE = "compose"  # merge for cross-refs
    LOP_COACH = "lop_coach"
    HUMAN_PRE_FINAL = "human_pre_final"  # checkpoint: approve or send back to writers
    EXPORT = "export"
    DONE = "done"


class HumanCheckpoint(StrEnum):
    """Explicit human gates (plan: intake, post-ToC, pre-final)."""

    INTAKE = "intake"
    POST_TOC = "post_toc"
    PRE_FINAL = "pre_final"


class OrchestratorState(BaseModel):
    """
    Graph state for the LOP run. All agents read/write this object.
    """

    run_id: str
    phase: Phase = Phase.INIT
    brief: Brief | None = None
    problem: ProblemStatement | None = None
    research_corpus: list[SourceRef] = Field(default_factory=list)  # retrieval results
    scaffolding: ScaffoldingOut | None = None
    lop: LOPDocument | None = None
    facts: FactsRegistry = Field(default_factory=FactsRegistry)
    conflicts: ConflictLog = Field(default_factory=ConflictLog)
    coach_report: LOPCoachReport | None = None
    pending_checkpoint: HumanCheckpoint | None = None
    last_error: str | None = None
    meta: dict[str, Any] = Field(default_factory=dict)

    def is_human_pause(self) -> bool:
        return self.pending_checkpoint is not None
