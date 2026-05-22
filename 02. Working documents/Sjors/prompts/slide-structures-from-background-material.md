# Slide structures (from `01. Background material/`)

Use this when building or reviewing **LoP** and **workplan** slides in Cursor. **`@`** one or more gold proposals under **`01. Background material/`** and **copy layout only** (columns, card count, table shape, title strip) — **not** text, numbers, or client facts from another pursuit.

Formatting of final copy: **`.cursor/rules/mckinsey-document-standards.mdc`** (action titles, sources, tables, etc.).

---

## How to pull structure from gold

1. Open / attach the gold file.
2. Note for the slide type you need: **(a)** section label line, **(b)** action title pattern, **(c)** body layout (table vs cards vs bullets), **(d)** footer / source line placement.
3. Rebuild the **same geometry** with **this** pursuit’s content from the Step 0 manifest and intake JSON.

---

## Workplan (required standard — your repo default)

These two logical blocks map to the **dashboard rail** (`End-deliverables` → `Workstreams` → `Week-by-week`) and to Cursor output **A / B / C** in `workplan-from-intake.md`.

### 1. Deliverables **per workstream**

**Purpose:** Show what each stream **produces**, not a generic backlog.

**Standard layout:**

- **Option A — Card grid:** one card per workstream. Each card contains:
  - **Workstream name**
  - **2–4 deliverable bullets** (nouns + “definition of done” in one clause each)
  - Optional: **Owner TBD** / **Dependency** line
- **Option B — Table:** columns `Workstream` | `Key deliverables` | `Definition of done` | `Notes`

Rows = **one per substantive workstream** (same set as section B). Prep/readout are **inside** streams, not separate “streams”.

### 2. Workplan **per workstream, per week**

**Purpose:** Week columns × workstream rows; first row = **milestones** (soft start, steerco, readout).

**Standard layout:**

- **Table:** first column `Workstream / milestone`, then `Week 1` … `Week N`.
- **Row 1 (milestones):** soft start, steerco/workshop cadence, readout — driven from intake (`softStartWeek1`, `steercoEveryWeeks`, `firstSteercoWeek`, `durationWeeks`).
- **Following rows:** one row per workstream; each cell = **2–4 short bullets** (activities + micro-deliverables).

Mirror **column width** and **header treatment** from gold workplan slides in `01. Background material/` where helpful.

---

## Other LoP slide types (structure only — mirror gold)

| Slide type | Typical gold structure to copy |
|------------|----------------------------------|
| Cover | Title block + subtitle + date line + confidentiality strip placement |
| Context & objectives | 2×2 or 3×1 card grid; or left narrative + right bullets |
| Why McKinsey | 3 proof cards or horizontal proof ladder; each card: claim + one evidence line |
| Timeline & team | Timeline band + resourcing strip; or table: phase / activity / owner |
| Team | Headshots row or role cards: Name / role / focus |
| Credentials | 2×2 case tiles or logo strip + one-line relevance |
| Market | Single exhibit + takeaway title; source block |
| Approach | Swimlane or phased row; workshop markers on timeline |
| Fees | Fee structure table **only** if sourced; else TBD callout box |
| Appendix / refs | Dense list or two-column refs; CV checklist table |

For each type, **`@`** gold and match **block count and reading order**, then fill with **manifest-only** facts.

---

## Output when the user asks “give me structures”

- Emit **markdown or HTML outline** per slide: title + layout sketch (e.g. “3 cards”, “table 5×7”).
- Do **not** invent pursuit content; use **TBD** where manifest is silent.
