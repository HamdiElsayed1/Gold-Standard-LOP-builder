# Sjors — your working folder

**This directory** (`02. Working documents/Sjors/`) holds your **LoP chapter agents**, **workplan** tools, and pursuit copies. Prefer editing here rather than under teammates’ folders (see repo `.cursor/rules/lop-builder-peer-folders.mdc`).

All **chapter agents** and their **prompt stubs** live **only under Sjors** (see table below). Formatting for client-facing text follows **`.cursor/rules/mckinsey-document-standards.mdc`** at the repository root.

---

## LoP chapter agents (Sjors-only)

**Rules:** [`Sjors/.cursor/rules/`](.cursor/rules/) — one `sjors-lop-agent-*.mdc` per chapter (`globs: "**/Sjors/**"`).

**Prompts:** [`Sjors/prompts/`](prompts/) — matching `sjors-lop-agent-*.md` to `@` in chat together with the rule file and sources.

**Gold tone:** [`prompts/background-material-for-lop-agents.md`](prompts/background-material-for-lop-agents.md) — how to use `01. Background material/` without cross-client facts.

**Slide layouts (gold geometry):** [`prompts/slide-structures-from-background-material.md`](prompts/slide-structures-from-background-material.md) — standard blocks per slide type; **workplan** = deliverables per workstream + weekly grid per workstream. Rule: [`Sjors/.cursor/rules/sjors-lop-agent-slide-structures.mdc`](.cursor/rules/sjors-lop-agent-slide-structures.mdc).

| Chapter | Cursor rule ( `@` path ) | Prompt stub |
|--------|---------------------------|---------------|
| Slide structures (all types) | `Sjors/.cursor/rules/sjors-lop-agent-slide-structures.mdc` | [`prompts/sjors-lop-agent-slide-structures.md`](prompts/sjors-lop-agent-slide-structures.md) + [`slide-structures-from-background-material.md`](prompts/slide-structures-from-background-material.md) |
| Context & objectives | `Sjors/.cursor/rules/sjors-lop-agent-context-objectives.mdc` | [`prompts/sjors-lop-agent-context-objectives.md`](prompts/sjors-lop-agent-context-objectives.md) |
| Why McKinsey | `Sjors/.cursor/rules/sjors-lop-agent-why-mckinsey.mdc` | [`prompts/sjors-lop-agent-why-mckinsey.md`](prompts/sjors-lop-agent-why-mckinsey.md) |
| Timeline and team | `Sjors/.cursor/rules/sjors-lop-agent-timeline-team.mdc` | [`prompts/sjors-lop-agent-timeline-team.md`](prompts/sjors-lop-agent-timeline-team.md) |
| Team | `Sjors/.cursor/rules/sjors-lop-agent-team.mdc` | [`prompts/sjors-lop-agent-team.md`](prompts/sjors-lop-agent-team.md) |
| Credentials | `Sjors/.cursor/rules/sjors-lop-agent-credentials.mdc` | [`prompts/sjors-lop-agent-credentials.md`](prompts/sjors-lop-agent-credentials.md) |
| Market trends | `Sjors/.cursor/rules/sjors-lop-agent-market-trends.mdc` | [`prompts/sjors-lop-agent-market-trends.md`](prompts/sjors-lop-agent-market-trends.md) |
| Approach | `Sjors/.cursor/rules/sjors-lop-agent-approach.mdc` | [`prompts/sjors-lop-agent-approach.md`](prompts/sjors-lop-agent-approach.md) |
| Fees | `Sjors/.cursor/rules/sjors-lop-agent-fees.mdc` | [`prompts/sjors-lop-agent-fees.md`](prompts/sjors-lop-agent-fees.md) |
| Appendix / refs / CVs | `Sjors/.cursor/rules/sjors-lop-agent-appendix.mdc` | [`prompts/sjors-lop-agent-appendix.md`](prompts/sjors-lop-agent-appendix.md) |
| Engagement workplan (A–D) | `Sjors/.cursor/rules/sjors-lop-agent-workplan.mdc` | [`prompts/sjors-lop-agent-workplan.md`](prompts/sjors-lop-agent-workplan.md) |

**Suggested order:** Slide-structure pass (gold `@`) → Context → Why McKinsey → Timeline & team → Team → Credentials → Market → Approach → Fees → Workplan → Appendix merge.

---

## What lives here

| Path | Purpose |
|------|--------|
| [`html-decks/workplan-dashboard.html`](html-decks/workplan-dashboard.html) | Unified **LoP + workplan** intake + horizontal McKinsey-style preview + **Copy JSON**. |
| [`prompts/slide-structures-from-background-material.md`](prompts/slide-structures-from-background-material.md) | **Standard slide/table layouts** from gold in `01. Background material/` (incl. workplan deliverables-per-WS + weekly matrix). |
| [`prompts/workplan-from-intake.md`](prompts/workplan-from-intake.md) | Workplan sections **A–D** from JSON (used with workplan agent). |
| [`pursuits/`](pursuits/) | Pursuit-specific trackers / copies. |

---

## Workplan-only flow (dashboard → Cursor)

1. Fill [`html-decks/workplan-dashboard.html`](html-decks/workplan-dashboard.html), **Copy JSON**.
2. **`@`** [`prompts/workplan-from-intake.md`](prompts/workplan-from-intake.md) + [`prompts/sjors-lop-agent-workplan.md`](prompts/sjors-lop-agent-workplan.md) + gold files under **`01. Background material/`**, paste JSON, ask for A–D.
3. Partner-review before client use.

### Context documents

- **Choose files** embeds text-like files under `intake.uploadedContextFiles` in JSON (size limits). PDF/PPT: still **`@`** in Cursor when needed.
- **Extra paths** field adds lines to the same JSON.

---

## Repo rules outside Sjors (read-only for you)

- **`.cursor/rules/sjors-workplan-intake.mdc`** (repo root) still applies on `**/Sjors/**` for engagement workplan structure — keep outputs consistent with that rule when drafting workplans.

## Background material

Use **`01. Background material/`** for **tone and structure** — **`@`** specific files when running any chapter agent. Do not copy facts from another client’s pursuit.
