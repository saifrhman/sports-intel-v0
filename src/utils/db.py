import os
import psycopg2


def get_connection():
    """
    Create and return a Postgres connection.
    DATABASE_URL must be set.
    """
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise RuntimeError("DATABASE_URL is not set")

    return psycopg2.connect(db_url)
