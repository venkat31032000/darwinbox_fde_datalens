# DataLens AI

**AI-Powered Data Q&A for CSV and Excel Files**

DataLens AI is a lightweight analytical web application that allows users to upload one or more CSV/Excel files and ask questions about their data in natural language.

The application uses a locally hosted open-source LLM to translate analytical intent into SQL, while DuckDB performs the actual computation. Results are presented as concise summaries, tables, and visualizations.

## Features

* Multi-file CSV and Excel upload
* Multi-sheet Excel support
* Natural-language analytical questions
* Cross-file analysis
* Independent analysis of unrelated datasets
* Automatic SQL generation
* Deterministic computation using DuckDB
* Automatic visualizations
* Dataset schema profiling
* Relationship detection
* Read-only SQL validation
* Bounded SQL repair
* Inspectable generated SQL
* Local open-source LLM execution through Ollama

## Architecture

```text
                 ┌─────────────────────┐
                 │     Streamlit UI    │
                 └──────────┬──────────┘
                            │
                     Upload datasets
                            │
                            ▼
                 ┌─────────────────────┐
                 │ Ingestion & Schema  │
                 │      Profiling      │
                 └──────────┬──────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │ Relationship        │
                 │ Detection           │
                 └──────────┬──────────┘
                            │
                     Natural-language
                         question
                            │
                            ▼
                 ┌─────────────────────┐
                 │ Qwen2.5-Coder 7B   │
                 │ Analysis Planning   │
                 └──────────┬──────────┘
                            │
              Split into independent analyses
                     when necessary
                            │
                            ▼
                 ┌─────────────────────┐
                 │    SQL Generation   │
                 └──────────┬──────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │ Read-Only SQL       │
                 │ Validation          │
                 └──────────┬──────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │      DuckDB         │
                 │ Deterministic Query │
                 │     Execution       │
                 └──────────┬──────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │ Summary + Table +   │
                 │ Visualization       │
                 └─────────────────────┘
```

A key design principle is that the **LLM does not calculate the final analytical result**.

The LLM is used for understanding natural-language intent, planning analyses, and generating SQL. Numerical computation is performed deterministically by DuckDB against the uploaded data.

## Tech Stack

| Component           | Technology       |
| ------------------- | ---------------- |
| Frontend / Web App  | Streamlit        |
| LLM                 | Qwen2.5-Coder 7B |
| Local Model Runtime | Ollama           |
| Analytical Database | DuckDB           |
| Data Processing     | Pandas           |
| Visualization       | Plotly           |
| Language            | Python           |

The application is designed to run locally and does not require sending uploaded datasets to a proprietary hosted LLM API.

## Project Structure

```text
darwinbox_fde/
│
├── app.py
├── requirements.txt
├── README.md
│
└── src/
    ├── ingestion.py
    ├── profiler.py
    ├── relationships.py
    ├── llm.py
    ├── validator.py
    ├── query_engine.py
    └── visualization.py
```

### Component Responsibilities

**`app.py`**
Streamlit application and orchestration layer.

**`ingestion.py`**
Loads CSV files and Excel sheets and converts them into queryable tables.

**`profiler.py`**
Extracts schema information used to ground the LLM.

**`relationships.py`**
Detects potential relationships between uploaded datasets.

**`llm.py`**
Handles analysis planning and SQL generation using the locally running Qwen model.

**`validator.py`**
Restricts generated SQL to safe, read-only analytical operations.

**`query_engine.py`**
Registers Pandas DataFrames with DuckDB and executes validated queries.

**`visualization.py`**
Selects and renders appropriate Plotly visualizations from query results.

## Setup

### 1. Prerequisites

Install:

* Python 3.10+
* Git
* Ollama

Verify Python:

```bash
python --version
```

Verify Ollama:

```bash
ollama --version
```

### 2. Clone the Repository

```bash
git clone <YOUR_REPOSITORY_URL>
cd darwinbox_fde
```

### 3. Create a Virtual Environment

Windows:

```bash
python -m venv .venv
.venv\Scripts\activate
```

macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

The main dependencies are:

```text
streamlit
pandas
duckdb
plotly
requests
openpyxl
```

### 5. Install the Local LLM

Pull Qwen2.5-Coder 7B through Ollama:

```bash
ollama pull qwen2.5-coder:7b
```

Verify that the model is available:

```bash
ollama list
```

You should see:

```text
qwen2.5-coder:7b
```

### 6. Start Ollama

Make sure Ollama is running before starting DataLens AI.

The application communicates with the local Ollama server for analysis planning and SQL generation.

### 7. Run DataLens AI

From the project directory:

```bash
python -m streamlit run app.py
```

Streamlit will provide a local URL, typically:

```text
http://localhost:8501
```

Open it in a browser.

## Using the Application

### Step 1 — Upload Data

Upload one or more:

* `.csv`
* `.xlsx`
* `.xls`

files.

Excel sheets are exposed as individual analytical tables.

### Step 2 — Inspect Loaded Data

DataLens profiles the uploaded datasets and displays information such as table names, row counts, columns, and detected relationships.

### Step 3 — Ask Questions

Example:

```text
How many employees are in each department?
```

Or:

```text
Which department has the highest average monthly income?
```

For multiple partitions of the same dataset:

```text
Across both NYC Taxi sheets, show the number of trips for each passenger count.
```

For multiple unrelated datasets:

```text
Using both datasets independently, show employee count by department
from HR and taxi trip count by passenger count across both NYC Taxi sheets.
Do not join the HR and taxi datasets.
```

### Step 4 — Inspect the Result

Depending on the question, DataLens can return:

* concise analytical summary
* result table
* visualization
* generated SQL

The SQL is exposed under **Analysis Details** to make the analytical process inspectable.

## Cross-File Analysis

DataLens supports multiple files within the same analytical session.

When multiple files or sheets represent partitions of the same logical dataset, they can be combined before aggregation.

For example:

```text
NYC Taxi Sheet 1 → 32,000 rows
NYC Taxi Sheet 2 → 32,000 rows
                     ↓
                  UNION ALL
                     ↓
              64,000 taxi trips
```

This allows questions to operate over the complete dataset instead of silently analyzing only one partition.

When uploaded datasets represent unrelated domains, DataLens can split the request into independent analytical tasks rather than forcing an invalid join.

## Delta Beyond Raw LLM Generation

A core goal of the implementation was to avoid treating LLM output as inherently correct.

The LLM is surrounded by deterministic application logic.

### Schema Grounding

The model receives information about the actual uploaded schema, reducing the likelihood of generating references to nonexistent tables or columns.

### Analysis Planning

A question may require more than one analytical operation.

DataLens first creates an analysis plan and can decompose questions involving unrelated datasets into independent analyses.

### Relationship Detection

Potential relationships between datasets are identified before analytical processing.

This provides information that can be used to avoid arbitrary cross-dataset joins.

### Read-Only SQL Validation

Generated SQL is validated before execution.

The application is designed for analytical queries and does not allow destructive database operations such as:

```text
DELETE
DROP
UPDATE
INSERT
ALTER
```

### Deterministic Computation

The LLM does not generate the final numerical answer.

DuckDB executes the SQL against the uploaded data and therefore remains the source of truth for computed values.

### Bounded Repair

If generated SQL fails during execution, DataLens can perform a bounded repair attempt rather than entering an uncontrolled retry loop.

### Inspectability

Generated SQL is visible in the UI so users can inspect how an answer was calculated.

## Example Evaluation Scenarios

### Basic Aggregation

```text
How many employees are in each department?
```

Tests table selection, grouping, counting, and visualization.

### Cross-File Aggregation

```text
Across both NYC Taxi sheets, show trip count by passenger count.
```

Tests whether multiple partitions are correctly incorporated into one analysis.

### Multi-Dataset Planning

```text
Using both datasets independently, show employee count by department
and taxi trip count by passenger count across both taxi sheets.
```

Tests whether the planner can separate unrelated analytical tasks.

### Safety

```text
Delete all employees where Attrition = 'Yes'.
```

Tests whether destructive SQL is rejected.

### Semantic Relationship Test

```text
Join the HR dataset with the NYC Taxi dataset and determine whether
employees with higher monthly income pay higher taxi fares.
```

There is no meaningful key connecting an HR employee to an NYC taxi trip. This scenario is useful for evaluating whether the system can detect and prevent unsupported cross-dataset reasoning.

## Design Decisions

### Why DuckDB?

DuckDB provides fast analytical SQL directly over in-memory tabular data without requiring a separate database server.

It is well suited for a lightweight prototype involving CSV, Excel, and Pandas data.

### Why Qwen2.5-Coder?

Qwen2.5-Coder is an open-source model with strong code and SQL-generation capabilities and can be executed locally through Ollama.

### Why Not RAG?

The task primarily involves structured analytical data.

SQL over DuckDB provides a more deterministic mechanism for aggregation, filtering, comparison, and trend analysis than embedding tabular rows into a vector database.

### Why Not an Agent Framework?

The workflow is intentionally small:

```text
Plan → Generate → Validate → Execute → Present
```

Adding a full agent orchestration framework would introduce additional complexity without materially improving the core requirements of this prototype.

## Current Limitations

* Relationship detection is heuristic rather than a full semantic data model.
* Ambiguous questions may require clearer user intent.
* LLM inference speed depends on local hardware.
* Very large datasets may require additional memory and query optimization.
* Automatic visualization selection currently supports a constrained set of chart patterns.
* Semantic validation of arbitrary cross-domain joins can be strengthened further.

## What I Would Build Next

With additional development time, I would add:

* stronger semantic join validation
* clarification flow for ambiguous analytical questions
* automated evaluation suite
* query/result caching
* richer visualization selection
* better temporal-column detection
* data-quality profiling
* provenance for each generated result
* larger-file ingestion and optimization
* optional deployment configuration

## Key Design Principle

> **Use AI for ambiguity; use deterministic systems for correctness.**

The LLM understands the user's analytical intent and generates a structured query plan. Schema validation, safety controls, DuckDB execution, and visualization provide the deterministic layer around the model.

This keeps the prototype small while making the analytical process more reliable, inspectable, and extensible.
