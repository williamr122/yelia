"""
Proyecto: YELIA4AP
Archivo: backend/routes/chat_routes_auth.py
Descripción: Módulo del backend para la lógica asociada a esta carpeta/funcionalidad.

Revisión: 2026-02-10
"""
"""Chat Routes Auth
Archivo del backend del sistema YELIA4AP.

Responsabilidad:
- Implementa la lógica asociada a este módulo.
"""

#
# Archivo: backend/routes/chat_routes_auth.py
# Rol: Módulo del backend (Flask) de YELIA4AP.

"""backend/routes/chat_routes_auth.py

Backend Flask — YELIA (módulo de servidor)

Propósito:
    Este archivo pertenece al backend (Flask) de YELIA. Contiene lógica de servidor
    y/o utilidades que soportan rutas, servicios, persistencia y orquestación NLP.
    En particular, este módulo define rutas relacionadas con la autenticación
    mínima basada en sesiones para usuarios de chat.
"""

# ============================================================================
# IMPORTS
# ============================================================================
import os
import structlog
from flask import request, session
from werkzeug.security import check_password_hash, generate_password_hash

from .chat_routes import (
    chat_bp,
    limiter,
    _ok,
    _err,
    obtener_usuario_actual,
)
from backend.core.validation import validate_password, validate_student_code

# Import necesario para crear el registro en la tabla usuarios al login
from backend.db.session import db_session, get_or_create_usuario

logger = structlog.get_logger()


# ============================================================================
# ENDPOINTS
# ============================================================================
@chat_bp.route("/api/auth/login", methods=["POST"])
@limiter.limit(os.getenv("RATE_LIMIT_LOGIN", "30 per hour"))
def api_auth_login():
    """
    Login mínimo basado en sesión (no es un sistema de auth completo).

    - Si no se envía student_code:
        • se mantiene modo guest
    - Si se envía:
        • se sanitiza y se guarda en session como STU-<code>
        • se crea registro en tabla usuarios si no existe (para que aparezca en panel admin/teacher)

    Esto permite:
    - separar conversaciones por usuario
    - personalizar progreso sin exigir registro real
    - que el estudiante aparezca en el listado de /admin y /teacher
    """
    data = request.get_json(silent=True) or {}
    raw = (data.get("student_code") or "").strip()
    guest_id_raw = (data.get("guest_id") or "").strip()
    password = str(data.get("password") or "")
    create = bool(data.get("create"))

    if not raw:
        guest_id = "".join(ch for ch in guest_id_raw if ch.isalnum() or ch in ("-", "_"))[:48]
        if guest_id:
            usuario = f"GUEST-{guest_id}"
            session["usuario"] = usuario
            session["auth_mode"] = "guest"
            try:
                get_or_create_usuario(usuario)
            except Exception:
                pass
        else:
            session.pop("usuario", None)
            session.pop("auth_mode", None)
            usuario = obtener_usuario_actual()
        session.permanent = True
        logger.info("Auth login opcional (guest)", usuario=usuario)
        return _ok({"usuario": usuario, "mode": "guest"})

    # Validación + sanitización (modo producción opcional)
    # - Solo [A-Za-z0-9_-]
    # - Longitud mínima configurable
    # - Allowlist opcional (modo estricto)
    min_len = int(os.getenv("STUDENT_CODE_MIN_LEN", "4"))
    strict = os.getenv("STUDENT_AUTH_STRICT", "0") == "1"
    fail_open = os.getenv("STUDENT_AUTH_FAIL_OPEN", "0") == "1"
    allowlist_raw = os.getenv("STUDENT_CODES_ALLOWLIST", "")

    # Sanitización: solo alfanumérico y - _
    code, code_error = validate_student_code(raw)

    # Reglas mínimas
    if code_error or len(code or "") < min_len:
        session.pop("usuario", None)
        session.pop("auth_mode", None)
        session.permanent = True
        usuario = obtener_usuario_actual()
        logger.info(
            "Auth login: codigo invalido, continua como guest",
            reason=code_error or "min_len",
            min_len=min_len,
        )
        return _ok({
            "usuario": usuario,
            "mode": "guest",
            "reason": code_error or "Codigo de estudiante invalido.",
        })

    # Modo estricto: solo códigos permitidos
    if strict and allowlist_raw.strip():
        allowed = {c.strip() for c in allowlist_raw.split(",") if c.strip()}
        if code not in allowed:
            if not fail_open:
                # En producción es mejor bloquear
                return _err("Código de estudiante no autorizado.", 403)
            # Fail-open: deja pasar pero registra warning
            logger.warning("Auth login strict: no autorizado pero fail_open", code=code)


    usuario = f"STU-{code}"

    try:
        with db_session(write=True) as conn:
            cur = conn.cursor()
            cur.execute("SELECT password_hash, status FROM usuarios WHERE alias = ?;", (usuario,))
            row = cur.fetchone()
            if row and (row["status"] or "active") != "active":
                return _err("Cuenta de estudiante bloqueada.", 403)
            existing_hash = row["password_hash"] if row else None
            if existing_hash:
                if not password or not check_password_hash(existing_hash, password):
                    return _err("Codigo o contrasena de estudiante incorrectos.", 401)
            elif create and password:
                password_error = validate_password(password, min_len=6, label="La contrasena del estudiante")
                if password_error:
                    return _err(password_error, 400)
                get_or_create_usuario(usuario)
                cur.execute(
                    "UPDATE usuarios SET password_hash = ?, updated_at = CURRENT_TIMESTAMP WHERE alias = ?;",
                    (generate_password_hash(password, method="pbkdf2:sha256", salt_length=16), usuario),
                )
    except Exception as exc:
        logger.warning("No se pudo verificar clave de estudiante", usuario=usuario, error=str(exc))

    session["usuario"] = usuario
    session["auth_mode"] = "student"
    session.permanent = True

    # ╔══════════════════════════════════════════════════════════════╗
    # ║ CORRECCIÓN PRINCIPAL: Crear registro en tabla usuarios      ║
    # ║ Esto asegura que el usuario aparezca en el listado admin/   ║
    # ║ teacher después del primer login.                            ║
    # ╚══════════════════════════════════════════════════════════════╝
    try:
        user_id = get_or_create_usuario(usuario)
        logger.info(
            "Usuario creado o encontrado en tabla usuarios",
            usuario=usuario,
            user_id=user_id
        )
    except Exception as e:
        logger.warning(
            "No se pudo crear usuario en tabla usuarios (continúa como guest)",
            usuario=usuario,
            error=str(e)
        )

    logger.info("Auth login (session)", usuario=usuario)
    return _ok({"usuario": usuario, "mode": "student", "auth_strength": "alias"})


@chat_bp.route("/api/auth/logout", methods=["POST"])
def api_auth_logout():
    """
    Logout simple: elimina la clave 'usuario' de la sesión.
    """
    session.pop("usuario", None)
    session.pop("auth_mode", None)
    session.permanent = True
    usuario = obtener_usuario_actual()
    logger.info("Auth logout", usuario=usuario)
    return _ok({"usuario": usuario})


@chat_bp.route("/api/auth/whoami", methods=["GET"])
def api_auth_whoami():
    """
    Endpoint utilitario para que el frontend sepa
    cuál es el usuario actual (STU-... o guest).
    """
    usuario = obtener_usuario_actual()

    # Nickname opcional (persistente en perfil JSON)
    nickname = None
    try:
        from backend.repositories.student_profile_repo import get_profile
        nickname = (get_profile(usuario) or {}).get("nickname")
    except Exception:
        nickname = None

    return _ok({
        "usuario": usuario,
        "nickname": nickname,
        "mode": session.get("auth_mode") or ("guest" if usuario.startswith(("Anon-", "GUEST-")) else "student"),
        "auth_strength": "guest" if usuario.startswith(("Anon-", "GUEST-")) else "alias",
    })


@chat_bp.route("/api/auth/csrf", methods=["GET"])
def api_auth_csrf():
    """Genera/retorna un token CSRF para el frontend.

    - Se guarda en la sesión (cookie) y se devuelve al cliente.
    - Solo se exige si `REQUIRE_CSRF=1` en el servidor.
    """
    from flask import session
    import secrets

    if not session.get("csrf_token"):
        session["csrf_token"] = secrets.token_urlsafe(32)

    return _ok({"csrf_token": session["csrf_token"]})
