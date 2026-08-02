# CSV / Data Q&A Agent — Project Outline

## 0. Problem Statement
**Input:** A CSV/Excel file + a plain-English question.
**Output:** A computed, verifiable answer (number/table) + the exact code that produced it.
**Non-goal:** The LLM never states a number from its own reasoning. Every number in the final answer must come from executed code output.

---

## 1. System Architecture

```
┌─────────────┐
│  CLI Input  │  question (string)
└──────┬──────┘
       ↓
┌─────────────────┐
│  Schema Context  │  df.dtypes, df.columns, df.head(3), df.shape
│  (loader.py)     │  — built once at startup, reused every turn
└──────┬───────────┘
       ↓
┌─────────────────────┐
│  Prompt Builder       │  system prompt + schema + question
│  (prompt_builder.py)  │  → strict instruction: "output only pandas code"
└──────┬───────────────┘
       ↓
┌─────────────────┐
│  LLM Client       │  generate_code(prompt) -> raw code string
│  (llm_client.py)  │
└──────┬───────────┘
       ↓
┌─────────────────────┐
│  Code Sanitizer       │  strip markdown fences, block dangerous
│  (executor.py)        │  tokens (import os, eval, exec, __, open)
└──────┬───────────────┘
       ↓
┌─────────────────────┐
│  Sandboxed Executor    │  exec(code, restricted_globals, locals)
│  (executor.py)         │  restricted_globals = {"pd": pd, "df": df}
└──────┬─────────────────┘
       ↓
   success? ──No──→ ┌────────────────────┐
       │            │ Error-Repair Loop    │  feed traceback back to LLM
       │            │ (1 retry max)        │  → new code → re-execute
       │            └──────────┬───────────┘
       │                       ↓
       │◄──────────────────────┘
       ↓ Yes
┌─────────────────────┐
│  Result Formatter     │  DataFrame → to_string()/to_markdown()
│  (agent.py)           │  scalar → direct print
│                        │  Series → formatted table
└──────┬───────────────┘
       ↓
┌─────────────────┐
│  CLI Output       │  answer + "Computed via:" + code shown + table shown
└─────────────────┘
```

---

## 2. Module-by-Module Spec

### `loader.py`
- `load_dataset(path: str) -> pd.DataFrame`
- `build_schema_context(df: pd.DataFrame) -> str`
  - Returns a compact text block: column names, dtypes, non-null counts, 3 sample rows
  - This string is injected into every prompt — it's the model's only knowledge of the data

### `prompt_builder.py`
- `build_code_prompt(schema: str, question: str) -> str`
  - System instruction fixed: "You are a data analyst. You only output raw pandas code operating on a variable `df`. No prose, no explanations, no markdown fences. The last line must assign the answer to a variable named `result`."
- `build_repair_prompt(original_code: str, error: str, question: str) -> str`
  - Feeds the failed code + traceback back, asks for a corrected version

### `llm_client.py`
- `generate_code(prompt: str) -> str`
  - Wraps Groq/Claude call, temperature low (0–0.2) for determinism
  - Strips any accidental markdown fences from response

### `executor.py`
- `sanitize(code: str) -> code | raises SecurityError`
  - Blocklist: `import`, `exec`, `eval`, `__`, `open(`, `os.`, `sys.`, `subprocess`
- `execute(code: str, df: pd.DataFrame) -> result | raises Exception`
  - Runs in restricted namespace: `{"pd": pd, "df": df.copy()}`
  - `.copy()` ensures no question can mutate the source data for the next question

### `agent.py`
- `answer_question(df, schema, question) -> AgentResponse`
  - Orchestrates: prompt → generate → sanitize → execute → (retry once on failure) → format
  - Returns a structured object: `{question, code, result, success, error_note}`

### `cli.py`
- Load dataset once at startup, print schema summary
- Loop: `input("Ask a question: ")` → `agent.answer_question(...)` → print code block + result table
- `exit`/`quit` to break loop

---

## 3. Data Model (`AgentResponse`)
```python
@dataclass
class AgentResponse:
    question: str
    code: str
    result: Any            # DataFrame, Series, or scalar
    success: bool
    attempts: int           # 1 or 2 (if repair loop triggered)
    error_note: str | None  # populated only if failed after retry
```
This structure is what you dump into `sample_qa/qa_transcript.md` — gives you consistent, reviewable output per question.

---

## 4. Safety / Anti-Hallucination Design
This is your strongest tradeoff-notes material — document all three layers:

1. **Structural constraint**: model is instructed to always end in `result = ...`, never to output a final answer in prose. Nothing in the response is trusted except the code.
2. **Execution-only truth**: the "answer" shown to the user is never sourced from the model's response text — it's read from the `result` variable *after* real execution against the actual DataFrame.
3. **Sandboxing**: restricted globals block filesystem/network/process access. Explicitly note in your README this is a "reasonable sandbox for a 24h assessment," not production-grade isolation (no true sandboxing like a subprocess/container) — an honest limitation is a scored point, not a weakness to hide.

---

## 5. Sample Dataset Spec
Synthetic sales dataset, generated once and committed to `data/sample_sales.csv`:

| Column | Type | Notes |
|---|---|---|
| `date` | date | daily or monthly granularity |
| `region` | category | North/South/East/West |
| `product` | category | 4–6 SKUs |
| `units_sold` | int | |
| `revenue` | float | |
| `quarter` | derived or explicit | needed for growth questions |

[Guessing] ~200–500 rows is enough to make groupby/growth questions meaningful without bloating token cost per schema context.

---

## 6. Question Set (8–10, spanning computation types)
1. Total revenue filter (single condition)
2. Groupby + max (highest-revenue region in a quarter)
3. Quarter-over-quarter growth calc (multi-step)
4. Multi-condition filter (region + year + metric)
5. Top-N ranking (top 3 products by units)
6. Variance/consistency across groups (advanced agg)
7. Nonexistent-entity edge case (tests graceful failure, not crash)
8. Ambiguous phrasing (tests the repair loop / reasonable interpretation)
9. Time-series trend (multi-row result, not a scalar)
10. Comparative (two-group side-by-side)

---

## 7. Deliverables Checklist (per submission brief)
- [ ] Public GitHub repo, all commits inside the 24h window
- [ ] `README.md` — install, env vars, run instructions, one worked example
- [ ] Runnable CLI agent
- [ ] `data/sample_sales.csv`
- [ ] `sample_qa/qa_transcript.md` — all 8–10 Q&A pairs with code + results
- [ ] `notes/computation_approach.md` — the anti-hallucination explanation (Section 4 above, expanded)
- [ ] Tradeoffs section in README (generate-and-execute vs. alternatives, known limitations, what you'd add with more time)

---

## 8. README Skeleton
```
# CSV / Data Q&A Agent

## What it does
## Setup
  - clone, venv, pip install -r requirements.txt
  - copy .env.example → .env, add API key
## Run
  - python cli.py
  - example session (paste one real transcript)
## Architecture
  - one-paragraph summary + link to notes/computation_approach.md
## Design tradeoffs
  - why exec-based code-gen over LangChain/PandasAI
  - why single-retry repair loop, not multi-turn
  - sandboxing limitations (explicit, honest)
## Known limitations
  - single CSV only, no joins across files
  - ambiguous questions may need rephrasing
  - no persistent conversation memory across questions
## What I'd improve with more time
  - chart generation
  - multi-file / multi-table support
  - stronger sandbox (subprocess isolation)
```

---

## 9. Explicit Non-Scope (say this out loud to yourself before you start coding)
- No multi-turn conversational memory — each question is independent, uses fresh schema context
- No support for joins across multiple files — single dataset only
- No chart/image generation — table + code output only

Naming these upfront is what stops scope creep at hour 14 when you're tempted to add "just one more feature." The UI below is the one exception to "keep it minimal" — build it last, and never let it become your only tested path.

---

## 10. Minimal UI (Streamlit)

**New file: `app.py`** — thin wrapper, reuses `agent.py`/`loader.py` untouched:

```python
import streamlit as st
from src.loader import load_dataset, build_schema_context
from src.agent import answer_question

st.title("CSV / Data Q&A Agent")

uploaded = st.file_uploader("Upload CSV", type=["csv"])
if uploaded:
    df = load_dataset(uploaded)
    schema = build_schema_context(df)
    st.text("Schema detected:")
    st.code(schema)

    question = st.text_input("Ask a question about this data")
    if question:
        response = answer_question(df, schema, question)
        st.subheader("Answer")
        st.write(response.result)
        st.subheader("Code used")
        st.code(response.code, language="python")
        if not response.success:
            st.error(response.error_note)
```

Rules:
- Build this **after** the CLI is fully working and your 8–10 Q&A transcript is already captured through the CLI (hour 19–20 in the plan, not earlier).
- Do not modify `agent.py`, `executor.py`, or `loader.py` logic to accommodate the UI — any conversion (e.g., uploaded file object → DataFrame) happens inside `app.py` only.
- Add `streamlit` to `requirements.txt`.
- README gets a short "Optional UI" subsection *below* the main CLI run instructions — CLI stays the documented default path reviewers hit first.

Commit for this, appended to the sequence:
```
19. feat: add minimal Streamlit UI wrapper (reuses core agent logic)
```