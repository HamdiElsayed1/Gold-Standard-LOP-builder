# LoP Builder — Phase 1

Local Streamlit demo of the agentic LoP workflow: Intake → Context → Synthesis → Gate A → Mock Answers → Validation → Gate B → Dot-Dash → Gate C.

---

## Prerequisites

- Python 3.10 or newer
- Access to the McKinsey / QuantumBlack OpenAI gateway (JWT-auth)

---

## Setup

### 1. Open a terminal in this folder

```powershell
cd "02. Working documents\Hamdi\src"
```

### 2. Create and activate a virtual environment (recommended)

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```powershell
pip install -r requirements.txt
```

### 4. Configure credentials

The `src/.env` file is pre-configured with the McKinsey / QuantumBlack AI gateway credentials. If you need to reset it, copy the example:

```powershell
Copy-Item .env.example .env
notepad .env
```

**Values in `.env`:**

| Variable | What it does |
|----------|-------------|
| `OPENAI_BASE_URL` | Routes calls through the McKinsey OpenAI gateway instead of OpenAI's public API |
| `OPENAI_API_KEY` | McKinsey-issued JWT token — **expires every 24 hours** |
| `OPENAI_MODEL` | OpenAI "Faster" model identifier; `gpt-5.4-mini-2026-03-17` is the default |
| `OPENAI_MODEL_FULL` | OpenAI "Better" model identifier; pin to a date-stamped `gpt-5.5-…` |
| `ANTHROPIC_BASE_URL` | Routes Claude calls through the McKinsey Anthropic gateway |
| `ANTHROPIC_API_KEY` | Same McKinsey JWT as `OPENAI_API_KEY` — also expires every 24 hours |
| `ANTHROPIC_MODEL` | Claude identifier used when "Claude" is chosen; `claude-opus-4-7` is the default |

**Token refresh:** The McKinsey JWT token expires approximately 24 hours after it is issued. When the app returns an authentication error, generate a fresh token from the McKinsey auth portal and replace **both** `OPENAI_API_KEY` and `ANTHROPIC_API_KEY` in `src/.env` (they are the same JWT — only the gateway base URL differs).

---

## Per-step model selection — three tracks

Above every Run button there is a "Model for this step" expander with three options. The orchestrator routes calls automatically based on the model identifier (anything starting with `claude-` goes to the Anthropic gateway; everything else goes to OpenAI).

| Track | Default identifier | When to pick it |
|-------|-------------------|-----------------|
| **Faster** | `gpt-5.4-mini-2026-03-17` | Pure extraction / mapping / rubric work — intake, validation, voice splitter, slide author. Lowest latency, lowest cost. |
| **Better** | `gpt-5.5-2026-04-23` | Reliable upgrade for any thinking step when Claude is unavailable or rate-limited. Roughly 3x slower than Faster. |
| **Claude** | `claude-opus-4-7` | Premium prose track — recommended for **synthesis**, **dot-dash**, **BA support**, and the **context structuring** step in Deep mode. Strongest at partner-grade prose, declarative action titles, and faithful long-document compression. ~5–7x slower than Faster. |

**Pre-seeded recommendations** (you can override per step):

| Step | Recommendation | Why |
|------|---------------|-----|
| Intake | Faster | Pure extraction — Opus's prose strengths add no value. |
| Context (structuring) | Claude | Preserves named individuals / dated events from the Deep Research report. |
| Synthesis | Claude | First artefact a partner reads — biggest visible quality win. |
| Validation | Faster | Rubric work — Mini already excellent. |
| Dot-Dash | Claude | The flagship slot. Sharpest action titles + confidence-honest dashes. |
| BA Support | Claude | Partner-grade emails — strongest at natural professional prose. |
| Slides | Faster | Runs 9x per deck. Claude here would push render to 12–20 min; reserve for re-running a single drifting slide. |
| Client Evaluator | Claude | Buyer-perspective critique — strongest at owner-voice prose and willing to call generic content generic. |
| Loss-Risk Evaluator | Claude | Red-team critique — strongest at partner-grade red-team prose and richest model knowledge of named competitor firms. |

**Paths that stay on OpenAI regardless of the picker** (no Anthropic equivalent on the gateway):

- The `web_search` tool used by Context Agent in Quick / Deep mode.
- The Deep Research model (`o4-mini-deep-research-2025-06-26` / `o3-deep-research-2025-06-26`).
- Whisper-1 audio transcription for voice memos.

---

## Running the app

```powershell
streamlit run app.py
```

The app opens at **http://localhost:8501** in your browser.

---

## Workflow

Each step unlocks after the previous one completes.

| Step | What happens |
|------|-------------|
| **Upload** | Upload RFP / RFI / best-practice LoP files (PDF, DOCX, TXT). Tag each with its type. |
| **Intake Agent** | Reads all documents, classifies content by LoP chapter, extracts key facts, lists gaps. |
| **Context Agent** | Builds company profile and market context from the model's training knowledge. Labelled as model knowledge — validate before using in the LoP. |
| **Synthesis Agent** | Merges intake + context into a brief, problem statement, win themes, and a partner question list. |
| **Gate A** | Review the synthesis. Edit question text inline. Approve the list or iterate with notes to re-run synthesis. |
| **Mock Answers** | Mock Partner Agent generates placeholder partner answers (deliberately varied in quality). Edit any answer before running validation. |
| **Validation Agent** | Audits each answer for completeness, proposes follow-up questions for the residual gaps, and gives an explicit go/no-go verdict on whether enough input exists to produce a credible dot-dash. |
| **Gate B** | Decide what to do with the validation result. Two paths: (a) **Loop back** — append the proposed follow-up questions to the question list and re-run mock answers + validation; or (b) **Proceed** — send the current state to the Dot-Dash Agent (you can override the verdict to draft a placeholder dot-dash if needed). |
| **Dot-Dash Agent** | Produces the LoP storyline as a chapter-by-chapter dot-dash: per chapter a headline ("dot") and 3–5 supporting points ("dashes"), with confidence and notes. |
| **Gate C** | Review the dot-dash. Edit headlines, supporting points, and notes inline. Approve to lock the storyline, or iterate with notes to re-run the Dot-Dash Agent in revision mode. |
| **BA Support Pack** | After Gate C, produces a BA-facing handoff bundle: concrete to-dos, ready-to-send email drafts for every partner-named contact, and a chapter-by-chapter source-pack checklist. |
| **Render Slides** | Renders the approved dot-dash as one HTML slide per chapter at 1920×1080, in McKinsey format or with a client-style overlay. Exports a single self-contained HTML deck. |
| **Evaluators (Step 9)** | Two independent reads on the same proposal, sharing one source picker (rendered deck or uploaded final HTML / PDF / PPTX). |
| &nbsp;&nbsp;↳ *Client (owner) review* | Plays the role of the company owner / business sponsor and grades the proposal from the buyer's perspective: RFP coverage, owner priorities (explicit + inferred), per-chapter view, reasonableness of timeline / fees / team / approach, top concerns, missing items, and recommended changes. |
| &nbsp;&nbsp;↳ *Loss-risk review* | Independent red-team reviewer asking one question — "Why would we lose this proposal" (or "...to <competitor>") — and proposing ranked key improvements tied to each loss reason. Auto-frames against `competitor_firms` from intake, with an optional partner-supplied competitor override. |

The **Start Over** button in the sidebar resets all state and starts a new session.

---

## Editing agent prompts

Each agent's behaviour is defined entirely in its markdown spec file under `Hamdi/agents/`. Open these files and edit the `## System Prompt` section to change how any agent behaves — no Python changes needed.

| File | Controls |
|------|---------|
| `agents/intake-agent.md` | How documents are classified, what counts as a gap |
| `agents/context-agent.md` | Depth and structure of company/market context |
| `agents/synthesis-agent.md` | Brief format, win theme framing, question list design, revision mode |
| `agents/mock-partner-agent.md` | Style and quality variation of mock partner answers |
| `agents/validation-agent.md` | Completeness criteria, follow-up question generation, dot-dash readiness verdict |
| `agents/dot-dash-agent.md` | Storyline shape, headline/dashes discipline, revision mode |
| `agents/ba-support-agent.md` | To-do, email draft, and source-pack discipline for the BA handoff |
| `agents/slide-*-agent.md` | Per-chapter slide authoring (cover, context, why-mckinsey, timeline-team, team, credentials, market-trends, approach, fees, appendix) |
| `agents/client-evaluator-agent.md` | Owner-perspective evaluation rubric: RFP coverage, owner priorities, chapter view, reasonableness checks, verdict and score |
| `agents/loss-analysis-agent.md` | Red-team rubric: framing question, top loss reasons, per-competitor angles, vulnerable chapters, loss-risk score and likelihood, save-or-kill verdict, and ranked key improvements |

After editing a spec file, no restart is needed — the orchestrator reads the file fresh on each agent call.

---

## Run logs

Every session writes a log file to `Hamdi/runs/`:

```
Hamdi/runs/YYYYMMDD_HHMMSS_lop_run.log
```

The log records **key sentences only** — not full JSON. It captures:

- Client name, industry, geography from the Intake Agent
- Gap list (first 5 items) and problem statement
- Win themes and partner question list (one line per question)
- Mock partner answers (first ~110 chars each)
- Per-question validation verdicts, follow-up needs, residual gaps
- Dot-dash readiness verdict (can proceed / cannot proceed) and blockers/risks
- Follow-up questions proposed for the partner
- Dot-dash storyline summary, slide-by-slide headlines, and open risks
- Gate A / B / C approvals and iteration notes

Open the log in any text editor or tail it during a run:

```powershell
Get-Content -Wait -Tail 20 "..\runs\<timestamp>_lop_run.log"
```

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `OPENAI_API_KEY not set` | Add your key to `src/.env` and restart |
| Authentication error after a day or two | JWT expired — refresh the token in `src/.env` |
| Agent returns JSON parse error | Re-run the step; the orchestrator already attempts multi-strategy JSON extraction |
| `FileNotFoundError: Agent spec not found` | Check that `Hamdi/agents/*.md` files exist; path is resolved relative to `src/` |
| Streamlit shows blank page | Ensure `.venv` is activated and `streamlit` is installed |
| DOCX file not readable | Confirm the file is a real `.docx` (not a renamed `.doc`); legacy `.doc` format is not supported |
| Validation says "cannot proceed to dot-dash" | Use the Gate B loop-back: append the proposed follow-up questions, re-generate mock answers, re-run validation |
| Slide content sits mid-slide / footnote text overlaps the `Source:` line | The bundled `slide.css` and the slide-author / timeline-team prompts now top-anchor the `.content` zone and hard-clip the bottom strip. Existing exports under `Hamdi/exports/<run_id>/index.html` are stamped with the old CSS and slide HTML — re-run **Step 8 (Render Slides)** to pick up the new layout rules. |
