from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field

from lop_workflow.models.source import Citation, SourceRef


class ResolutionStatus(StrEnum):
    OPEN = "open"
    RESOLVED = "resolved"
    ESCALATED = "escalated"


class ConflictEntry(BaseModel):
    id: str
    field: str  # logical key e.g. "fees_structure", "timeline"
    value_a: str
    value_b: str
    source_a: SourceRef | None = None
    source_b: SourceRef | None = None
    status: ResolutionStatus = ResolutionStatus.OPEN
    resolution: str = ""
    resolution_citations: list[Citation] = Field(default_factory=list)


class ConflictLog(BaseModel):
    entries: list[ConflictEntry] = Field(default_factory=list)


class ClientTruth(BaseModel):
    """Single resolved object writers must use; populated by planner or human."""

    key_values: dict[str, str] = Field(default_factory=dict)  # e.g. "currency": "USD"
    citations: list[Citation] = Field(default_factory=list)
