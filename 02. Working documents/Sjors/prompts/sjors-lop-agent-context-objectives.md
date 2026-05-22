# Sjors prompt — Context & objectives

**Cursor agent rule (Sjors):** `@02. Working documents/Sjors/.cursor/rules/sjors-lop-agent-context-objectives.mdc`

**Preview alignment:** The workplan dashboard rail slide **Context & objectives** ([`../html-decks/workplan-dashboard.html`](../html-decks/workplan-dashboard.html)) uses the same **50/50 column logic** and **objective buckets** below — keep LoP copy consistent when the user compares deck text to that preview.

## Attach

1. This file + [`background-material-for-lop-agents.md`](./background-material-for-lop-agents.md).
2. Manifest **Y** rows (RFP, partner, CST).
3. **`@01. Background material/`** gold files (tone/structure only).
4. Optional: **dashboard JSON** (`Copy JSON` from the dashboard — use `intake.*` fields literally for context column; do not invent client facts).

## Ask the model

Draft the **Context & objectives** chapter so it reads as **one slide (or one section) split in two equal halves**:

| Half | Source | What to include |
|------|--------|-----------------|
| **Left — Context** | Dashboard intake JSON (when provided) + **Y** manifest | **Client** (`intake.clientName`), **topic** (`intake.topic`), **title / framing** (`intake.gateAProblemDraft` if present), **program notes** (`intake.otherNotes`), **reference materials** (`intake.relatedContextDocuments` lines; `intake.uploadedContextFiles` as file names — use `textContent` only if present and relevant; for binary-only entries say metadata only and point to attached RFP/docs). Supplement with **RFP/manifest** only where **Y**-confirmed. |
| **Right — Objectives** | **Project scope** (`intake.scope`) plus **Y** RFP evaluation / success language | Break objectives into **four logical buckets** (MECE-style), in this order, mapping **scope lines or clauses in order** into buckets 1→4; any **fifth+** distinct scope elements go under **Additional scope elements**. |

### Four objective buckets (fixed labels)

1. **Program outcomes & sponsor intent** — what “good” looks like; sponsor-level intent.
2. **Decisions, design, and recommendation depth** — choices, options, depth of recommendations.
3. **Stakeholders, data, and dependencies** — who, data access, critical dependencies.
4. **Success metrics, timing, and governance** — metrics, cadence, decision forums.

**Scope parsing (when structuring the right column):** Prefer **one line per objective fragment** if `intake.scope` uses multiple lines; otherwise split on **`;`** or, if still a single narrative, on **sentence boundaries**. If scope is thin, keep buckets explicit with **TBD** placeholders rather than inventing client commitments.

### Output discipline

- **Declarative action title** (one or two lines) per `.cursor/rules/mckinsey-document-standards.mdc`.
- **Pyramid:** title states the answer; each column supports it.
- Label **Inference** anywhere the text goes beyond **Y** manifest or pasted intake.
- End with **`Sources used:`** listing manifest rows, dashboard JSON fields used, and any web/RFP citations.
