"""
Proyecto: YELIA4AP
Archivo: backend/routes/admin_routes.py
Descripción: Módulo del backend para la lógica asociada a esta carpeta/funcionalidad.

Revisión: 2026-02-10
"""
from __future__ import annotations

"""
Archivo: backend/routes/admin_routes.py
Proyecto: YELIA4AP
Última revisión: 2026-02-10

Módulo de backend en Python.

Convenciones:
- Funciones pequeñas, nombres descriptivos y manejo de errores explícito.
- Evitar prints en producción: usar logging si aplica.
"""


#
# Archivo: backend/routes/admin_routes.py
# Rol: Módulo del backend (Flask) de YELIA4AP.


"""Admin Routes
Archivo del backend del sistema YELIA4AP.

Responsabilidad:
- Implementa la lógica asociada a este módulo.

backend/routes/admin_routes.py

Panel Administrador/Docente — YELIA

Objetivo:
- Gestionar usuarios (estudiantes) y cuentas (docentes/admin).
- Consultar actividad (temas buscados, chats, adjuntos, métricas).
- Mantener compatibilidad con ADMIN_TOKEN (acceso por header/query en dev)
  y agregar login por usuario/contraseña para roles "teacher/admin".

Notas de seguridad (entorno académico):
- En producción, usar HTTPS + auth real.
- Aquí se usa sesión Flask + password hash (Werkzeug).
"""


import os
import json
from typing import Any, Dict, Optional, List, Tuple

import structlog  # type: ignore
from flask import Blueprint, request, session
from backend.core.frontend import frontend_redirect
from werkzeug.security import generate_password_hash, check_password_hash

from ..db import db_session
from ..core.validation import validate_password, validate_username
from ..repositories import student_profile_repo
from .db_viewer_routes import _require_admin_or_teacher

logger = structlog.get_logger()

admin_bp = Blueprint("admin", __name__, url_prefix="")  # rutas /admin y /api/admin

# Token simple SOLO para DEV/LOCAL (no sustituye auth real)
# - Se toma de .env (ADMIN_TOKEN) para no hardcodear en código.
# - En producción/hosting, se recomienda desactivar este acceso.
DEV_FALLBACK_TOKEN = (os.getenv("DEV_FALLBACK_ADMIN_TOKEN") or "").strip()

# ============================================================
# Helpers de respuesta (contrato API unificado)
# ============================================================
from ..core.utils import ok as _ok_api, err as _err_api


def _ok(data: Dict[str, Any], status: int = 200):
    return _ok_api(data, status=status, code="OK")


def _err(message: str, status: int = 400, extra: Optional[Dict[str, Any]] = None, code: str = "ERROR"):
    extra = extra or {}
    return _err_api(message, status=status, code=code, **extra)


# ============================================================
# Paginación uniforme (limit/offset)
# ============================================================

def _get_pagination(default_limit: int = 50, max_limit: int = 200) -> tuple[int, int]:
    """Lee limit/offset de querystring y aplica límites seguros.

    - default_limit: usado si no se envía limit.
    - max_limit: techo duro para evitar cargas masivas.
    """
    raw_limit = request.args.get("limit")
    raw_offset = request.args.get("offset")

    try:
        limit = int(raw_limit) if raw_limit is not None else int(default_limit)
        offset = int(raw_offset) if raw_offset is not None else 0
    except Exception:
        limit, offset = int(default_limit), 0

    limit = max(1, min(int(limit), int(max_limit)))
    offset = max(0, int(offset))
    return limit, offset


# ============================================================
# Seguridad (compatibilidad: ADMIN_TOKEN + sesión por roles)
# ============================================================

def _env_is_dev() -> bool:
    env = (os.getenv("FLASK_ENV") or os.getenv("ENV") or "production").lower()
    return env in ("development", "dev", "local", "test", "testing")


def _get_token_candidate() -> str:
    # 1) Header (preferido)
    header = (request.headers.get("X-Admin-Token") or "").strip()
    if header:
        return header
    # 2) Querystring (solo dev/test)
    token = (request.args.get("token") or "").strip()
    return token


def _is_admin_token_valid() -> bool:
    """
    Valida token por:
      - ADMIN_TOKEN (si está configurado en entorno)
      - DEV_FALLBACK_ADMIN_TOKEN (solo en desarrollo/local/testing, si se define)
    """
    token = _get_token_candidate()
    if not token:
        return False

    token_env = (os.getenv("ADMIN_TOKEN") or "").strip()
    if token_env and token == token_env:
        return True

    # Fallback DEV (solo si NO configuraste ADMIN_TOKEN en el entorno)
    if _env_is_dev() and not token_env and DEV_FALLBACK_TOKEN and token == DEV_FALLBACK_TOKEN:
        return True

    return False


def _admin_role() -> str:
    return (session.get("admin_role") or "").strip().lower()


def _teacher_role() -> str:
    return (session.get("teacher_role") or "").strip().lower()


def _any_role() -> str:
    # Rol activo en cualquiera de los paneles (teacher/admin)
    return (_admin_role() or _teacher_role()).strip().lower()


def _any_username() -> str:
    return session.get("admin_username") or session.get("teacher_username") or ""


def _require_admin() -> Optional[Tuple[Any, int]]:
    """Protege endpoints SOLO admin por sesión y rol.

    - Acepta rol: admin.
    - (Opcional) fallback por token SOLO si ALLOW_ADMIN_TOKEN_FALLBACK=1.
      Útil para desarrollo/local y pruebas.
    """
    from backend.core.security import require_roles

    allow_token = (os.getenv("ALLOW_ADMIN_TOKEN_FALLBACK", "1").strip() == "1")

    if not require_roles("admin", allow_token=allow_token):
        return _err("Acceso denegado (solo admin).", 403, code="FORBIDDEN")

    return None


def _audit(action: str, target: Optional[str] = None, meta: Optional[Dict[str, Any]] = None) -> None:
    """Registra acciones administrativas para trazabilidad."""
    actor = _any_username() or ("token" if _is_admin_token_valid() else "unknown")
    try:
        with db_session() as conn:
            cur = conn.cursor()
            # Insertamos sólo columnas base y dejamos el resto con DEFAULT/NULL.
            cur.execute(
                "INSERT INTO audit_logs (actor, action, target, meta_json) VALUES (?, ?, ?, ?);",
                (str(actor), str(action), target, json.dumps(meta or {}, ensure_ascii=False)),
            )
            conn.commit()
    except Exception:
        logger.exception("audit_log_failed", action=action, target=target)


# ============================================================
# Utils: esquema SQLite (compatibilidad con BD vieja/nueva)
# ============================================================

def _table_columns(conn, table: str) -> set:
    cur = conn.cursor()
    cur.execute(f"PRAGMA table_info({table});")
    rows = cur.fetchall() or []
    # sqlite row puede ser tuple o dict; manejamos ambos
    cols = set()
    for r in rows:
        try:
            cols.add(r[1])
        except Exception:
            cols.add(r.get("name"))  # type: ignore
    return cols


def _table_exists(conn, table: str) -> bool:
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM sqlite_master WHERE type IN ('table','view') AND name = ? LIMIT 1;", (table,))
    return cur.fetchone() is not None


def _select_cols_with_fallback(table: str, want_cols: List[str], fallback_null: Optional[Dict[str, str]] = None) -> str:
    """Devuelve lista SELECT con fallback NULL AS col si no existe.

    - fallback_null: permite expresiones personalizadas por columna.
    """
    fallback_null = fallback_null or {}
    # Esta función se usa junto con _table_columns, así que el caller decide.
    # Aquí solo formateamos.
    out = []
    for c in want_cols:
        if c in fallback_null:
            out.append(fallback_null[c])
        else:
            out.append(c)
    return ", ".join(out)


# ============================================================
# VISTAS (HTML)
# ============================================================

@admin_bp.route("/admin")
def admin_page():
    """UI del Panel Administrador (solo admin)."""
    denied = _require_admin()
    if denied is not None:
        # UX: si no está autenticado, enviar al login (no renderizamos el panel aquí).
        # Esto hace que los botones de /launcher y /demo siempre tengan un comportamiento consistente.
        return frontend_redirect("/admin/login")
    return frontend_redirect("/admin")


@admin_bp.route("/admin/login")
def admin_login_page():
    """Página de login (alias).

    Si aún NO existe ningún admin, igualmente muestra el login y ofrece un
    acceso visible al Setup Wizard (/admin/setup).

    Motivo (UX):
    - Los botones de /launcher y /demo deben llevar siempre a una pantalla de
      login consistente.
    - El flujo de creación del primer admin vive en /admin/setup.
    """
    # Requerimiento demo/tribunal: NO auto-login por cookie; siempre mostrar login.
    return frontend_redirect("/admin/login")


# ============================================================
# Setup Wizard (primer admin) — Modo PRO
# ============================================================

def _any_admin_exists() -> bool:
    """Retorna True si existe al menos un usuario con rol 'admin' en la tabla accounts."""
    try:
        with db_session() as conn:
            cur = conn.cursor()
            cur.execute("SELECT 1 FROM accounts WHERE role = 'admin' LIMIT 1;")
            return cur.fetchone() is not None
    except Exception:
        logger.exception("admin_exists_check_failed")
        # En caso de duda, mejor asumir que existe para NO abrir setup accidentalmente
        return True


@admin_bp.route("/admin/setup")
def admin_setup_page():
    """
    Página de configuración inicial.

    Comportamiento:
    - Si NO existe ningún admin: permite crear el primer admin (requiere SETUP_TOKEN).
    - Si YA existe un admin: la página sigue siendo accesible (para documentación / hosting),
      pero el endpoint de creación del "primer admin" permanece bloqueado.
      La creación de administradores adicionales debe hacerse desde el Panel Admin (usuario autenticado).
    """
    admin_exists = _any_admin_exists()
    setup_token = os.getenv("SETUP_TOKEN", "").strip()
    setup_enabled = bool(setup_token)

    # Si es el primer setup, exigimos token configurado.
    if (not admin_exists) and (not setup_enabled):
        return ("Setup deshabilitado: falta SETUP_TOKEN en variables de entorno.", 403)

    return frontend_redirect("/admin/setup")


@admin_bp.route("/api/admin/setup/status", methods=["GET"])
def api_admin_setup_status():
    """Estado del primer arranque para que Next muestre el flujo correcto."""
    admin_exists = _any_admin_exists()
    setup_enabled = bool(os.getenv("SETUP_TOKEN", "").strip())
    return _ok({
        "adminExists": admin_exists,
        "noAdmin": not admin_exists,
        "setupEnabled": setup_enabled,
        "canCreateFirstAdmin": (not admin_exists) and setup_enabled,
    })


@admin_bp.route("/api/admin/setup", methods=["POST"])
def api_admin_setup_create_first_admin():
    """Crea o restablece el admin. Requiere SETUP_TOKEN."""
    setup_token = os.getenv("SETUP_TOKEN", "").strip()
    if not setup_token:
        return _err("Setup deshabilitado (SETUP_TOKEN no configurado).", 403)

    body = request.get_json(silent=True) or {}
    token = (body.get("token") or "").strip()
    username_raw = (body.get("username") or "admin").strip()
    email = (body.get("email") or "admin@yelia.local").strip() or None
    password = (body.get("password") or "").strip()

    if token != setup_token:
        return _err("Token inválido.", 401)
    username, username_error = validate_username(username_raw)
    if username_error:
        return _err(username_error, 400)
    password_error = validate_password(password, min_len=8, label="La contrasena del admin")
    if password_error:
        return _err(password_error, 400)

    pw_hash = generate_password_hash(password, method="pbkdf2:sha256", salt_length=16)

    try:
        with db_session() as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM accounts WHERE role = 'admin';")
            cur.execute(
                "INSERT INTO accounts (username, email, password_hash, role, status) VALUES (?, ?, ?, 'admin', 'active');",
                (username, email, pw_hash),
            )
            conn.commit()

        # No iniciar sesión automáticamente (requerimiento del usuario).
        _audit("admin.setup", target=username, meta={"email": email})
        return _ok({"message": "Administrador creado/restablecido. Inicia sesión para continuar.", "redirect": "/admin/login"}, 201)

    except Exception:
        logger.exception("admin_setup_create_failed")
        return _err("No se pudo crear o restablecer el administrador (¿username repetido?).", 400)


@admin_bp.route("/admin/db")
def db_viewer_page_shortcut():
    """Atajo: UI del visor de base de datos (solo admin)."""
    denied = _require_admin()
    if denied is not None:
        return frontend_redirect("/admin/login")
    return frontend_redirect("/admin/db")


# ============================================================
# AUTH (login por cuentas)
# ============================================================

@admin_bp.route("/api/admin/auth/login", methods=["POST"])
def api_admin_login():
    """Login para cuentas (docentes/admin)."""
    body = request.get_json(silent=True) or {}
    username = (body.get("username") or "").strip()
    password = (body.get("password") or "")

    if not username or not password:
        return _err("Faltan credenciales.", 400)

    with db_session() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, username, password_hash, role, status FROM accounts WHERE username = ?;",
            (username,),
        )
        row = cur.fetchone()

    if not row:
        return _err("Usuario o contraseña incorrectos.", 401)

    if (row["status"] or "").lower() != "active":
        return _err("Cuenta bloqueada.", 403)
    if (row["role"] or "").lower() != "admin":
        return _err("Esta cuenta no tiene permiso de administrador.", 403)

    # Evitar 500 por hashes no soportados (ej: scrypt)
    try:
        ok = check_password_hash(row["password_hash"], password)
    except ValueError:
        logger.exception("password_hash_unsupported")
        return _err(
            "Hash de contraseña incompatible. Reinstala dependencias o recrea la cuenta admin.",
            500,
        )

    if not ok:
        return _err("Usuario o contraseña incorrectos.", 401)

    session["admin_username"] = row["username"]
    session["admin_role"] = (row["role"] or "teacher").lower()
    session.permanent = True

    # touch last_seen
    try:
        with db_session() as conn:
            cur = conn.cursor()
            cur.execute(
                "UPDATE accounts SET last_seen = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP WHERE id = ?;",
                (row["id"],),
            )
            conn.commit()
    except Exception:
        logger.exception("accounts_last_seen_update_failed")

    _audit("auth.login", target=row["username"], meta={"role": session.get("admin_role")})
    
    print("INTENTANDO GUARDAR METRICS_EVENTS")
    
    try:
        with db_session(write=True) as conn:
            cur = conn.cursor()

            cur.execute("ALTER TABLE metrics_events ADD COLUMN IF NOT EXISTS event_type TEXT;")
            cur.execute("ALTER TABLE metrics_events ADD COLUMN IF NOT EXISTS usuario TEXT;")
            cur.execute("ALTER TABLE metrics_events ADD COLUMN IF NOT EXISTS path TEXT;")
            cur.execute("ALTER TABLE metrics_events ADD COLUMN IF NOT EXISTS meta_json TEXT;")
            cur.execute("ALTER TABLE metrics_events ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;")

            cur.execute(
                """
                INSERT INTO metrics_events (event_type, usuario, path, meta_json)
                VALUES (?, ?, ?, ?)
                """,
                ("auth.login", row["username"], "/api/admin/auth/login", '{"role":"admin"}'),
            )

        conn.commit()
    except Exception as e:
        print("ERROR METRICS_EVENTS:", e)
    
    return _ok({"message": "Login ok", "role": session.get("admin_role"), "username": row["username"]})


@admin_bp.route("/api/admin/auth/logout", methods=["POST"])
def api_admin_logout():
    u = session.get("admin_username")
    session.pop("admin_username", None)
    session.pop("admin_role", None)
    _audit("auth.logout", target=u)
    return _ok({"message": "Logout ok"})


@admin_bp.route("/api/admin/me", methods=["GET"])
def api_admin_me():
    # Solo la sesión del panel admin
    if _admin_role() == "admin":
        return _ok({"authenticated": True, "role": _admin_role(), "username": session.get("admin_username")})
    # Token válido solo si no hay sesión activa en ningún panel
    if not _any_role() and _is_admin_token_valid():
        return _ok({"authenticated": True, "role": "admin", "username": "token"})
    return _ok({"authenticated": False})


# ============================================================
# ACCOUNTS (docentes/admin)  — SOLO ADMIN
# ============================================================

@admin_bp.route("/api/admin/accounts", methods=["GET"])
def api_accounts_list():
    denied = _require_admin()
    if denied is not None:
        return denied

    q = (request.args.get("q") or "").strip().lower()
    status = (request.args.get("status") or "").strip().lower()
    role = (request.args.get("role") or "").strip().lower()

    limit, offset = _get_pagination(default_limit=50, max_limit=200)

    base_sql = "FROM accounts"
    select_sql = "SELECT id, username, email, role, status, created_at, last_seen, updated_at " + base_sql
    where = []
    params: List[Any] = []

    if q:
        where.append("(LOWER(username) LIKE ? OR LOWER(COALESCE(email,'')) LIKE ?)")
        params.extend([f"%{q}%", f"%{q}%"])
    if status:
        where.append("LOWER(status)=?")
        params.append(status)
    if role:
        where.append("LOWER(role)=?")
        params.append(role)

    count_sql = "SELECT COUNT(*) as cnt " + base_sql
    if where:
        where_sql = " WHERE " + " AND ".join(where)
        select_sql += where_sql
        count_sql += where_sql

    select_sql += " ORDER BY created_at DESC, id DESC LIMIT ? OFFSET ?;"

    with db_session() as conn:
        cur = conn.cursor()
        cur.execute(count_sql, tuple(params))
        total = int(cur.fetchone()[0] or 0)

        cur.execute(select_sql, tuple(params) + (limit, offset))
        rows = [dict(r) for r in cur.fetchall()]

    return _ok(
        {
            "accounts": rows,
            "items": rows,
            "total": total,
            "total_accounts": total,
            "limit": limit,
            "offset": offset,
            "has_more": bool(offset + len(rows) < total),
        }
    )


@admin_bp.route("/api/admin/accounts", methods=["POST"])
def api_accounts_create():
    denied = _require_admin()
    if denied is not None:
        return denied

    body = request.get_json(silent=True) or {}
    username_raw = (body.get("username") or "").strip()
    password = (body.get("password") or "").strip()
    email = (body.get("email") or "").strip() or None
    role = ((body.get("role") or "teacher").strip().lower())

    username, username_error = validate_username(username_raw)
    if username_error:
        return _err(username_error, 400)
    password_error = validate_password(password, min_len=8)
    if password_error:
        return _err(password_error, 400)
    if role not in ("teacher", "admin"):
        return _err("role inválido (teacher|admin).", 400)

    pw_hash = generate_password_hash(password, method="pbkdf2:sha256", salt_length=16)

    try:
        with db_session() as conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO accounts (username, email, password_hash, role, status) VALUES (?, ?, ?, ?, 'active');",
                (username, email, pw_hash, role),
            )
            conn.commit()
        _audit("account.create", target=username, meta={"role": role})
        return _ok({"message": "Cuenta creada."}, 201)
    except Exception:
        logger.exception("account_create_failed")
        return _err("No se pudo crear la cuenta (¿username repetido?).", 400)


@admin_bp.route("/api/admin/accounts/<int:account_id>", methods=["PATCH"])
def api_accounts_update(account_id: int):
    denied = _require_admin()
    if denied is not None:
        return denied

    body = request.get_json(silent=True) or {}
    fields = []
    params: List[Any] = []

    if "email" in body:
        fields.append("email = ?")
        params.append((body.get("email") or "").strip() or None)
    if "role" in body:
        role = ((body.get("role") or "").strip().lower())
        if role not in ("teacher", "admin"):
            return _err("role inválido (teacher|admin).", 400)
        fields.append("role = ?")
        params.append(role)
    if "status" in body:
        status = ((body.get("status") or "").strip().lower())
        if status not in ("active", "blocked"):
            return _err("status inválido (active|blocked).", 400)
        fields.append("status = ?")
        params.append(status)
    if "password" in body and (body.get("password") or "").strip():
        password_error = validate_password((body.get("password") or "").strip(), min_len=8)
        if password_error:
            return _err(password_error, 400)
        fields.append("password_hash = ?")
        params.append(
            generate_password_hash(
                (body.get("password") or "").strip(),
                method="pbkdf2:sha256",
                salt_length=16,
            )
        )

    if not fields:
        return _err("Nada que actualizar.", 400)

    fields.append("updated_at = CURRENT_TIMESTAMP")
    sql = f"UPDATE accounts SET {', '.join(fields)} WHERE id = ?;"
    params.append(account_id)

    with db_session() as conn:
        cur = conn.cursor()
        cur.execute(sql, tuple(params))
        conn.commit()

    _audit("account.update", target=str(account_id), meta={"fields": list(body.keys())})
    return _ok({"message": "Cuenta actualizada."})


@admin_bp.route("/api/admin/accounts/<int:account_id>", methods=["DELETE"])
def api_accounts_delete(account_id: int):
    denied = _require_admin()
    if denied is not None:
        return denied

    with db_session() as conn:
        cur = conn.cursor()
        cur.execute("SELECT username FROM accounts WHERE id = ?;", (account_id,))
        row = cur.fetchone()
        cur.execute("DELETE FROM accounts WHERE id = ?;", (account_id,))
        conn.commit()

    _audit("account.delete", target=(row["username"] if row else str(account_id)))
    return _ok({"message": "Cuenta eliminada."})


# ============================================================
# TEACHER REQUESTS (compatibilidad panel admin)
# ============================================================

@admin_bp.route("/api/admin/teacher-requests", methods=["GET"])
def api_teacher_requests_list():
    denied = _require_admin()
    if denied is not None:
        return denied

    q = (request.args.get("q") or "").strip().lower()
    limit, offset = _get_pagination(default_limit=50, max_limit=200)

    with db_session() as conn:
        if not _table_exists(conn, "teacher_requests"):
            return _ok({"requests": [], "items": [], "total": 0, "limit": limit, "offset": offset})

        cols = _table_columns(conn, "teacher_requests")
        select_cols = [c for c in ("id", "username", "email", "reason", "status", "created_at", "updated_at", "decided_by", "decided_at") if c in cols]
        if not select_cols:
            select_cols = ["id"]

        where = []
        params: List[Any] = []
        if q:
            searchable = [c for c in ("username", "email", "reason", "status") if c in cols]
            if searchable:
                where.append("(" + " OR ".join([f"LOWER(COALESCE({c},'')) LIKE ?" for c in searchable]) + ")")
                params.extend([f"%{q}%"] * len(searchable))

        where_sql = " WHERE " + " AND ".join(where) if where else ""
        cur = conn.cursor()
        cur.execute(f"SELECT COUNT(1) FROM teacher_requests{where_sql};", tuple(params))
        total = int(cur.fetchone()[0] or 0)
        cur.execute(
            f"""
            SELECT {", ".join(select_cols)}
            FROM teacher_requests{where_sql}
            ORDER BY id DESC
            LIMIT ? OFFSET ?;
            """,
            tuple(params + [limit, offset]),
        )
        rows = [dict(r) for r in cur.fetchall()]

    return _ok({"requests": rows, "items": rows, "total": total, "limit": limit, "offset": offset})


@admin_bp.route("/api/admin/teacher-requests/<int:request_id>/<action>", methods=["POST"])
def api_teacher_requests_decide(request_id: int, action: str):
    denied = _require_admin()
    if denied is not None:
        return denied

    action = (action or "").strip().lower()
    if action not in ("approve", "reject"):
        return _err("Accion invalida.", 400)

    with db_session() as conn:
        if not _table_exists(conn, "teacher_requests"):
            return _err("No hay tabla de solicitudes docentes configurada.", 404)

        cur = conn.cursor()
        cur.execute("SELECT id, username, email, password_hash, status FROM teacher_requests WHERE id = ?;", (request_id,))
        req = cur.fetchone()
        if not req:
            return _err("Solicitud no encontrada.", 404)
        if (req["status"] or "pending").lower() != "pending":
            return _err("La solicitud ya fue procesada.", 400)

        status = "approved" if action == "approve" else "rejected"
        if action == "approve":
            cur.execute("SELECT 1 FROM accounts WHERE username = ? LIMIT 1;", (req["username"],))
            if cur.fetchone():
                return _err("Ya existe una cuenta con ese usuario.", 400)
            cur.execute(
                "INSERT INTO accounts (username, email, password_hash, role, status) VALUES (?, ?, ?, 'teacher', 'active');",
                (req["username"], req["email"], req["password_hash"]),
            )
        cur.execute(
            "UPDATE teacher_requests SET status = ?, decided_by = ?, decided_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP WHERE id = ?;",
            (status, _any_username() or "admin", request_id),
        )
        conn.commit()

    _audit(f"teacher_request.{action}", target=str(request_id))
    return _ok({"message": "Solicitud actualizada.", "id": request_id, "status": status})


# ============================================================
# STUDENTS (usuarios + perfiles + progreso)
# ============================================================

def _calc_level(points: int) -> str:
    if points >= 200:
        return "Avanzado"
    if points >= 80:
        return "Intermedio"
    return "Inicial"


@admin_bp.route("/api/admin/students", methods=["GET", "POST"])
def api_students_list():
    denied = _require_admin_or_teacher()
    if denied is not None:
        return denied

    if request.method == "POST":
        body = request.get_json(silent=True) or {}

        alias = (body.get("alias") or "").strip()
        if not alias:
            return _err("Alias requerido.", 400)

        email = (body.get("email") or "").strip() or None
        status = ((body.get("status") or "active").strip().lower())
        if status not in ("active", "blocked"):
            return _err("status inválido (active|blocked).", 400)

        role = "student"

        try:
            with db_session() as conn:
                cur = conn.cursor()
                cur.execute(
                    "INSERT INTO usuarios (alias, email, role, status) VALUES (?,?,?,?);",
                    (alias, email, role, status),
                )
                new_id = cur.lastrowid
                conn.commit()
        except Exception:
            logger.exception("admin_create_student_failed", alias=alias)
            return _err("No se pudo crear el estudiante (alias duplicado o BD).", 400)

        _audit("student.create", target=alias, meta={"email": email})
        return _ok({"id": new_id, "alias": alias}, 201)

    q = (request.args.get("q") or "").strip().lower()
    limit, offset = _get_pagination(default_limit=50, max_limit=200)

    sort = (request.args.get("sort") or "created_at").strip().lower()
    direction = (request.args.get("dir") or "desc").strip().lower()
    if direction not in ("asc", "desc"):
        direction = "desc"
    sort_map = {
        "created_at": "u.created_at",
        "last_seen": "u.last_seen",
        "alias": "u.alias",
        "status": "u.status",
        "id": "u.id",
    }
    order_col = sort_map.get(sort, "u.created_at")

    sql = """
    SELECT
        u.id,
        u.alias,
        COALESCE(u.email,'') AS email,
        COALESCE(u.role,'student') AS role,
        COALESCE(u.status,'active') AS status,
        u.created_at,
        u.last_seen
    FROM usuarios u
    WHERE LOWER(COALESCE(u.role,'student')) IN ('student','estudiante')
    """
    params: List[Any] = []

    if q:
        sql += " AND (LOWER(u.alias) LIKE ? OR LOWER(COALESCE(u.email,'')) LIKE ?)"
        like = f"%{q}%"
        params.extend([like, like])

    count_sql = "SELECT COUNT(1) FROM (" + sql + ") x;"
    sql += f" ORDER BY {order_col} {direction.upper()} LIMIT ? OFFSET ?"
    params_paged = list(params) + [limit, offset]

    with db_session() as conn:
        cur = conn.cursor()
        cur.execute(count_sql, tuple(params))
        total = int(cur.fetchone()[0])

        cur.execute(sql, tuple(params_paged))
        rows = [dict(r) for r in cur.fetchall()]

    return _ok(
        {
            "students": rows,
            "items": rows,
            "total": total,
            "total_students": total,
            "limit": limit,
            "offset": offset,
            "has_more": bool(offset + len(rows) < total),
        }
    )


@admin_bp.route("/api/admin/students/<int:user_id>", methods=["PATCH"])
def api_students_update(user_id: int):
    denied = _require_admin_or_teacher()
    if denied is not None:
        return denied

    body = request.get_json(silent=True) or {}
    fields = []
    params: List[Any] = []

    if "alias" in body:
        alias = (body.get("alias") or "").strip()
        if not alias:
            return _err("Alias requerido.", 400)
        fields.append("alias = ?")
        params.append(alias)

    if "email" in body:
        fields.append("email = ?")
        params.append((body.get("email") or "").strip() or None)

    if "status" in body:
        status = ((body.get("status") or "").strip().lower())
        if status not in ("active", "blocked"):
            return _err("status inválido (active|blocked).", 400)
        fields.append("status = ?")
        params.append(status)

    if "role" in body:
        role = ((body.get("role") or "").strip().lower())
        if role not in ("student", "teacher", "admin"):
            return _err("role inválido (student|teacher|admin).", 400)
        fields.append("role = ?")
        params.append(role)

    if not fields:
        return _err("Nada que actualizar.", 400)

    fields.append("updated_at = CURRENT_TIMESTAMP")
    sql = f"UPDATE usuarios SET {', '.join(fields)} WHERE id = ?;"
    params.append(user_id)

    with db_session() as conn:
        cur = conn.cursor()
        cur.execute(sql, tuple(params))
        conn.commit()

    _audit("student.update", target=str(user_id), meta={"fields": list(body.keys())})
    return _ok({"message": "Usuario actualizado."})


@admin_bp.route("/api/admin/students/<int:user_id>", methods=["DELETE"])
def api_students_delete(user_id: int):
    denied = _require_admin_or_teacher()
    if denied is not None:
        return denied

    if _any_role() != "admin" and not _is_admin_token_valid():
        return _err("Solo un admin puede eliminar usuarios.", 403)

    try:
        with db_session(write=True) as conn:
            cur = conn.cursor()
            
            # 1. Verificar existencia del usuario
            cur.execute("SELECT alias, role FROM usuarios WHERE id = ?;", (user_id,))
            row = cur.fetchone()
            if not row:
                return _err("Estudiante no encontrado.", 404)
            
            alias = row["alias"]
            role = (row["role"] or "student").strip().lower()
            
            # 2. Bloquear eliminación si no es estudiante
            if role not in ("student", "estudiante"):
                return _err("No se permite eliminar administradores o docentes desde esta acción.", 403)
            
            # 3. Calcular variaciones del alias para borrar en cascada
            aliases_to_delete = {alias}
            if alias.startswith("STU-"):
                base = alias[4:]
                aliases_to_delete.add(base)
                aliases_to_delete.add(f"GUEST-{base}")
            elif alias.startswith("GUEST-"):
                base = alias[6:]
                aliases_to_delete.add(base)
                aliases_to_delete.add(f"STU-{base}")
            else:
                aliases_to_delete.add(f"STU-{alias}")
                aliases_to_delete.add(f"GUEST-{alias}")
            aliases_list = [a.lower() for a in aliases_to_delete]
            
            placeholders = ", ".join(["?"] * len(aliases_list))
            
            # 4. Eliminar registros de manera ordenada respetando llaves foráneas
            # a) interacciones (llave foránea directa: usuario_id REFERENCES usuarios(id))
            if _table_exists(conn, "interacciones"):
                cur.execute("DELETE FROM interacciones WHERE usuario_id = ?;", (user_id,))
            
            # b) metrics_events (llave foránea a conversaciones y mensajes en algunos esquemas, sin ON DELETE CASCADE)
            # Para evitar violar restricciones de FK, eliminamos metrics_events de este usuario primero.
            if _table_exists(conn, "metrics_events"):
                q_metrics = f"""
                    DELETE FROM metrics_events 
                    WHERE LOWER(usuario) IN ({placeholders})
                       OR conv_id IN (SELECT id FROM conversaciones WHERE LOWER(usuario) IN ({placeholders}));
                """
                cur.execute(q_metrics, tuple(aliases_list) + tuple(aliases_list))
                
            # c) Tablas de métricas adicionales
            for tbl in ("metrics_feedback", "metrics_perf", "metrics_recommendations", "metrics_adaptive_feedback", "diagnostic_attempts", "learning_routes", "progreso"):
                if _table_exists(conn, tbl):
                    cur.execute(f"DELETE FROM {tbl} WHERE LOWER(usuario) IN ({placeholders});", tuple(aliases_list))
                    
            # d) student_profiles
            if _table_exists(conn, "student_profiles"):
                cur.execute(f"DELETE FROM student_profiles WHERE LOWER(student_id) IN ({placeholders});", tuple(aliases_list))
                
            # e) quizzes, attachments y messages que referencian a conversaciones/mensajes del usuario
            if _table_exists(conn, "structured_quizzes"):
                q_quizzes = f"""
                    DELETE FROM structured_quizzes 
                    WHERE LOWER(usuario) IN ({placeholders})
                       OR conv_id IN (SELECT id FROM conversaciones WHERE LOWER(usuario) IN ({placeholders}));
                """
                cur.execute(q_quizzes, tuple(aliases_list) + tuple(aliases_list))
                
            if _table_exists(conn, "attachments"):
                q_attachments = f"""
                    DELETE FROM attachments 
                    WHERE LOWER(usuario) IN ({placeholders})
                       OR conv_id IN (SELECT id FROM conversaciones WHERE LOWER(usuario) IN ({placeholders}));
                """
                cur.execute(q_attachments, tuple(aliases_list) + tuple(aliases_list))
                
            if _table_exists(conn, "messages"):
                q_messages = f"""
                    DELETE FROM messages 
                    WHERE LOWER(usuario) IN ({placeholders})
                       OR conv_id IN (SELECT id FROM conversaciones WHERE LOWER(usuario) IN ({placeholders}));
                """
                cur.execute(q_messages, tuple(aliases_list) + tuple(aliases_list))
                
            # f) conversaciones
            if _table_exists(conn, "conversaciones"):
                cur.execute(f"DELETE FROM conversaciones WHERE LOWER(usuario) IN ({placeholders});", tuple(aliases_list))
                
            # g) Finalmente, eliminar de la tabla principal usuarios
            cur.execute("DELETE FROM usuarios WHERE id = ?;", (user_id,))
            
        # Auditoría fuera de la transacción para mantener el historial
        _audit("student.delete", target=(alias or str(user_id)))
        return _ok({"message": f"Estudiante '{alias}' y sus datos asociados eliminados correctamente."})
        
    except Exception as e:
        logger.exception("student_delete_failed", user_id=user_id)
        return _err(f"Error inesperado al intentar eliminar el estudiante: {str(e)}", 500)


@admin_bp.route("/api/admin/students/<alias>/activity", methods=["GET"])
def api_student_activity(alias: str):
    """Actividad agregada del estudiante.

    ✅ Compatible con BD vieja/nueva:
    - Si falta columna `tema` en interacciones/metrics/messages, devuelve NULL.
    - attachments: usa conv_id (no conversation_id).
    - Usuario puede estar guardado como "STU-<alias>" o "<alias>".
    """
    denied = _require_admin_or_teacher()
    if denied is not None:
        return denied

    alias = (alias or "").strip()
    if not alias:
        return _err("Alias inválido.", 400)

    stu_usuario = f"STU-{alias}"

    # --------------------------------------------------------
    # Teacher UX: incluir sesiones anónimas (Anon-*) en el panel
    # --------------------------------------------------------
    # Problema típico en demos: el chat público (/chat) guarda como Anon-xxxx,
    # mientras que el docente selecciona un estudiante (STU-alias). Para que
    # el panel docente no quede "vacío", permitimos incluir anónimos.
    #
    # - Si el frontend envía ?include_anon=1 -> se incluyen.
    # - Si NO envía nada y el usuario está en sesión docente -> se incluyen.
    # - El panel admin (sesión admin pura) no cambia su comportamiento.
    include_anon_param = (request.args.get("include_anon") or "").strip().lower()
    include_anon = include_anon_param in ("1", "true", "yes", "y", "on")
    if not include_anon:
        include_anon = bool((session.get("teacher_role") or "").strip())
    with db_session() as conn:
        cur = conn.cursor()

        # -------------------------
        # Interacciones
        # -------------------------
        inter_cols = _table_columns(conn, "interacciones")
        # Columnas deseadas
        want_inter = ["id", "pregunta"]
        # tema puede no existir
        if "tema" in inter_cols:
            want_inter.append("tema")
            tema_expr = "tema"
        else:
            want_inter.append("tema")
            tema_expr = "NULL AS tema"
        want_inter.append("created_at")

        cur.execute(
            f"""
            SELECT id,
                   pregunta,
                   {tema_expr},
                   created_at
            FROM interacciones
            WHERE usuario_id = (SELECT id FROM usuarios WHERE alias = ?)
            ORDER BY created_at DESC
            LIMIT 200;
            """,
            (alias,),
        )
        inter = [dict(r) for r in cur.fetchall()]

        # -------------------------
        # Conversaciones
        # -------------------------
        cur.execute(
            """
            SELECT c.id,
                   COALESCE(c.titulo,'') AS title,
                   c.created_at,
                   COALESCE((SELECT MAX(created_at) FROM messages m WHERE m.conv_id = c.id), c.created_at) AS updated_at,
                   COALESCE(c.focus_topic,'') AS focus_topic
            FROM conversaciones c
            WHERE (LOWER(c.usuario) IN (LOWER(?), LOWER(?))
               OR (? = 1 AND LOWER(c.usuario) LIKE 'anon-%'))
            ORDER BY updated_at DESC
            LIMIT 50;
            """,
            (alias, stu_usuario, 1 if include_anon else 0),
        )
        convs = [dict(r) for r in cur.fetchall()]

        # -------------------------
        # Adjuntos (conv_id)
        # -------------------------
        cur.execute(
            """
            SELECT id, original_name, mime, size_bytes, created_at, url, conv_id, COALESCE(usuario,'') AS owner
            FROM attachments
            WHERE (LOWER(usuario) IN (LOWER(?), LOWER(?))
               OR (? = 1 AND LOWER(usuario) LIKE 'anon-%'))
            ORDER BY created_at DESC
            LIMIT 100;
            """,
            (alias, stu_usuario, 1 if include_anon else 0),
        )
        atts = [dict(r) for r in cur.fetchall()]

        # -------------------------
        # Métricas (schema-aware)
        # -------------------------
        mcols = _table_columns(conn, "metrics_events")

        # tema puede faltar; confusion_detectada puede faltar
        tema_expr = "tema" if "tema" in mcols else "NULL AS tema"
        confusion_expr = "confusion_detectada" if "confusion_detectada" in mcols else "NULL AS confusion_detectada"
        nivel_expr = "nivel_detectado" if "nivel_detectado" in mcols else None
        quality_expr = "quality_score" if "quality_score" in mcols else None

        select_parts = ["id", "created_at", "usuario", tema_expr]
        if nivel_expr:
            select_parts.append(nivel_expr)
        select_parts.append(confusion_expr)
        if quality_expr:
            select_parts.append(quality_expr)

        cur.execute(
            f"""
            SELECT {", ".join(select_parts)}
            FROM metrics_events
            WHERE (LOWER(usuario) IN (LOWER(?), LOWER(?))
               OR (? = 1 AND LOWER(usuario) LIKE 'anon-%'))
            ORDER BY created_at DESC
            LIMIT 200;
            """,
            (alias, stu_usuario, 1 if include_anon else 0),
        )
        mevents = [dict(r) for r in cur.fetchall()]

    return _ok(
        {
            "alias": alias,
            "include_anon": bool(include_anon),
            "interacciones": inter,
            "conversaciones": convs,
            "attachments": atts,
            "metrics_events": mevents,
        }
    )


# ============================================================
# Global: Chats (conversaciones) y Adjuntos
# ============================================================

@admin_bp.route("/api/admin/chats", methods=["GET"])
def api_admin_chats_global():
    denied = _require_admin_or_teacher()
    if denied is not None:
        return denied

    q = (request.args.get("q") or "").strip().lower()
    student = (request.args.get("student") or "").strip()

    try:
        days = int(request.args.get("days") or 0)
    except Exception:
        days = 0
    days = max(0, min(days, 365))

    limit = int(request.args.get("limit") or 25)
    offset = int(request.args.get("offset") or 0)
    limit = max(1, min(limit, 200))
    offset = max(0, offset)

    sort = (request.args.get("sort") or "id").strip().lower()
    direction = (request.args.get("dir") or "desc").strip().lower()
    if direction not in ("asc", "desc"):
        direction = "desc"
    sort_map = {
        "id": "c.id",
        "created_at": "c.created_at",
        "updated_at": "updated_at",
        "usuario": "c.usuario",
        "title": "c.titulo",
    }
    order_col = sort_map.get(sort, "c.id")

    where_sql = ""
    params: List[Any] = []
    where = []
    if q:
        where.append("(LOWER(COALESCE(c.usuario,'')) LIKE ? OR LOWER(COALESCE(c.titulo,'')) LIKE ?)")
        like = f"%{q}%"
        params.extend([like, like])
    if student:
        where.append("LOWER(COALESCE(c.usuario,'')) = LOWER(?)")
        params.append(student)
    if days and days > 0:
        where.append("datetime(c.created_at) >= datetime('now', ?)")
        params.append(f"-{days} days")

    if where:
        where_sql = " WHERE " + " AND ".join(where)

    with db_session() as conn:
        cur = conn.cursor()
        cur.execute(f"SELECT COUNT(*) AS n FROM conversaciones c{where_sql};", params)
        total = int(cur.fetchone()["n"])

        cur.execute(
            f"""
            SELECT
                c.id,
                c.usuario,
                c.titulo AS title,
                c.created_at,
                (
                    SELECT m.tema
                    FROM messages m
                    WHERE m.conv_id = c.id
                      AND COALESCE(m.tema, '') <> ''
                    ORDER BY m.created_at DESC, m.id DESC
                    LIMIT 1
                ) AS topic,
                COALESCE((SELECT MAX(m.created_at) FROM messages m WHERE m.conv_id = c.id), c.created_at) AS updated_at
            FROM conversaciones c{where_sql}
            ORDER BY {order_col} {direction.upper()}
            LIMIT ? OFFSET ?;
            """,
            params + [limit, offset],
        )
        rows = [dict(r) for r in cur.fetchall()]

    return _ok({"rows": rows, "total": total, "limit": limit, "offset": offset})


@admin_bp.route("/api/admin/attachments", methods=["GET"])
def api_admin_attachments_global():
    denied = _require_admin_or_teacher()
    if denied is not None:
        return denied

    q = (request.args.get("q") or "").strip().lower()
    student = (request.args.get("student") or "").strip()
    try:
        days = int(request.args.get("days") or 0)
    except Exception:
        days = 0
    days = max(0, min(days, 365))

    limit = int(request.args.get("limit") or 25)
    offset = int(request.args.get("offset") or 0)
    limit = max(1, min(limit, 200))
    offset = max(0, offset)

    sort = (request.args.get("sort") or "id").strip().lower()
    direction = (request.args.get("dir") or "desc").strip().lower()
    if direction not in ("asc", "desc"):
        direction = "desc"
    sort_map = {
        "id": "id",
        "created_at": "created_at",
        "size_bytes": "size_bytes",
        "usuario": "usuario",
        "original_name": "original_name",
    }
    order_col = sort_map.get(sort, "id")

    where_sql = ""
    params: List[Any] = []
    where = []
    if q:
        where.append("(LOWER(COALESCE(usuario,'')) LIKE ? OR LOWER(COALESCE(original_name,'')) LIKE ? OR LOWER(COALESCE(mime,'')) LIKE ?)")
        like = f"%{q}%"
        params.extend([like, like, like])
    if student:
        where.append("LOWER(COALESCE(usuario,'')) = LOWER(?)")
        params.append(student)
    if days and days > 0:
        where.append("datetime(created_at) >= datetime('now', ?)")
        params.append(f"-{days} days")
    if where:
        where_sql = " WHERE " + " AND ".join(where)

    with db_session() as conn:
        cur = conn.cursor()
        cur.execute(f"SELECT COUNT(*) AS n FROM attachments{where_sql};", params)
        total = int(cur.fetchone()["n"])
        cur.execute(
            f"""
            SELECT id, created_at, usuario, conv_id, original_name, stored_name, mime, size_bytes, sha256, url
            FROM attachments{where_sql}
            ORDER BY {order_col} {direction.upper()}
            LIMIT ? OFFSET ?;
            """,
            params + [limit, offset],
        )
        rows = [dict(r) for r in cur.fetchall()]

    return _ok({"rows": rows, "total": total, "limit": limit, "offset": offset})


# ============================================================
# Perfil avanzado del estudiante (student_profiles.profile_json)
# ============================================================

@admin_bp.route("/api/admin/students/<alias>/profile", methods=["GET"])
def api_student_profile_get(alias: str):
    denied = _require_admin_or_teacher()
    if denied is not None:
        return denied

    profile = student_profile_repo.get_profile(alias)
    return _ok({"profile": profile})


@admin_bp.route("/api/admin/students/<alias>/profile", methods=["PATCH"])
def api_student_profile_patch(alias: str):
    denied = _require_admin_or_teacher()
    if denied is not None:
        return denied

    payload = request.get_json(silent=True) or {}
    if not isinstance(payload, dict):
        return _err("Body inválido (JSON).", 400)

    current = student_profile_repo.get_profile(alias)

    allowed = {"level_current", "course", "tags", "notes", "goals"}
    updates = {k: payload.get(k) for k in payload.keys() if k in allowed}

    if "tags" in updates:
        tags = updates.get("tags")
        if isinstance(tags, str):
            tags = [t.strip() for t in tags.split(",") if t.strip()]
        if tags is None:
            tags = []
        if not isinstance(tags, list):
            return _err("tags debe ser lista o texto separado por comas.", 400)
        tags = [str(t).strip() for t in tags if str(t).strip()]
        updates["tags"] = tags

    if "goals" in updates:
        goals = updates.get("goals")
        if isinstance(goals, str):
            goals = [g.strip() for g in goals.splitlines() if g.strip()]
        if goals is None:
            goals = []
        if not isinstance(goals, list):
            return _err("goals debe ser lista o texto multilinea.", 400)
        goals = [str(g).strip() for g in goals if str(g).strip()]
        updates["goals"] = goals

    if "level_current" in updates and updates["level_current"] is not None:
        lvl = str(updates["level_current"]).strip().lower()
        if lvl not in {"basico", "intermedio", "avanzado"}:
            return _err("level_current inválido (basico/intermedio/avanzado).", 400)
        updates["level_current"] = lvl

    merged = dict(current or {})
    merged.update({k: v for k, v in updates.items()})

    student_profile_repo.save_profile(alias, merged)
    _audit("student.profile.update", target=alias)
    return _ok({"message": "Perfil actualizado.", "profile": student_profile_repo.get_profile(alias)})


# ============================================================
# Detalle de conversación (mensajes)
# ============================================================

@admin_bp.route("/api/admin/conversations/<int:conv_id>/messages", methods=["GET"])
def api_admin_conversation_messages(conv_id: int):
    denied = _require_admin_or_teacher()
    if denied is not None:
        return denied

    limit, offset = _get_pagination(default_limit=200, max_limit=500)

    with db_session() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM conversaciones WHERE id = ?;", (conv_id,))
        conv = cur.fetchone()
        if not conv:
            return _err("Conversación no encontrada.", 404)

        cur.execute("SELECT COUNT(*) AS n FROM messages WHERE conv_id = ?;", (conv_id,))
        total_messages = int(cur.fetchone()[0] or 0)

        # Schema-aware: messages.tema puede faltar
        mcols = _table_columns(conn, "messages")
        tema_expr = "tema" if "tema" in mcols else "NULL AS tema"

        cur.execute(
            f"""
            SELECT id, remitente, contenido, {tema_expr}, created_at
            FROM messages
            WHERE conv_id = ?
            ORDER BY id ASC
            LIMIT ? OFFSET ?;
            """,
            (conv_id, limit, offset),
        )
        msgs = [dict(r) for r in cur.fetchall()]

    return _ok(
        {
            "conversation": dict(conv),
            "messages": msgs,
            "total_messages": total_messages,
            "limit": limit,
            "offset": offset,
            "has_more": bool(offset + len(msgs) < total_messages),
        }
    )


# ============================================================
# Auditoría (solo admin)
# ============================================================

@admin_bp.route("/api/admin/audit", methods=["GET"])
def api_admin_audit():
    denied = _require_admin()
    if denied is not None:
        return denied

    q = (request.args.get("q") or "").strip().lower()
    action = (request.args.get("action") or "").strip().lower()
    actor = (request.args.get("actor") or "").strip().lower()

    try:
        limit = int(request.args.get("limit") or 50)
        offset = int(request.args.get("offset") or 0)
    except Exception:
        limit, offset = 50, 0

    limit = max(1, min(limit, 200))
    offset = max(0, offset)

    base_sql = """
    SELECT id, created_at, actor, action, target, meta_json
    FROM audit_logs
    WHERE 1=1
    """
    params: List[Any] = []
    if q:
        base_sql += " AND (LOWER(COALESCE(actor,'')) LIKE ? OR LOWER(COALESCE(action,'')) LIKE ? OR LOWER(COALESCE(target,'')) LIKE ?)"
        like = f"%{q}%"
        params.extend([like, like, like])
    if action:
        base_sql += " AND LOWER(COALESCE(action,'')) = ?"
        params.append(action)
    if actor:
        base_sql += " AND LOWER(COALESCE(actor,'')) = ?"
        params.append(actor)

    count_sql = "SELECT COUNT(1) FROM (" + base_sql + ") x;"
    sql = base_sql + " ORDER BY id DESC LIMIT ? OFFSET ?"
    params_count = list(params)
    params.extend([limit, offset])

    with db_session() as conn:
        cur = conn.cursor()
        cur.execute(count_sql, tuple(params_count))
        total = int(cur.fetchone()[0])
        cur.execute(sql, tuple(params))
        rows = [dict(r) for r in cur.fetchall()]

    for r in rows:
        mj = r.get("meta_json")
        if mj:
            try:
                r["meta"] = json.loads(mj)
            except Exception:
                r["meta"] = mj
        else:
            r["meta"] = None

    return _ok({"items": rows, "total": total, "limit": limit, "offset": offset})
