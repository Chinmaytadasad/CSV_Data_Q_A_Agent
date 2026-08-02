# CSV / Data Q&A Agent

Answers plain-English questions about a CSV file by generating and executing real pandas code — never by guessing numbers from the model's own reasoning.

**Scope:** Takes a CSV/Excel file and a plain-English question, and produces a computed numeric/tabular answer along with the exact pandas code that produced it.

---

## Setup

**Requirements:** Python 3.10+

```bash
git clone https://github.com/Chinmaytadasad/CSV_Data_Q_A_Agent.git
cd CSV_Data_Q_A_Agent
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and add your Groq API key:
```
GROQ_API_KEY=your_key_here
```
Get a free key at [console.groq.com](https://console.groq.com).

---

## Run

**CLI (primary interface):**
```bash
python cli.py data/sample_sales.csv
```
```
Loaded dataset:
Columns: date, region, product, units_sold, revenue, quarter
...
Ask a question: which region had the highest revenue in q1
Code used:
result = df[df['quarter'] == 'Q1'].groupby('region')['revenue'].sum().idxmax()
Result:
East
Ask a question: exit
```

**Streamlit UI (optional):**
```bash
streamlit run app.py
```
Upload a CSV, ask questions in the text box. Answers stack in a session-scoped history so previous Q&A stay visible as you ask more questions.

---

## Architecture

```
User question
     ↓
Load CSV + build schema summary (columns, dtypes, sample rows)
     ↓
LLM generates pandas code (Groq, llama-3.3-70b-versatile)
     ↓
Code is sanitized (blocklist: import, exec, eval, __, open, os, sys, subprocess)
     ↓
Code executes in a restricted namespace against a copy of the DataFrame
     ↓
   success → format and display result + code
   failure → feed error back to LLM, retry once → success or clear failure message
```

The answer shown to the user is always read from the executed code's `result` variable — never from the model's text output. See `notes/computation_approach.md` for the full design rationale.

---

## Design Tradeoffs

- **Generate-and-execute over LangChain/PandasAI agents:** a direct, single-purpose pipeline (prompt → code → sandboxed exec) is easier to fully understand, debug, and explain than a general-purpose agent framework, at the cost of less built-in tooling for multi-step reasoning.
- **Single-retry repair loop, not multi-turn:** one repair attempt catches most transient generation errors (bad column reference, syntax slip) without letting failures spiral into long, costly retry chains.
- **String-blocklist sandboxing, not process isolation:** sufficient for this assessment's scope, but not a real security boundary — see limitations below.

Testing surfaced several real, specific limitations — a namespace bug that silently returned `None`, over-aggressive refusal of legitimate boolean questions, phrasing-dependent output structure and refusal behavior, and non-deterministic handling of compound questions. Full details, root causes, and what I'd change with more time are documented in **`notes/computation_approach.md`**.

---

## Known Limitations

- Sandboxing is a string blocklist, not real process/container isolation
- Output structure for multi-part questions depends on how explicitly the question is phrased
- "Not found" entities are sometimes handled by direct computation (e.g. `0.0` for an empty filter) and sometimes by refusal (UNANSWERABLE), depending on question wording
- The answerable/unanswerable classification is folded into the same LLM call as code generation, so it isn't fully deterministic across runs
- No support for joins across multiple files — single dataset only
- No multi-turn conversational memory — each question is answered independently with fresh schema context
- No chart/image generation — table and code output only

---

## What I'd Improve With More Time

- Separate the "answerable vs. not" decision into its own deterministic step, independent of code generation
- Post-process multi-part questions to explicitly request labeled/structured output
- Replace the blocklist sandbox with real subprocess or container isolation
- Standardize not-found-entity handling to always compute rather than refuse based on phrasing
- Add automated regression tests covering the specific edge cases found during manual testing
- Test against real-world (e.g. Kaggle) datasets with messier column names, missing values, and mixed dtypes — current testing was primarily against the bundled synthetic dataset

---

## Project Structure

```
├── cli.py                          # CLI entry point
├── app.py                          # Streamlit UI (optional)
├── src/
│   ├── loader.py                   # CSV loading + schema extraction
│   ├── prompt_builder.py           # Prompt construction for generation/repair
│   ├── llm_client.py                # Groq API wrapper
│   ├── executor.py                 # Sanitization + sandboxed execution
│   └── agent.py                    # Orchestration + retry logic
├── data/
│   └── sample_sales.csv            # Synthetic sample dataset
├── sample_qa/
│   └── qa_transcript.md            # 10 real Q&A runs, including edge cases
├── notes/
│   └── computation_approach.md     # Full anti-hallucination design + limitations
└── scripts/
    └── generate_transcript.py      # Reproducible transcript generator
```