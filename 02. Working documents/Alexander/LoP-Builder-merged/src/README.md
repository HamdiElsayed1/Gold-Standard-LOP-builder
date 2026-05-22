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

**Three values in `.env`:**

| Variable | What it does |
|----------|-------------|
| `OPENAI_BASE_URL` | Routes calls through the McKinsey OpenAI gateway instead of OpenAI's public API |
| `OPENAI_API_KEY` | McKinsey-issued JWT token — **expires every 24 hours** |
| `OPENAI_MODEL` | OpenAI model identifier; `gpt-5-mini` is the default |

**Token refresh:** The McKinsey JWT token expires approximately 24 hours after it is issued. When the app returns an authentication error, generate a fresh token from the McKinsey auth portal and replace the `OPENAI_API_KEY` value in `src/.env`.

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
