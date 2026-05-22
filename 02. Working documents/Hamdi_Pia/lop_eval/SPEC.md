# LoP output consistency evaluation — specification

This suite evaluates **proposal-like documents** for **internal consistency** and optional **faithfulness to a source-of-truth** artifact. It does **not** draft proposals and does **not** emit HTML.

## Objectives

1. Flag **false consistency**: subtle contradictions (numbers, dates, scope, units, labels), not only obvious typos.
2. Prefer **deterministic** signals; reserve **LLM judgment** for ambiguous synonym/entity-alias cases behind an explicit adapter (off by default in CI).
3. Remain **extensible**: new checkers register with the orchestrator without changing core types.

## Document model (input)

Evaluation consumes a **structured document** (see `lop_eval.document`):

- **Metadata**: `document_id`, optional `title`, `metadata` key/values.
- **Sections**: ordered list with stable `id`, optional `title`, and **blocks**:
  - `heading` — level + text
  - `paragraph` — plain text (post-rendered / semantic text, not raw HTML)
  - `list` — items
  - `table` — headers + rows (all cell values as strings)
  - `footnote` / `caption` — short text tied to a section (optional `ref_block_id`)

Paragraphs, tables, captions, and footnotes are **first-class** so checks can align prose vs tabular claims.

## Consistency rules (1–10)

### 1. Numeric consistency

**Rule:** A **numeric claim** (currency amount, count, percent, multiple, bp, etc.) that refers to the **same underlying metric** must match across the document unless a **later block** provides an explicit revision (e.g. “updated to…”, “restated…”).

**Extract:** Normalize numbers with `normalize.py` (currency, scale mln/bln, `%` vs fraction where flagged, thousand separators).

**Pass:** No cluster of “same metric” observations contains values outside a **tolerance** (default: exact for integers/counts; 0.5% relative or 1 ulp for floats; percent points vs percent disambiguated).

**Fail:** Conflicting values for the same cluster; **different as-of years** for the same price/level without restatement; rounding that changes leading digits at stated precision.

**Severities:**

| Severity | Example |
|----------|---------|
| Critical | Same KPI two incompatible values (e.g. EUR 100 mln vs EUR 120 mln) in executive summary vs body. |
| Major | Inconsistent as-of year for stock price; inconsistent FY label. |
| Minor | Format-only difference (“10%” vs “10.0%”) with same meaning. |

### 2. Terminology consistency

**Rule:** **Primary labels** for the same program/initiative should not drift to **unrelated** nouns without definitional bridging.

**Deterministic signals:** Build a **token bucket** of capitalized multi-word phrases and headline noun phrases; flag if two buckets co-occur that match **known drift pairs** (configurable synonym classes) **and** never both tie to a definitional phrase (“also referred to as…”).

**LLM (optional):** When two labels are not in the dictionary, call `SemanticDriftAdapter` (not implemented by default).

**Severities:** Major if drift pair hits; Minor if weak fuzzy match only.

### 3. Entity consistency

**Rule:** Client, company, product, region names should not alias to **different** canonical strings without explicit “doing business as” bridge.

**Deterministic:** Known entity list from config + **similarity** between unmatched capitalized spans (Levenshtein / ratio threshold). Critical if near-duplicate could plausibly be two different real-world entities (tuned conservatively — prefer false positives in draft QC).

### 4. Timeline consistency

**Rule:** **Phase labels** + **month/year** mentions for the same phase must not contradict.

**Deterministic:** Extract `(phase_keyword, date_span)` tuples; graph order; flag if “Phase 2 starts March” vs “Phase 2 begins May”.

**Severities:** Major for direct date clash; Minor for tense oddities (heuristic).

### 5. Scope consistency

**Rule:** Geographic or organizational scope must not **narrow** then **widen** without explanation.

**Deterministic:** Tag lines with scope markers (`EMEA`, `global`, `North America`, `division X`). Flag if one section asserts EMEA-only and another implies global for the **same engagement object**.

### 6. Unit consistency

**Rule:** Same magnitude must not appear as **different units** (EUR vs USD, mln vs bln, % vs 0.xx, bp vs %) without conversion text.

**Deterministic:** Parse unit annotations adjacent to numbers; cluster; conflict if incompatible.

### 7. Formatting / representation consistency

**Rule:** Same semantic ratio should not appear as **10%** in one place and **0.1** in another **without** explicit “share of” labeling (heuristic: if both appear, flag Major).

**Deterministic:** Pair-scan percents vs decimals in same section/table.

### 8. Claim–support consistency

**Rule:** Numbers repeated in **tables** must appear in **narrative** (or caption/footnote) with the same normalized value where the narrative **claims** to describe that table.

**Deterministic (v1):** Within a section, extract numbers from table cells; for each numeric cell, require a matching normalized value in a paragraph/caption/footnote in that section **if** the table has ≤ 20 numeric cells (configurable). Flag mismatches when narrative cites a figure that differs.

**Note:** Full semantic “this sentence describes this row” needs LLM in future; v1 uses **co-occurrence in section**.

### 9. Abbreviation consistency

**Rule:** First expansion should appear before repeated acronym; same acronym should not map to two expansions.

**Deterministic:** Regex `LONG (ACRONYM)` and “ACRONYM (LONG)”; maintain map per acronym; flag duplicate definitions.

### 10. Comparative consistency

**Rule:** Superlatives and comparatives (`largest`, `fastest`, `best`, `higher than`) should not contradict across sections.

**Deterministic (v1):** Extract comparative sentences; if two bear **opposite polarity** on the **same extracted subject** (heuristic keyword overlap), flag Major.

## Pass/fail and scoring

### Issue severity weights (default)

| Severity | Points deducted |
|----------|-----------------|
| Critical | 25 |
| Major    | 10 |
| Minor    | 3 |

- `overall_score = max(0, 100 - sum(deductions))` with **per-type caps** optional (see `EvalConfig`).
- **`passed`:** `overall_score >= threshold` (default **70**) **and** `critical_count == 0`.

### Why configurable

Partners may accept minors on formatting; automated CI might fail on any Major+.

## Source of truth (faithfulness)

Optional `SourceOfTruth` object:

- Flat **facts**: list of `{ key, value_text, unit?, valid_from?, valid_to? }`.
- Evaluators may register **fact keys** (e.g. `client_name`, `revenue_fy2024`) and flag document text that **contradicts** a fact.

If no SoT is provided, faithfulness checks are skipped (consistency-only).

## Outputs

Machine output: JSON matching `schema/eval_result.schema.json` (Pydantic models mirror this).

Human output: optional Markdown summary (not HTML deck).

## Versioning

Bump `SPEC_VERSION` in `lop_eval/__init__.py` when rule definitions change.
