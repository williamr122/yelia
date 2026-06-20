"""
Proyecto: YELIA4AP
Archivo: backend/repositories/chat_repo.py
Descripción: Módulo del backend para la lógica asociada a esta carpeta/funcionalidad.

Revisión: 2026-02-10
"""
"""Chat Repo
Archivo del backend del sistema YELIA4AP.

Responsabilidad:
- Implementa la lógica asociada a este módulo.
"""

#
# Archivo: backend/repositories/chat_repo.py
# Rol: Módulo del backend (Flask) de YELIA4AP.

"""backend/repositories/chat_repo.py

Backend Flask — YELIA (módulo de servidor)

Propósito:
    Este archivo pertenece al backend (Flask) de YELIA. Contiene lógica de servidor
    y/o utilidades que soportan rutas, servicios, persistencia y orquestación NLP.
    En particular, este módulo implementa un repositorio de acceso a datos
    relacionado con el módulo de chat.
"""

# ============================================================
# PROPÓSITO:
#   Repositorio de acceso a datos relacionado con el módulo de chat.
#
# CONTEXTO DEL PROYECTO:
#   Actualmente, el prototipo aún realiza consultas a la base de datos
#   directamente desde rutas o servicios.
#
#   Este repositorio se introduce como:
#   - Punto de transición arquitectónica
#   - Base para una migración gradual hacia el patrón Repositorio
#
# BENEFICIO DEL DISEÑO:
#   - Centraliza el acceso a datos
#   - Facilita pruebas y mantenimiento
#   - Permite desacoplar la lógica de negocio del motor de BD
#
# NOTA IMPORTANTE:
#   Aunque hoy su uso es mínimo, este archivo deja preparada
#   la estructura para una evolución ordenada del sistema.
# ============================================================

# Repositorio de chat (SQLite).
# consultas desde rutas/servicios. Este repo queda listo para migración gradual.

from backend.db.session import db_session


def healthcheck() -> bool:
    """
    Verifica el estado de la conexión a la base de datos.

    Uso principal:
    - Comprobaciones de salud del sistema (health checks)
    - Validar disponibilidad de la BD al iniciar la aplicación
    - Soporte para monitoreo o endpoints /health

    Retorna:
    - True  → la conexión y la consulta funcionan correctamente
    - False → ocurrió una excepción al acceder a la BD
    """
    try:
        # Apertura de una sesión de solo lectura para validar conectividad
        with db_session() as conn:
            conn.execute("SELECT 1")
        return True
    except Exception:
        # Cualquier error se interpreta como falla de salud
        return False
