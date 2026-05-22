# LoP builder agent — project instructions

This folder uses **Cursor project rules** under `.cursor/rules/` to steer the assistant when building **Letters of Proposal (LoP)**.

## Intent

- **Persona**: Standard structure, expert-level rigor without invented facts, agent as fellow builder.
- **Deliverable**: Strong LoP in **PPT and HTML** in v0.1 (compare quality; habitual delivery may stay PPT-heavy), aligned to RFP and internal gold examples.
- **Operating reality**: Thin beach context or busy partners — optimize for speed, gap visibility, and few review loops.

## Rules (machine-readable)

| File | Focus |
|------|--------|
| `mckinsey-document-standards.mdc` | **Project-wide** McKinsey deck/memo formatting (pyramid, action titles, typography, palette, tables, charts, sources, tone) — `alwaysApply: true` |
| `lop-builder-core.mdc` | Persona, role, risks, scenarios |
| `lop-builder-workflow.mdc` | Chapter spine, cadence, data pipeline |
| `lop-builder-tools-data.mdc` | Tools, sources, evaluation |
| `lop-builder-peer-folders.mdc` | Do not edit other teammates’ folders under `02. Working documents/`; default personal LoP work to `Fleur/` unless explicitly asked |
| `sjors-workplan-intake.mdc` | When working under **`Sjors/`**: generate **engagement** end-deliverables, workstreams, and week grid from dashboard **intake JSON** (no invented client facts) |

## Human workflow artifact

For each pursuit, copy **`02. Working documents/Fleur/pursuits/_template-lop-pursuit/`** to **`02. Working documents/Fleur/pursuits/<LoP-Client-Topic>/`**, then copy **`02. Working documents/Fleur/lop-build-tracker.template.md`** into that folder as **`lop-build-tracker.md`** and work there through intake → synthesis → drafts → review (see **`Fleur/README.md`**). Pia CLI exports default to **`Fleur/exports/`** (see `LOP_EXPORT_DIR` to colocate with a pursuit). An alternate skeleton lives under `Jasper/templates/lop-pursuit-template/` for teams that standardize on that layout—do not mix two templates in one pursuit without intent.

## Cursor LoP workflow (v0.1)

- **Friendly HTML overview (review in browser):** [`02. Working documents/Jasper/lop-workflow-overview.html`](02.%20Working%20documents/Jasper/lop-workflow-overview.html) — what was built and where to click next.  
- **Runbook (start here):** [`02. Working documents/Jasper/lop-cursor-runbook.md`](02.%20Working%20documents/Jasper/lop-cursor-runbook.md) — Step 0 source manifest, HITL gates A/B/C, **PPT + HTML** outputs, beach-friendly sequencing.  
- **Prompt stubs:** [`02. Working documents/Jasper/prompts/README.md`](02.%20Working%20documents/Jasper/prompts/README.md) — copy into chat with `@` sources attached.  
- **Boilerplate / disclaimers:** add approved snippets under team **`Background Material/`** (see `Fleur/README.md`; create the folder beside `Fleur/` if your squad does not have it yet) or the pursuit’s `inputs/` tree; **never invent** legal text.  
- **Rules sync:** if `.cursor/rules/*.mdc` still show old spine labels, apply edits in [`02. Working documents/Jasper/LOP-cursor-rules-sync.md`](02.%20Working%20documents/Jasper/LOP-cursor-rules-sync.md).  
- **Sjors (personal workplan / dashboard):** user guide and file locations — [`02. Working documents/Sjors/README.md`](02.%20Working%20documents/Sjors/README.md).

## Related

`02. Working documents/Jasper/.cursor/rules/workplan-agent.mdc` — when the task is **program / workplan** drafting (not the LoP itself), that rule applies on matching paths.
