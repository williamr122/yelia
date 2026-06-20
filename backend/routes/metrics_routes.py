"""
Proyecto: YELIA4AP
Archivo: backend/routes/metrics_routes.py
Descripción: Módulo del backend para la lógica asociada a esta carpeta/funcionalidad.

Revisión: 2026-02-10
"""
"""Metrics Routes
Archivo del backend del sistema YELIA4AP.

Responsabilidad:
- Implementa la lógica asociada a este módulo.
"""

#
# Archivo: backend/routes/metrics_routes.py
# Rol: Módulo del backend (Flask) de YELIA4AP.

"""backend/routes/metrics_routes.py

Backend Flask — YELIA (módulo de servidor)

Propósito:
    Este archivo pertenece al backend (Flask) de YELIA. Contiene lógica de servidor
    y/o utilidades que soportan rutas, servicios, persistencia y orquestación NLP.
    Aquí se definen las rutas relacionadas con métricas y feedback de usuarios.
"""

import os
import json
import datetime
from flask import Blueprint, request, jsonify, session
from backend.core.frontend import frontend_redirect
import structlog

from backend.db.session import db_session

from .chat_routes import limiter, _ok, _err

# ✅ FIX: asegurar tablas antes de consultar métricas
from backend.repositories.metrics_repo import _ensure_tables, save_feedback
from backend.services.progreso_service import obtener_usuario_actual

logger = structlog.get_logger()

metrics_bp = Blueprint("metrics", __name__)


def _require_admin() -> bool:
    """Valida acceso a la UI de métricas.

    Reglas:
    - En local/dev: permitir abrir el dashboard sin sesión (para demo rápida).
    - En producción: exigir rol (admin/docente) o token (si ALLOW_ADMIN_TOKEN_FALLBACK=1).
    """
    # Local/dev: permitir ver métricas sin login (el usuario lo pidió explícitamente).
    env = (os.getenv("FLASK_ENV") or os.getenv("ENV") or "production").lower().strip()
    host = (request.host or "").lower()
    is_local = any(x in host for x in ("127.0.0.1", "localhost"))
    if env in ("development", "dev", "local", "test", "testing") or is_local:
        return True

    from backend.core.security import require_roles
    allow_token = (os.getenv("ALLOW_ADMIN_TOKEN_FALLBACK", "1").strip() == "1")
    return require_roles("admin", "teacher", "docente", allow_token=allow_token)



@metrics_bp.route("/api/metrics", methods=["GET"])
@limiter.limit(os.getenv("RATE_LIMIT_METRICS", "30 per hour"))
def api_metrics():
    """api_metrics.

    Returns:
        Any: TODO: Describe the return value."""
    if not _require_admin():
        return _err("No autorizado.", 401, "UNAUTHORIZED")

    # ✅ FIX 1: crea tablas métricas antes de leerlas (best-effort)
    try:
        _ensure_tables()
    except Exception:
        pass

    try:
        with db_session(write=False) as conn:
            cur = conn.cursor()

            cur.execute("SELECT COUNT(*) AS total FROM conversaciones;")
            total_conversaciones = cur.fetchone()["total"]

            cur.execute("SELECT COUNT(*) AS total FROM messages;")
            total_mensajes = cur.fetchone()["total"]

            cur.execute("SELECT COUNT(DISTINCT usuario) AS total FROM conversaciones;")
            total_usuarios = cur.fetchone()["total"]

            mensajes_promedio = round(total_mensajes / total_conversaciones, 2) if total_conversaciones else 0.0

            cur.execute(
                """
                SELECT tema, COUNT(*) AS total
                FROM messages
                WHERE tema IS NOT NULL AND tema <> ''
                  AND remitente = 'bot'
                GROUP BY tema
                ORDER BY total DESC
                LIMIT 5;
                """
            )
            filas_temas = cur.fetchall()
            top_temas = [{"tema": row["tema"], "total": row["total"]} for row in filas_temas]

            # Latencia (metrics_perf)
            cur.execute(
                """
                SELECT latency_ms
                FROM metrics_perf
                WHERE endpoint = '/api/chat'
                  AND latency_ms IS NOT NULL
                ORDER BY latency_ms ASC;
                """
            )
            lat_rows = [r["latency_ms"] for r in cur.fetchall()]

            avg_latency_ms = round(sum(lat_rows) / len(lat_rows), 1) if lat_rows else None
            p95_latency_ms = None
            if lat_rows:
                idx = int(round(0.95 * (len(lat_rows) - 1)))
                p95_latency_ms = lat_rows[max(0, min(idx, len(lat_rows) - 1))]

            # Feedback (metrics_feedback)
            cur.execute(
                """
                SELECT
                  SUM(CASE WHEN rating = 'up' THEN 1 ELSE 0 END) AS up,
                  SUM(CASE WHEN rating = 'down' THEN 1 ELSE 0 END) AS down
                FROM metrics_feedback;
                """
            )
            fb_row = cur.fetchone()

            # ✅ FIX 2: sqlite3.Row -> dict antes de usar .get
            if fb_row:
                fb = {k: fb_row[k] for k in fb_row.keys()}
            else:
                fb = {"up": 0, "down": 0}

            fb_up = int((fb.get("up") or 0))
            fb_down = int((fb.get("down") or 0))
            fb_total = fb_up + fb_down
            fb_ratio = round((fb_up / fb_total) * 100, 1) if fb_total else None


            # =========================================================
            # MÉTRICAS DE USABILIDAD (ISO 9241-11) — versión mínima
            # ---------------------------------------------------------
            # Nota:
            # - Estas métricas se calculan a partir de tablas existentes:
            #   conversaciones, messages, metrics_feedback.
            # - Son apropiadas para prototipos, porque miden:
            #   (1) eficiencia: tiempo/esfuerzo para resolver una consulta
            #   (2) efectividad: si se logró completar (👍)
            #   (3) abandono: si el usuario deja la conversación sin resolver
            # =========================================================

                        # 1) Consultas resueltas:
            #    conversación resuelta = tiene al menos 1 mensaje user y 1 respuesta bot.
            cur.execute(
                """
                SELECT COUNT(*) AS n
                FROM (
                    SELECT c.id
                    FROM conversaciones c
                    LEFT JOIN messages mu
                      ON mu.conv_id = c.id AND mu.remitente = 'user'
                    LEFT JOIN messages mb
                      ON mb.conv_id = c.id AND mb.remitente = 'bot'
                    GROUP BY c.id
                    HAVING COUNT(mu.id) >= 1 AND COUNT(mb.id) >= 1
                ) t;
                """
            )
            resueltas_n = int(cur.fetchone()["n"] or 0)

            tareas_completadas_percent = (
                round((resueltas_n / total_conversaciones) * 100, 1)
                if total_conversaciones else 0.0
            )

            # 2) Tiempo medio de resolución:
            #    desde el primer mensaje del usuario hasta la primera respuesta del bot.
            cur.execute(
                """
                SELECT
                    c.id AS conv_id,
                    MIN(mu.created_at) AS first_user_msg_at,
                    MIN(mb.created_at) AS first_bot_msg_at
                FROM conversaciones c
                JOIN messages mu
                  ON mu.conv_id = c.id AND mu.remitente = 'user'
                JOIN messages mb
                  ON mb.conv_id = c.id AND mb.remitente = 'bot'
                GROUP BY c.id;
                """
            )

            rows = cur.fetchall()
            tiempos = []

            for r in rows:
                try:
                    t0 = datetime.datetime.fromisoformat(
                        str(r["first_user_msg_at"]).replace("Z", "")
                    )
                    t1 = datetime.datetime.fromisoformat(
                        str(r["first_bot_msg_at"]).replace("Z", "")
                    )
                    dt = (t1 - t0).total_seconds()
                    if dt >= 0:
                        tiempos.append(dt)
                except Exception:
                    pass

            tiempo_medio_resolucion_s = (
                round((avg_latency_ms or 0) / 1000, 1)
                if avg_latency_ms is not None else 0.0
            )

            # 3) Mensajes por consulta
            mensajes_por_consulta = (
                round(total_mensajes / total_conversaciones, 2)
                if total_conversaciones else 0.0
            )

            # 4) Abandono:
            #    conversación abandonada = tiene mensajes de usuario, pero no respuesta bot.
            cur.execute(
                """
                SELECT COUNT(*) AS n
                FROM (
                    SELECT c.id
                    FROM conversaciones c
                    LEFT JOIN messages mu
                      ON mu.conv_id = c.id AND mu.remitente = 'user'
                    LEFT JOIN messages mb
                      ON mb.conv_id = c.id AND mb.remitente = 'bot'
                    GROUP BY c.id
                    HAVING COUNT(mu.id) >= 1 AND COUNT(mb.id) = 0
                ) t;
                """
            )
            abandono_n = int(cur.fetchone()["n"] or 0)

            abandono_percent = (
                round((abandono_n / total_conversaciones) * 100, 1)
                if total_conversaciones else 0.0
            )

            def _clean_label(value, fallback="Sin dato"):
                text = str(value or "").strip()
                return text if text else fallback

            def _level_from_points(points):
                try:
                    points = int(points or 0)
                except Exception:
                    points = 0
                if points < 10:
                    return "Inicial"
                if points < 30:
                    return "Intermedio"
                return "Avanzado"

            def _parse_topics(value):
                if not value:
                    return []
                try:
                    raw = json.loads(value)
                    if not isinstance(raw, list):
                        return []
                    return [str(item).strip() for item in raw if str(item or "").strip()]
                except Exception:
                    return []

            cur.execute(
                """
                SELECT usuario,
                       COUNT(*) AS total_messages,
                       SUM(CASE WHEN remitente = 'user' THEN 1 ELSE 0 END) AS user_messages,
                       SUM(CASE WHEN remitente = 'bot' THEN 1 ELSE 0 END) AS bot_messages,
                       COUNT(DISTINCT NULLIF(tema, '')) AS distinct_topics,
                       MAX(created_at) AS last_activity
                FROM messages
                GROUP BY usuario;
                """
            )
            message_by_user = {
                row["usuario"]: {
                    "total_messages": int(row["total_messages"] or 0),
                    "user_messages": int(row["user_messages"] or 0),
                    "bot_messages": int(row["bot_messages"] or 0),
                    "distinct_topics": int(row["distinct_topics"] or 0),
                    "last_activity": row["last_activity"],
                }
                for row in cur.fetchall()
            }

            cur.execute(
                """
                SELECT usuario, COUNT(*) AS total, MAX(created_at) AS last_conversation
                FROM conversaciones
                GROUP BY usuario;
                """
            )
            conversations_by_user = {
                row["usuario"]: {
                    "conversations": int(row["total"] or 0),
                    "last_conversation": row["last_conversation"],
                }
                for row in cur.fetchall()
            }

            cur.execute(
                """
                SELECT usuario,
                       COUNT(*) AS total,
                       SUM(CASE WHEN history_based = 1 THEN 1 ELSE 0 END) AS history_based_total
                FROM metrics_recommendations
                GROUP BY usuario;
                """
            )
            recommendations_by_user = {
                row["usuario"]: {
                    "recommendations": int(row["total"] or 0),
                    "history_based": int(row["history_based_total"] or 0),
                }
                for row in cur.fetchall()
            }

            cur.execute(
                """
                SELECT usuario, COALESCE(NULLIF(recommendation_type, ''), 'general') AS key, COUNT(*) AS total
                FROM metrics_recommendations
                GROUP BY usuario, key
                ORDER BY usuario ASC, total DESC;
                """
            )
            preferred_recommendation_type = {}
            for row in cur.fetchall():
                user = row["usuario"]
                if user not in preferred_recommendation_type:
                    preferred_recommendation_type[user] = {"type": row["key"], "total": int(row["total"] or 0)}

            cur.execute(
                """
                SELECT usuario, COALESCE(NULLIF(topic, ''), 'Sin tema') AS key, COUNT(*) AS total
                FROM metrics_recommendations
                GROUP BY usuario, key
                ORDER BY usuario ASC, total DESC;
                """
            )
            preferred_recommendation_topic = {}
            for row in cur.fetchall():
                user = row["usuario"]
                if user not in preferred_recommendation_topic:
                    preferred_recommendation_topic[user] = {"topic": row["key"], "total": int(row["total"] or 0)}

            cur.execute(
                """
                SELECT usuario, puntos, temas_aprendidos, ciclo_academico,
                       estado_materia, nivel_materia, updated_at
                FROM progreso
                ORDER BY puntos DESC, updated_at DESC;
                """
            )
            progreso_rows = cur.fetchall()
            progreso_by_user = {row["usuario"]: row for row in progreso_rows}

            all_users = set(message_by_user.keys()) | set(conversations_by_user.keys()) | set(recommendations_by_user.keys())
            for row in progreso_rows:
                all_users.add(row["usuario"])

            topic_counts_by_user = {}
            topic_totals = {}

            cur.execute(
                """
                SELECT usuario, COALESCE(NULLIF(tema, ''), 'Sin tema') AS tema, COUNT(*) AS total
                FROM messages
                WHERE remitente = 'user'
                  AND tema IS NOT NULL
                  AND tema <> ''
                GROUP BY usuario, tema
                ORDER BY total DESC;
                """
            )
            for row in cur.fetchall():
                user = row["usuario"]
                topic = row["tema"]
                total = int(row["total"] or 0)
                topic_counts_by_user.setdefault(user, {})[topic] = total
                topic_totals[topic] = topic_totals.get(topic, 0) + total

            cur.execute(
                """
                SELECT usuario, COALESCE(NULLIF(tema, ''), 'Sin tema') AS tema, COUNT(*) AS total
                FROM metrics_events
                WHERE tema IS NOT NULL
                  AND tema <> ''
                GROUP BY usuario, tema
                ORDER BY total DESC;
                """
            )
            for row in cur.fetchall():
                user = row["usuario"]
                topic = row["tema"]
                total = int(row["total"] or 0)
                current = topic_counts_by_user.setdefault(user, {}).get(topic, 0)
                topic_counts_by_user[user][topic] = current + total
                topic_totals[topic] = topic_totals.get(topic, 0) + total

            heatmap_topics = [topic for topic, _total in sorted(topic_totals.items(), key=lambda item: item[1], reverse=True)[:10]]
            max_heat_value = 0
            heatmap_rows = []
            for user in sorted(all_users):
                counts = topic_counts_by_user.get(user, {})
                values = []
                for topic in heatmap_topics:
                    value = int(counts.get(topic, 0))
                    max_heat_value = max(max_heat_value, value)
                    values.append({"topic": topic, "value": value})
                heatmap_rows.append({"usuario": user, "values": values})

            cur.execute(
                """
                SELECT COALESCE(NULLIF(recommendation_type, ''), 'general') AS key, COUNT(*) AS total
                FROM metrics_recommendations
                GROUP BY key
                ORDER BY total DESC
                LIMIT 8;
                """
            )
            recommendation_types = [{"type": row["key"], "total": int(row["total"] or 0)} for row in cur.fetchall()]

            cur.execute(
                """
                SELECT COALESCE(NULLIF(topic, ''), 'Sin tema') AS key, COUNT(*) AS total
                FROM metrics_recommendations
                GROUP BY key
                ORDER BY total DESC
                LIMIT 8;
                """
            )
            recommendation_topics = [{"topic": row["key"], "total": int(row["total"] or 0)} for row in cur.fetchall()]

            cur.execute(
                """
                SELECT COALESCE(NULLIF(level_used, ''), 'Sin nivel') AS key, COUNT(*) AS total
                FROM metrics_recommendations
                GROUP BY key
                ORDER BY total DESC;
                """
            )
            recommendation_levels = [{"level": row["key"], "total": int(row["total"] or 0)} for row in cur.fetchall()]

            cur.execute(
                """
                SELECT COALESCE(NULLIF(emotion_used, ''), 'neutral') AS key, COUNT(*) AS total
                FROM metrics_recommendations
                GROUP BY key
                ORDER BY total DESC
                LIMIT 8;
                """
            )
            recommendation_emotions = [{"emotion": row["key"], "total": int(row["total"] or 0)} for row in cur.fetchall()]

            cur.execute(
                """
                SELECT id, created_at, usuario, recommendation_type, title, topic,
                       level_used, emotion_used, priority, history_based, source, url, reason
                FROM metrics_recommendations
                ORDER BY id DESC
                LIMIT 10;
                """
            )
            recent_recommendations = [dict(row) for row in cur.fetchall()]

            cur.execute(
                """
                SELECT COALESCE(NULLIF(kind, ''), 'sin_clasificar') AS key,
                       COUNT(*) AS total,
                       SUM(COALESCE(score_delta, 0)) AS score_delta_total
                FROM metrics_adaptive_feedback
                GROUP BY key
                ORDER BY total DESC
                LIMIT 8;
                """
            )
            adaptive_feedback_kinds = [
                {
                    "kind": row["key"],
                    "total": int(row["total"] or 0),
                    "score_delta_total": int(row["score_delta_total"] or 0),
                }
                for row in cur.fetchall()
            ]

            cur.execute(
                """
                SELECT usuario,
                       COUNT(*) AS total,
                       AVG(CASE WHEN last_score IS NOT NULL THEN last_score END) AS avg_score,
                       SUM(CASE WHEN status = 'completed' OR answered_at IS NOT NULL THEN 1 ELSE 0 END) AS completed
                FROM structured_quizzes
                GROUP BY usuario;
                """
            )
            quizzes_by_user = {
                row["usuario"]: {
                    "quizzes": int(row["total"] or 0),
                    "avg_score": round(float(row["avg_score"]), 1) if row["avg_score"] is not None else None,
                    "completed": int(row["completed"] or 0),
                }
                for row in cur.fetchall()
            }

            students = []
            level_distribution = {}
            for user in sorted(all_users):
                progreso_row = progreso_by_user.get(user)
                learned_topics = _parse_topics(progreso_row["temas_aprendidos"]) if progreso_row else []
                points = int(progreso_row["puntos"] or 0) if progreso_row else 0
                level = _clean_label(progreso_row["nivel_materia"] if progreso_row else None, _level_from_points(points))
                if level == "Sin dato":
                    level = _level_from_points(points)
                level_distribution[level] = level_distribution.get(level, 0) + 1

                studied_topics = sorted(set(learned_topics) | set(topic_counts_by_user.get(user, {}).keys()))
                missing_topics = [topic for topic in heatmap_topics if topic not in studied_topics][:5]
                msg_stats = message_by_user.get(user, {})
                conv_stats = conversations_by_user.get(user, {})
                rec_stats = recommendations_by_user.get(user, {})
                quiz_stats = quizzes_by_user.get(user, {})
                preferred_type = preferred_recommendation_type.get(user, {})
                preferred_topic = preferred_recommendation_topic.get(user, {})
                engagement_score = min(
                    100,
                    (points * 2)
                    + int(msg_stats.get("user_messages", 0) or 0)
                    + int(rec_stats.get("history_based", 0) or 0)
                    + (len(studied_topics) * 4)
                    + (int(quiz_stats.get("completed", 0) or 0) * 5),
                )

                students.append(
                    {
                        "usuario": user,
                        "puntos": points,
                        "nivel": level,
                        "ciclo_academico": progreso_row["ciclo_academico"] if progreso_row else None,
                        "estado_materia": progreso_row["estado_materia"] if progreso_row else None,
                        "temas_aprendidos": learned_topics,
                        "temas_investigados": studied_topics,
                        "temas_no_investigados": missing_topics,
                        "conversaciones": int(conv_stats.get("conversations", 0) or 0),
                        "mensajes_usuario": int(msg_stats.get("user_messages", 0) or 0),
                        "mensajes_bot": int(msg_stats.get("bot_messages", 0) or 0),
                        "recomendaciones": int(rec_stats.get("recommendations", 0) or 0),
                        "recomendaciones_con_historial": int(rec_stats.get("history_based", 0) or 0),
                        "recomendacion_preferida": preferred_type.get("type"),
                        "tema_recomendado_preferido": preferred_topic.get("topic"),
                        "quizzes": int(quiz_stats.get("quizzes", 0) or 0),
                        "quizzes_completados": int(quiz_stats.get("completed", 0) or 0),
                        "quiz_promedio": quiz_stats.get("avg_score"),
                        "engagement_score": engagement_score,
                        "ultima_actividad": msg_stats.get("last_activity") or conv_stats.get("last_conversation"),
                    }
                )

            students.sort(key=lambda item: (item["engagement_score"], item["puntos"], item["mensajes_usuario"]), reverse=True)

            cur.execute(
                """
                SELECT substr(created_at, 1, 10) AS day,
                       COUNT(*) AS total,
                       SUM(CASE WHEN remitente = 'user' THEN 1 ELSE 0 END) AS user_messages,
                       SUM(CASE WHEN remitente = 'bot' THEN 1 ELSE 0 END) AS bot_messages
                FROM messages
                WHERE created_at IS NOT NULL
                GROUP BY day
                ORDER BY day DESC
                LIMIT 14;
                """
            )
            activity_by_day = [
                {
                    "day": row["day"],
                    "total": int(row["total"] or 0),
                    "user_messages": int(row["user_messages"] or 0),
                    "bot_messages": int(row["bot_messages"] or 0),
                }
                for row in reversed(cur.fetchall())
            ]

            learning_route_rows = []
            try:
                cur.execute(
                    """
                    SELECT usuario, route_json, updated_at
                    FROM learning_routes
                    ORDER BY updated_at DESC
                    LIMIT 200;
                    """
                )
                learning_route_rows = [dict(row) for row in cur.fetchall()]
            except Exception:
                learning_route_rows = []

            route_items = []
            for row in learning_route_rows:
                try:
                    route = json.loads(row.get("route_json") or "{}")
                except Exception:
                    route = {}
                units = route.get("units") if isinstance(route.get("units"), dict) else {}
                unit_progress = []
                done_units = 0
                for unit_id in range(1, 5):
                    state = units.get(str(unit_id), {}) if isinstance(units.get(str(unit_id), {}), dict) else {}
                    progress = max(0, min(100, int(state.get("progress") or 0)))
                    unit_progress.append(progress)
                    if (state.get("status") or "").lower() == "done":
                        done_units += 1
                final_eval = route.get("final_evaluation") if isinstance(route.get("final_evaluation"), dict) else {}
                progress = round(sum(unit_progress) / 4) if unit_progress else 0
                route_items.append({
                    "usuario": row.get("usuario") or "",
                    "current_unit": int(route.get("currentUnit") or 1),
                    "progress": progress,
                    "done_units": done_units,
                    "route_completed": bool(route.get("route_completed")),
                    "final_percent": final_eval.get("percent"),
                    "updated_at": str(row.get("updated_at") or route.get("updated_at") or ""),
                })

            route_active = [item for item in route_items if not item.get("route_completed")]
            route_completed = [item for item in route_items if item.get("route_completed")]
            route_avg_progress = round(sum(item["progress"] for item in route_items) / len(route_items)) if route_items else 0

        metrics = {
            "total_conversaciones": total_conversaciones,
            "total_mensajes": total_mensajes,
            "total_usuarios": total_usuarios,
            "mensajes_promedio_por_conversacion": mensajes_promedio,
            "top_temas": top_temas,
            "avg_latency_ms": avg_latency_ms,
            "p95_latency_ms": p95_latency_ms,
            "feedback": {
                "up": fb_up,
                "down": fb_down,
                "up_ratio_percent": fb_ratio,
            },
            "usabilidad": {
                "tiempo_medio_resolucion_s": tiempo_medio_resolucion_s,
                "mensajes_por_consulta": mensajes_por_consulta,
                "tareas_completadas_percent": tareas_completadas_percent,
                "abandono_percent": abandono_percent,
            },
            "academic": {
                "students": students,
                "student_count": len(students),
                "heatmap": {
                    "topics": heatmap_topics,
                    "rows": heatmap_rows,
                    "max_value": max_heat_value,
                },
                "level_distribution": [
                    {"level": key, "total": value}
                    for key, value in sorted(level_distribution.items(), key=lambda item: item[0])
                ],
                "recommendations": {
                    "by_type": recommendation_types,
                    "by_topic": recommendation_topics,
                    "by_level": recommendation_levels,
                    "by_emotion": recommendation_emotions,
                    "recent": recent_recommendations,
                },
                "adaptive_feedback": {
                    "by_kind": adaptive_feedback_kinds,
                },
                "learning_routes": {
                    "items": route_items,
                    "summary": {
                        "students": len(route_items),
                        "active": len(route_active),
                        "completed": len(route_completed),
                        "avg_progress": route_avg_progress,
                    },
                },
                "activity_by_day": activity_by_day,
            },
            "generated_at": datetime.datetime.now().isoformat(timespec="seconds"),
        }

        logger.info("Métricas calculadas", **metrics)
        return _ok({"metrics": metrics})

    except Exception as e:
        logger.error("Error al obtener métricas", error=str(e))
        return _err("No se pudieron obtener las métricas.", 500)


@metrics_bp.route("/admin/metrics", methods=["GET"])
def admin_metrics_dashboard():
    """admin_metrics_dashboard.

    Returns:
        Any: TODO: Describe the return value."""
    if not _require_admin():
        # UX: si se accede desde /launcher o /demo sin sesión, llevar al login.
        return frontend_redirect("/admin/login")
    return frontend_redirect("/metricas")


@metrics_bp.route("/api/feedback", methods=["POST"])
@limiter.limit(os.getenv("RATE_LIMIT_FEEDBACK", "120 per hour"))
def api_feedback():
    """api_feedback.

    Returns:
        Any: TODO: Describe the return value."""
    usuario = obtener_usuario_actual()
    data = request.get_json(silent=True) or {}

    rating = (data.get("rating") or data.get("value") or "").strip().lower()
    conv_id = data.get("conversation_id")

    if isinstance(conv_id, str) and conv_id.isdigit():
        conv_id = int(conv_id)
    if not isinstance(conv_id, int):
        conv_id = None

    if rating not in ("up", "down"):
        return _err("rating inválido (usa 'up' o 'down')", 400, "BAD_REQUEST")

    note = data.get("note") or data.get("message")

    try:
        save_feedback(usuario=usuario, conversation_id=conv_id, rating=rating, note=note)
        return _ok({"saved": True})
    except Exception as e:
        logger.error("Error guardando feedback", error=str(e), usuario=usuario)
        return _err("No se pudo guardar el feedback.", 500, "SERVER_ERROR")


@metrics_bp.route("/api/metrics/pro", methods=["GET"])
@limiter.limit(os.getenv("RATE_LIMIT_METRICS", "30 per hour"))
def api_metrics_pro():
    """api_metrics_pro.

    Returns:
        Any: TODO: Describe the return value."""
    if not _require_admin():
        return _err("No autorizado.", 401, "UNAUTHORIZED")

    # ✅ FIX: asegurar tablas también aquí
    try:
        _ensure_tables()
    except Exception:
        pass

    today = datetime.date.today()
    start_14 = today - datetime.timedelta(days=13)
    start_30 = today - datetime.timedelta(days=29)

    def _date_str(d: datetime.date) -> str:
        """_date_str.

        Args:
            d (datetime.date): TODO: Describe this parameter.

        Returns:
            str: TODO: Describe the return value."""
        return d.strftime("%Y-%m-%d")

    try:
        with db_session(write=False) as conn:
            cur = conn.cursor()

            cur.execute("SELECT COUNT(*) AS total FROM conversaciones;")
            total_conversaciones = cur.fetchone()["total"]

            cur.execute("SELECT COUNT(*) AS total FROM messages;")
            total_mensajes = cur.fetchone()["total"]

            cur.execute("SELECT COUNT(DISTINCT usuario) AS total FROM conversaciones;")
            total_usuarios = cur.fetchone()["total"]

            mensajes_promedio = round(total_mensajes / total_conversaciones, 2) if total_conversaciones else 0.0

            cur.execute(
                """
                SELECT rating, COUNT(*) AS total
                FROM metrics_feedback
                GROUP BY rating;
                """
            )
            fb_rows = cur.fetchall() or []
            fb = {r["rating"]: r["total"] for r in fb_rows}
            up = int(fb.get("up", 0) or 0)
            down = int(fb.get("down", 0) or 0)
            clarity_ratio = round((up / (up + down)) * 100, 2) if (up + down) else 0.0

            cur.execute(
                """
                SELECT latency_ms
                FROM metrics_perf
                WHERE endpoint = '/api/chat'
                  AND latency_ms IS NOT NULL
                ORDER BY id DESC
                LIMIT 1200;
                """
            )
            lat = [int(r["latency_ms"]) for r in (cur.fetchall() or []) if r["latency_ms"] is not None]
            latency_avg = round(sum(lat) / len(lat), 2) if lat else 0.0
            latency_p95 = 0
            if lat:
                lat_sorted = sorted(lat)
                k = int(round(0.95 * (len(lat_sorted) - 1)))
                latency_p95 = int(lat_sorted[k])

            cur.execute(
                """
                SELECT substr(created_at, 1, 10) AS day,
                       SUM(CASE WHEN event_type='message_received' THEN 1 ELSE 0 END) AS received,
                       SUM(CASE WHEN event_type='response_generated' THEN 1 ELSE 0 END) AS generated
                FROM metrics_events
                WHERE substr(created_at, 1, 10) >= ?
                GROUP BY day
                ORDER BY day ASC;
                """,
                (_date_str(start_14),)
            )
            raw_series = {r["day"]: {"received": r["received"], "generated": r["generated"]} for r in (cur.fetchall() or [])}

            series_days = []
            series_received = []
            series_generated = []
            for i in range(14):
                d = start_14 + datetime.timedelta(days=i)
                ds = _date_str(d)
                series_days.append(ds)
                series_received.append(int(raw_series.get(ds, {}).get("received", 0)))
                series_generated.append(int(raw_series.get(ds, {}).get("generated", 0)))

            cur.execute(
                """
                SELECT COALESCE(NULLIF(intencion, ''), 'otro') AS key,
                       COUNT(*) AS total
                FROM metrics_events
                WHERE event_type='response_generated'
                  AND substr(created_at, 1, 10) >= ?
                GROUP BY key
                ORDER BY total DESC
                LIMIT 7;
                """,
                (_date_str(start_30),)
            )
            top_intents = [{"intencion": r["key"], "total": r["total"]} for r in (cur.fetchall() or [])]

            cur.execute(
                """
                SELECT COALESCE(NULLIF(tema, ''), 'Sin tema') AS key,
                       COUNT(*) AS total
                FROM metrics_events
                WHERE event_type='response_generated'
                  AND substr(created_at, 1, 10) >= ?
                GROUP BY key
                ORDER BY total DESC
                LIMIT 7;
                """,
                (_date_str(start_30),)
            )
            top_topics = [{"tema": r["key"], "total": r["total"]} for r in (cur.fetchall() or [])]

        return _ok(
            {
                "total_conversaciones": total_conversaciones,
                "total_mensajes": total_mensajes,
                "total_usuarios": total_usuarios,
                "mensajes_promedio": mensajes_promedio,
                "feedback_up": up,
                "feedback_down": down,
                "clarity_ratio": clarity_ratio,
                "latency_avg_ms": latency_avg,
                "latency_p95_ms": latency_p95,
                "series": {
                    "days": series_days,
                    "received": series_received,
                    "generated": series_generated,
                },
                "top_intents": top_intents,
                "top_topics": top_topics,
            }
        )
    except Exception as e:
        logger.error("Error metrics_pro", error=str(e))
        return _err("No se pudieron calcular métricas pro.", 500, "SERVER_ERROR")
