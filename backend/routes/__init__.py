"""
Proyecto: YELIA4AP
Archivo: backend/routes/__init__.py
Descripción: Inicialización del paquete Python para exponer módulos y facilitar imports.

Revisión: 2026-02-10
"""
"""  Init
Archivo del backend del sistema YELIA4AP.

Responsabilidad:
- Implementa la lógica asociada a este módulo.
"""

#
# Archivo: backend/routes/__init__.py
# Rol: Módulo del backend (Flask) de YELIA4AP.

"""backend/routes/__init__.py

Backend Flask — YELIA (módulo de servidor)

Propósito:
    Este archivo pertenece al backend (Flask) de YELIA. Contiene lógica de servidor
    y/o utilidades que soportan rutas, servicios, persistencia y orquestación NLP.
    Aquí se centraliza el registro de Blueprints y la inicialización de dependencias
    globales para las rutas de la aplicación.
"""

# ============================================================
# PROPÓSITO:
#   Centralizar el registro de Blueprints de la aplicación Flask
#   y definir el orden de inicialización de dependencias globales.
#
# ESTRUCTURA DE RUTAS:
#   - chat_routes.py    -> UI + APIs principales
#                         (chat, historial, perfil, progreso, temas)
#   - metrics_routes.py -> Endpoints de métricas
#                         (/api/metrics y /admin/metrics)
#   - health_routes.py  -> Endpoint de salud del sistema (/health)
#
# ENFOQUE PROFESIONAL:
#   Este archivo actúa como el "router principal" del backend,
#   manteniendo el arranque de la app limpio y ordenado.
# ============================================================

from .chat_routes import chat_bp, limiter, cargar_dependencias_iniciales
from .metrics_routes import metrics_bp
from .health_routes import health_bp
from .docs_routes import docs_bp
from .admin_routes import admin_bp
from .export_routes import export_bp
from .db_viewer_routes import db_bp
from .teacher_routes import teacher_bp
from .upload_routes_secure import secure_uploads_bp

# Importar modulos que registran endpoints sobre chat_bp mediante decoradores.
# Sin estos imports, Flask no llega a registrar esas rutas.
from . import learning_routes  # noqa: F401


def init_routes(app):
    """Inicializa y registra todas las rutas de la aplicación.

    Flujo de inicialización:
    1) Carga dependencias necesarias en memoria
       (por ejemplo, temas, catálogos o recursos estáticos).
    2) Inicializa el sistema de rate limiting en la app Flask.
    3) Registra todos los blueprints disponibles.

    Este orden garantiza:
    - Que los datos necesarios estén listos antes de atender peticiones.
    - Que el rate limiting se aplique globalmente.
    - Que las rutas queden correctamente expuestas.

    Args:
        app: Parámetro de entrada.

    Returns:
        Resultado de la operación.
    """

    # --------------------------------------------------------
    # 1) Carga de dependencias iniciales
    # --------------------------------------------------------
    # Se ejecuta una sola vez al arrancar la app.
    # Es rápido y evita lecturas repetidas en cada request.
    cargar_dependencias_iniciales()

    # --------------------------------------------------------
    # 2) Inicialización del rate limiter
    # --------------------------------------------------------
    # Se asocia el limitador global a la instancia de Flask.
    limiter.init_app(app)

    # --------------------------------------------------------
    # 3) Registro de blueprints
    # --------------------------------------------------------
    # Cada blueprint encapsula un conjunto de rutas relacionadas,
    # manteniendo la app modular y escalable.
    app.register_blueprint(chat_bp)
    app.register_blueprint(metrics_bp)
    app.register_blueprint(health_bp)
    app.register_blueprint(docs_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(teacher_bp)
    app.register_blueprint(export_bp)
    app.register_blueprint(db_bp)
    app.register_blueprint(secure_uploads_bp)
