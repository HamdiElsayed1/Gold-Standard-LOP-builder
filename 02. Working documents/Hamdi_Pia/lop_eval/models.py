"""Pydantic models mirroring schema/eval_result.schema.json and document input."""

from __future__ import annotations

from enum import Enum
from typing import Annotated, Any, Literal, Union

from pydantic import BaseModel, Field


class IssueSeverity(str, Enum):
    critical = "critical"
    major = "major"
    minor = "minor"


class IssueLocation(BaseModel):
    section_id: str | None = None
    section_title: str | None = None
    block_index: int | None = None
    block_id: str | None = None
    note: str | None = None


class EvalIssue(BaseModel):
    type: str
    severity: IssueSeverity
    description: str
    offending_text: str
    expected_text_or_rule: str
    location: IssueLocation | None = None
    related_locations: list[dict[str, Any]] | None = None
    checker_id: str | None = None
    evidence: dict[str, Any] | None = None


class EvalSummary(BaseModel):
    critical: int = 0
    major: int = 0
    minor: int = 0


class EvalResult(BaseModel):
    document_id: str
    eval_version: str
    overall_score: float = Field(ge=0, le=100)
    passed: bool
    threshold: float | None = None
    issues: list[EvalIssue]
    summary: EvalSummary
    score_breakdown: dict[str, float] = Field(
        default_factory=dict,
        description="Points deducted per checker key",
    )
    issue_counts_by_checker: dict[str, int] = Field(default_factory=dict)
    checker_weights_used: dict[str, float] = Field(default_factory=dict)


# --- Document input (structured, semantic text only) ---


class BlockBase(BaseModel):
    id: str | None = None


class HeadingBlock(BlockBase):
    type: Literal["heading"] = "heading"
    level: int = 1
    text: str


class ParagraphBlock(BlockBase):
    type: Literal["paragraph"] = "paragraph"
    text: str


class ListBlock(BlockBase):
    type: Literal["list"] = "list"
    items: list[str]


class TableBlock(BlockBase):
    type: Literal["table"] = "table"
    headers: list[str]
    rows: list[list[str]]
    caption: str | None = None


class FootnoteBlock(BlockBase):
    type: Literal["footnote"] = "footnote"
    text: str


class CaptionBlock(BlockBase):
    type: Literal["caption"] = "caption"
    text: str


Block = Annotated[
    Union[
        HeadingBlock,
        ParagraphBlock,
        ListBlock,
        TableBlock,
        FootnoteBlock,
        CaptionBlock,
    ],
    Field(discriminator="type"),
]


class Section(BaseModel):
    id: str
    title: str | None = None
    blocks: list[Block] = Field(default_factory=list)


class FactRecord(BaseModel):
    key: str
    value_text: str
    unit: str | None = None
    valid_from: str | None = None
    valid_to: str | None = None


class SourceOfTruth(BaseModel):
    facts: list[FactRecord] = Field(default_factory=list)


class ProposalDocument(BaseModel):
    document_id: str
    title: str | None = None
    metadata: dict[str, str] = Field(default_factory=dict)
    sections: list[Section] = Field(default_factory=list)


class EvalConfig(BaseModel):
    pass_threshold: float = 70.0
    deduct_critical: float = 25.0
    deduct_major: float = 10.0
    deduct_minor: float = 3.0
    fail_on_critical: bool = True
    """If True, passed is False when any critical issue exists regardless of score."""

    numeric_relative_tolerance: float = 0.005
    near_duplicate_ratio: float = 0.86
    """Ratio for fuzzy entity / label similarity (0-1)."""

    drift_term_classes: list[list[str]] = Field(
        default_factory=lambda: [
            ["transformation", "sprint", "initiative", "project", "program"],
        ]
    )
    """Within a class, co-occurrence of two terms without definitional bridge → terminology drift."""

    scope_exclusive_tags: list[str] = Field(
        default_factory=lambda: ["emea", "apac", "americas", "north america", "global", "worldwide"]
    )

    checker_weights: dict[str, float] = Field(default_factory=dict)
    """Per-checker multiplier on severity deductions (1.0 = default)."""
