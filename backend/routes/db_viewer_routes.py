"""
Proyecto: YELIA4AP
Archivo: backend/routes/db_viewer_routes.py
Descripción: Módulo del backend para la lógica asociada a esta carpeta/funcionalidad.

Revisión: 2026-02-10
"""
from __future__ import annotations

"""
Archivo: backend/routes/db_viewer_routes.py
Proyecto: YELIA4AP
Última revisión: 2026-02-10

Módulo de backend en Python.

Convenciones:
- Funciones pequeñas, nombres descriptivos y manejo de errores explícito.
- Evitar prints en producción: usar logging si aplica.
"""


#
# Archivo: backend/routes/db_viewer_routes.py
# Rol: Módulo del backend (Flask) de YELIA4AP.


"""Db Viewer Routes
Archivo del backend del sistema YELIA4AP.

Responsabilidad:
- Implementa la lógica asociada a este módulo.

backend/routes/db_viewer_routes.py

Visor de Base de Datos — YELIA

Objetivo:
- Permitir al admin/docente visualizar tablas, columnas y registros
  de forma segura (solo lectura).
- Útil para depurar y verificar usuarios/roles sin herramientas externas.

Seguridad:
- Requiere rol admin/docente (sesión) o ADMIN_TOKEN por header.
"""


import os
from typing import Any, Dict, List, Optional, Tuple

import structlog
from flask import Blueprint, request, jsonify, session
from backend.core.frontend import frontend_redirect

from backend.db import db_session, get_db_path, is_postgres

logger = structlog.get_logger()

db_bp = Blueprint("db", __name__)


# --- respuestas (contrato API unificado) ---
from backend.core.utils import ok as _ok, err as _err

# Nota de limpieza: algunos imports typing/jsonify podrían no usarse; se mantienen
# para evitar conflictos con ediciones/plantillas futuras.



# --- seguridad (compatibilidad con ADMIN_TOKEN) ---
def _is_admin_token_valid() -> bool:
    token_env = (os.getenv("ADMIN_TOKEN") or "").strip()
    if not token_env:
        return False
    header = (request.headers.get("X-Admin-Token") or "").strip()
    if header and header == token_env:
        return True

    env = (os.getenv("FLASK_ENV") or os.getenv("ENV") or "production").lower()
    if env in ("development", "dev", "local", "test", "testing"):
        token = (request.args.get("token") or "").strip()
        return bool(token) and token == token_env

    return False


def _require_admin_or_teacher() -> Optional[Tuple[Any, int]]:
    # Local/dev: permitir abrir /db sin sesión (para verificación rápida)
    env = (os.getenv("FLASK_ENV") or os.getenv("ENV") or "production").lower().strip()
    host = (request.host or "").lower()
    is_local = any(x in host for x in ("127.0.0.1", "localhost"))
    if env in ("development", "dev", "local", "test", "testing") or is_local:
        return None

    # Compatibilidad: algunos flujos guardan "docente" como rol.
    role = (session.get("admin_role") or session.get("teacher_role") or session.get("role") or "").strip().lower()
    if role in ("admin", "teacher", "docente"):
        return None
    if _is_admin_token_valid():
        return None
    return _err("No autorizado (se requiere rol admin/docente).", 401)




def _is_postgres_conn(conn) -> bool:
    return conn.__class__.__name__ == "PgConnection" or hasattr(conn, "_conn")


def _quote_ident(name: str) -> str:
    """Cita identificadores SQL ya validados para evitar inyección."""
    return '"' + name.replace('"', '""') + '"'


def _list_tables(conn) -> List[Dict[str, Any]]:
    cur = conn.cursor()
    if _is_postgres_conn(conn):
        cur.execute(
            """
            SELECT table_name AS name,
                   CASE WHEN table_type='BASE TABLE' THEN 'table' ELSE lower(table_type) END AS type
            FROM information_schema.tables
            WHERE table_schema='public'
            ORDER BY table_type, table_name;
            """
        )
    else:
        cur.execute("SELECT name, type FROM sqlite_master WHERE type IN ('table','view') ORDER BY type, name;")
    rows = [dict(r) for r in cur.fetchall()]
    return [r for r in rows if r.get("name") != "sqlite_sequence"]


def _table_exists(conn, table: str) -> bool:
    cur = conn.cursor()
    if _is_postgres_conn(conn):
        cur.execute(
            """
            SELECT 1
            FROM information_schema.tables
            WHERE table_schema='public' AND table_name=%s
            LIMIT 1;
            """,
            (table,),
        )
    else:
        cur.execute("SELECT 1 FROM sqlite_master WHERE type IN ('table','view') AND name = ? LIMIT 1;", (table,))
    return cur.fetchone() is not None


def _get_columns(conn, table: str) -> List[Dict[str, Any]]:
    cur = conn.cursor()
    if _is_postgres_conn(conn):
        cur.execute(
            """
            SELECT ordinal_position - 1 AS cid,
                   column_name AS name,
                   data_type AS type,
                   CASE WHEN is_nullable='NO' THEN 1 ELSE 0 END AS notnull,
                   column_default AS dflt,
                   CASE WHEN column_name='id' THEN 1 ELSE 0 END AS pk
            FROM information_schema.columns
            WHERE table_schema='public' AND table_name=%s
            ORDER BY ordinal_position;
            """,
            (table,),
        )
        return [dict(r) for r in cur.fetchall()]
    cur.execute(f"PRAGMA table_info({_quote_ident(table)});")
    return [
        {"cid": r[0], "name": r[1], "type": r[2], "notnull": r[3], "dflt": r[4], "pk": r[5]}
        for r in cur.fetchall()
    ]

# ============================================================
# UI
# ============================================================

@db_bp.route("/db")
def db_viewer_page():
    auth = _require_admin_or_teacher()
    if auth is not None:
        # UX: mantener comportamiento consistente desde /launcher y /demo
        return frontend_redirect("/admin/login")
    return frontend_redirect("/db")


# ============================================================
# API (solo lectura)
# ============================================================

@db_bp.route("/api/db/tables", methods=["GET"])
def api_db_tables():
    auth = _require_admin_or_teacher()
    if auth is not None:
        return auth

    with db_session() as conn:
        rows = _list_tables(conn)

    return _ok({"tables": rows})


@db_bp.route("/api/db/health", methods=["GET"])
def api_db_health():
    auth = _require_admin_or_teacher()
    if auth is not None:
        return auth

    engine = "postgresql" if is_postgres() else "sqlite"
    try:
        with db_session() as conn:
            cur = conn.cursor()
            cur.execute("SELECT 1 AS ok;")
            cur.fetchone()
            tables = _list_tables(conn)
        return _ok({
            "ok": True,
            "engine": engine,
            "db_engine": engine,
            "target": get_db_path(),
            "count": len(tables),
            "tables": [row.get("name") for row in tables if row.get("name")],
        })
    except Exception as exc:
        logger.exception("db_health_failed", engine=engine)
        return _ok({
            "ok": False,
            "engine": engine,
            "db_engine": engine,
            "target": get_db_path(),
            "count": 0,
            "tables": [],
            "error": str(exc),
        })


@db_bp.route("/api/db/schema/<table>", methods=["GET"])
def api_db_schema(table: str):
    auth = _require_admin_or_teacher()
    if auth is not None:
        return auth

    table = (table or "").strip()
    if not table:
        return _err("Tabla inválida.", 400)

    with db_session() as conn:
        if not _table_exists(conn, table):
            return _err("Tabla inválida o no existe.", 400)
        cols = _get_columns(conn, table)

    return _ok({"table": table, "columns": cols})



@db_bp.route("/api/db/table/<table>", methods=["GET"])
def api_db_table_rows(table: str):
    auth = _require_admin_or_teacher()
    if auth is not None:
        return auth

    table = (table or "").strip()
    if not table:
        return _err("Tabla inválida.", 400)

    q = (request.args.get("q") or "").strip()
    try:
        limit = int(request.args.get("limit") or 50)
        offset = int(request.args.get("offset") or 0)
    except ValueError:
        return _err("Paginación inválida.", 400)
    limit = max(1, min(limit, 200))
    offset = max(0, offset)

    with db_session() as conn:
        if not _table_exists(conn, table):
            return _err("Tabla inválida o no existe.", 400)

        cur = conn.cursor()
        try:
            cols = [c["name"] for c in _get_columns(conn, table)]
            ident = _quote_ident(table)
            where_sql = ""
            params: List[Any] = []

            if q and cols:
                like = f"%{q}%"
                if _is_postgres_conn(conn):
                    parts = [f"CAST({_quote_ident(c)} AS TEXT) ILIKE %s" for c in cols]
                else:
                    parts = [f"CAST({_quote_ident(c)} AS TEXT) LIKE ?" for c in cols]
                where_sql = " WHERE " + " OR ".join(parts)
                params = [like] * len(cols)

            cur.execute(f"SELECT COUNT(*) AS n FROM {ident}{where_sql};", params)
            total = int(cur.fetchone()["n"])

            cur.execute(f"SELECT * FROM {ident}{where_sql} LIMIT ? OFFSET ?;", params + [limit, offset])
            rows = [dict(r) for r in cur.fetchall()]
        except Exception:
            logger.exception("db_view_table_failed", table=table)
            return _err("No se pudo leer la tabla.", 400)

    return _ok({
        "table": table,
        "q": q,
        "limit": limit,
        "offset": offset,
        "total": total,
        "total_rows": total,
        "has_more": bool(offset + len(rows) < total),
        "rows": rows,
    })
