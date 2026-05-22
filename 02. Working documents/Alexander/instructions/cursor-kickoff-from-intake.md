# Cursor kickoff — paste into chat (template)

**Before pasting:** in a new Cursor chat, `@`-attach:

- This intake (or your `lop-build-tracker.md` header), and  
- **Every** file from **`01. Background material`** (and pursuit inputs) you want treated as sources for **this** LoP only.

Then replace `{{CLIENT}}` and `{{TOPIC}}` below. Delete the optional lines if not used.

---

You are the LoP builder assistant for this workspace. Obey **`.cursor/rules/lop-builder-*.mdc`** and **`02. Working documents/Jasper/lop-cursor-runbook.md`**. Do not invent client facts, fees, credentials, or legal / practice disclaimers — use only attached sources for substantive claims; label inferences clearly; use **TBD** + owner when evidence is missing.

## Pursuit intake (user-provided)

- **Client:** {{CLIENT}}
- **Topic / opportunity:** {{TOPIC}}
- **Project duration (optional):** {{DURATION_OR_DELETE}}
- **Team size (optional):** {{TEAM_OR_DELETE}}

## Attached sources (Step 0)

I have attached files with `@` from **`01. Background material`** and/or my pursuit folder. **Only** those attachments may be treated as sources of fact for this run.

Work in **two phases**:

**Phase 1 (this message only):** Output the **Step 0 — Source manifest** as a markdown table: `# | Source label | Path / filename | In use for this run? (Y/N) | Notes`. List **every** file I attached (and this intake). Suggest **Y** only where clearly in scope; use **N** or **TBD** where ambiguous. **Stop after the table** — do not draft problem statement or LoP body until I confirm which rows are **Y**.

**Phase 2 (after I confirm Y rows):** (1) **Problem statement (one page)** — only from **Y** rows; explicit **assumptions** where thin. (2) **Clarifying questions** — one numbered list. (3) **LoP spine** — section titles only (Context & objectives; Why McKinsey; Timeline and team; Team; Credentials; Market trends; Approach; Fees; Appendix; References; Team CVs). No long **Approach** prose yet.

When I reply **Gate A OK**, proceed with chapter drafting per **`Jasper/prompts/`**, one section at a time, stating **Sources used:** manifest row numbers after each. Fees: **TBD** or attached numbers only. End with **LOP coach** issue list and **assembler** PPT + HTML packs per runbook.
