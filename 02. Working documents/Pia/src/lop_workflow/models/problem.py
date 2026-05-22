from __future__ import annotations

from pydantic import BaseModel, Field

from lop_workflow.models.brief import LOPCategory


class ProblemStatement(BaseModel):
    """Squad-synthesized problem (phase 2)."""

    statement: str
    success_criteria: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    lop_category: LOPCategory | None = None
    rationale: str = ""  # why this framing
