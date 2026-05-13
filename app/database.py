import os
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://vendas:vendas123@postgres:5432/chatbot_vendas")


def get_connection():
    return psycopg2.connect(DATABASE_URL)


@contextmanager
def get_cursor():
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            yield cur
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def execute_query(sql: str, params=None) -> list[dict]:
    with get_cursor() as cur:
        cur.execute(sql, params)
        if cur.description:
            return [dict(row) for row in cur.fetchall()]
        return []


def get_table_data(table: str, limit: int = 50, offset: int = 0) -> dict:
    allowed = {"vendas_resumo", "vendas_detalhada"}
    if table not in allowed:
        raise ValueError(f"Tabela não permitida: {table}")
    with get_cursor() as cur:
        cur.execute(f"SELECT COUNT(*) as total FROM {table}")
        total = cur.fetchone()["total"]
        cur.execute(
            f"SELECT * FROM {table} ORDER BY id_carrinho DESC, data_carrinho DESC LIMIT %s OFFSET %s",
            (limit, offset),
        )
        rows = [dict(r) for r in cur.fetchall()]
    return {"total": total, "limit": limit, "offset": offset, "data": rows}
