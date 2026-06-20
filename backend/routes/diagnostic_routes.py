"""Diagnostic routes for the student onboarding flow."""

from __future__ import annotations

import os
import re
from flask import request, session
import structlog
from werkzeug.security import check_password_hash, generate_password_hash

from backend.core.validation import validate_password, validate_student_code
from backend.db.session import _ensure_column, db_session, get_or_create_usuario
from backend.services.diagnostic_service import QUESTION_BANK, random_questions, score_answers
from backend.services.progreso_service import actualizar_perfil_usuario, actualizar_progreso

from .chat_routes import chat_bp, limiter, _err, _ok, obtener_usuario_actual

logger = structlog.get_logger()


def _clean_alias(value: str) -> str:
    raw = str(value or "").strip()
    cleaned = re.sub(r"[^A-Za-z0-9._ -]", "", raw)[:48].strip()
    return cleaned or "Invitado 1"


def _student_user(alias: str) -> str:
    normalized = "-".join(_clean_alias(alias).split())
    code, _ = validate_student_code(normalized)
    return f"STU-{code or 'Estudiante'}"


def _guest_user(alias: str) -> str:
    code = "-".join(_clean_alias(alias).split())
    code = "".join(ch for ch in code if ch.isalnum() or ch in ("-", "_"))[:48]
    return f"GUEST-{code or 'Invitado-1'}"


def _ensure_attempts_table() -> None:
    with db_session(write=True) as conn:
        cur = conn.cursor()
        _ensure_column(cur, "usuarios", "password_hash", "TEXT")
        _ensure_column(cur, "usuarios", "diagnostic_locked", "INTEGER DEFAULT 0")
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS diagnostic_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario TEXT NOT NULL,
                alias TEXT,
                ciclo_academico TEXT,
                estado_materia TEXT,
                nivel_materia TEXT,
                score INTEGER DEFAULT 0,
                total INTEGER DEFAULT 0,
                answers_json TEXT,
                feedback TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
        )


def _diagnostic_done(usuario: str) -> bool:
    _ensure_attempts_table()
    with db_session() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id FROM diagnostic_attempts WHERE usuario = ? ORDER BY id DESC LIMIT 1;", (usuario,))
        if cur.fetchone():
            return True
        cur.execute("SELECT nivel_materia FROM progreso WHERE usuario = ?;", (usuario,))
        row = cur.fetchone()
        return bool(row and row["nivel_materia"])


def _verify_student_password(usuario: str, password: str, create: bool = False):
    with db_session(write=True) as conn:
        cur = conn.cursor()
        cur.execute("SELECT password_hash, status FROM usuarios WHERE alias = ?;", (usuario,))
        row = cur.fetchone()
        if row and (row["status"] or "active") != "active":
            return False, "Cuenta de estudiante bloqueada."
        existing_hash = row["password_hash"] if row else None
        if existing_hash:
            if not password or not check_password_hash(existing_hash, password):
                return False, "Codigo o clave de estudiante incorrectos."
            return True, ""
        if not create:
            return True, ""
        password_error = validate_password(password or "", min_len=6, label="La clave del estudiante")
        if password_error:
            return False, password_error
        get_or_create_usuario(usuario)
        cur.execute(
            "UPDATE usuarios SET password_hash = ?, updated_at = CURRENT_TIMESTAMP WHERE alias = ?;",
            (generate_password_hash(password, method="pbkdf2:sha256", salt_length=16), usuario),
        )
        return True, ""


@chat_bp.route("/api/diagnostic/status", methods=["POST"])
@limiter.limit(os.getenv("RATE_LIMIT_DIAGNOSTIC_STATUS", "60 per hour"))
def api_diagnostic_status():
    data = request.get_json(silent=True) or {}
    alias = _clean_alias(data.get("alias") or data.get("student_code") or "")
    mode = "guest" if data.get("guest") or str(data.get("mode") or "").lower() == "guest" else "student"
    password = str(data.get("password") or "")
    usuario = _guest_user(alias) if mode == "guest" else _student_user(alias)
    try:
        if mode != "guest":
            ok, message = _verify_student_password(usuario, password, create=False)
            if not ok:
                return _err(message, 401)
        done = _diagnostic_done(usuario)
        if done:
            session["usuario"] = usuario
            session["auth_mode"] = mode
            session.permanent = True
        return _ok({"usuario": usuario, "alias": alias, "mode": mode, "diagnostic_completed": done})
    except Exception as exc:
        logger.error("Error consultando estado diagnostico", usuario=usuario, error=str(exc))
        return _err("No se pudo consultar el estado del diagnostico.", 500)


@chat_bp.route("/api/diagnostic/questions", methods=["GET"])
@limiter.limit(os.getenv("RATE_LIMIT_DIAGNOSTIC", "60 per hour"))
def api_diagnostic_questions():
    """Return five random diagnostic questions without the correct answers."""
    try:
        count = int(request.args.get("count", 5))
    except Exception:
        count = 5
    return _ok({"questions": random_questions(count), "total_bank": len(QUESTION_BANK)})


@chat_bp.route("/api/diagnostic/submit", methods=["POST"])
@limiter.limit(os.getenv("RATE_LIMIT_DIAGNOSTIC_SUBMIT", "30 per hour"))
def api_diagnostic_submit():
    """Score the diagnostic and persist the detected academic level."""
    data = request.get_json(silent=True) or {}
    alias = _clean_alias(data.get("alias") or data.get("student_code") or data.get("nickname") or "")
    mode = "guest" if data.get("guest") or str(data.get("mode") or "").lower() == "guest" else "student"
    password = str(data.get("password") or "")
    ciclo = (data.get("ciclo_academico") or data.get("ciclo") or "").strip()
    estado = (data.get("estado_materia") or data.get("estado") or "").strip()
    answers = data.get("answers") or {}

    if not ciclo or not estado:
        return _err("Completa ciclo/semestre y estado respecto a la materia.", 400)
    if not answers:
        return _err("Responde las preguntas del diagnostico.", 400)

    usuario = _guest_user(alias) if mode == "guest" else _student_user(alias)
    if mode != "guest":
        ok, message = _verify_student_password(usuario, password, create=True)
        if not ok:
            return _err(message, 400 if "clave" in message.lower() else 401)
        if _diagnostic_done(usuario):
            return _err("Este estudiante ya completo el diagnostico inicial. Continua con la ruta academica.", 409)

    session["usuario"] = usuario
    session["auth_mode"] = mode
    session.permanent = True

    try:
        get_or_create_usuario(usuario)
    except Exception as exc:
        logger.warning("No se pudo asegurar usuario diagnostico", usuario=usuario, error=str(exc))

    result = score_answers(answers)
    level = result["level"]

    try:
        _ensure_attempts_table()
        actualizar_perfil_usuario(
            usuario,
            ciclo_academico=ciclo,
            estado_materia=estado,
            nivel_materia=level,
        )
        actualizar_progreso(usuario, tema_nuevo="Diagnostico inicial", puntos_delta=int(result["score"]))
        try:
            import json
            with db_session(write=True) as conn:
                cur = conn.cursor()
                cur.execute(
                    """
                    INSERT INTO diagnostic_attempts (
                        usuario, alias, ciclo_academico, estado_materia,
                        nivel_materia, score, total, answers_json, feedback
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
                    """,
                    (
                        usuario,
                        alias,
                        ciclo,
                        estado,
                        level,
                        int(result["score"]),
                        int(result["total"]),
                        json.dumps(result["details"], ensure_ascii=False),
                        result["feedback"],
                    ),
                )
                cur.execute(
                    "UPDATE usuarios SET diagnostic_locked = 1, updated_at = CURRENT_TIMESTAMP WHERE alias = ?;",
                    (usuario,),
                )
        except Exception as exc:
            logger.warning("No se pudo guardar intento diagnostico", usuario=usuario, error=str(exc))

        try:
            from backend.repositories.student_profile_repo import set_nickname
            set_nickname(usuario, alias)
        except Exception:
            pass

        return _ok({
            "usuario": usuario,
            "alias": alias,
            "mode": mode,
            "diagnostic": result,
            "profile": {
                "alias": alias,
                "ciclo": ciclo,
                "estado": estado,
                "nivel": level,
                "ciclo_academico": ciclo,
                "estado_materia": estado,
                "nivel_materia": level,
            },
        })
    except Exception as exc:
        logger.error("Error en diagnostico", usuario=usuario or obtener_usuario_actual(), error=str(exc))
        return _err("No se pudo guardar el diagnostico.", 500)
