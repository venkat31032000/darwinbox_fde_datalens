import json
import re
import requests

DEFAULT_MODEL = "qwen2.5-coder:7b"
BASE_URL = "http://localhost:11434"


def _chat(model, messages, base_url=BASE_URL):
    r = requests.post(
        f"{base_url}/api/chat",
        json={
            "model": model,
            "messages": messages,
            "stream": False,
            "keep_alive": "10m",
            "options": {"num_ctx": 4096, "temperature": 0},
        },
        timeout=120,
    )
    r.raise_for_status()
    return r.json()["message"]["content"].strip()


def _clean_sql(sql: str) -> str:
    if not sql:
        return ""
    sql = re.sub(r"\x1b\[[0-?]*[ -/]*[@-~]", "", sql).strip()
    sql = re.sub(r"^```(?:sql)?\s*", "", sql, flags=re.I)
    sql = re.sub(r"\s*```$", "", sql)
    sql = sql.replace("`", '"').strip()
    if sql.endswith(";"):
        sql = sql[:-1].rstrip()
    return sql


def _extract_json(text):
    text = re.sub(r"\x1b\[[0-?]*[ -/]*[@-~]", "", text).strip()
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.I)
    text = re.sub(r"\s*```$", "", text)
    start = text.find("[")
    end = text.rfind("]")
    if start == -1 or end == -1:
        raise ValueError("The model did not return a JSON analysis plan.")
    return json.loads(text[start:end + 1])


def plan_analyses(question, schema, relationships, model=DEFAULT_MODEL):
    """
    Split a user request into independent analyses when unrelated datasets
    are requested together. Returns a list of {title, question}.
    """
    rel_text = "\n".join(
        f'{r["left"]}.{r["column"]} <-> {r["right"]}.{r["column"]} ({r["confidence"]})'
        for r in relationships
    ) or "No meaningful relationships were pre-detected."

    prompt = f"""You are planning analytics over uploaded tables.

Return ONLY a JSON array. No markdown.

Each array item must contain exactly:
- "title": short human-readable analysis title
- "question": one self-contained analytical request

Rules:
- If the user asks about unrelated datasets, create SEPARATE analyses.
- NEVER invent a relationship between unrelated domains.
- If multiple tables/sheets clearly represent partitions of the SAME dataset,
  keep them in the SAME analysis and explicitly say to combine all relevant
  partitions before aggregating.
- If the user asks about only one logical dataset, return one item.
- Preserve the user's requested metrics and grouping dimensions.
- Do not write SQL here.
- Maximum 4 analyses.

SCHEMA:
{schema}

POSSIBLE RELATIONSHIPS:
{rel_text}

USER QUESTION:
{question}
"""
    raw = _chat(model, [{"role": "user", "content": prompt}])
    plan = _extract_json(raw)

    if not isinstance(plan, list) or not plan:
        raise ValueError("No analyses were produced.")

    cleaned = []
    for item in plan[:4]:
        if not isinstance(item, dict):
            continue
        title = str(item.get("title", "Analysis")).strip()
        subquestion = str(item.get("question", "")).strip()
        if subquestion:
            cleaned.append({"title": title, "question": subquestion})

    if not cleaned:
        raise ValueError("No valid analyses were produced.")
    return cleaned


def generate_sql(question, schema, relationships, model=DEFAULT_MODEL, error=None):
    rel_text = "\n".join(
        f'{r["left"]}.{r["column"]} <-> {r["right"]}.{r["column"]} ({r["confidence"]})'
        for r in relationships
    ) or (
        "No relationships pre-detected. Do NOT join unrelated tables. "
        "Infer joins only when justified by meaningful matching columns."
    )

    prompt = f"""You are a careful analytics engineer.
Generate EXACTLY ONE DuckDB SELECT statement answering the analytical request.

STRICT RULES:
- Return SQL ONLY. No markdown, comments, explanation, or code fences.
- Return EXACTLY ONE read-only SELECT/WITH statement.
- Use DuckDB SQL only.
- NEVER use MySQL backticks.
- Never invent tables or columns. Use ONLY the supplied schema.
- NEVER join unrelated datasets.
- If two or more tables/sheets are partitions of the SAME logical dataset and
  the request asks for the complete/full/across-all dataset, combine those
  partitions with UNION ALL FIRST, then aggregate the combined rows.
- Do not accidentally analyze only one partition when the request says all,
  complete, combined, or across both sheets.
- Use explicit JOIN conditions for genuine relationships.
- Use CTEs/subqueries where helpful.
- Return descriptive aliases appropriate to the analysis, such as
  "Department", "Employee Count", "Passenger Count", and "Trip Count".
- For trends return the time/category dimension plus the numeric metric.
- Perform calculations in SQL.
- End with at most one semicolon.

SCHEMA:
{schema}

POSSIBLE RELATIONSHIPS:
{rel_text}

ANALYTICAL REQUEST:
{question}
"""
    if error:
        prompt += f"""
The previous SQL failed:
{error}

Correct it while following every rule above.
"""
    return _clean_sql(_chat(model, [{"role": "user", "content": prompt}]))
