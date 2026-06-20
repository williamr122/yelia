"""
Proyecto: YELIA4AP
Archivo: backend/core/__init__.py
Descripción: Inicialización del paquete Python para exponer módulos y facilitar imports.

Revisión: 2026-02-10
"""
"""  Init
Archivo del backend del sistema YELIA4AP.

Responsabilidad:
- Implementa la lógica asociada a este módulo.
"""

#
# Archivo: backend/core/__init__.py
# Rol: Módulo del backend (Flask) de YELIA4AP.

"""backend/core/__init__.py

Backend Flask — YELIA (módulo de servidor)

Propósito:
    Este archivo pertenece al backend (Flask) de YELIA. Contiene lógica de servidor
    y/o utilidades que soportan rutas, servicios, persistencia y orquestación NLP.
    Específicamente, este archivo inicializa el paquete `core`, que agrupa
    funcionalidades transversales compartidas por múltiples capas del sistema.
    No contiene lógica ejecutable directa, solo sirve para marcar la carpeta
    como paquete Python y documentar su propósito.
"""

# ============================================================
# MÓDULO: CORE
# ------------------------------------------------------------
# PROPÓSITO:
#   Inicializar el paquete `core` del backend.
#
# QUÉ ES EL MÓDULO CORE:
#   Es el núcleo de utilidades transversales del sistema,
#   compartidas por múltiples capas (NLP, services, repositories).
#
# CONTENIDO TÍPICO DEL CORE:
#   - Manejo centralizado de errores
#   - Seguridad (headers, validaciones, protecciones)
#   - Rate limiting / control de abuso
#   - Helpers reutilizables de bajo nivel
#
# PRINCIPIO DE DISEÑO:
#   El módulo core NO contiene lógica de negocio.
#   Solo agrupa funcionalidades genéricas y reutilizables
#   que no pertenecen a un dominio específico.
#
#   Este archivo no ejecuta código.
#   Su función es marcar la carpeta como paquete Python
# ============================================================

#
# Módulo core del backend.
#
# Este archivo indica que la carpeta `core` es un paquete Python.
# Aquí se agrupan utilidades transversales del sistema como:
# - manejo de errores
# - seguridad
# - rate limiting
# - helpers reutilizables
#
# No contiene lógica ejecutable directa, solo inicializa el módulo.

# Aquí podríamos importar submódulos o definir variables globales si es necesario.
