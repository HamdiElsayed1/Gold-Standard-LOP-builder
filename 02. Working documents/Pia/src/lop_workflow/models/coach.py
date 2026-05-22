from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field

from lop_workflow.models.section import SectionId
from lop_workflow.models.source import SourceRef


class IssueSeverity(StrEnum):
    INFO = "info"
    WARN = "warn"
    BLOCK = "block"


class LOPCoachIssue(BaseModel):
    code: str
    message: str
    severity: IssueSeverity = IssueSeverity.WARN
    section_id: SectionId | None = None
    fact_key: str | None = None


class SectionScore(BaseModel):
    section_id: SectionId
    score: float = Field(ge=0.0, le=1.0)
    pass_gate: bool = True


class LOPCoachReport(BaseModel):
    issues: list[LOPCoachIssue] = Field(default_factory=list)
    section_scores: list[SectionScore] = Field(default_factory=list)
    overall_ok: bool = True
    summary: str = ""
    # Research corpus + RFP/tender on the brief (inputs to the coach).
    background_materials: list[SourceRef] = Field(default_factory=list)
    # Human-readable table aligned to Jasper `lop-coach.md` output shape.
    issue_table_markdown: str = ""
    # Qualitative gates (green / amber / red / review) for LoP card-style review.
    rubric_dimensions: dict[str, str] = Field(default_factory=dict)
