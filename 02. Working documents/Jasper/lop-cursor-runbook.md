# LoP in Cursor — runbook (v0.1)

Use this with the pursuit folder, [`lop-build-tracker.template.md`](../Fleur/lop-build-tracker.template.md) (copy into your pursuit as `lop-build-tracker.md` per [`AGENTS.md`](../../AGENTS.md)), and prompts in [`prompts/`](./prompts/README.md). **Default:** one Cursor chat; use `@` to attach the **exact** files in your **Step 0 source manifest** only.

---

## Not in v0.1 (do not assume)

- Live connectors to Know, MVI, email, or voice pipelines unless **you** have configured them and policy allows.
- Silent invention of **client facts**, **fees**, **credentials**, or **legal / practice disclaimers**.

---

## Outputs (v0.1)

Produce **both**:

1. **PPT-oriented** structure (slide titles, narrative bullets, speaker notes as needed) for your normal McKinsey workflow.  
2. **HTML-oriented** parallel (semantic sections, same spine) so the team can compare quality.

---

## Step 0 — Source manifest (mandatory)

**Before any drafting**, with the user:

1. List **every** input: RFP path, partner email export, CST notes, gold LoP file(s), market clips, **`Background Material/`** boilerplate files, pursuit `inputs/` subfolders, etc.  
2. Record them in the tracker **Step 0 — Source manifest** table.  
3. Confirm **Y** only for sources that apply to **this** pursuit — avoid **cross-LoP pollution** (wrong deck, wrong client).  
4. For each later step, state **which manifest rows** you are using.

If the user adds a source mid-flight: **append** to manifest and confirm.

---

## Intake pack (gather into the pursuit folder or `@` in chat)

| Bucket | Examples |
|--------|----------|
| RFP / tender | Client ask, evaluation criteria |
| Partner | Strategy email, win themes, red lines |
| CST / client | Personas, workshops (only if approved to use) |
| Gold / prior LoP | Internal examples (competitive vs exploratory — label them) |
| Market | Public sources; **cite**; do not conflate with confidential client facts |
| Boilerplate | Approved disclaimers / footers from `Background Material/` or pursuit `inputs/` — **never invent** |

Then run **Intake & synthesis** prompt → one-page **problem statement** + assumptions + numbered questions.

---

## Gate A (HITL)

- Squad / partner (as your firm defines) confirms **problem statement**, **assumptions**, and resolution of **opposing inputs** (or explicit Option A / B + owner).  
- Update tracker **Gate A** row.  
- Do **not** start long **Approach** prose here unless partner-approved scope exists.

---

## Chapter pass (v0.1 policy)

| Spine section | v0.1 stance | Prompt file (in [`prompts/`](./prompts/README.md)) |
|---------------|-------------|-----------------------------------------------------|
| **Context & objectives** | Draft from RFP/partner/CST in manifest; label inferences. | `chapter-context-objectives.md` |
| **Why McKinsey** | **Agent-first**; evidence-bound; `evidence required` where missing. | `chapter-why-mckinsey.md` |
| **Timeline and team** | Neutral staffing labels; no invented FTE; **TBD** if unknown. | `chapter-timeline-team.md` |
| **Team** | **Agent-first** structure + placeholders; **shortlist** names **only** from user-supplied lists/CVs. | `chapter-team-shortlist.md` |
| **Credentials** | **Agent-first**; same evidence rules as Why McKinsey. | `chapter-credentials.md` |
| **Market trends** | Cite sources; no fabricated stats; skeleton if no market inputs. | `chapter-market-trends.md` |
| **Approach** | **Human-first:** outline + questions only until partner-approved scope. | `chapter-approach-outline.md` |
| **Fees** | **TBD** or sourced numbers only — **never** invent rates. | `chapter-fees.md` |
| **Appendix / References / Team CVs** | Merge pass; CV checklist vs named team. | `chapter-appendix-references.md` |

After each chapter, one line: **Sources used:** manifest rows #…

**Merge pass (appendix / references / CV checklist):** run [`chapter-appendix-references.md`](./prompts/chapter-appendix-references.md) **once** the body sections are drafted, **before Gate B**. Consolidate citations and CV checklist; **no new facts**.

---

## Gate B (HITL)

Human pass on **direction**, **missing inputs** (owned or cut), and consistency.

---

## LOP coach pass

Run **LOP coach** prompt on the **full** draft + source index. Output: **issue list by chapter** — **no** unilateral rewrite of facts.

Apply revisions **only** for human-approved fixes.

---

## Assembler handoff (v0.1)

After coach fixes are applied, run [`assembler-ppt-html.md`](./prompts/assembler-ppt-html.md) on the **human-approved** narrative. Deliver:

- **PPT pack:** suggested slide order, titles, bullet copy per slide, appendix list.  
- **HTML pack:** `<main>` section outline with `id`s matching spine, plus same body copy as markdown-friendly blocks.

---

## Gate C (HITL)

Final sign-off on the **packaged** output (PPT + HTML handoff) before client send.

---

## Pilot (optional)

Log **Pilot timing** rows in the tracker after each milestone.

---

## Single chat vs multi-tab

- **Default:** one chat for traceability.  
- **Optional:** parallel chats per **independent** chapter only if you duplicate **Step 0 manifest** into each chat header — otherwise risk input mix-up.
