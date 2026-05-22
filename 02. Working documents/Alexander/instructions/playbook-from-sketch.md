# LoP playbook — from the sketch (MD + Cursor only)

This is the **executable** version of the whiteboard: **[`../Workflow.jpeg`](../Workflow.jpeg)** and **[`../workflow-from-sketch.md`](../workflow-from-sketch.md)**. Follow in order; keep the tracker honest.

**Principle:** instructions and human checkpoints first. Add Python or other automation only when the team agrees it is worth it.

---

## 0. Open the anchors (once per session)

In Cursor, keep these within reach (open or `@`-attach as needed):

| Asset | Path |
|-------|------|
| Cursor runbook | [`../../Jasper/lop-cursor-runbook.md`](../../Jasper/lop-cursor-runbook.md) |
| Chapter prompts | [`../../Jasper/prompts/`](../../Jasper/prompts/) |
| Tracker template | [`../../Fleur/lop-build-tracker.template.md`](../../Fleur/lop-build-tracker.template.md) |
| Rules | [`../../../.cursor/rules/lop-builder-core.mdc`](../../../.cursor/rules/lop-builder-core.mdc) (and sibling `lop-builder-*.mdc`) |

**Optional — browser intake:** open **[`../intake.html`](../intake.html)** to capture **client name**, **topic**, and optionally **project duration** and **team size**; copy the tracker block and the **Cursor kickoff** into a new chat after `@`-attaching files from **`01. Background material`**. Full sequence: **[`flow-intake-to-lop.md`](flow-intake-to-lop.md)**. Metadata only — not a substitute for Step 0 sources or RFP facts.

---

## 1. Our workflow (sketch — do this in order)

From the handwritten line on the sketch:

**workplan → information gathering → identify agents → divide work → work on elements → review / iterate**

| Sketch phrase | What you do (MD / Cursor) |
|---------------|---------------------------|
| **Workplan** | In `lop-build-tracker.md`: roles, due date, pipeline row, context spine table headers. One paragraph: what “done” looks like for this LoP. |
| **Information gathering** | Drop or link sources under the pursuit folder (see [`../next-steps.md`](../next-steps.md)). Voice → notes file; partner/CST/RFP/gold/market each dated or versioned. |
| **Identify agents** | List who must input or approve which spine sections (partner, CST, BD, expert). Put names in the tracker **Roles** table and note gaps. |
| **Divide work** | Assign owners to spine rows or to prompt bundles (e.g. one person owns Approach + Fees). Cursor can draft **only** where manifest rows are **Y**. |
| **Work on elements** | Runbook chapter passes + assembler handoff (PPT pack + HTML pack). After each chapter: one line **Sources used:** manifest row numbers. |
| **Review / iterate** | Feedback loop: capture decisions in `04-review-and-feedback/` (or your skeleton’s equivalent); do not silently drop partner text. |

---

## 2. Pipeline (sketch vertical flow)

Map to tracker **Pipeline status** and runbook gates:

1. **Human — data gathering** — Voice (~7 min or whatever you have), emails, RFP, CST notes, gold LoPs, market clips. **No drafting** until Step 0 is filled.
2. **Squad — synthesizing** — One-page **problem statement** + win themes + explicit assumptions. **Gate A** before long Approach prose.
3. **Draft output** — Contents table + clarifying questions (single Q block per runbook).
4. **Feedback loop** — Partner/squad rounds; resolve opposing inputs or branch Option A/B with an owner.
5. **Output** — PPT-oriented structure **and** HTML-oriented parallel (v0.1 compare), then **Gate C** before client send.

---

## 3. Contents (spine) — checklist

Use the tracker **Context spine** table; statuses **Ready / TBD / Owner**:

1. Context & objectives  
2. Why McKinsey *(sketch: “have we done this 100x?” → evidence only from manifest)*  
3. Timeline and team *(rules checklist — align to RFP if different from sketch list)*  
4. Team  
5. Credentials  
6. Market trends  
7. Approach  
8. Fees  
9. Appendix  
10. References  
11. Team CVs  

**Guidelines (sketch):** per-chapter guidelines, best practices, stakeholders, specific sources — all tied to manifest rows, not memory.

---

## 4. Step 0 — source manifest (mandatory)

Before any `@` drafting:

1. List **every** file or paste for **this** pursuit only.  
2. Mark **Y/N**; only **Y** may be used as sources of fact.  
3. If a new file arrives, **append** and re-confirm.

Stub: [`../source-manifest.template.md`](../source-manifest.template.md). Full table: copy from [`../../Fleur/lop-build-tracker.template.md`](../../Fleur/lop-build-tracker.template.md) into your pursuit as `lop-build-tracker.md`.

---

## 5. Risks (sketch) — how you mitigate in MD

| Risk | Mitigation |
|------|------------|
| Hallucination | Label inferences vs quotes; **TBD** + owner when evidence missing. |
| Wrong prior input | File name + date in manifest; never reuse another pursuit’s folder in the same chat without a fresh manifest. |
| Opposing inputs | Gate A: resolve or branch; document in tracker. |

---

## 6. Tools & data (sketch) — what “counts” in v0.1

**Tools:** LoP coach pass (prompt in Jasper), PPT/Excel/HTML as **deliverable shapes**, web only for **cited** market context, voice → text as **input** only. Know/MVI/email connectors — only if your environment has them and policy allows.

**Data sources:** best-practice LoPs (label competitive vs exploratory vs relationship), tender/RFP, CST context, partner input, market input — each as manifest rows.

---

## 7. Evaluation (sketch)

After major milestones, one line in the tracker **Evaluation log**: win outcome (when known), time saved (estimate), quality notes, time spent. Add **audit** trail if your firm requires it (e.g. who approved Gate C).

---

## 8. Starting a pursuit folder

See **[`../next-steps.md`](../next-steps.md)** — copy one skeleton into [`../pursuits/`](../pursuits/), add `lop-build-tracker.md`, then return to **section 1** of this playbook.

---

## 9. When Python would become “really necessary”

Only if the team explicitly wants **automated** corpus runs, schema-driven exports, or CI-style checks. Until then, this playbook + Cursor + the Jasper prompts are the agent.
