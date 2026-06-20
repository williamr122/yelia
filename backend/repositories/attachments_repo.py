"""
Proyecto: YELIA4AP
Archivo: backend/repositories/attachments_repo.py
Descripción: Módulo del backend para la lógica asociada a esta carpeta/funcionalidad.

Revisión: 2026-02-10
"""
from __future__ import annotations

"""
Archivo: backend/repositories/attachments_repo.py
Proyecto: YELIA4AP
Última revisión: 2026-02-10

Módulo de backend en Python.

Convenciones:
- Funciones pequeñas, nombres descriptivos y manejo de errores explícito.
- Evitar prints en producción: usar logging si aplica.
"""


#
# Archivo: backend/repositories/attachments_repo.py
# Rol: Módulo del backend (Flask) de YELIA4AP.


"""Attachments Repo
Archivo del backend del sistema YELIA4AP.

Responsabilidad:
- Implementa la lógica asociada a este módulo.

backend/repositories/attachments_repo.py

Backend Flask — YELIA (módulo de servidor)

Propósito:
    Este archivo pertenece al backend (Flask) de YELIA. Contiene lógica de servidor
    y/o utilidades que soportan rutas, servicios, persistencia y orquestación NLP.
    En particular, este módulo maneja la persistencia y recuperación de metadatos
    de archivos adjuntos en la base de datos.

FIX:
    - Compatible con PostgreSQL y SQLite.
    - PostgreSQL usa SERIAL y placeholders %s.
    - SQLite usa AUTOINCREMENT y placeholders ?.
    - Se agregan columnas file_path y filename si no existen.
"""
# =====================================
# Imports
# =====================================

import datetime
import json
from typing import Optional, Dict, Any, List


# =====================================
# Configuración / Constantes
# =====================================
from backend.db.session import db_session


# =====================================
# Helpers internos
# =====================================

def _is_postgres_conn(conn) -> bool:
    """Detecta si la conexión activa es PostgreSQL."""
    module = conn.__class__.__module__.lower()
    name = conn.__class__.__name__.lower()
    return "psycopg" in module or "postgres" in module or "pg" in name


def _ph(conn) -> str:
    """Placeholder SQL según motor."""
    return "%s" if _is_postgres_conn(conn) else "?"


def _row_to_dict(cur, row) -> Optional[Dict[str, Any]]:
    """Convierte una fila sqlite/postgres a dict de forma segura."""
    if not row:
        return None

    if isinstance(row, dict):
        return row

    try:
        return {k: row[k] for k in row.keys()}
    except Exception:
        cols = [d[0] for d in cur.description]
        return dict(zip(cols, row))


# =====================================
# Funciones / Clases
# =====================================

def _ensure_tables() -> None:
    """Crea la tabla de adjuntos si no existe — usa conv_id (consistente con session.py).

    Compatible con:
    - PostgreSQL: SERIAL, ALTER TABLE ADD COLUMN IF NOT EXISTS
    - SQLite: AUTOINCREMENT, PRAGMA table_info
    """
    with db_session(write=True) as conn:
        cur = conn.cursor()

        if _is_postgres_conn(conn):
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS attachments (
                    id SERIAL PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    usuario TEXT,
                    conv_id INTEGER,
                    original_name TEXT NOT NULL,
                    stored_name TEXT NOT NULL,
                    mime TEXT,
                    size_bytes INTEGER,
                    sha256 TEXT,
                    url TEXT,

                    -- Campos opcionales útiles para adjuntos
                    file_path TEXT,
                    filename TEXT,

                    -- Campos opcionales (se llenan cuando se analiza el adjunto)
                    analyzed_at TEXT,
                    extracted_text TEXT,
                    extracted_meta_json TEXT
                );
                """
            )

            # Compatibilidad PostgreSQL:
            # Si la tabla ya existía sin columnas nuevas, las agregamos sin romper.
            for col in [
                "file_path",
                "filename",
                "analyzed_at",
                "extracted_text",
                "extracted_meta_json",
            ]:
                try:
                    cur.execute(f"ALTER TABLE attachments ADD COLUMN IF NOT EXISTS {col} TEXT;")
                except Exception:
                    pass

        else:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS attachments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    usuario TEXT,
                    conv_id INTEGER,
                    original_name TEXT NOT NULL,
                    stored_name TEXT NOT NULL,
                    mime TEXT,
                    size_bytes INTEGER,
                    sha256 TEXT,
                    url TEXT,

                    -- Campos opcionales útiles para adjuntos
                    file_path TEXT,
                    filename TEXT,

                    -- Campos opcionales (se llenan cuando se analiza el adjunto)
                    analyzed_at TEXT,
                    extracted_text TEXT,
                    extracted_meta_json TEXT
                );
                """
            )

            # Compatibilidad SQLite: si la tabla ya existía sin columnas,
            # intentamos agregarlas sin romper el servidor.
            cur.execute("PRAGMA table_info(attachments);")
            cols = {row[1] for row in cur.fetchall()}

            to_add: List[str] = []
            if "file_path" not in cols:
                to_add.append("ALTER TABLE attachments ADD COLUMN file_path TEXT;")
            if "filename" not in cols:
                to_add.append("ALTER TABLE attachments ADD COLUMN filename TEXT;")
            if "analyzed_at" not in cols:
                to_add.append("ALTER TABLE attachments ADD COLUMN analyzed_at TEXT;")
            if "extracted_text" not in cols:
                to_add.append("ALTER TABLE attachments ADD COLUMN extracted_text TEXT;")
            if "extracted_meta_json" not in cols:
                to_add.append("ALTER TABLE attachments ADD COLUMN extracted_meta_json TEXT;")

            for stmt in to_add:
                try:
                    cur.execute(stmt)
                except Exception:
                    # best-effort: no fallar por migración parcial
                    pass


def save_attachment(
    *,
    usuario: Optional[str],
    conv_id: Optional[int],
    original_name: str,
    stored_name: str,
    mime: Optional[str],
    size_bytes: int,
    sha256: Optional[str],
    url: str,
    file_path: Optional[str] = None,   # ✅ nuevo
    filename: Optional[str] = None,    # ✅ nuevo
) -> int:
    """Guarda metadata del archivo y retorna su id."""
    _ensure_tables()

    with db_session(write=True) as conn:
        cur = conn.cursor()

        values = (
            datetime.datetime.now().isoformat(timespec="seconds"),
            usuario,
            conv_id,
            original_name,
            stored_name,
            mime,
            int(size_bytes) if size_bytes is not None else 0,
            sha256,
            url,
            file_path or stored_name,
            filename or original_name,
        )

        if _is_postgres_conn(conn):
            cur.execute(
                """
                INSERT INTO attachments (
                    created_at, usuario, conv_id, original_name, stored_name,
                    mime, size_bytes, sha256, url, file_path, filename
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id;
                """,
                values,
            )
            row = cur.fetchone()
            if isinstance(row, dict):
                return int(row["id"])
            return int(row[0])

        cur.execute(
            """
            INSERT INTO attachments (
                created_at, usuario, conv_id, original_name, stored_name,
                mime, size_bytes, sha256, url, file_path, filename
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            values,
        )

        lastrowid = cur.lastrowid
        return int(lastrowid) if lastrowid is not None else 0


def get_attachment(att_id: int) -> Optional[Dict[str, Any]]:
    """Obtiene un adjunto por id."""
    _ensure_tables()

    with db_session(write=False) as conn:
        cur = conn.cursor()
        ph = _ph(conn)

        cur.execute(
            f"""
            SELECT id, created_at, usuario, conv_id,
                   original_name, stored_name, mime, size_bytes, sha256, url,
                   file_path, filename,
                   analyzed_at, extracted_text, extracted_meta_json
            FROM attachments
            WHERE id = {ph}
            LIMIT 1;
            """,
            (int(att_id),),
        )

        return _row_to_dict(cur, cur.fetchone())


def save_attachment_analysis(
    att_id: int,
    *,
    extracted_text: str,
    extracted_meta: Optional[Dict[str, Any]] = None,
) -> None:
    """Guarda el resultado del análisis (texto extraído y metadata) en DB."""
    _ensure_tables()

    try:
        meta_json = json.dumps(extracted_meta or {}, ensure_ascii=False)
    except Exception:
        meta_json = "{}"

    with db_session(write=True) as conn:
        cur = conn.cursor()
        ph = _ph(conn)

        cur.execute(
            f"""
            UPDATE attachments
            SET analyzed_at = {ph},
                extracted_text = {ph},
                extracted_meta_json = {ph}
            WHERE id = {ph};
            """,
            (
                datetime.datetime.now().isoformat(timespec="seconds"),
                extracted_text or "",
                meta_json,
                int(att_id),
            ),
        )


def get_latest_analyzed_attachment(
    *,
    usuario: Optional[str],
    conv_id: Optional[int],
) -> Optional[Dict[str, Any]]:
    """Obtiene el adjunto más reciente (analizado) para un usuario/conversación."""
    _ensure_tables()

    with db_session(write=False) as conn:
        cur = conn.cursor()
        ph = _ph(conn)

        if conv_id is not None:
            cur.execute(
                f"""
                SELECT id, created_at, usuario, conv_id,
                       original_name, stored_name, mime, size_bytes, sha256, url,
                       file_path, filename,
                       analyzed_at, extracted_text, extracted_meta_json
                FROM attachments
                WHERE conv_id = {ph}
                  AND extracted_text IS NOT NULL
                  AND TRIM(extracted_text) <> ''
                ORDER BY COALESCE(analyzed_at, created_at) DESC, id DESC
                LIMIT 1;
                """,
                (int(conv_id),),
            )
        else:
            if not usuario:
                return None

            cur.execute(
                f"""
                SELECT id, created_at, usuario, conv_id,
                       original_name, stored_name, mime, size_bytes, sha256, url,
                       file_path, filename,
                       analyzed_at, extracted_text, extracted_meta_json
                FROM attachments
                WHERE usuario = {ph}
                  AND extracted_text IS NOT NULL
                  AND TRIM(extracted_text) <> ''
                ORDER BY COALESCE(analyzed_at, created_at) DESC, id DESC
                LIMIT 1;
                """,
                (usuario,),
            )

        return _row_to_dict(cur, cur.fetchone())


def get_attachment_analysis(att_id: int) -> Optional[Dict[str, Any]]:
    """Obtiene el análisis guardado de un adjunto."""
    _ensure_tables()

    with db_session(write=False) as conn:
        cur = conn.cursor()
        ph = _ph(conn)

        cur.execute(
            f"""
            SELECT analyzed_at, extracted_text, extracted_meta_json
            FROM attachments
            WHERE id = {ph}
            LIMIT 1;
            """,
            (int(att_id),),
        )

        row = _row_to_dict(cur, cur.fetchone())
        if not row:
            return None

    meta = {}
    raw = row.get("extracted_meta_json")
    if raw:
        try:
            meta = json.loads(raw)
            if not isinstance(meta, dict):
                meta = {}
        except Exception:
            meta = {}

    return {
        "analyzed_at": row.get("analyzed_at"),
        "extracted_text": row.get("extracted_text") or "",
        "extracted_meta": meta,
    }