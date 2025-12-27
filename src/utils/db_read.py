import os
import pandas as pd
import psycopg2


def read_sql_df(sql: str, params=None) -> pd.DataFrame:
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise RuntimeError("DATABASE_URL is not set")
    conn = psycopg2.connect(db_url)
    try:
        return pd.read_sql_query(sql, conn, params=params)
    finally:
        conn.close()
