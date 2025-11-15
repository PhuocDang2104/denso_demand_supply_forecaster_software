import os

import psycopg2
from psycopg2.extras import RealDictCursor

# Simple psycopg2 helper; in future can be replaced by SQLAlchemy.
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "5432"),
    "dbname": os.getenv("DB_NAME", "denso_forecast"),
    "user": os.getenv("DB_USER", "denso"),
    "password": os.getenv("DB_PASSWORD", "admin"),
}


def query_all(sql, params=None):
    """Run SELECT and return all rows as list[dict]."""
    with psycopg2.connect(**DB_CONFIG) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, params or ())
            return cur.fetchall()


def query_one(sql, params=None):
    """Run SELECT and return single row (dict) or None."""
    rows = query_all(sql, params)
    return rows[0] if rows else None


def execute_sql(sql, params=None):
    """Run INSERT/UPDATE/DELETE."""
    with psycopg2.connect(**DB_CONFIG) as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params or ())
        conn.commit()
