"""
Proyecto: YELIA4AP
Archivo: backend/db/__init__.py
Descripción: Inicialización del paquete Python para exponer módulos y facilitar imports.

Revisión: 2026-02-10
"""
"""  Init
Archivo del backend del sistema YELIA4AP.

Responsabilidad:
- Implementa la lógica asociada a este módulo.
"""

#
# Archivo: backend/db/__init__.py
# Rol: Módulo del backend (Flask) de YELIA4AP.

"""backend/db/__init__.py

Backend Flask — YELIA (módulo de servidor)

Propósito:
    Este archivo pertenece al backend (Flask) de YELIA. Contiene lógica de servidor
    y/o utilidades que soportan rutas, servicios, persistencia y orquestación NLP.
    Este archivo marca la carpeta `db` como un paquete Python exporta el API público
    de la capa de base de datos (BD).
"""

# ============================================================
# PROPÓSITO:
# - Marcar la carpeta `db` como paquete Python.
# - Exponer (re-exportar) el API público de la capa de BD.
#
# BENEFICIO:
# - Permite importar desde un único punto, por ejemplo:
#     from backend.db import db_session, init_db, get_db_connection
#   en lugar de:
#     from backend.db.session import db_session, init_db, ...
#
# - `noqa` se usa para evitar warnings de linters por:
#   F401: imported but unused
#   F403: import * used
# ============================================================

from .session import *  # noqa: F401,F403
