from __future__ import annotations

from pydantic import BaseModel, Field

from lop_workflow.models.source import Citation, SourceRef


class FactEntry(BaseModel):
    """A grounded claim; writers and coach both reference this register."""

    key: str
    claim: str
    citations: list[Citation] = Field(default_factory=list)
    support_sources: list[SourceRef] = Field(default_factory=list)
    verified: bool = False
    used_in_sections: list[str] = Field(default_factory=list)  # SectionId values as strings


class FactsRegistry(BaseModel):
    """Shared facts to reduce cross-section contradiction."""

    entries: list[FactEntry] = Field(default_factory=list)
    supersedes_version: int = 1
