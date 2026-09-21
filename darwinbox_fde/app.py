import streamlit as st
import pandas as pd

from src.ingestion import load_upload
from src.profiler import profile_tables, schema_prompt
from src.relationships import detect_relationships
from src.query_engine import make_connection, run_query
from src.validator import validate_readonly
from src.llm import generate_sql, plan_analyses
from src.visualization import auto_chart


st.set_page_config(page_title="DataLens AI", page_icon="📊", layout="wide")
st.title("DataLens AI")
st.caption("Ask analytical questions across CSV and Excel files — locally, with an open-source LLM.")


def format_value(value):
    if pd.isna(value):
        return "N/A"
    if isinstance(value, float):
        return f"{value:,.2f}"
    if isinstance(value, int):
        return f"{value:,}"
    return str(value)


def deterministic_summary(df):
    if df is None or df.empty:
        return "No matching records were found."

    if len(df) == 1 and len(df.columns) == 1:
        return f"**{df.columns[0]}:** {format_value(df.iloc[0, 0])}"

    numeric = list(df.select_dtypes(include="number").columns)
    labels = [c for c in df.columns if c not in numeric]

    if numeric and labels:
        metric = numeric[-1]
        vals = pd.to_numeric(df[metric], errors="coerce")
        valid = vals.dropna()
        if not valid.empty:
            idx = valid.idxmax()
            return (
                f"Highest **{metric}**: **{df.loc[idx, labels[-1]]}** — "
                f"**{format_value(df.loc[idx, metric])}**"
            )

    return f"Returned **{len(df):,} rows**."


with st.sidebar:
    st.header("Data sources")
    uploads = st.file_uploader(
        "Upload CSV / Excel",
        type=["csv", "xlsx", "xls"],
        accept_multiple_files=True,
    )
    model = st.text_input("Ollama model", "qwen2.5-coder:7b")
    st.caption(
        "The local LLM plans the analysis and generates read-only SQL; "
        "DuckDB computes the results."
    )

if not uploads:
    st.info("Upload one or more CSV/Excel files to begin.")
    st.stop()

tables = {}
try:
    for f in uploads:
        loaded = load_upload(f)
        for name, df in loaded.items():
            unique = name
            n = 2
            while unique in tables:
                unique = f"{name}_{n}"
                n += 1
            tables[unique] = df
except Exception as e:
    st.error(f"Could not load a file: {e}")
    st.stop()

profile = profile_tables(tables)
relationships = detect_relationships(tables)
con = make_connection(tables)
schema = schema_prompt(profile)

with st.sidebar:
    for name, p in profile.items():
        st.success(f"{name}: {p['rows']:,} rows × {p['columns']} cols")

    st.subheader("Detected relationships")
    if relationships:
        for r in relationships:
            st.write(
                f"`{r['left']}.{r['column']}` ↔ "
                f"`{r['right']}.{r['column']}` · {r['confidence']}"
            )
    else:
        st.caption("No strong same-column relationships detected.")

with st.expander("Inspect uploaded data & schema"):
    tabs = st.tabs(list(tables))
    for tab, (name, df) in zip(tabs, tables.items()):
        with tab:
            st.dataframe(df.head(100), use_container_width=True)
            st.json(profile[name]["schema"])

question = st.chat_input(
    "Ask a question, e.g. 'Compare average salary by department'"
)

if question:
    with st.chat_message("user"):
        st.write(question)

    with st.chat_message("assistant"):
        try:
            with st.spinner("Planning and querying your data..."):
                analyses = plan_analyses(
                    question, schema, relationships, model
                )

            st.caption(
                f"Planned {len(analyses)} independent "
                f"{'analysis' if len(analyses) == 1 else 'analyses'}."
            )

            for analysis in analyses:
                st.markdown(f"### {analysis['title']}")

                try:
                    with st.spinner(f"Running {analysis['title']}..."):
                        sql = validate_readonly(
                            generate_sql(
                                analysis["question"],
                                schema,
                                relationships,
                                model,
                            )
                        )

                        try:
                            result = run_query(con, sql)
                        except Exception as first_error:
                            sql = validate_readonly(
                                generate_sql(
                                    analysis["question"],
                                    schema,
                                    relationships,
                                    model,
                                    str(first_error),
                                )
                            )
                            result = run_query(con, sql)

                    st.markdown(deterministic_summary(result))

                    if not result.empty:
                        st.dataframe(result, use_container_width=True)
                        fig = auto_chart(result, analysis["question"])
                        if fig is not None:
                            st.plotly_chart(fig, use_container_width=True)

                    with st.expander(f"Analysis details — {analysis['title']}"):
                        st.code(sql, language="sql")
                        st.caption(
                            "Read-only SQL validation is applied before "
                            "execution. One bounded repair attempt is allowed."
                        )

                except Exception as analysis_error:
                    st.error(
                        f"{analysis['title']} failed: {analysis_error}"
                    )

        except Exception as e:
            st.error(f"Analysis failed: {e}")
            st.info(
                "Check that Ollama is running and the configured model is "
                "installed. Inspect the schema if the question references "
                "columns that are not present."
            )
