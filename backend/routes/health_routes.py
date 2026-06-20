"""
Proyecto: YELIA4AP
Archivo: backend/routes/health_routes.py
Descripción: Módulo del backend para la lógica asociada a esta carpeta/funcionalidad.

Revisión: 2026-02-10
"""
from __future__ import annotations

"""
Archivo: backend/routes/health_routes.py
Proyecto: YELIA4AP
Última revisión: 2026-02-10

Módulo de backend en Python.

Convenciones:
- Funciones pequeñas, nombres descriptivos y manejo de errores explícito.
- Evitar prints en producción: usar logging si aplica.
"""


#
# Archivo: backend/routes/health_routes.py
# Rol: Módulo del backend (Flask) de YELIA4AP.


"""Health Routes
Archivo del backend del sistema YELIA4AP.

Responsabilidad:
- Implementa la lógica asociada a este módulo.

backend/routes/health_routes.py

Health + Status endpoints (YELIA4AP)

- /health: liviano, siempre devuelve JSON con contrato { ok, data }
- /api/status/summary: conteos para el panel
- /status: página HTML

Notas:
- En hosting/proxy, el working dir puede cambiar. Por eso normalizamos DB_PATH a absoluto.
"""
# =====================================
# Imports
# =====================================


import datetime
import os
import sqlite3
from flask import Blueprint, jsonify
from backend.core.frontend import frontend_redirect

# =====================================
# Configuración / Constantes
# =====================================
from ..core.utils import ok, err
from ..db import get_db_path
from ..db.session import db_session, is_postgres

health_bp = Blueprint("health", __name__)
# =====================================
# Funciones / Clases
# =====================================



def _abs_db_path() -> str:
    """Ruta absoluta de SQLite (unificada con el resto del backend)."""
    return get_db_path()


def _utc_now_z() -> str:
    """ISO 8601 en UTC con sufijo Z (timezone-aware)."""
    return (
        datetime.datetime.now(datetime.UTC)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _utc_from_ts_z(ts: float) -> str:
    """timestamp -> ISO 8601 UTC con Z (timezone-aware)."""
    return (
        datetime.datetime.fromtimestamp(ts, tz=datetime.UTC)
        .isoformat()
        .replace("+00:00", "Z")
    )


@health_bp.route("/health", methods=["GET"])
@health_bp.route("/health/", methods=["GET"])
@health_bp.route("/api/health", methods=["GET"])
@health_bp.route("/api/health/", methods=["GET"])
def health():
    """Health check del backend compatible con PostgreSQL 15 y SQLite legacy."""
    try:
        payload = {
            "status": "ok",
            "service": "yelia-backend",
            "version": os.getenv("APP_VERSION", "dev"),
            "time": _utc_now_z(),
        }

        db_path = _abs_db_path()
        payload["db_path"] = db_path
        payload["db_engine"] = "postgresql" if is_postgres() else "sqlite"

        if is_postgres():
            try:
                with db_session(write=False) as conn:
                    cur = conn.cursor()
                    cur.execute("SELECT 1 AS ok;")
                    cur.fetchone()
                payload["db"] = "ok"
            except Exception as e:
                payload["db"] = "error"
                payload["db_error"] = str(e)
        else:
            if os.path.exists(db_path):
                try:
                    payload["db_size_bytes"] = str(os.path.getsize(db_path))
                    payload["db_mtime"] = _utc_from_ts_z(os.path.getmtime(db_path))
                except Exception:
                    pass
                try:
                    con = sqlite3.connect(db_path, timeout=3)
                    con.execute("SELECT 1")
                    con.close()
                    payload["db"] = "ok"
                except Exception as e:
                    payload["db"] = "error"
                    payload["db_error"] = str(e)
            else:
                payload["db"] = "missing"

        return ok(payload)
    except Exception as e:
        return jsonify({
            "ok": False,
            "status": "error",
            "service": "yelia-backend",
            "time": _utc_now_z(),
            "db": "error",
            "error": str(e),
        })


@health_bp.route("/api/status/summary", methods=["GET"])
@health_bp.route("/api/status/summary/", methods=["GET"])
def status_summary():
    """Resumen de conteos del sistema."""
    try:
        # Import local para evitar ciclos
        from backend.db.session import db_session

        summary = {}
        note = "Fuente: /api/status/summary"

        with db_session(write=False) as conn:
            cur = conn.cursor()

            def scalar(q: str):
                cur.execute(q)
                row = cur.fetchone()
                return int(row[0]) if row and row[0] is not None else 0

            # Tablas típicas (ajusta si cambian)
            summary["students_total"] = (
                scalar("SELECT COUNT(*) FROM usuarios WHERE COALESCE(role, 'student') IN ('student','estudiante')")
                if _table_exists(cur, "usuarios")
                else 0
            )
            summary["teachers_total"] = (
                scalar("SELECT COUNT(*) FROM accounts WHERE role = 'teacher'")
                if _table_exists(cur, "accounts")
                else 0
            )
            summary["admins_total"] = (
                scalar("SELECT COUNT(*) FROM accounts WHERE role = 'admin'")
                if _table_exists(cur, "accounts")
                else 0
            )
            summary["accounts_total"] = (
                scalar("SELECT COUNT(*) FROM accounts")
                if _table_exists(cur, "accounts")
                else 0
            )

            # Compatibilidad PostgreSQL/legacy:
            # El sistema real usa la tabla "conversaciones"; algunas versiones
            # antiguas o reportes externos esperaban "conversations".
            if _table_exists(cur, "conversations"):
                summary["conversations_total"] = scalar("SELECT COUNT(*) FROM conversations")
                summary["conversations_table"] = "conversations"
            elif _table_exists(cur, "conversaciones"):
                summary["conversations_total"] = scalar("SELECT COUNT(*) FROM conversaciones")
                summary["conversations_table"] = "conversaciones"
            else:
                summary["conversations_total"] = 0
                summary["conversations_table"] = None
            summary["messages_total"] = (
                scalar("SELECT COUNT(*) FROM messages")
                if _table_exists(cur, "messages")
                else 0
            )
            summary["attachments_total"] = (
                scalar("SELECT COUNT(*) FROM attachments")
                if _table_exists(cur, "attachments")
                else 0
            )
            
            summary["feedback_total"] = (
                scalar("SELECT COUNT(*) FROM metrics_feedback")
                if _table_exists(cur, "metrics_feedback")
                else 0
            )

            # Evento de métricas puede estar en metrics_events
            if _table_exists(cur, "metrics_events"):
                summary["metrics_events_total"] = scalar("SELECT COUNT(*) FROM metrics_events")
            elif _table_exists(cur, "metrics_perf"):
                summary["metrics_events_total"] = scalar("SELECT COUNT(*) FROM metrics_perf")
            else:
                summary["metrics_events_total"] = 0

        return ok({"summary": summary, "note": note})
    except Exception as e:
        return err(f"No se pudo leer resumen: {e}", 500)


@health_bp.route("/api/status/diagnostics", methods=["GET"])
@health_bp.route("/api/status/diagnostics/", methods=["GET"])
def status_diagnostics():
    """Diagnostico operativo seguro para el panel de estado."""
    try:
        runtime = {
            "recent_messages": 0,
            "avg_chat_latency_ms": None,
        }

        with db_session(write=False) as conn:
            cur = conn.cursor()

            if _table_exists(cur, "messages"):
                try:
                    if is_postgres():
                        cur.execute("SELECT COUNT(*) FROM messages WHERE created_at >= NOW() - INTERVAL '1 day'")
                    else:
                        cur.execute("SELECT COUNT(*) FROM messages WHERE datetime(created_at) >= datetime('now', '-1 day')")
                    row = cur.fetchone()
                    runtime["recent_messages"] = int(row[0] or 0) if row else 0
                except Exception:
                    runtime["recent_messages"] = 0

            if _table_exists(cur, "metrics_perf"):
                try:
                    cur.execute("SELECT AVG(latency_ms) FROM metrics_perf WHERE latency_ms IS NOT NULL")
                    row = cur.fetchone()
                    if row and row[0] is not None:
                        runtime["avg_chat_latency_ms"] = round(float(row[0]), 1)
                except Exception:
                    runtime["avg_chat_latency_ms"] = None

        providers = {
            "selected": os.getenv("AI_PROVIDER", os.getenv("LLM_PROVIDER", "router")),
            "groq": bool(os.getenv("GROQ_API_KEY")),
            "gemini": bool(os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")),
            "deepseek": bool(os.getenv("DEEPSEEK_API_KEY")),
            "openai": bool(os.getenv("OPENAI_API_KEY")),
        }

        diagnostics = {
            "environment": os.getenv("FLASK_ENV", os.getenv("APP_ENV", "development")),
            "debug": os.getenv("FLASK_DEBUG", "0") in {"1", "true", "True"},
            "providers": providers,
            "runtime": runtime,
            "rate_limit": {
                "storage_uri": os.getenv("RATELIMIT_STORAGE_URI", "memory"),
            },
            "security": {
                "csrf_required": os.getenv("CSRF_REQUIRED", "0") in {"1", "true", "True"},
            },
            "uploads": {
                "require_auth_uploads": os.getenv("REQUIRE_AUTH_UPLOADS", "0") in {"1", "true", "True"},
            },
        }
        return ok({"diagnostics": diagnostics})
    except Exception as e:
        return err(f"No se pudo leer diagnostico: {e}", 500)


def _table_exists(cur, name: str) -> bool:
    try:
        if is_postgres():
            cur.execute(
                """
                SELECT EXISTS (
                    SELECT 1
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                    AND table_name = %s
                )
                """,
                (name,),
            )
            row = cur.fetchone()
            return bool(row[0]) if row is not None else False
        else:
            cur.execute(
                "SELECT 1 FROM sqlite_master WHERE type IN ('table','view') AND name = ? LIMIT 1;",
                (name,),
            )
            return cur.fetchone() is not None
    except Exception:
        return False

@health_bp.route("/status", methods=["GET"])
def status_page():
    return frontend_redirect("/status")
