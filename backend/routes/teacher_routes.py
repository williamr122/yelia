from __future__ import annotations

import datetime
import json
import os

from flask import Blueprint, jsonify, session, request
from backend.core.frontend import frontend_redirect
from werkzeug.security import check_password_hash, generate_password_hash

from ..core.rate_limit import limiter
from ..core.validation import validate_password, validate_username
from backend.db.session import db_session, is_postgres
from backend.repositories.student_profile_repo import get_profile, save_profile

teacher_bp = Blueprint("teacher", __name__, url_prefix="")


def _teacher_role() -> str:
    return (session.get("teacher_role") or "").strip().lower()


def _require_teacher_or_admin() -> bool:
    return _teacher_role() in ("admin", "docente", "teacher")


def _teacher_action_message(action_label: str, detail: str, topic: str, insight_key: str) -> str:
    topic_text = (topic or "el tema trabajado").strip()
    label = (action_label or "Recomendacion docente").strip()
    body = (detail or "").strip()

    if insight_key == "resources":
        prefix = f"Recurso recomendado por el docente para {topic_text}:"
    elif insight_key == "feedback":
        prefix = "Retroalimentacion personalizada del docente:"
    elif insight_key == "adaptive":
        prefix = "Ajuste de personalizacion adaptativa:"
    elif insight_key == "profile":
        prefix = "Seguimiento de perfil academico:"
    else:
        prefix = "Accion docente sugerida:"

    return f"{prefix}\n\n{label}. {body}".strip()


def _route_summary(usuario: str, raw_route: str | None, updated_at=None) -> dict:
    try:
        route = json.loads(raw_route or "{}")
    except Exception:
        route = {}
    units = route.get("units") if isinstance(route.get("units"), dict) else {}
    unit_states = []
    for unit_id in range(1, 5):
        state = units.get(str(unit_id), {}) if isinstance(units.get(str(unit_id), {}), dict) else {}
        unit_states.append({
            "id": unit_id,
            "status": state.get("status") or ("active" if unit_id == 1 else "locked"),
            "progress": max(0, min(100, int(state.get("progress") or 0))),
            "quiz_percent": (state.get("quiz") or {}).get("percent") if isinstance(state.get("quiz"), dict) else None,
            "passed": bool((state.get("quiz") or {}).get("passed")) if isinstance(state.get("quiz"), dict) else False,
        })
    done = sum(1 for item in unit_states if item["status"] == "done")
    progress = round(sum(item["progress"] for item in unit_states) / 4)
    final_eval = route.get("final_evaluation") if isinstance(route.get("final_evaluation"), dict) else {}
    return {
        "usuario": usuario,
        "display_name": usuario.replace("GUEST-", "Invitado ").replace("-", " ") if str(usuario).startswith("GUEST-") else usuario,
        "current_unit": int(route.get("currentUnit") or 1),
        "progress": progress,
        "done_units": done,
        "units": unit_states,
        "route_completed": bool(route.get("route_completed")),
        "final_percent": final_eval.get("percent"),
        "final_passed": bool(final_eval.get("passed")),
        "updated_at": str(updated_at or route.get("updated_at") or ""),
    }


@limiter.exempt
@teacher_bp.route("/teacher")
def teacher_page():
    if not _require_teacher_or_admin():
        return frontend_redirect("/teacher/login")
    return frontend_redirect("/teacher")


@limiter.exempt
@teacher_bp.route("/teacher/login")
def teacher_login():
    teacher_user = session.get("teacher_username")
    teacher_role = session.get("teacher_role")
    if teacher_user and teacher_role in ("docente", "teacher", "admin"):
        return frontend_redirect("/teacher")
    return frontend_redirect("/teacher/login")


@teacher_bp.route("/api/teacher/auth/login", methods=["POST"])
def api_teacher_login():
    body = request.get_json(silent=True) or {}
    username_raw = (body.get("username") or "").strip()
    password = body.get("password") or ""

    username, username_error = validate_username(username_raw)
    if username_error or not password:
        return jsonify({"success": False, "message": "Usuario o contrasena invalida."}), 400

    with db_session(write=True) as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, username, password_hash, role, status FROM accounts WHERE username = ?;",
            (username,),
        )
        row = cur.fetchone()

        if not row:
            return jsonify({"success": False, "message": "Usuario o contraseña incorrectos."}), 401

        if (row["status"] or "").lower() != "active":
            return jsonify({"success": False, "message": "Cuenta bloqueada."}), 403

        if not check_password_hash(row["password_hash"], password):
            return jsonify({"success": False, "message": "Usuario o contraseña incorrectos."}), 401

        cur.execute(
            "UPDATE accounts SET last_seen = CURRENT_TIMESTAMP WHERE id = ?;",
            (row["id"],),
        )
        conn.commit()

    session["teacher_username"] = row["username"]
    session["teacher_role"] = (row["role"] or "teacher").lower()
    session.permanent = True

    return jsonify({
        "success": True,
        "message": "Login ok",
        "role": session.get("teacher_role"),
        "username": row["username"],
    })


@teacher_bp.route("/api/teacher/request-account", methods=["POST"])
def api_teacher_request_account():
    body = request.get_json(silent=True) or {}
    username_raw = (body.get("username") or "").strip()
    email = (body.get("email") or "").strip() or None
    password = body.get("password") or ""
    reason = (body.get("reason") or "").strip()[:800]

    username, username_error = validate_username(username_raw)
    if username_error:
        return jsonify({"success": False, "message": username_error}), 400
    password_error = validate_password(password, min_len=8, label="La contrasena docente")
    if password_error:
        return jsonify({"success": False, "message": password_error}), 400

    with db_session(write=True) as conn:
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM accounts WHERE username = ? LIMIT 1;", (username,))
        if cur.fetchone():
            return jsonify({"success": False, "message": "Ya existe una cuenta con ese usuario."}), 400
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS teacher_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                email TEXT,
                password_hash TEXT NOT NULL,
                reason TEXT,
                status TEXT NOT NULL DEFAULT 'pending',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                decided_by TEXT,
                decided_at TEXT
            );
            """
        )
        cur.execute(
            "SELECT 1 FROM teacher_requests WHERE username = ? AND status = 'pending' LIMIT 1;",
            (username,),
        )
        if cur.fetchone():
            return jsonify({"success": False, "message": "Ya existe una solicitud pendiente con ese usuario."}), 400
        cur.execute(
            """
            INSERT INTO teacher_requests (username, email, password_hash, reason, status)
            VALUES (?, ?, ?, ?, 'pending');
            """,
            (username, email, generate_password_hash(password, method="pbkdf2:sha256", salt_length=16), reason),
        )
        conn.commit()

    return jsonify({
        "success": True,
        "message": "Solicitud enviada. El administrador principal debe aprobarla.",
    }), 201


@teacher_bp.route("/api/teacher/auth/logout", methods=["POST"])
def api_teacher_logout():
    u = session.get("teacher_username")
    session.pop("teacher_username", None)
    session.pop("teacher_role", None)
    return jsonify({"success": True, "message": "Logout ok", "username": u})


@teacher_bp.route("/api/teacher/me", methods=["GET"])
def api_teacher_me():
    if _require_teacher_or_admin():
        return jsonify({
            "success": True,
            "authenticated": True,
            "role": _teacher_role(),
            "username": session.get("teacher_username"),
        })
    return jsonify({"success": True, "authenticated": False})


@limiter.exempt
@teacher_bp.route("/teacher/metrics")
def teacher_metrics():
    if not _require_teacher_or_admin():
        return frontend_redirect("/teacher/login")
    return frontend_redirect("/teacher/metrics")


@limiter.exempt
@teacher_bp.route("/teacher/db")
def teacher_db():
    if not _require_teacher_or_admin():
        return frontend_redirect("/teacher/login")
    return frontend_redirect("/teacher/db")


@teacher_bp.get("/api/teacher/dashboard")
def api_teacher_dashboard():
    if not _require_teacher_or_admin():
        return jsonify({"ok": False, "message": "No autenticado."}), 401

    try:
        days = int(request.args.get("days") or 7)
    except Exception:
        days = 7

    days = max(1, min(days, 90))

    with db_session() as conn:
        cur = conn.cursor()

        cur.execute("SELECT COUNT(1) FROM interacciones;")
        interactions = int(cur.fetchone()[0])

        cur.execute("SELECT COUNT(1) FROM conversaciones;")
        conversations = int(cur.fetchone()[0])

        cur.execute("SELECT COUNT(1) FROM attachments;")
        attachments = int(cur.fetchone()[0])

        cur.execute(
            """
            SELECT COALESCE(tema,'(sin tema)') AS tema, COUNT(1) AS n
            FROM interacciones
            GROUP BY COALESCE(tema,'(sin tema)')
            ORDER BY n DESC
            LIMIT 8;
            """
        )
        top_temas = [dict(r) for r in cur.fetchall()]

        cur.execute("SELECT COUNT(DISTINCT usuario_id) FROM interacciones;")
        active_students = int(cur.fetchone()[0])

    return jsonify({
        "ok": True,
        "days": days,
        "kpis": {
            "interactions": interactions,
            "conversations": conversations,
            "attachments": attachments,
            "active_students": active_students,
        },
        "top_temas": top_temas,
    })


@teacher_bp.get("/api/teacher/learning-routes")
def api_teacher_learning_routes():
    if not _require_teacher_or_admin():
        return jsonify({"success": False, "message": "No autenticado."}), 401

    q = (request.args.get("q") or "").strip().lower()
    try:
        limit = int(request.args.get("limit") or 80)
    except Exception:
        limit = 80
    limit = max(1, min(limit, 200))

    rows = []
    with db_session() as conn:
        cur = conn.cursor()
        try:
            cur.execute(
                """
                SELECT usuario, route_json, updated_at
                FROM learning_routes
                ORDER BY updated_at DESC
                LIMIT ?;
                """,
                (limit,),
            )
            rows = [dict(row) for row in cur.fetchall()]
        except Exception:
            rows = []

    summaries = [_route_summary(row.get("usuario") or "", row.get("route_json"), row.get("updated_at")) for row in rows]
    if q:
        summaries = [
            item for item in summaries
            if q in (item.get("usuario") or "").lower() or q in (item.get("display_name") or "").lower()
        ]
    active = [item for item in summaries if not item.get("route_completed")]
    completed = [item for item in summaries if item.get("route_completed")]
    avg_progress = round(sum(item["progress"] for item in summaries) / len(summaries)) if summaries else 0

    return jsonify({
        "success": True,
        "items": summaries,
        "summary": {
            "students": len(summaries),
            "active": len(active),
            "completed": len(completed),
            "avg_progress": avg_progress,
        },
    })


@teacher_bp.get("/api/teacher/students")
def api_teacher_students():
    if not _require_teacher_or_admin():
        return jsonify({"success": False, "message": "No autenticado."}), 401

    q = (request.args.get("q") or "").strip().lower()
    try:
        limit = int(request.args.get("limit") or 40)
        offset = int(request.args.get("offset") or 0)
    except Exception:
        limit, offset = 40, 0
    limit = max(1, min(limit, 200))
    offset = max(0, offset)

    where = "WHERE LOWER(COALESCE(role,'student')) IN ('student','estudiante')"
    params = []
    if q:
        where += " AND (LOWER(COALESCE(alias,'')) LIKE ? OR LOWER(COALESCE(email,'')) LIKE ?)"
        params.extend([f"%{q}%", f"%{q}%"])

    with db_session() as conn:
        cur = conn.cursor()
        cur.execute(f"SELECT COUNT(1) FROM usuarios {where};", tuple(params))
        total = int(cur.fetchone()[0] or 0)
        cur.execute(
            f"""
            SELECT id, alias, COALESCE(email,'') AS email, COALESCE(role,'student') AS role,
                   COALESCE(status,'active') AS status, created_at, last_seen
            FROM usuarios
            {where}
            ORDER BY COALESCE(last_seen, created_at) DESC, id DESC
            LIMIT ? OFFSET ?;
            """,
            tuple(params + [limit, offset]),
        )
        rows = [dict(r) for r in cur.fetchall()]

    return jsonify({
        "success": True,
        "students": rows,
        "items": rows,
        "total": total,
        "limit": limit,
        "offset": offset,
        "has_more": bool(offset + len(rows) < total),
    })


@teacher_bp.get("/api/teacher/conversations/<int:conv_id>/messages")
def api_teacher_conversation_messages(conv_id: int):
    if not _require_teacher_or_admin():
        return jsonify({"success": False, "message": "No autenticado."}), 401

    with db_session() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM conversaciones WHERE id = ?;", (conv_id,))
        conv = cur.fetchone()

        if not conv:
            return jsonify({"success": False, "message": "Conversación no encontrada."}), 404

        cur.execute(
            """
            SELECT id, remitente, contenido, tema, created_at
            FROM messages
            WHERE conv_id = ?
            ORDER BY id ASC
            LIMIT 500;
            """,
            (conv_id,),
        )
        msgs = [dict(r) for r in cur.fetchall()]

    return jsonify({"success": True, "conversation": dict(conv), "messages": msgs}), 200


@teacher_bp.post("/api/teacher/conversations/<int:conv_id>/actions")
def api_teacher_conversation_action(conv_id: int):
    if not _require_teacher_or_admin():
        return jsonify({"success": False, "message": "No autenticado."}), 401

    body = request.get_json(silent=True) or {}
    action_key = (body.get("action_key") or "").strip()[:64]
    insight_key = (body.get("insight_key") or "").strip()[:64]
    action_label = (body.get("action_label") or "").strip()[:120]
    detail = (body.get("detail") or "").strip()[:800]
    topic = (body.get("topic") or "").strip()[:120]
    teacher = session.get("teacher_username") or "docente"

    if not action_label:
        return jsonify({"success": False, "message": "Accion invalida."}), 400

    with db_session(write=True) as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM conversaciones WHERE id = ?;", (conv_id,))
        conv = cur.fetchone()
        if not conv:
            return jsonify({"success": False, "message": "Conversacion no encontrada."}), 404

        usuario = conv["usuario"]
        meta = {
            "conv_id": conv_id,
            "usuario": usuario,
            "teacher": teacher,
            "action_key": action_key,
            "insight_key": insight_key,
            "action_label": action_label,
            "detail": detail,
            "topic": topic,
            "created_at": datetime.datetime.utcnow().isoformat(timespec="seconds") + "Z",
            "status": "pending",
        }
        cur.execute(
            """
            INSERT INTO audit_logs (actor, action, target, meta_json)
            VALUES (?, 'teacher_conversation_action', ?, ?);
            """,
            (teacher, f"conversation:{conv_id}", json.dumps(meta, ensure_ascii=False)),
        )

    profile = get_profile(usuario)
    actions = profile.setdefault("teacher_actions", [])
    actions.append(meta)
    profile["teacher_actions"] = actions[-30:]
    profile.setdefault("adaptive", {})
    profile["adaptive"]["last_teacher_action"] = {
        "label": action_label,
        "detail": detail,
        "topic": topic,
        "insight": insight_key,
    }
    if insight_key == "adaptive":
        profile["adaptive"]["support_mode"] = True
        profile["adaptive"]["next_best_action"] = action_key or action_label
    save_profile(usuario, profile)

    return jsonify({
        "success": True,
        "message": "Accion docente enviada al perfil del estudiante.",
        "teacher_action": meta,
    }), 200


@teacher_bp.get("/api/settings")
def api_get_settings():
    with db_session() as conn:
        cur = conn.cursor()
        cur.execute("SELECT key, value FROM global_settings;")
        rows = cur.fetchall()
        settings = {row["key"]: row["value"] for row in rows}
    if "allow_pdf_download" not in settings:
        settings["allow_pdf_download"] = "1"
    return jsonify({"success": True, "settings": settings})


@teacher_bp.get("/api/teacher/settings")
def api_get_teacher_settings():
    if not _require_teacher_or_admin():
        return jsonify({"success": False, "message": "No autenticado."}), 401
    with db_session() as conn:
        cur = conn.cursor()
        cur.execute("SELECT key, value FROM global_settings;")
        rows = cur.fetchall()
        settings = {row["key"]: row["value"] for row in rows}
    if "allow_pdf_download" not in settings:
        settings["allow_pdf_download"] = "1"
    return jsonify({"success": True, "settings": settings})


@teacher_bp.post("/api/teacher/settings")
def api_post_teacher_settings():
    if not _require_teacher_or_admin():
        return jsonify({"success": False, "message": "No autenticado."}), 401
    
    body = request.get_json(silent=True) or {}
    allow_pdf_download = body.get("allow_pdf_download")
    if allow_pdf_download not in ("0", "1", 0, 1):
        return jsonify({"success": False, "message": "Valor no válido para allow_pdf_download."}), 400
        
    val_str = "1" if str(allow_pdf_download) in ("1", "True", "true") else "0"
    
    with db_session(write=True) as conn:
        cur = conn.cursor()
        if is_postgres():
            cur.execute(
                """
                INSERT INTO global_settings (key, value)
                VALUES ('allow_pdf_download', %s)
                ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value;
                """,
                (val_str,),
            )
        else:
            cur.execute(
                """
                INSERT OR REPLACE INTO global_settings (key, value)
                VALUES ('allow_pdf_download', ?);
                """,
                (val_str,),
            )
        conn.commit()
        
    return jsonify({"success": True, "message": "Configuración actualizada correctamente.", "allow_pdf_download": val_str})
