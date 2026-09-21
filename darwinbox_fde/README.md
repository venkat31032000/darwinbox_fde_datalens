# DataLens AI — Darwinbox FDE Assignment

A small AI-powered data Q&A web app. Upload multiple CSV/XLSX files, ask analytical questions in natural language, and receive a grounded answer, result table, and (when appropriate) chart.

## Why this design
The LLM **does not calculate business metrics itself**. It translates the question into schema-aware, read-only DuckDB SQL. DuckDB performs deterministic computation, and the LLM summarizes only the returned rows. This separation improves correctness and auditability.

### Delta beyond a basic AI wrapper
- Automatic profiling of every uploaded table/sheet.
- Lightweight cross-file relationship detection from shared columns/value overlap.
- Read-only SQL validation with `sqlglot`.
- One bounded self-repair attempt when generated SQL fails.
- Transparent generated SQL for audit/debugging.
- Automatic chart selection for trend/comparison-shaped results.
- Local open-source model via Ollama; raw datasets do not need to be sent to a hosted proprietary model.

## Stack
- Streamlit — web UI
- Pandas/openpyxl — CSV/XLSX ingestion
- DuckDB — analytical query engine
- Ollama + Qwen2.5-Coder (default) — open-source LLM
- sqlglot — SQL validation
- Plotly — charts

## Run locally
Requires Python 3.10+ and Ollama.

1. Install Ollama and start it.
2. Pull the default model:
   `ollama pull qwen2.5-coder:7b`
3. Create a virtual environment and install dependencies:
   `python -m venv .venv`
   `source .venv/bin/activate` (Windows: `.venv\\Scripts\\activate`)
   `pip install -r requirements.txt`
4. Start the app:
   `streamlit run app.py`
5. Open the URL Streamlit prints (normally localhost:8501).

## Demo questions
With the included sample files:
- What is the average salary by department?
- Which department has the highest total salary?
- Compare average salary for employees with rating above 4 by department.
- Show the average performance rating by year.
- Which departments improved their average rating from 2025 to 2026?

## Known limitations / trade-offs
This is intentionally a 4–6 hour prototype. Relationship detection is heuristic and works best when join keys share column names. The LLM may still generate semantically wrong SQL even if it is syntactically valid; production would add a semantic layer, stronger query verification/evals, user-confirmed ambiguous joins, row/column access controls, persistent sessions, observability, and scalable ingestion.

## Suggested demo flow
Upload `employees.csv` + `performance.csv` + `compensation.xlsx`; show detected relationships; ask a single-file aggregation, a cross-file filter/join question, and a trend question; then expand **Analysis details** to show the SQL and explain the reliability boundary.
