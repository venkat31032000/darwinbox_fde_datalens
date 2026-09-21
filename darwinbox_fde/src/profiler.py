import pandas as pd


def profile_tables(tables):
    profile = {}
    for name, df in tables.items():
        profile[name] = {
            "rows": len(df),
            "columns": len(df.columns),
            "schema": {str(c): str(df[c].dtype) for c in df.columns},
            "nulls": {str(c): int(df[c].isna().sum()) for c in df.columns},
        }
    return profile


def schema_prompt(profile):
    chunks = []
    for name, p in profile.items():
        cols = ", ".join(f'"{c}" ({t})' for c, t in p["schema"].items())
        chunks.append(f'Table "{name}" [{p["rows"]} rows]: {cols}')
    return "\n".join(chunks)
