from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field

from lop_workflow.models.source import Citation, SourceRef


class SectionId(StrEnum):
    """
    Canonical chapter spine aligned to lop-builder-workflow (Context → CVs).
    Enum definition order is the default document / composer order.
    """

    CONTEXT = "context_objectives"
    WHY_MCKINSEY = "why_mckinsey"
    TIMELINE_TEAM = "timeline_team"
    TEAM = "team"
    CREDENTIALS = "credentials"
    MARKET = "market_trends"
    APPROACH = "approach"
    FEES = "fees"
    APPENDIX = "appendix"
    REFERENCES = "references"
    TEAM_CVS = "team_cvs"


SECTION_DOCUMENT_ORDER: tuple[SectionId, ...] = (
    SectionId.CONTEXT,
    SectionId.WHY_MCKINSEY,
    SectionId.TIMELINE_TEAM,
    SectionId.TEAM,
    SectionId.CREDENTIALS,
    SectionId.MARKET,
    SectionId.APPROACH,
    SectionId.FEES,
    SectionId.APPENDIX,
    SectionId.REFERENCES,
    SectionId.TEAM_CVS,
)


class SectionSpec(BaseModel):
    section_id: SectionId
    title: str
    dependencies: list[SectionId] = Field(default_factory=list)  # order for composer
    needs_more_input: bool = False
    notes: str = ""
    min_slides: int = 1
    max_slides: int = 5


class ToCEntry(BaseModel):
    order: int
    section_id: SectionId
    title: str


class SectionContent(BaseModel):
    section_id: SectionId
    outline_bullets: list[str] = Field(default_factory=list)
    body_markdown: str = ""  # main narrative
    sources: list[SourceRef] = Field(default_factory=list)
    inline_citations: list[Citation] = Field(default_factory=list)
    confidence: float = Field(0.0, ge=0.0, le=1.0)
    last_review: str = ""  # ISO-8601; set by LOP Coach or human
    extra: dict[str, Any] = Field(default_factory=dict)


class SectionDraft(BaseModel):
    section_id: SectionId
    content: SectionContent


class LOPDocument(BaseModel):
    """Single structured model mapping to slides/outline for export."""

    run_id: str
    project_name: str
    version: int = 1
    section_specs: list[SectionSpec] = Field(default_factory=list)
    sections: list[SectionContent] = Field(default_factory=list)
    style_guide: dict[str, str] = Field(default_factory=dict)  # e.g. tone, naming

    def by_section_id(self) -> dict[SectionId, SectionContent]:
        return {s.section_id: s for s in self.sections}
