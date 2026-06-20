"""
Proyecto: YELIA4AP
Archivo: backend/routes/chat_routes.py
Descripción: Módulo del backend para la lógica asociada a esta carpeta/funcionalidad.

Revisión: 2026-02-10
"""
"""Chat Routes
Archivo del backend del sistema YELIA4AP.

Responsabilidad:
- Implementa la lógica asociada a este módulo.
"""

#
# Archivo: backend/routes/chat_routes.py
# Rol: Módulo del backend (Flask) de YELIA4AP.

"""backend/routes/chat_routes.py

Backend Flask — YELIA (módulo de servidor)

Propósito:
    Este archivo pertenece al backend (Flask) de YELIA. Contiene lógica de servidor
    y/o utilidades que soportan rutas, servicios, persistencia y orquestación NLP.
Responsabilidades:
    - Definir el controlador HTTP principal del sistema de chat.
    - Servir la UI y exponer la API consumida por el frontend.
Diseño:
    - Validación y normalización en la capa de rutas.
    - Orquestación de negocio delegada a la capa services.
    - Persistencia controlada mediante db_session (repositorio/db layer).
    - Rate limiting por endpoint para proteger el backend.
Notas:
    - Las métricas se movieron a metrics_routes.py para mantener rutas limpias.
"""

# ============================================================
# PROPÓSITO:
#   Este módulo define el “controlador HTTP” principal del sistema de chat.
#
# RESPONSABILIDADES:
#   - Servir la UI: "/" -> index.html
#   - Exponer la API que consume el frontend:
#       /api/chat, /api/history, /api/conversation/<id>, /api/temas,
#       /api/progreso, /api/update-profile, auth endpoints, rename/delete
#
# PRINCIPIOS DE DISEÑO APLICADOS:
#   - Validación y normalización en la capa de rutas
#   - Orquestación de negocio delegada a la capa services
#   - Persistencia controlada mediante db_session (repositorio/db layer)
#   - Rate limiting por endpoint para proteger el backend
#
#   Las métricas se movieron a metrics_routes.py para mantener rutas limpias.
# ============================================================

from typing import Dict, Any, Optional
import os
import re
import time
import uuid
import hashlib
from pathlib import Path

from werkzeug.utils import secure_filename
from flask import Blueprint, jsonify, request, session, Response, redirect
from backend.core.frontend import frontend_redirect, frontend_url
from backend.core.security import require_staff_or_token
import structlog


from backend.db.session import (
    db_session,
    obtener_conversaciones_usuario,
    obtener_mensajes_conversacion,
)

from backend.repositories.metrics_repo import log_event, log_perf
from backend.repositories.attachments_repo import save_attachment
from backend.config import MAX_MESSAGE_LENGTH  # Límite operativo (demo/hosting)

# ✅ SOLO UNA puerta: routes -> chat_service (orquestador)
# Esto garantiza que toda la lógica de negocio de chat esté centralizada.
from backend.services.chat_service import procesar_mensaje_chat

from backend.services.progreso_service import (
    obtener_usuario_actual,
    cargar_progreso,
    actualizar_progreso,
    actualizar_perfil_usuario,
)

from backend.services.temas_service import cargar_temas, TEMAS_DISPONIBLES


# Logger estructurado para auditoría, debugging y observabilidad
logger = structlog.get_logger()

# Blueprint principal del chat (agrupa UI + APIs de chat)
chat_bp = Blueprint("chat", __name__)

# ------------------------------------------------------------
# RATE LIMITING (Protección contra abuso)
# ------------------------------------------------------------
# - key_func: identifica al cliente por IP
# - storage_uri: permite backend configurable (memory, redis, etc.)
# Rate limiter global (centralizado)
from ..core.rate_limit import limiter

# ---------------------------------------------------------------------------
# NOTAS DE MANTENIMIENTO
# - Se detectaron imports potencialmente no usados (uuid/hashlib/secure_filename,
#   y algunos helpers de db/attachments). No se eliminan aquí para evitar romper
#   flujos que dependan de imports por efectos laterales o cambios futuros.
# - Si en una limpieza futura se confirma que no se usan, puede removerse sin
#   afectar la lógica (solo reduce ruido).
# ---------------------------------------------------------------------------



def cargar_dependencias_iniciales() -> None:
    """
    Carga dependencias/catálogos en memoria al arrancar el backend.

    En este caso:
    - temas.json se precarga para que /api/temas y el NLP
      respondan más rápido y de forma consistente.

    Diseño defensivo:
    - Si falla, el backend no se cae (solo loguea).
    """
    try:
        cargar_temas()
    except Exception as e:
        logger.error("No se pudo cargar temas al iniciar", error=str(e))


# ------------------------------------------------------------
# HELPERS DE RESPUESTA (estándar JSON)
# ------------------------------------------------------------
# En core/utils.py ya hay ok/err; este módulo mantiene los suyos
# por compatibilidad/formato y para incluir "data" automáticamente.

def _ok(payload: Dict[str, Any], status: int = 200):
    """Respuesta JSON exitosa estándar.

    - Siempre incluye ok=True
    - Asegura la clave data con un payload resumido

    Args:
        payload: Contenido JSON adicional a incluir en la respuesta.
        status: Código HTTP asociado a la respuesta.

    Returns:
        Resultado de la operación.
    """
    payload = dict(payload or {})
    payload["ok"] = True
    if "data" not in payload:
        payload["data"] = {k: v for k, v in payload.items() if k not in ("ok", "data")}
    return jsonify(payload), status


def _err(message: str, status: int = 400, code: str = "ERROR", extra: Optional[Dict[str, Any]] = None):
    """Respuesta JSON de error estándar.

    - ok=False
    - error: mensaje user-facing
    - code: código interno para clasificación
    - data: None (contrato consistente)

    Args:
        message: Mensaje principal del error.
        status: Código HTTP asociado a la respuesta.
        code: Código interno opcional de clasificación.
        extra: Parámetro de entrada.

    Returns:
        Resultado de la operación.
    """
    payload: Dict[str, Any] = {"ok": False, "error": message, "code": code, "data": None}
    if extra:
        payload.update(extra)
    return jsonify(payload), status


def _validate_chat_payload(data: Dict[str, Any]) -> Dict[str, Any]:
    """Valida y normaliza el payload de /api/chat.

    Reglas:
    - message debe ser string y no vacío (tras normalizar espacios)
    - limita longitud máxima por env var (CHAT_MAX_MESSAGE_LEN)
    - conversation_id puede venir como int o string numérico
    - titulo es opcional, pero si viene debe ser string no vacío

    Retorna:
    - {"ok": True, ...campos normalizados...}
    - {"ok": False, "error": "..."} si no es válido

    Args:
        data: Parámetro de entrada.

    Returns:
        Valor retornado por la función.
    """
    mensaje_raw = data.get("message")
    if not isinstance(mensaje_raw, str):
        return {"ok": False, "error": "El campo 'message' debe ser texto."}

    # Normalización: colapsa espacios múltiples para estabilidad del input
    mensaje = mensaje_raw.strip()
    if not mensaje:
        return {"ok": False, "error": "El mensaje no puede estar vacío."}

    max_len = max(int(os.getenv("CHAT_MAX_MESSAGE_LEN", str(MAX_MESSAGE_LENGTH))), MAX_MESSAGE_LENGTH)
    if len(mensaje) > max_len:
        return {"ok": False, "error": f"El mensaje es demasiado largo (máx. {max_len} caracteres)."}

    conv_id_raw = data.get("conversation_id")
    conv_id: Optional[int] = None
    if isinstance(conv_id_raw, int):
        conv_id = conv_id_raw
    elif isinstance(conv_id_raw, str) and conv_id_raw.isdigit():
        conv_id = int(conv_id_raw)

    titulo_raw = data.get("titulo")
    titulo = titulo_raw.strip() if isinstance(titulo_raw, str) and titulo_raw.strip() else None

    return {"ok": True, "message": mensaje, "conversation_id": conv_id, "titulo": titulo}


# ---------------------------
# UI
# ---------------------------
@chat_bp.route("/", methods=["GET"])
def index():
    """
    Página inicial (home).

    Decisión de UX (tesis):
    - La entrada principal del sistema es el selector de roles para la tesis.
    - El chat y launcher siguen disponibles como accesos directos.

    Configuración:
    - HOME_PAGE=portal    -> redirige al portal de roles (default)
    - HOME_PAGE=launcher  -> redirige a /launcher
    - HOME_PAGE=chat      -> redirige a /chat
    """
    home = (os.getenv("HOME_PAGE") or "portal").strip().lower()
    if home == "chat":
        return frontend_redirect("/chat")
    elif home == "launcher":
        return frontend_redirect("/launcher")
    return frontend_redirect("/")


@chat_bp.route("/chat", methods=["GET"], strict_slashes=False)
def chat_ui():
    """
    UI del chat sin redirección.
    Útil cuando DEMO_HOME=1 (porque "/" redirige al launcher).
    """
    return frontend_redirect("/chat")


@chat_bp.route("/launcher", methods=["GET"], strict_slashes=False)
def launcher():
    """
    HUB de inicio (local/hosting): una sola pantalla con accesos.
    """
    return frontend_redirect("/launcher")

@chat_bp.route("/demo", methods=["GET"])
def demo_page():
    """
    Página de accesos rápidos para DEMO (tribunal/profesor).

    Seguridad:
    - En producción, esta vista NO debe estar abierta al usuario final.
    - Se exige sesión de personal (admin/docente) o ADMIN_TOKEN (solo soporte dev/local).
    - Se puede deshabilitar por completo con DISABLE_DEMO=1.
    """
    if (os.getenv("DISABLE_DEMO") or "0").strip() == "1":
        return "No encontrado.", 404

    # --------------------------------------------------------
    # UX (local/dev): permitir abrir /demo sin login
    #
    # En el entorno local (127.0.0.1 / localhost) el botón
    # "Presentación" debe funcionar sin requerir sesión.
    # En producción se mantiene protegido por sesión o token.
    # --------------------------------------------------------
    env = (os.getenv("FLASK_ENV") or os.getenv("ENV") or "production").lower().strip()
    host = (request.host or "").lower()
    is_local = any(x in host for x in ("127.0.0.1", "localhost"))

    if env in ("development", "dev", "local", "test", "testing") or is_local:
        return frontend_redirect("/demo")

    if not require_staff_or_token():
        # No filtramos info de módulos internos en caso de acceso no autorizado.
        return frontend_redirect("/launcher")

    return frontend_redirect("/demo")


# ---------------------------
# API: Temas (informativo)
# ---------------------------
@chat_bp.route("/api/temas", methods=["GET"])
@limiter.limit(os.getenv("RATE_LIMIT_TEMAS", "60 per minute"))
def api_temas():
    """
    Devuelve la lista de temas educativos disponibles.

    Nota:
    - Endpoint informativo (no requiere usuario/conv_id).
    - Incluye métricas de performance best-effort para el dashboard.
    """
    perf_start = time.perf_counter()
    try:
        temas = cargar_temas()
        if temas is None:
            temas = []
        return _ok({"temas": temas, "total": len(temas)})
    finally:
        # PERF + EVENTO: best-effort (no debe romper el endpoint)
        try:
            latency_ms = round((time.perf_counter() - perf_start) * 1000.0, 1)
            log_perf(
                usuario="",
                conversation_id=None,
                endpoint="/api/temas",
                latency_ms=latency_ms,
            )
            log_event(
                usuario="",
                conversation_id=None,
                event_type="temas_listed",
                dominio_status=None,
                modo_interaccion=None,
                intencion=None,
                tema=None,
                confusion_detectada=False,
            )
        except Exception:
            pass


# ---------------------------
# API: Auth mínimo
# ---------------------------
# (Los endpoints están modularizados en submódulos importados abajo)


# ============================================================================
# IMPORTACIÓN DE SUBMÓDULOS (registro de endpoints)
# ----------------------------------------------------------------------------
# Importar estos módulos es intencional: al importarlos, sus decoradores
# `@chat_bp.route(...)` se ejecutan y registran los endpoints en el mismo
# Blueprint, manteniendo:
#   - mismas URLs
#   - mismos nombres de funciones
#   - mismo comportamiento
# ============================================================================
from . import chat_routes_auth  # noqa: F401
from . import chat_routes_conversations  # noqa: F401
from . import chat_routes_chat  # noqa: F401
from . import diagnostic_routes  # noqa: F401
from . import learning_routes  # noqa: F401

@chat_bp.get("/api/demo/links")
def api_demo_links():
    """Dev/demo helper: returns important local links for presentation."""
    base = frontend_url("/").rstrip("/")
    links = {
        "base": base,
        "chat": f"{base}/chat",
        "demo": f"{base}/demo",
        "admin_login": f"{base}/admin/login",
        "admin_panel": f"{base}/admin",
        "teacher_login": f"{base}/teacher/login",
        "teacher_panel": f"{base}/teacher",
        "metrics": f"{base}/metricas",
        "db_viewer": f"{base}/db",
        "swagger_ui": f"{base}/docs",
        "openapi_json": f"{base}/openapi.json",
        "health": f"{base}/health",
    }
    return jsonify({"success": True, "links": links})

@chat_bp.get("/api/demo/links/")
def api_demo_links_slash():
    """Alias to avoid 404 when a trailing slash is used."""
    return api_demo_links()



@chat_bp.get("/api/demo/links.txt")
def api_demo_links_txt():
    """Dev/demo helper: downloads a TXT file with important local links."""
    base = frontend_url("/").rstrip("/")
    links = {
        "chat": f"{base}/chat",
        "demo": f"{base}/demo",
        "admin_login": f"{base}/admin/login",
        "admin_panel": f"{base}/admin",
        "teacher_login": f"{base}/teacher/login",
        "teacher_panel": f"{base}/teacher",
        "metrics": f"{base}/metricas",
        "db_viewer": f"{base}/db",
        "swagger_ui": f"{base}/docs",
        "openapi_json": f"{base}/openapi.json",
        "health": f"{base}/health",
        "status": f"{base}/status",
    }

    lines = [
        "YELIA — LINKS DE DEMO (LOCAL)",
        "--------------------------------",
        f"Chat: {links['chat']}",
        f"Demo HUB: {links['demo']}",
        f"Admin Login: {links['admin_login']}",
        f"Admin Panel: {links['admin_panel']}",
        f"Docente Login: {links['teacher_login']}",
        f"Docente Panel: {links['teacher_panel']}",
        f"Métricas: {links['metrics']}",
        f"DB Viewer: {links['db_viewer']}",
        f"Swagger UI: {links['swagger_ui']}",
        f"OpenAPI JSON: {links['openapi_json']}",
        f"Health: {links['health']}",
        f"Status: {links['status']}",
        ""
    ]
    content = "\n".join(lines)

    return Response(
        content,
        mimetype="text/plain; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=links_demo.txt"}
    )

@chat_bp.get("/api/demo/links.txt/")
def api_demo_links_txt_slash():
    """Alias to avoid 404 when a trailing slash is used."""
    return api_demo_links_txt()


# ============================================================
# Accesos cortos (para el jurado/demo)
# - El launcher y la demo usan estos endpoints “bonitos”.
# - Internamente delegan a /api/demo/links.* para evitar duplicar lógica.
# ============================================================

@chat_bp.get("/links.json")
def links_json():
    """Alias amigable: /links.json -> JSON de links."""
    return api_demo_links()


@chat_bp.get("/links.json/")
def links_json_slash():
    return api_demo_links()


@chat_bp.get("/links.txt")
def links_txt():
    """Alias amigable: /links.txt -> TXT de links."""
    return api_demo_links_txt()


@chat_bp.get("/links.txt/")
def links_txt_slash():
    return api_demo_links_txt()


@chat_bp.get("/links")
def links_redirect():
    """Atajo: /links -> /links.json"""
    return redirect("/api/demo/links")


@chat_bp.get("/links/")
def links_redirect_slash():
    return redirect("/api/demo/links")


@chat_bp.get("/metricas")
def metricas_alias():
    """Alias amigable: /metricas -> /admin/metrics"""
    return frontend_redirect("/metricas")


@chat_bp.get("/metricas/")
def metricas_alias_slash():
    return frontend_redirect("/metricas")
