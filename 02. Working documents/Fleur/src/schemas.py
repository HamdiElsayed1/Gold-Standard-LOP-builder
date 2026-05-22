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
from pydantic import BaseModel, BeforeValidator, Field, model_validator


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
    # `claim` and `source_note` are default-safe so a partial citation never
    # blocks the whole ContextDoc from validating. In practice the agent must
    # populate both — but LLMs occasionally drop one (especially `claim` on
    # model_knowledge citations where they only label the source). The
    # `_coerce_citation` validator below repairs the dict before field
    # validation: if `claim` is missing/empty but `source_note` is present,
    # we copy the source_note into `claim` (with the "Model knowledge — "
    # prefix stripped) so the partner still sees something meaningful.
    claim: str = ""
    source_note: str = ""

    # --- Context v2 fields (default-safe so model-knowledge entries still validate) ---
    # kind: "web" | "model_knowledge"
    kind: str = "model_knowledge"
    # Populated when kind == "web"; the page URL the claim was sourced from.
    url: str = ""
    # Page title from the web_search annotation (may be empty even for web sources).
    title: str = ""
    # ISO date string (e.g. "2026-05-02") set by the call-site after parsing.
    retrieved_at: str = ""

    @model_validator(mode="before")
    @classmethod
    def _coerce_citation(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data

        claim = (data.get("claim") or "").strip() if isinstance(data.get("claim"), str) else ""
        note = (data.get("source_note") or "").strip() if isinstance(data.get("source_note"), str) else ""

        if not claim and note:
            derived = note
            for prefix in ("Model knowledge — ", "Model knowledge - ", "Model knowledge: "):
                if derived.startswith(prefix):
                    derived = derived[len(prefix):]
                    break
            data["claim"] = derived or "(claim not specified)"

        if not data.get("source_note") and claim:
            kind = (data.get("kind") or "model_knowledge").strip().lower()
            data["source_note"] = (
                "Model knowledge — source not specified"
                if kind == "model_knowledge"
                else "Source not specified"
            )

        return data


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

    # --- Intake v2 fields (all default-safe so older runs still validate) ---
    # pursuit_type: "rfp" | "rfi_only" | "rfp_with_rfi" | "unclear"
    pursuit_type: str = "unclear"
    # competitive_status: "competitive" | "non_competitive" | "unclear"
    competitive_status: str = "unclear"
    # Firms named as competing in the pursuit (empty unless competitive AND named)
    competitor_firms: StringList = []
    # Early-stage signals from the RFI (empty when no RFI in inputs)
    rfi_signals: StringList = []
    # gold_standard_mode: "guidance" | "examples_synthesis" | "none"
    gold_standard_mode: str = "none"
    # Authoritative guidance text when mode == "guidance"
    gold_standard_guidance: str = ""
    # Pattern synthesis from example LoPs when mode == "examples_synthesis"
    gold_standard_synthesis: str = ""


# ─── CONTEXT AGENT OUTPUT ─────────────────────────────────────────────────────

class RecentSignal(BaseModel):
    """
    One material event observed in the public record about the client.
    Categories: leadership_change | news | m&a | financial | operational | risk_event.
    Used by Context v3 Deep mode to surface things like CEO/CFO moves,
    acquisitions, restructurings, earnings milestones, public commitments,
    cyber incidents, lawsuits, recalls.
    """
    category: str = ""
    headline: str
    detail: str = ""
    date: str = ""           # "YYYY-MM" or "YYYY"
    citation_urls: StringList = []


class RegulatoryItem(BaseModel):
    """
    One law, regulation, directive, or enforcement action material to the
    client's industry and problem_area, with explicit client-impact framing.
    """
    topic: str
    summary: str = ""
    client_impact: str = ""
    effective_date: str = ""  # "YYYY" | "in force" | "proposed"
    citation_urls: StringList = []


class ChapterTakeaways(BaseModel):
    """
    Bridge between the research and the LoP itself: 2-3 sentence synthesis
    per chapter that external research can sharpen. Other chapters
    (Team, Fees, Timeline, Appendix) rely on partner inputs, not research.
    """
    context_and_objectives: str = ""
    why_mckinsey: str = ""
    approach: str = ""
    market_trends: str = ""
    credentials: str = ""


class ContextDoc(BaseModel):
    client_profile: str
    market_trends: str
    competitive_landscape: str
    relevant_challenges: str
    citations: list[Citation]
    evidence_gaps: StringList
    knowledge_cutoff_note: str

    # --- Context v2 fields (default-safe so older runs still validate) ---
    # search_mode: "quick" | "deep" | "deep_fallback" | "model_knowledge_fallback"
    search_mode: str = "model_knowledge_fallback"
    # Verbatim copy of the user's free-text additional context (audit trail).
    additional_context_used: str = ""
    # Query strings the agent reports it ran (informational, not authoritative).
    searches_performed: StringList = []

    # --- Context v3 fields (LoP-aligned research dimensions) ---
    # All default-safe so v1/v2 runs still validate.
    recent_signals: list[RecentSignal] = []
    regulatory_environment: list[RegulatoryItem] = []
    chapter_takeaways: ChapterTakeaways = Field(default_factory=ChapterTakeaways)


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


# ─── BA SUPPORT AGENT OUTPUT ──────────────────────────────────────────────────

class Todo(BaseModel):
    """One concrete next action for the BA, derived from the upstream pack."""
    id: str
    owner: str = "BA"
    chapter: str = "cross-chapter"  # canonical chapter name OR "cross-chapter"
    action: str
    dependency: str = ""             # what must be true before this can start
    due_relative: str = ""           # e.g. "day 1", "before partner sync", "T-3"
    priority: str = "normal"         # blocker | high | normal


class EmailDraft(BaseModel):
    """A copy-paste-ready email the BA can send to a partner-named contact."""
    id: str
    recipient_name: str
    recipient_role: str = ""
    purpose: str  # credentials_request | expert_intro | team_confirm | fee_model_request | followup_other
    subject: str
    body: str
    linked_chapter: str = ""
    linked_todo_id: str = ""


class SourceItem(BaseModel):
    """One concrete source artefact still needed to draft a chapter."""
    id: str
    chapter: str
    item_type: str  # case_one_pager | cv | fee_model | reference_doc | client_artifact
    description: str
    contact_name: str = ""
    status: str = "to_pull"  # to_pull | requested | received


class BASupportPack(BaseModel):
    summary: str
    todo_list: list[Todo]
    email_drafts: list[EmailDraft]
    source_pack: list[SourceItem]


# ─── SLIDE AUTHOR AGENT OUTPUT ────────────────────────────────────────────────

class SlideHTML(BaseModel):
    """One rendered slide: chapter, output filename, and the inner HTML body."""
    chapter: str
    filename: str
    html: str
    notes: str = ""


class SlideDeck(BaseModel):
    """The full HTML deck produced by Step 8."""
    format_mode: str = "mckinsey"  # mckinsey | client
    client_style_summary: str = ""
    slides: list[SlideHTML]
