"""
Proyecto: YELIA4AP
Archivo: backend/repositories/metrics_repo.py
Descripción: Módulo del backend para la lógica asociada a esta carpeta/funcionalidad.

Revisión: 2026-02-10
"""
from __future__ import annotations

"""
Archivo: backend/repositories/metrics_repo.py
Proyecto: YELIA4AP
Última revisión: 2026-02-10

Módulo de backend en Python.

Convenciones:
- Funciones pequeñas, nombres descriptivos y manejo de errores explícito.
- Evitar prints en producción: usar logging si aplica.
"""


#
# Archivo: backend/repositories/metrics_repo.py
# Rol: Módulo del backend (Flask) de YELIA4AP.


"""Metrics Repo
Archivo del backend del sistema YELIA4AP.

Responsabilidad:
- Implementa la lógica asociada a este módulo.

backend/repositories/metrics_repo.py

Backend Flask — YELIA (módulo de servidor)

Propósito:
    Este archivo pertenece al backend (Flask) de YELIA. Contiene lógica de servidor
    y/o utilidades que soportan rutas, servicios, persistencia y orquestación NLP.
    En particular, este módulo implementa un repositorio para registrar métricas
    de uso, eventos de interacción y feedback del estudiante.
"""


# ============================================================
# PROPÓSITO:
#   Repositorio encargado de registrar métricas de uso,
#   eventos de interacción y feedback del estudiante.
#
# OBJETIVO PRINCIPAL:
#   - Medir cómo se usa el tutor YELIA
#   - Analizar modos de interacción, intención y dominio
#   - Registrar feedback de claridad (👍 / 👎)
#
# IMPORTANTE:
#   Su función es exclusivamente analítica y de mejora continua.
#
# ENFOQUE PROFESIONAL:
#   Implementa una capa de observabilidad mínima pero útil,
#   alineada con proyectos académicos y sistemas reales.
# ============================================================


import datetime
import json
from typing import Optional, Dict, Any, List

from backend.db.session import db_session


def _ensure_tables() -> None:
    """
    Garantiza la existencia de las tablas de métricas.

    Características:
    - Crea las tablas solo si no existen
    - NO modifica tablas existentes del sistema
    - Permite agregar analítica sin romper el esquema actual

    Esta estrategia es ideal para prototipos y migraciones graduales.
    """
    with db_session(write=True) as conn:
        cur = conn.cursor()

        # Tabla de eventos de interacción
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS metrics_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                usuario TEXT,
                conversation_id INTEGER,
                event_type TEXT NOT NULL,
                dominio_status TEXT,
                modo_interaccion TEXT,
                intencion TEXT,
                tema TEXT,
                confusion_detectada INTEGER DEFAULT 0
            );
            """
        )

        # Tabla de feedback explícito del estudiante
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS metrics_feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                usuario TEXT NOT NULL,
                conversation_id INTEGER,
                rating TEXT NOT NULL,        -- 'up' | 'down'
                note TEXT
            );
            """
        )

        # Tabla de performance por endpoint (latencia)
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS metrics_perf (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                usuario TEXT,
                conversation_id INTEGER,
                endpoint TEXT NOT NULL,
                latency_ms REAL
            );
            """
        )

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS metrics_recommendations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                usuario TEXT,
                conversation_id INTEGER,
                recommendation_type TEXT NOT NULL,
                title TEXT,
                topic TEXT,
                level_used TEXT,
                emotion_used TEXT,
                priority TEXT,
                history_based INTEGER DEFAULT 0,
                history_reason TEXT,
                source TEXT,
                url TEXT,
                reason TEXT
            );
            """
        )

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS metrics_adaptive_feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                usuario TEXT,
                conversation_id INTEGER,
                kind TEXT,
                status TEXT,
                topic TEXT,
                level_used TEXT,
                emotion_used TEXT,
                next_action TEXT,
                score_delta INTEGER DEFAULT 0,
                recommendation TEXT
            );
            """
        )

        def _ensure_column(table: str, column: str, ddl: str) -> None:
            try:
                cur.execute(f"PRAGMA table_info({table});")
                cols = [str(r[1]) for r in cur.fetchall()]
                if column not in cols:
                    cur.execute(f"ALTER TABLE {table} ADD COLUMN {column} {ddl};")
            except Exception:
                return

        # Migracion suave para bases creadas con versiones anteriores.
        for col, ddl in {
            "created_at": "TEXT",
            "usuario": "TEXT",
            "conversation_id": "INTEGER",
            "event_type": "TEXT",
            "dominio_status": "TEXT",
            "modo_interaccion": "TEXT",
            "intencion": "TEXT",
            "tema": "TEXT",
            "confusion_detectada": "INTEGER DEFAULT 0",
        }.items():
            _ensure_column("metrics_events", col, ddl)

        for col, ddl in {
            "created_at": "TEXT",
            "usuario": "TEXT",
            "conversation_id": "INTEGER",
            "endpoint": "TEXT",
            "latency_ms": "REAL",
        }.items():
            _ensure_column("metrics_perf", col, ddl)


def log_event(
    *,
    usuario: str = "",
    conversation_id: Optional[int] = None,
    event_type: str = "generic",
    dominio_status: Optional[str] = None,
    modo_interaccion: Optional[str] = None,
    intencion: Optional[str] = None,
    tema: Optional[str] = None,
    confusion_detectada: bool = False,
    **kwargs: Any,
) -> None:
    """Registra un evento funcional del chat.

    Acepta aliases adicionales para no romper llamadas futuras.
    """
    _ensure_tables()

    if not usuario:
        usuario = str(kwargs.get("user") or kwargs.get("username") or "")
    if conversation_id is None:
        conversation_id = kwargs.get("conv_id")
    if not event_type:
        event_type = str(kwargs.get("tipo") or "generic")

    with db_session(write=True) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO metrics_events
            (created_at, usuario, conversation_id, event_type,
             dominio_status, modo_interaccion, intencion, tema, confusion_detectada)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            (
                datetime.datetime.now().isoformat(timespec="seconds"),
                usuario,
                conversation_id,
                event_type,
                dominio_status,
                modo_interaccion,
                intencion,
                tema,
                1 if confusion_detectada else 0,
            ),
        )


def save_feedback(
    *,
    usuario: str,
    conversation_id: Optional[int],
    rating: str,
    note: Optional[str] = None,
) -> None:
    """save_feedback.

    Args:
        usuario (str): Identificador del usuario (ej. username o id).
        conversation_id (Optional[int]): ID de la conversación asociada (si aplica).
        rating (str): Valoración: 'up' o 'down'.
        note (Optional[str]): Nota opcional breve del usuario.

    Returns:
        None

    Raises:
        ValueError: Si rating no es 'up' o 'down'.
    """
    if rating not in ("up", "down"):
        raise ValueError("rating inválido (usa 'up' o 'down')")

    _ensure_tables()

    with db_session(write=True) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO metrics_feedback
            (created_at, usuario, conversation_id, rating, note)
            VALUES (?, ?, ?, ?, ?);
            """,
            (
                datetime.datetime.now().isoformat(timespec="seconds"),
                usuario,
                conversation_id,
                rating,
                (note or "").strip()[:280] if note else None,
            ),
        )


def get_last_feedback(usuario: str) -> Optional[Dict[str, Any]]:
    """Recupera el último feedback registrado por un usuario.

    Args:
        usuario: Parámetro de entrada.

    Returns:
        Valor retornado por la función.
    """
    _ensure_tables()

    with db_session(write=False) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, created_at, conversation_id, rating, note
            FROM metrics_feedback
            WHERE usuario = ?
            ORDER BY id DESC
            LIMIT 1;
            """,
            (usuario,),
        )
        row = cur.fetchone()

        # ✅ FIX: sqlite3.Row -> dict seguro
        if not row:
            return None
        return {k: row[k] for k in row.keys()}


def get_latest_clarity_for_user(usuario: str) -> Optional[int]:
    """get_latest_clarity_for_user.

    Args:
        usuario (str): Identificador del usuario.

    Returns:
        Optional[int]: 0 si el último rating fue 'down', 1 si fue 'up', o None si no hay feedback.
    """
    fb = get_last_feedback(usuario)
    if not fb:
        return None
    return 0 if fb.get("rating") == "down" else 1


def log_recommendations(
    *,
    usuario: str,
    conversation_id: Optional[int],
    recommendations: List[Dict[str, Any]],
) -> None:
    """Registra recomendaciones generadas para evidencia de tesis."""
    if not recommendations:
        return
    try:
        _ensure_tables()
        now = datetime.datetime.now().isoformat(timespec="seconds")
        with db_session(write=True) as conn:
            cur = conn.cursor()
            for rec in recommendations[:12]:
                cur.execute(
                    """
                    INSERT INTO metrics_recommendations
                    (created_at, usuario, conversation_id, recommendation_type, title,
                     topic, level_used, emotion_used, priority, history_based,
                     history_reason, source, url, reason)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                    """,
                    (
                        now,
                        usuario,
                        conversation_id,
                        rec.get("type"),
                        rec.get("title"),
                        rec.get("topic_used"),
                        rec.get("level_used"),
                        rec.get("emotion_used"),
                        rec.get("priority"),
                        1 if rec.get("history_based") else 0,
                        rec.get("history_reason"),
                        rec.get("source"),
                        rec.get("url"),
                        rec.get("reason"),
                    ),
                )
    except Exception:
        return


def log_adaptive_feedback(
    *,
    usuario: str,
    conversation_id: Optional[int],
    feedback: Optional[Dict[str, Any]],
) -> None:
    """Registra retroalimentacion personalizada detectada en el chat."""
    if not isinstance(feedback, dict) or not feedback.get("detected"):
        return
    try:
        _ensure_tables()
        with db_session(write=True) as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO metrics_adaptive_feedback
                (created_at, usuario, conversation_id, kind, status, topic,
                 level_used, emotion_used, next_action, score_delta, recommendation)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    datetime.datetime.now().isoformat(timespec="seconds"),
                    usuario,
                    conversation_id,
                    feedback.get("kind"),
                    feedback.get("status"),
                    feedback.get("topic"),
                    feedback.get("level"),
                    feedback.get("emotion"),
                    feedback.get("next_action"),
                    int(feedback.get("score_delta") or 0),
                    feedback.get("recommendation"),
                ),
            )
    except Exception:
        return


def get_adaptive_metrics_summary() -> Dict[str, Any]:
    """Devuelve resumen de recomendaciones, historial y feedback adaptativo."""
    _ensure_tables()
    with db_session(write=False) as conn:
        cur = conn.cursor()

        cur.execute("SELECT COUNT(*) AS total FROM metrics_recommendations;")
        total_recommendations = int(cur.fetchone()["total"] or 0)

        cur.execute("SELECT COUNT(*) AS total FROM metrics_recommendations WHERE history_based = 1;")
        history_based_total = int(cur.fetchone()["total"] or 0)

        cur.execute("SELECT COUNT(*) AS total FROM metrics_adaptive_feedback;")
        total_adaptive_feedback = int(cur.fetchone()["total"] or 0)

        cur.execute(
            """
            SELECT recommendation_type AS key, COUNT(*) AS total
            FROM metrics_recommendations
            GROUP BY recommendation_type
            ORDER BY total DESC
            LIMIT 10;
            """
        )
        by_type = [{"type": r["key"], "total": int(r["total"] or 0)} for r in cur.fetchall()]

        cur.execute(
            """
            SELECT COALESCE(NULLIF(topic, ''), 'Sin tema') AS key, COUNT(*) AS total
            FROM metrics_recommendations
            GROUP BY key
            ORDER BY total DESC
            LIMIT 10;
            """
        )
        by_topic = [{"topic": r["key"], "total": int(r["total"] or 0)} for r in cur.fetchall()]

        cur.execute(
            """
            SELECT COALESCE(NULLIF(emotion_used, ''), 'neutral') AS key, COUNT(*) AS total
            FROM metrics_recommendations
            GROUP BY key
            ORDER BY total DESC
            LIMIT 10;
            """
        )
        by_emotion = [{"emotion": r["key"], "total": int(r["total"] or 0)} for r in cur.fetchall()]

        cur.execute(
            """
            SELECT COALESCE(NULLIF(level_used, ''), 'intermedio') AS key, COUNT(*) AS total
            FROM metrics_recommendations
            GROUP BY key
            ORDER BY total DESC
            LIMIT 10;
            """
        )
        by_level = [{"level": r["key"], "total": int(r["total"] or 0)} for r in cur.fetchall()]

        cur.execute(
            """
            SELECT COALESCE(NULLIF(history_reason, ''), 'no_history') AS key, COUNT(*) AS total
            FROM metrics_recommendations
            WHERE history_based = 1
            GROUP BY key
            ORDER BY total DESC
            LIMIT 10;
            """
        )
        by_history_reason = [{"reason": r["key"], "total": int(r["total"] or 0)} for r in cur.fetchall()]

        cur.execute(
            """
            SELECT COALESCE(NULLIF(kind, ''), 'unknown') AS key, COUNT(*) AS total
            FROM metrics_adaptive_feedback
            GROUP BY key
            ORDER BY total DESC
            LIMIT 10;
            """
        )
        feedback_by_kind = [{"kind": r["key"], "total": int(r["total"] or 0)} for r in cur.fetchall()]

        cur.execute(
            """
            SELECT id, created_at, usuario, conversation_id, recommendation_type,
                   title, topic, level_used, emotion_used, history_based,
                   history_reason, source, url
            FROM metrics_recommendations
            ORDER BY id DESC
            LIMIT 20;
            """
        )
        recent_recommendations = [dict(r) for r in cur.fetchall()]

    return {
        "total_recommendations": total_recommendations,
        "history_based_total": history_based_total,
        "total_adaptive_feedback": total_adaptive_feedback,
        "by_type": by_type,
        "by_topic": by_topic,
        "by_emotion": by_emotion,
        "by_level": by_level,
        "by_history_reason": by_history_reason,
        "feedback_by_kind": feedback_by_kind,
        "recent_recommendations": recent_recommendations,
    }


def log_perf(
    *,
    usuario: Optional[str] = None,
    conversation_id: Optional[int] = None,
    endpoint: str = "",
    latency_ms: float = 0.0,
    **kwargs: Any,
) -> None:
    """Guarda métricas de rendimiento por endpoint.

    Conserva la firma actual y acepta aliases como conv_id.
    """
    if conversation_id is None:
        conversation_id = kwargs.get("conv_id")
    if not usuario:
        usuario = kwargs.get("user")
    if not endpoint:
        endpoint = str(kwargs.get("route") or kwargs.get("operation") or "")

    if not endpoint:
        return

    try:
        _ensure_tables()
        with db_session(write=True) as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO metrics_perf (created_at, usuario, conversation_id, endpoint, latency_ms)
                VALUES (?, ?, ?, ?, ?);
                """,
                (
                    datetime.datetime.now().isoformat(timespec="seconds"),
                    usuario,
                    conversation_id,
                    endpoint,
                    float(latency_ms) if latency_ms is not None else None,
                ),
            )
    except Exception:
        return
