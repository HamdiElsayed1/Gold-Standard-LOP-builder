"""
Pydantic v2 schemas for all agent inputs and outputs.
Each schema maps directly to the JSON structure defined in the corresponding
agent spec file under Hamdi/agents/*.md.

Note: agents are instructed to return list[str] for gap-style fields, but
LLMs occasionally elaborate items into small dicts (e.g. {"topic": ...,
"verify_with": ...}). The StringList type below coerces such items back into
readable strings so a well-meaning model deviation does not break the pipeline.
"""

from typing import Annotated, Any
from pydantic import BaseModel, BeforeValidator, Field


# ─── COERCION HELPER ──────────────────────────────────────────────────────────

def _stringify(item: Any) -> str:
    """Convert any single item to a clean string."""
    if isinstance(item, str):
        return item
    if isinstance(item, dict):
        # Format dict as "value1 — value2 — value3" using non-empty values
        # in original key order. Falls back to JSON-ish key:value if values
        # are nested.
        parts: list[str] = []
        for k, v in item.items():
            if v is None or v == "":
                continue
            if isinstance(v, (list, dict)):
                parts.append(f"{k}: {v}")
            else:
                parts.append(str(v))
        return " — ".join(parts) if parts else str(item)
    if isinstance(item, (list, tuple)):
        return " — ".join(_stringify(x) for x in item)
    return str(item)


def _coerce_string_list(v: Any) -> Any:
    """Coerce each item in a list to a string. Pass non-lists through unchanged."""
    if not isinstance(v, list):
        return v
    return [_stringify(item) for item in v]


def _normalise_question_list(v: Any) -> Any:
    """
    Accept either {"questions": [...]} or a bare [...] list.
    Models occasionally collapse the wrapper object into a plain array.
    """
    if isinstance(v, list):
        return {"questions": v}
    return v


StringList = Annotated[list[str], BeforeValidator(_coerce_string_list)]


# ─── SHARED ───────────────────────────────────────────────────────────────────

class ChapterBucket(BaseModel):
    chapter: str
    extracted_content: str
    quality: str  # expected: complete | partial | missing  (kept lenient on purpose)
    notes: str = ""


class Citation(BaseModel):
    claim: str
    source_note: str  # always starts with "Model knowledge — "


class Question(BaseModel):
    id: str
    chapter: str
    question: str
    why_asked: str
    expected_answer_type: str  # narrative | list | name | number | yes/no | date


class QuestionList(BaseModel):
    questions: list[Question]


class Answer(BaseModel):
    question_id: str
    answer_text: str


class AnswerList(BaseModel):
    answers: list[Answer]


# ─── INTAKE AGENT OUTPUT ──────────────────────────────────────────────────────

class IntakePackage(BaseModel):
    client_name: str
    industry: str
    geography: str
    problem_area: str
    chapter_buckets: list[ChapterBucket]
    gap_list: StringList
    key_facts: StringList
    rfp_requirements: StringList


# ─── CONTEXT AGENT OUTPUT ─────────────────────────────────────────────────────

class ContextDoc(BaseModel):
    client_profile: str
    market_trends: str
    competitive_landscape: str
    relevant_challenges: str
    citations: list[Citation]
    evidence_gaps: StringList
    knowledge_cutoff_note: str


# ─── SYNTHESIS AGENT OUTPUT ───────────────────────────────────────────────────

class SynthesisDoc(BaseModel):
    brief_summary: str
    problem_statement: str
    win_themes: StringList
    question_list: Annotated[QuestionList, BeforeValidator(_normalise_question_list)]


# ─── VALIDATION AGENT OUTPUT ──────────────────────────────────────────────────

class QuestionVerdict(BaseModel):
    question_id: str
    question_text: str
    answer_text: str
    completeness: str  # expected: complete | partial | missing
    assessment: str
    follow_up: str = ""


class ValidationReport(BaseModel):
    overall_readiness: str  # expected: ready | conditional | not_ready
    readiness_score: int = Field(ge=0, le=100)
    verdicts: list[QuestionVerdict]
    follow_up_questions: list[Question] = []
    can_proceed_to_dot_dash: bool = False
    dot_dash_blockers: StringList = []
    residual_gaps: StringList
    recommendation: str


# ─── DOT-DASH AGENT OUTPUT ────────────────────────────────────────────────────

class DotDashSlide(BaseModel):
    """One chapter of the LoP storyline: a headline ('dot') and supporting points ('dashes')."""
    chapter: str
    headline: str  # the "dot" — a complete-sentence insight, not a label
    supporting_points: list[str]  # the "dashes" — 3-5 bullet supporting points
    confidence: str = "complete"  # expected: complete | partial | placeholder
    notes: str = ""  # what's missing, what needs partner sign-off, etc.


class DotDashDoc(BaseModel):
    storyline_summary: str  # 1-2 sentences on the through-line of the LoP
    slides: list[DotDashSlide]
    open_risks: StringList = []  # cross-cutting risks the BA should know before sharing


# ─── LOP QUALITY EVAL AGENT OUTPUT ────────────────────────────────────────────

class LopEvalElement(BaseModel):
    """One of the 10 Gold Standard completeness checks."""

    element_name: str
    status: str  # Strong | Needs Work | Missing
    feedback: str


class ReferenceJudgement(BaseModel):
    """LLM-as-judge comparison when a gold / best-practice reference is supplied."""

    reference_provided: bool = False
    score: int | None = Field(default=None, ge=0, le=1)  # 1 = PASS, 0 = FAIL; null if no reference
    reasoning: str = ""


class LopEvalReport(BaseModel):
    """Structured Gold Standard evaluation report from lop-quality-eval-agent."""

    overall_score: int = Field(ge=0, le=10)
    verdict: str
    high_level_feedback: str
    elements_breakdown: list[LopEvalElement]
    storyline: str
    client_centricity: str
    brevity: str
    magic_moment: str
    top_action_items: list[str] = Field(min_length=3, max_length=3)
    reference_judgement: ReferenceJudgement = Field(default_factory=ReferenceJudgement)
