from __future__ import annotations

from pydantic import BaseModel, Field


class SourceRef(BaseModel):
    """Provenance for RAG, CRM, or uploaded docs (metadata only; content lives in retrieval)."""

    source_id: str
    source_type: str  # e.g. "tender", "internal_lop", "cst_context", "partner_memo", "web"
    title: str = ""
    uri: str = ""
    retrieved_at: str = ""  # ISO-8601
    snippet: str = ""


class Citation(BaseModel):
    """A citeable line tied to a fact or claim."""

    key: str
    text: str
    source_refs: list[SourceRef] = Field(default_factory=list)
    page_or_slide_hint: str = ""
