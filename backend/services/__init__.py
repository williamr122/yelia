"""
Proyecto: YELIA4AP
Archivo: backend/services/__init__.py
Descripción: Inicialización del paquete Python para exponer módulos y facilitar imports.

Revisión: 2026-02-10
"""
"""  Init
Archivo del backend del sistema YELIA4AP.

Responsabilidad:
- Implementa la lógica asociada a este módulo.
"""

#
# Archivo: backend/services/__init__.py
# Rol: Módulo del backend (Flask) de YELIA4AP.

"""backend/services/__init__.py

Backend Flask — YELIA (módulo de servidor)

Propósito:
    Este archivo pertenece al backend (Flask) de YELIA. Contiene lógica de servidor
    y/o utilidades que soportan rutas, servicios, persistencia y orquestación NLP.
    No debe contener lógica de infraestructura ni acceso directo a datos.
    Su función principal es inicializar el paquete `services`.
"""

# backend/services/__init__.py
# ============================================================
# PROPÓSITO:
#   Inicializar el paquete `services`, que contiene la lógica
#   de negocio de la aplicación.
#
# QUÉ ES LA CAPA SERVICES:
#   Es la capa intermedia entre:
#   - routes  → manejo HTTP / endpoints
#   - repositories → acceso a datos
#
# RESPONSABILIDADES TÍPICAS:
#   - Orquestar flujos de negocio
#   - Aplicar reglas de dominio
#   - Combinar datos de distintos repositorios
#   - Preparar información para el NLP o el frontend
#
# LO QUE NO DEBE HACER:
#   - No manejar directamente HTTP
#   - No ejecutar SQL directo
#   - No contener lógica de infraestructura
#
# ENFOQUE PROFESIONAL:
#   Mantener esta separación facilita pruebas,
#   mantenimiento y escalabilidad del sistema.
# ============================================================

# Este archivo marca el directorio como paquete Python.
# No contiene lógica ejecutable.
