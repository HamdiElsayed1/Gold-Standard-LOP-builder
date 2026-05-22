from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field

from lop_workflow.models.conflict import ClientTruth
from lop_workflow.models.section import ToCEntry
from lop_workflow.models.source import Citation, SourceRef


class LOPCategory(StrEnum):
    COMPETITIVE = "competitive"
    NON_COMPETITIVE = "non_competitive"
    EXPLORATORY = "exploratory"
    RELATIONSHIP = "relationship_building"


class VoiceIngestionMeta(BaseModel):
    """Optional metadata for the ~7 min voice capture."""

    raw_transcript: str
    language: str = "en"
    duration_seconds_est: float | None = None
    cleaned_bullets: list[str] = Field(default_factory=list)
    pii_flags: list[str] = Field(default_factory=list)  # field names that may need redaction

    @classmethod
    def from_transcript(cls, transcript: str) -> "VoiceIngestionMeta":
        return cls(raw_transcript=transcript, cleaned_bullets=[l.strip() for l in transcript.splitlines() if l.strip()])


class Assumptions(BaseModel):
    """Explicit priors; human must confirm; diff on change."""

    items: list[str] = Field(default_factory=list)
    confirmed: bool = False
    last_changed_at: str = ""  # ISO-8601
    version: int = 1


class OpenQuestion(BaseModel):
    id: str
    question: str
    blocking: bool = True
    suggested_owner: str = "CST"  # CST, Partner, client, etc.


class Brief(BaseModel):
    """
    Normalized output of phase 1 (human + optional email/docs).
    """

    run_id: str
    project_name: str = ""
    client_name: str = ""
    voice: VoiceIngestionMeta | None = None
    email_excerpt: str = ""
    rfp_tender_references: list[SourceRef] = Field(default_factory=list)
    open_questions: list[OpenQuestion] = Field(default_factory=list)
    lop_category: LOPCategory | None = None
    assumptions: Assumptions = Field(default_factory=Assumptions)
    # Resolved single source of truth after conflict handling (populated in later stages)
    client_truth: ClientTruth = Field(default_factory=ClientTruth)
    extra: dict[str, Any] = Field(default_factory=dict)


class ScaffoldingOut(BaseModel):
    """ToC + clarifying questions (phase 3)."""

    questions_for_user: list[OpenQuestion] = Field(default_factory=list)
    toc: list[ToCEntry] = Field(default_factory=list)
    lop_category: LOPCategory | None = None
