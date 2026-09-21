import duckdb


def make_connection(tables):
    con = duckdb.connect(database=":memory:")
    for name, df in tables.items():
        con.register(name, df)
    return con


def run_query(con, sql):
    return con.execute(sql).df()
