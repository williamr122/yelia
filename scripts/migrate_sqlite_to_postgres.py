from __future__ import annotations

import argparse
import os
import sqlite3
import sys
from pathlib import Path
from typing import Iterable

import psycopg2
from psycopg2.extras import execute_values


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SQLITE = ROOT / "yelia.db"
DEFAULT_PG_URL = "postgresql://yelia:<password>@localhost:5432/yelia4ap"

TABLE_ORDER = [
    "usuarios",
    "accounts",
    "conversaciones",
    "messages",
    "progreso",
    "student_profiles",
    "interacciones",
    "structured_quizzes",
    "attachments",
    "metrics_events",
    "metrics_feedback",
    "metrics_perf",
    "metrics_recommendations",
    "metrics_adaptive_feedback",
    "audit_logs",
]


def sqlite_tables(conn: sqlite3.Connection) -> list[str]:
    rows = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;").fetchall()
    return [row[0] for row in rows if not str(row[0]).startswith("sqlite_")]


def sqlite_columns(conn: sqlite3.Connection, table: str) -> list[str]:
    return [row[1] for row in conn.execute(f'PRAGMA table_info("{table}");').fetchall()]


def pg_tables(conn) -> list[str]:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name;
            """
        )
        return [row[0] for row in cur.fetchall()]


def pg_columns(conn, table: str) -> list[str]:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = %s
            ORDER BY ordinal_position;
            """,
            (table,),
        )
        return [row[0] for row in cur.fetchall()]


def quote_ident(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def ordered_tables(source_tables: Iterable[str], target_tables: Iterable[str]) -> list[str]:
    source = set(source_tables)
    target = set(target_tables)
    known = [table for table in TABLE_ORDER if table in source and table in target]
    extra = sorted((source & target) - set(known))
    return known + extra


def ensure_postgres_schema(pg_url: str) -> None:
    old_database_url = os.environ.get("DATABASE_URL")
    old_db_url = os.environ.get("DB_URL")
    old_database_path = os.environ.get("DATABASE_PATH")
    old_db_path = os.environ.get("DB_PATH")

    os.environ["DATABASE_URL"] = pg_url
    os.environ.pop("DB_URL", None)
    os.environ.pop("DATABASE_PATH", None)
    os.environ.pop("DB_PATH", None)

    sys.path.insert(0, str(ROOT))
    try:
        from app import create_app
        from backend.repositories.metrics_repo import _ensure_tables

        create_app()
        _ensure_tables()
    finally:
        if old_database_url is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = old_database_url
        if old_db_url is None:
            os.environ.pop("DB_URL", None)
        else:
            os.environ["DB_URL"] = old_db_url
        if old_database_path is None:
            os.environ.pop("DATABASE_PATH", None)
        else:
            os.environ["DATABASE_PATH"] = old_database_path
        if old_db_path is None:
            os.environ.pop("DB_PATH", None)
        else:
            os.environ["DB_PATH"] = old_db_path

    with psycopg2.connect(pg_url) as conn:
        with conn.cursor() as cur:
            cur.execute("ALTER TABLE metrics_events ADD COLUMN IF NOT EXISTS conversation_id INTEGER;")
            cur.execute("ALTER TABLE metrics_events ADD COLUMN IF NOT EXISTS event_type TEXT;")
            cur.execute("ALTER TABLE metrics_events ADD COLUMN IF NOT EXISTS dominio_status TEXT;")
            cur.execute("ALTER TABLE metrics_events ADD COLUMN IF NOT EXISTS modo_interaccion TEXT;")
            cur.execute("ALTER TABLE metrics_events ADD COLUMN IF NOT EXISTS intencion TEXT;")
            cur.execute("ALTER TABLE metrics_events ADD COLUMN IF NOT EXISTS tema TEXT;")
            cur.execute("ALTER TABLE metrics_events ADD COLUMN IF NOT EXISTS confusion_detectada INTEGER DEFAULT 0;")


def fetch_sqlite_rows(conn: sqlite3.Connection, table: str, columns: list[str]) -> list[tuple]:
    col_sql = ", ".join(quote_ident(col) for col in columns)
    rows = conn.execute(f"SELECT {col_sql} FROM {quote_ident(table)} ORDER BY rowid;").fetchall()
    return [tuple(row[col] for col in columns) for row in rows]


def reset_sequences(pg_conn, tables: list[str]) -> None:
    with pg_conn.cursor() as cur:
        for table in tables:
            cols = pg_columns(pg_conn, table)
            if "id" not in cols:
                continue
            cur.execute("SELECT pg_get_serial_sequence(%s, 'id');", (f"public.{table}",))
            seq = cur.fetchone()[0]
            if not seq:
                continue
            cur.execute(f"SELECT COALESCE(MAX(id), 0) FROM {quote_ident(table)};")
            max_id = int(cur.fetchone()[0] or 0)
            cur.execute("SELECT setval(%s, %s, %s);", (seq, max_id if max_id > 0 else 1, max_id > 0))


def migrate(sqlite_path: Path, pg_url: str, execute: bool) -> None:
    if not sqlite_path.exists():
        raise FileNotFoundError(f"No existe SQLite: {sqlite_path}")

    ensure_postgres_schema(pg_url)

    sqlite_conn = sqlite3.connect(str(sqlite_path))
    sqlite_conn.row_factory = sqlite3.Row
    pg_conn = psycopg2.connect(pg_url)

    try:
        source_tables = sqlite_tables(sqlite_conn)
        target_tables = pg_tables(pg_conn)
        tables = ordered_tables(source_tables, target_tables)

        print("Plan de migracion SQLite -> PostgreSQL")
        print(f"SQLite: {sqlite_path}")
        print(f"PostgreSQL: {pg_url}")
        print(f"Modo: {'EJECUCION' if execute else 'PRUEBA'}")
        print("")

        plan = []
        for table in tables:
            source_cols = sqlite_columns(sqlite_conn, table)
            target_cols = pg_columns(pg_conn, table)
            common_cols = [col for col in source_cols if col in target_cols]
            row_count = sqlite_conn.execute(f"SELECT COUNT(*) FROM {quote_ident(table)};").fetchone()[0]
            plan.append((table, common_cols, row_count))
            ignored = [col for col in source_cols if col not in target_cols]
            ignored_text = f" | ignoradas: {', '.join(ignored)}" if ignored else ""
            print(f"- {table}: {row_count} filas, {len(common_cols)} columnas{ignored_text}")

        if not execute:
            print("\nNo se escribio nada. Ejecuta con --execute para migrar.")
            return

        with pg_conn:
            with pg_conn.cursor() as cur:
                cur.execute("SET session_replication_role = replica;")
                cur.execute(
                    "TRUNCATE TABLE "
                    + ", ".join(quote_ident(table) for table, _cols, _count in reversed(plan))
                    + " RESTART IDENTITY CASCADE;"
                )

                for table, columns, row_count in plan:
                    if row_count == 0 or not columns:
                        print(f"Copiado {table}: 0")
                        continue
                    rows = fetch_sqlite_rows(sqlite_conn, table, columns)
                    insert_sql = (
                        f"INSERT INTO {quote_ident(table)} "
                        f"({', '.join(quote_ident(col) for col in columns)}) VALUES %s"
                    )
                    execute_values(cur, insert_sql, rows, page_size=500)
                    print(f"Copiado {table}: {len(rows)}")

                reset_sequences(pg_conn, [table for table, _cols, _count in plan])
                cur.execute("SET session_replication_role = DEFAULT;")

        print("\nMigracion terminada.")
    finally:
        sqlite_conn.close()
        pg_conn.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Migra datos desde yelia.db SQLite a PostgreSQL.")
    parser.add_argument("--sqlite", default=str(DEFAULT_SQLITE), help="Ruta al archivo SQLite.")
    parser.add_argument("--pg-url", default=os.getenv("DATABASE_URL"), help="URL PostgreSQL. Tambien puede definirse con DATABASE_URL.")
    parser.add_argument("--execute", action="store_true", help="Ejecuta cambios reales. Sin esto solo muestra plan.")
    args = parser.parse_args()

    if not args.pg_url:
        parser.error("Define --pg-url o DATABASE_URL. Ejemplo: postgresql://usuario:clave@localhost:5432/yelia4ap")

    migrate(Path(args.sqlite).resolve(), args.pg_url, args.execute)


if __name__ == "__main__":
    main()
