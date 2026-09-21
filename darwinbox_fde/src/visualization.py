import pandas as pd
import plotly.express as px


def auto_chart(df: pd.DataFrame, question: str):
    if df.empty or len(df.columns) < 2:
        return None

    q = question.lower()

    numeric = list(df.select_dtypes(include="number").columns)
    nonnumeric = [c for c in df.columns if c not in numeric]

    if not numeric:
        return None

    # Prefer known analytical category/metric pairs.
    lower_map = {str(c).lower().replace(" ", "").replace("_", ""): c for c in df.columns}

    category_names = [
        "department",
        "passengercount",
        "jobrole",
        "month",
        "year",
        "hour",
        "date",
        "category",
    ]
    metric_names = [
        "tripcount",
        "employeecount",
        "count",
        "averagefare",
        "avgfare",
        "fareamount",
        "monthlyincome",
        "attritionrate",
    ]

    x = next((lower_map[n] for n in category_names if n in lower_map), None)
    y = next(
        (
            lower_map[n]
            for n in metric_names
            if n in lower_map and lower_map[n] != x
        ),
        None,
    )

    # Generic fallback:
    # If all columns are numeric, use the first numeric column as the
    # category/dimension and the LAST numeric column as the metric.
    if x is None:
        x = nonnumeric[0] if nonnumeric else df.columns[0]

    if y is None:
        candidates = [c for c in numeric if c != x]
        y = candidates[-1] if candidates else numeric[0]

    if x == y:
        return None

    if any(
        w in q
        for w in ["trend", "over time", "month", "year", "daily", "weekly", "hour"]
    ):
        return px.line(df, x=x, y=y, markers=True)

    if len(df) <= 50:
        return px.bar(df, x=x, y=y)

    return None
