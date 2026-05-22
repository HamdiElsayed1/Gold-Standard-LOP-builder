# LoP eval suite (Hamdi_Pia)

Eval-only tooling: **internal consistency** and optional **source-of-truth faithfulness** checks on structured proposal text. No HTML generation, no proposal drafting.

## Layout

```text
lop_eval/
  SPEC.md                 # Rule definitions, severities, scoring
  schema/
    eval_result.schema.json
  models.py               # Pydantic: document input + EvalResult
  evaluator.py            # Core orchestrator
  normalize.py            # Numbers / units helpers
  text_extract.py         # Flatten blocks to text spans
  document_io.py          # JSON load helper
  llm_adapter.py          # Stub protocol for optional LLM drift checks
  checkers/               # One module per rule family
  tests/                  # Pytest unit + integration tests
  fixtures/               # JSON golden documents
```

## Run tests

From `02. Working documents/Hamdi_Pia`:

```powershell
python -m pip install -r lop_eval/requirements-dev.txt
$env:PYTHONPATH = (Get-Location).Path
python -m pytest lop_eval/tests -q
```

## Programmatic use

```python
from lop_eval import evaluate_document, load_proposal

doc = load_proposal("lop_eval/fixtures/positive_numeric.json")
result = evaluate_document(doc)
print(result.model_dump_json(indent=2))
```

## Streamlit (Step 9 — Evals)

In `src/app.py`, **Step 9 — Evals** exposes three tabs:

1. Client (owner) review — LLM agent  
2. Loss-risk review — LLM agent  
3. **Consistency QC** — `lop_eval.evaluate_document` (instant; optional LLM judge)

Results aggregate into `ss.evals_bundle` (`EvalsBundle` in `schemas.py`). Sidebar shows one **Evals** milestone with sub-checklist for each read.

**Consistency QC tab** includes expandable **Scoring weights (per check)** — sliders per checker (0–2×) and pass threshold. Results show a deduction breakdown table.

**URL deep link:** append **`?evals=1`** to the Streamlit app URL (e.g. `http://localhost:8501/?evals=1`) to jump to Step 9 after **Render Slides** is complete, or use the sidebar **Jump to Step 9 — Evals** button (updates the URL).

**Run log**: each eval update writes `[EVALS]` lines to `runs/<run_id>_lop_run.log` and appends a `EVALS_JSON_EXPORT` block. Sidebar **Download run log** includes eval summaries when present.

## Stricter thresholds

Pass `EvalConfig(pass_threshold=85, deduct_major=15)` etc. A future release can add per-check weights; see `SPEC.md`.
