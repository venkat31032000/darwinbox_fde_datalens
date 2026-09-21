import sqlglot
from sqlglot import exp

FORBIDDEN = (exp.Insert, exp.Update, exp.Delete, exp.Drop, exp.Create, exp.Alter, exp.Command, exp.Copy)


def validate_readonly(sql: str) -> str:
    cleaned = sql.strip().strip("`")
    if cleaned.lower().startswith("sql"):
        cleaned = cleaned[3:].lstrip()
    trees = sqlglot.parse(cleaned, read="duckdb")
    if len(trees) != 1:
        raise ValueError("Only one SQL statement is allowed.")
    tree = trees[0]
    if any(tree.find(t) is not None for t in FORBIDDEN):
        raise ValueError("Only read-only analytical SQL is allowed.")
    if not isinstance(tree, (exp.Select, exp.Union)) and tree.find(exp.Select) is None:
        raise ValueError("Query must be a SELECT statement.")
    return cleaned
