"""
Proyecto: YELIA4AP
Archivo: backend/__init__.py
Descripción: Inicialización del paquete Python para exponer módulos y facilitar imports.

Revisión: 2026-02-10
"""
"""  Init
Archivo del backend del sistema YELIA4AP.

Responsabilidad:
- Implementa la lógica asociada a este módulo.
"""

#
# Archivo: backend/__init__.py
# Rol: Módulo del backend (Flask) de YELIA4AP.

"""backend/__init__.py

Backend Flask — YELIA (módulo de servidor)

Propósito:
    Este archivo pertenece al backend (Flask) de YELIA. Contiene lógica de servidor
    y/o utilidades que soportan rutas, servicios, persistencia y orquestación NLP.
Rol arquitectónico:
    Punto raíz del backend de la aplicación, permitiendo que los submódulos
    (core, nlp, routes, services, repositories, etc.) puedan importarse correctamente.
Uso actual:
    No contiene lógica ejecutable ni define configuraciones globales.
Uso futuro (opcional):
    Podría incluir inicialización global del backend, configuración compartida
    o hooks de arranque si el proyecto crece.
Enfoque profesional:
    Mantener este archivo ligero es una buena práctica: documenta la intención
    sin introducir dependencias innecesarias.
"""

# ============================================
# PROPÓSITO:
#   Marcar la carpeta `backend` como un paquete
#   Python válido dentro del proyecto.
#
# ROL ARQUITECTÓNICO:
#   Este archivo representa el punto raíz del
#   backend de la aplicación y permite que:
#   - Los submódulos (core, nlp, routes, services,
#     repositories, etc.) puedan importarse
#     correctamente.
#
# USO ACTUAL:
#   - No contiene lógica ejecutable.
#   - No define configuraciones globales.
#
# USO FUTURO (OPCIONAL):
#   - Inicialización global del backend
#   - Configuración compartida
#   - Hooks de arranque si el proyecto crece
#
# ENFOQUE PROFESIONAL:
#   Mantener este archivo ligero es una buena
#   práctica: documenta la intención sin
#   introducir dependencias innecesarias.
# ============================================

# Marca el directorio backend como paquete Python.
# Aquí podrías poner configuración global si la necesitas más adelante.
