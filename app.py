"""
Proyecto: YELIA4AP
Archivo: app.py
Descripción: Punto de entrada del backend. Inicializa la app, rutas y configuración principal.

Revisión: 2026-02-10
"""
"""App
Archivo del backend del sistema YELIA4AP.

Responsabilidad:
- Implementa la lógica asociada a este módulo.
"""

#
# Archivo: app.py
# Rol: Punto de entrada principal de la aplicación Flask.


# ============================================================
# app.py
# ============================================================
# Punto de entrada principal de la aplicación Flask – YELIA
#
# RESPONSABILIDADES DEL ARCHIVO:
# - Crear la instancia principal de Flask (create_app)
# - Cargar variables de entorno (.env)
# - Configurar rutas de templates y archivos estáticos
# - (Opcional) Configurar CORS para modo API (frontend externo)
# - Resolver correctamente la ruta de la base de datos SQLite
# - Inicializar la base de datos (crear tablas si no existen)
# - Registrar todas las rutas y APIs del backend
# - Ejecutar el servidor en modo desarrollo
#
# Este archivo actúa como orquestador central del sistema.
# ============================================================

import os
import webbrowser
import threading
from pathlib import Path
from datetime import timedelta  # [MEJORA TESIS] sesiones más controladas
import uuid

from flask import Flask, jsonify, request, g
from dotenv import load_dotenv
import structlog
from structlog import contextvars as slog_ctx
import logging
from logging.handlers import RotatingFileHandler

# CORS (solo se activa si FRONTEND_URL existe)
from flask_cors import CORS

from backend.db.session import init_db
from backend.routes import init_routes


# Logger estructurado (útil para debugging y trazabilidad)
logger = structlog.get_logger()

# ------------------------------------------------------------
# Configuración de structlog (logs consistentes en consola/archivo)
# ------------------------------------------------------------
# ------------------------------------------------------------
# Seguridad de logs: redacción de datos sensibles (prototipo)
# ------------------------------------------------------------
SENSITIVE_KEYS = {
    "api_key", "apikey", "authorization", "token", "access_token", "refresh_token",
    "password", "secret", "x-api-key",
    "prompt", "message", "user_message", "assistant_message",
}

def _redact_logs(logger, method_name, event_dict):
    """Processor de structlog para reducir exposición de datos sensibles.

    - Oculta claves sensibles si aparecen.
    - Trunca strings muy largos para evitar volcado de prompts/mensajes completos.

    Args:
        logger: Parámetro de entrada.
        method_name: Parámetro de entrada.
        event_dict: Diccionario del evento de log (clave/valor).

    Returns:
        Resultado de la operación.
    """
    try:
        cleaned = {}
        for k, v in (event_dict or {}).items():
            lk = str(k).lower()
            if lk in SENSITIVE_KEYS:
                cleaned[k] = "[REDACTED]"
                continue
            if isinstance(v, str) and len(v) > 400:
                cleaned[k] = v[:400] + "…"
                continue
            cleaned[k] = v
        return cleaned
    except Exception:
        return event_dict

structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        _redact_logs,
        structlog.processors.JSONRenderer(),
    ]
)

# ============================================================
# Intentar importar función de creación de admin inicial
# ============================================================
create_initial_admin = None
try:
    from create_admin import create_initial_admin
except ImportError:
    logger.warning("No se encontró 'create_initial_admin' en create_admin.py → se usará advertencia manual")


# ============================================================
# Creación automática de usuario administrador inicial
# ============================================================
def ensure_initial_admin(app):
    """
    Crea el usuario 'admin' por defecto SOLO si NO existe ningún usuario con rol 'admin'.
    Se ejecuta una única vez al iniciar la aplicación (después de init_db).
    """
    with app.app_context():
        # Opción preferida: usar la función definida en create_admin.py
        if create_initial_admin is not None:
            try:
                created = create_initial_admin(app)
                if created:
                    logger.warning("=" * 70)
                    logger.warning("🔐 ADMINISTRADOR INICIAL CREADO AUTOMÁTICAMENTE (por entorno)")
                    logger.warning("Usuario     : admin")
                    logger.warning("Rol         : admin (con privilegios teacher también)")
                    logger.warning("Accede aquí : /admin")
                    logger.warning("=" * 70)
                return
            except Exception as e:
                logger.error(f"Fallo al ejecutar create_initial_admin(): {e}")

        # Si no existe o falló
        logger.warning("⚠️  No se creó usuario administrador automáticamente")
        logger.warning("    → Posibles causas:")
        logger.warning("      - Falta create_admin.py o la función create_initial_admin")
        logger.warning("      - Error en la lógica de creación")
        logger.warning("    Alternativas recomendadas:")
        logger.warning("      - Visita /admin/setup (Setup Wizard) con SETUP_TOKEN")
        logger.warning("      - O ejecuta manualmente:")
        logger.warning("      python create_admin.py")


# ============================================================
# FUNCIÓN FACTORY: create_app
# ============================================================
def create_app() -> Flask:
    """Crea y configura la aplicación Flask principal (factory).

    Este factory encapsula la inicialización del servidor: carga de variables de entorno,
    configuración de sesión/seguridad, inicialización de la base de datos y registro de rutas.

    Returns:
        Flask: Instancia de la aplicación lista para ejecutarse (app.run) o para ser importada
        por un servidor WSGI (por ejemplo, Gunicorn).
    """

    # --------------------------------------------------------
    # 1) Carga de variables de entorno (.env)
    # --------------------------------------------------------
    load_dotenv()

    # Directorio raíz del proyecto
    base_dir = Path(__file__).resolve().parent

    # --------------------------------------------------------
    # 2) Creación de la instancia Flask
    # --------------------------------------------------------
    app = Flask(
        __name__,
        static_folder="static",
        template_folder="templates",
    )

    # --------------------------------------------------------
    # 2.0) Middleware de Request-ID (correlación de logs)
    # --------------------------------------------------------
    @app.before_request
    def _bind_request_context():
        rid = request.headers.get("X-Request-ID") or uuid.uuid4().hex
        g.request_id = rid
        try:
            slog_ctx.clear_contextvars()
            slog_ctx.bind_contextvars(
                request_id=rid,
                method=request.method,
                path=request.path,
            )
        except Exception:
            pass

    @app.after_request
    def _attach_request_id(resp):
        rid = getattr(g, "request_id", None)
        if rid:
            resp.headers["X-Request-ID"] = rid
        try:
            slog_ctx.clear_contextvars()
        except Exception:
            pass

        resp.headers.setdefault("X-Content-Type-Options", "nosniff")
        resp.headers.setdefault("X-Frame-Options", "DENY")
        resp.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        resp.headers.setdefault("Permissions-Policy", "camera=(), microphone=(self), geolocation=()")


        try:
            path = request.path or ""
            env = (os.getenv("FLASK_ENV") or os.getenv("ENV") or "development").lower()
            if path.startswith("/static/"):
                max_age = 3600 if env == "production" else 0
                if max_age > 0:
                    resp.headers["Cache-Control"] = f"public, max-age={max_age}"
                else:
                    resp.headers["Cache-Control"] = "no-store"
            elif (resp.mimetype or "").startswith("text/html"):
                resp.headers["Cache-Control"] = "no-store"
        except Exception:
            pass

        return resp

    # --------------------------------------------------------
    # 2.1) Logging a consola + archivo
    # --------------------------------------------------------
    log_dir = base_dir / "logs"
    log_dir.mkdir(exist_ok=True)

    log_file = os.getenv("LOG_FILE", str(log_dir / "app.log"))
    log_level = os.getenv("LOG_LEVEL", "INFO").upper().strip()

    root = logging.getLogger()
    if not root.handlers:
        root.setLevel(log_level)
        fmt = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
        fh = RotatingFileHandler(log_file, maxBytes=1_000_000, backupCount=3, encoding="utf-8")
        fh.setLevel(log_level)
        fh.setFormatter(fmt)
        ch = logging.StreamHandler()
        ch.setLevel(log_level)
        ch.setFormatter(fmt)
        root.addHandler(fh)
        root.addHandler(ch)

    logger.info("Logging listo", log_file=log_file, log_level=log_level)

    # --------------------------------------------------------
    # 3) Configuración de clave secreta, sesiones, CORS, CSRF, etc.
    # --------------------------------------------------------

    env = os.getenv("ENV", "development").lower().strip()
    secret_key = os.getenv("FLASK_SECRET_KEY")
    if not secret_key:
        if env in ("development", "dev", "local"):
            secret_key = "dev-secret-key"
            logger.warning("FLASK_SECRET_KEY no configurada; usando fallback SOLO en desarrollo")
        else:
            raise RuntimeError("FLASK_SECRET_KEY no configurada (requerida en producción)")

    app.config["SECRET_KEY"] = secret_key
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    app.config["SESSION_COOKIE_SECURE"] = (env == "production")
    app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=7)
    app.config["PREFERRED_URL_SCHEME"] = "https" if env == "production" else "http"
    app.config["JSON_SORT_KEYS"] = False

    max_kb = int(os.getenv("MAX_CONTENT_LENGTH_KB", "5120"))
    app.config["MAX_CONTENT_LENGTH"] = max_kb * 1024

    frontend_url = os.getenv("FRONTEND_URL", "").strip()
    if frontend_url:
        origins = [o.strip() for o in frontend_url.split(",") if o.strip()]
        if origins == ["*"]:
            raise RuntimeError("FRONTEND_URL='*' no permitido con sesiones/cookies")
        CORS(app, resources={r"/api/*": {"origins": origins}}, supports_credentials=True,
             methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
             allow_headers=["Content-Type", "Authorization", "X-CSRFToken"])
        logger.info("CORS habilitado", origins=origins)
    else:
        logger.info("CORS no habilitado (modo mismo dominio)")

    require_csrf = os.getenv("REQUIRE_CSRF", "0").strip() == "1"
    if require_csrf:
        from flask import session
        CSRF_EXEMPT = {"/api/auth/csrf", "/api/health"}
        @app.before_request
        def _csrf_protect():
            if request.method in ("POST", "PUT", "PATCH", "DELETE") and request.path.startswith("/api/"):
                if request.path in CSRF_EXEMPT:
                    return
                token = request.headers.get("X-CSRFToken") or request.headers.get("X-CSRF-Token")
                if not token or token != session.get("csrf_token"):
                    return jsonify({"ok": False, "error": "csrf_required"}), 403

    # --------------------------------------------------------
    # 4) Ruta de base de datos absoluta
    # --------------------------------------------------------
    db_url = (os.getenv("DATABASE_URL") or os.getenv("DB_URL") or "").strip()
    if db_url.startswith(("postgresql://", "postgres://")):
        app.config["DATABASE_URL"] = db_url
        db_path = "PostgreSQL"
    else:
        db_path = os.getenv("DATABASE_PATH")
        if not db_path:
            db_path = db_url.replace("sqlite:///", "") if db_url.startswith("sqlite:///") else "yelia.db"
        if not os.path.isabs(db_path):
            db_path = str((base_dir / db_path).resolve())
        app.config["DATABASE_PATH"] = db_path

    logger.info("Inicializando YELIA", database=db_path, env=env)
    # --------------------------------------------------------
    # 5) Inicialización de la base de datos
    # --------------------------------------------------------
    init_db(app)

    # Crear usuario admin inicial después de la base de datos
    ensure_initial_admin(app)

    # --------------------------------------------------------
    # 6) Registro de rutas y endpoints
    # --------------------------------------------------------
    init_routes(app)

    # --------------------------------------------------------
    # 6.1) Error handlers globales (API siempre responde JSON)
    # --------------------------------------------------------
    def _api_error(message: str, status: int, code: str = "ERROR"):
        """_api_error.

        Args:
            message (str): TODO: Describe this parameter.
            status (int): TODO: Describe this parameter.
            code (str): TODO: Describe this parameter.

        Returns:
            Any: TODO: Describe the return value."""
        # request_id permite correlacionar este error con los logs
        rid = getattr(g, "request_id", None)
        return jsonify({
            "ok": False,
            "error": message,
            "code": code,
            "data": None,
            "request_id": rid,
        }), status

    @app.errorhandler(404)
    def _handle_404(e):
        """_handle_404.

        Args:
            e (Any): TODO: Describe this parameter.

        Returns:
            Any: TODO: Describe the return value."""
        if request.path.startswith("/api/"):
            return _api_error("Recurso no encontrado.", 404, "NOT_FOUND")
        return e

    @app.errorhandler(405)
    def _handle_405(e):
        """_handle_405.

        Args:
            e (Any): TODO: Describe this parameter.

        Returns:
            Any: TODO: Describe the return value."""
        if request.path.startswith("/api/"):
            return _api_error("Método no permitido.", 405, "METHOD_NOT_ALLOWED")
        return e

    @app.errorhandler(413)
    def _handle_413(e):
        """_handle_413.

        Args:
            e (Any): TODO: Describe this parameter.

        Returns:
            Any: TODO: Describe the return value."""
        if request.path.startswith("/api/"):
            return _api_error("El request es demasiado grande.", 413, "PAYLOAD_TOO_LARGE")
        return e

    @app.errorhandler(429)
    def _handle_429(e):
        """_handle_429.

        Args:
            e (Any): TODO: Describe this parameter.

        Returns:
            Any: TODO: Describe the return value."""
        if request.path.startswith("/api/"):
            return _api_error("Demasiadas solicitudes. Intenta más tarde.", 429, "RATE_LIMIT")
        return e

    @app.errorhandler(500)
    def _handle_500(e):
        """_handle_500.

        Args:
            e (Any): TODO: Describe this parameter.

        Returns:
            Any: TODO: Describe the return value."""
        if request.path.startswith("/api/"):
            return _api_error("Error interno del servidor.", 500, "SERVER_ERROR")
        return e

    @app.errorhandler(Exception)
    def _handle_exception(e):
        """_handle_exception.

        Args:
            e (Any): TODO: Describe this parameter.

        Returns:
            Any: TODO: Describe the return value."""
        if request.path.startswith("/api/"):
            logger.error("Excepción no controlada", error=str(e))
            return _api_error("Error inesperado del servidor.", 500, "UNEXPECTED_ERROR")
        return e

    return app


# ============================================================
# EJECUCIÓN EN MODO DESARROLLO
# ============================================================
if __name__ == "__main__":
    app = create_app()

    # ------------------------------------------------------------
    # AUTO-OPEN BROWSER (solo cuando ejecutas: python app.py)
    # ------------------------------------------------------------
    # - En local (VS Code / terminal) es cómodo abrir el navegador solo.
    # - En hosting normalmente NO se ejecuta este bloque (Gunicorn usa create_app()).
    # - Control:
    #     AUTO_OPEN_BROWSER=1   -> abre navegador (default)
    #     AUTO_OPEN_BROWSER=0   -> no abre
    #     AUTO_OPEN_PATHS=...   -> rutas separadas por coma (default "/launcher,/admin/login")
    #
    # - usamos 127.0.0.1 para evitar "0.0.0.0" en navegador.
    # - /admin/login redirige a /admin/setup si aún no existe administrador.
    try:
        auto_open = os.getenv("AUTO_OPEN_BROWSER", "1").lower().strip() in ("1", "true", "yes", "y", "on")
        paths_raw = os.getenv("AUTO_OPEN_PATHS", "/launcher").strip()
        paths = [p.strip() for p in paths_raw.split(",") if p.strip()]
        frontend_raw = (
            os.getenv("NEXT_FRONTEND_URL")
            or os.getenv("PUBLIC_FRONTEND_URL")
            or os.getenv("FRONTEND_URL")
            or "http://localhost:3000"
        ).strip()
        if "," in frontend_raw:
            frontend_raw = frontend_raw.split(",", 1)[0].strip()
        frontend_base = frontend_raw.rstrip("/") or "http://localhost:3000"

        if auto_open:
            for i, p in enumerate(paths):
                if not p.startswith("/"):
                    p = "/" + p
                url = f"{frontend_base}{p}"
                # delay escalonado para abrir múltiples pestañas sin bloquear
                threading.Timer(1.0 + (0.35 * i), lambda u=url: webbrowser.open_new_tab(u)).start()
    except Exception:
        # no debe romper el arranque si el entorno no permite abrir navegador
        pass
    pass

    # DEBUG leído desde .env (permite activar/desactivar sin tocar código)
    debug_env = os.getenv("DEBUG", "True").lower().strip()
    debug = debug_env in ("1", "true", "yes", "y", "on")

    app.run(
        host="0.0.0.0",
        port=int(os.getenv("PORT", 5000)),
        debug=debug,
        use_reloader=False,  # evita doble ejecución por reloader
        threaded=False       # mantiene ejecución simple para prototipo
    )
