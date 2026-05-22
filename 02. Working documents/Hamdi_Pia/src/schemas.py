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

    @model_validator(mode="before")
    @classmethod
    def _coerce_item_ids(cls, data: Any) -> Any:
        """
        Ensure every Todo / EmailDraft / SourceItem in the agent's output
        carries a non-empty `id`. The BA Support Agent spec lists the field
        bullets for each list without naming `id` (only the JSON example
        shows it), so models occasionally drop the id on one of the three
        lists. Auto-assign sequential ids (`T{n}`, `E{n}`, `S{n}`) for any
        item missing one — items with ids keep them.
        """
        if not isinstance(data, dict):
            return data

        prefix_map = {"todo_list": "T", "email_drafts": "E", "source_pack": "S"}
        for list_name, prefix in prefix_map.items():
            items = data.get(list_name)
            if not isinstance(items, list):
                continue
            for idx, item in enumerate(items, start=1):
                if not isinstance(item, dict):
                    continue
                existing = item.get("id")
                if isinstance(existing, str) and existing.strip():
                    continue
                item["id"] = f"{prefix}{idx}"

        return data


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


class _SlideHTMLFragment(BaseModel):
    """One slide fragment as emitted by a chapter agent: just the inner
    `<section class="slide">…</section>` body and an optional note. The
    dispatcher decorates each fragment with the chapter/filename when
    folding it into the final `SlideHTML`/`SlideDeck`."""
    html_body: str = ""
    notes: str = ""


class ChapterSlideAuthorOutput(BaseModel):
    """
    Output schema for chapter-specialised slide agents that may emit one
    OR multiple slides for a single dot-dash chapter (e.g. Credentials
    with two anchor cases). Includes a before-validator that accepts the
    legacy single-slide shape `{ "html_body": "...", "notes": "..." }`
    and coerces it into `{ "slides": [{...}], "notes": "" }` so cover-
    style agents (and any chapter agent emitting one slide) keep parsing
    cleanly.
    """
    slides: list[_SlideHTMLFragment]
    notes: str = ""

    @model_validator(mode="before")
    @classmethod
    def _coerce_legacy_shape(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        # Already in the new shape — just normalise notes.
        if isinstance(data.get("slides"), list):
            return data
        # Legacy shape: { html_body, notes } -> { slides: [{...}], notes: "" }
        legacy_body = data.get("html_body")
        if isinstance(legacy_body, str):
            return {
                "slides": [
                    {
                        "html_body": legacy_body,
                        "notes": data.get("notes") or "",
                    }
                ],
                "notes": "",
            }
        return data


# ─── CLIENT EVALUATOR AGENT OUTPUT ────────────────────────────────────────────

class RFPCoverageItem(BaseModel):
    """One RFP requirement and how the proposal addresses it from the buyer's POV."""
    requirement: str
    status: str            # expected: covered | partial | missing
    evidence: str = ""
    concern: str = ""


class OwnerPriorityItem(BaseModel):
    """One thing the company owner / sponsor cares about, sourced from the
    RFP/RFI, partner answers, or inferred from industry/geography context."""
    priority: str
    source: str            # expected: rfp | rfi | partner_answer | inferred
    addressed: bool
    evidence: str = ""
    concern: str = ""


class ChapterClientView(BaseModel):
    """Owner-perspective verdict on one chapter actually shown in the proposal."""
    chapter: str
    verdict: str           # expected: strong | acceptable | weak | missing
    client_view: str


class ReasonablenessCheck(BaseModel):
    """One reasonableness check (timeline / fees / team / approach) from the buyer's POV."""
    verdict: str           # expected: reasonable | stretch | unreasonable | not_shown
    concern: str = ""


class ClientEvaluationReport(BaseModel):
    """
    Output of `client-evaluator-agent`. The agent plays the role of the
    company owner / sponsor receiving the LoP and produces a structured
    buyer-perspective verdict. Used by Step 9 of the Streamlit pipeline,
    runnable both on the in-app rendered deck and on an uploaded final
    deliverable (HTML / PDF / PPTX).
    """
    overall_verdict: str           # expected: would_buy | would_buy_with_revisions | would_not_buy
    score: int = Field(ge=0, le=100)
    headline_takeaway: str
    rfp_coverage: list[RFPCoverageItem] = []
    owner_priorities: list[OwnerPriorityItem] = []
    chapter_assessment: list[ChapterClientView] = []
    timeline_check: ReasonablenessCheck
    fees_check: ReasonablenessCheck
    team_check: ReasonablenessCheck
    approach_check: ReasonablenessCheck
    quality_assessment: str = ""
    top_concerns: StringList = []
    missing_for_owner: StringList = []
    recommended_changes: StringList = []


# ─── LOSS ANALYSIS AGENT OUTPUT ───────────────────────────────────────────────

class LossReason(BaseModel):
    """One ranked reason this proposal would lose, with severity, category, and proposal evidence."""
    reason: str
    severity: str       # expected: critical | high | medium | low
    category: str       # expected: narrative | credentials | fees | team |
                        # approach | timeline | win_themes | rfp_fit | other
    evidence: str = ""


class CompetitorAngle(BaseModel):
    """How one named competitor (or 'no_decision') would beat this proposal.

    `model_knowledge_note` is non-empty when the agent flags thin model
    knowledge of the competitor — the partner should validate before
    relying on the angle.
    """
    competitor: str               # firm name OR "no_decision"
    competitor_strength: str
    where_it_lands: str
    severity: str                  # expected: critical | high | medium | low
    model_knowledge_note: str = ""


class KeyImprovement(BaseModel):
    """One specific, internal action item that closes a loss reason.

    Internal-only — never names a competitor; that constraint is enforced
    by the agent spec, not the schema.
    """
    improvement: str
    expected_impact: str
    priority: str                  # expected: blocker | high | normal
    linked_chapter: str = "cross-chapter"


class LossAnalysisReport(BaseModel):
    """
    Output of `loss-analysis-agent`. The agent acts as the McKinsey
    team's red team and answers a single framing question — "Why would
    we lose this proposal" or "...to <competitor>" — then proposes
    ranked key improvements tied to each loss reason. Used by Step 9 of
    the Streamlit pipeline alongside `ClientEvaluationReport`.
    """
    framing_question: str
    competitive_context: str       # expected: competitive | non_competitive | unclear
    primary_competitors: StringList = []
    save_or_kill_verdict: str      # expected: competitive_as_is | needs_surgical_edits | needs_redo
    loss_likelihood: str           # expected: low | moderate | high | very_high
    loss_risk_score: int = Field(ge=0, le=100)
    punchline: str
    top_loss_reasons: list[LossReason] = []
    competitor_angles: list[CompetitorAngle] = []
    vulnerable_chapters: StringList = []
    key_improvements: list[KeyImprovement] = []


# ─── STEP 9 — AGGREGATED EVALS ────────────────────────────────────────────────


class EvalsBundle(BaseModel):
    """Step 9 bundle — consistency QC is required; buyer/loss LLM reviews optional."""

    run_id: str = ""
    proposal_source: str = "in_app_deck"  # in_app_deck | uploaded_file
    proposal_upload_name: str = ""
    client_eval: ClientEvaluationReport | None = None
    loss_eval: LossAnalysisReport | None = None
    consistency_eval: dict | None = None  # lop_eval EvalResult.model_dump()
    updated_at: str = ""
