"""
Proyecto: YELIA4AP
Archivo: backend/core/errors.py
Descripción: Definición y manejo de errores/excepciones del backend.

Revisión: 2026-02-10
"""
"""Errors
Archivo del backend del sistema YELIA4AP.

Responsabilidad:
- Implementa la lógica asociada a este módulo.
"""

#
# Archivo: backend/core/errors.py
# Rol: Módulo del backend (Flask) de YELIA4AP.

"""backend/core/errors.py

Backend Flask — YELIA (módulo de servidor)

Propósito:
    Este archivo pertenece al backend (Flask) de YELIA. Contiene lógica de servidor
    y/o utilidades que soportan rutas, servicios, persistencia y orquestación NLP.
    En particular, este módulo define excepciones personalizadas para la API.
"""

# ============================================================
# PROPÓSITO:
#   Definir excepciones personalizadas para la API del backend.
#
# QUÉ PROBLEMA RESUELVE:
#   - Centraliza el manejo de errores controlados
#   - Evita lanzar excepciones genéricas no interpretables
#   - Permite devolver respuestas HTTP coherentes al cliente
#
# ENFOQUE PROFESIONAL:
#   En lugar de depender solo de Exception o errores del framework,
#   se define una jerarquía propia para representar errores de negocio
#   y validaciones esperadas.
# ============================================================

#
# Definición de errores personalizados para la API.
#
# Este módulo centraliza las excepciones propias del backend
# para poder manejar errores de forma consistente en toda la aplicación.


class APIError(Exception):
    """
    Excepción base para errores controlados de la API.

    Uso típico:
    - Errores de validación de datos
    - Reglas de negocio incumplidas
    - Accesos no permitidos
    - Estados esperados pero incorrectos

    IMPORTANTE:
    - Esta excepción NO representa fallos del sistema.
    - Representa errores previstos que deben comunicarse
      claramente al cliente (frontend).
    """

    def __init__(self, message: str, status: int = 400, code: str | None = None):
        """Inicializa una instancia de APIError.

        Parámetros:
        - message: Mensaje legible que se enviará al cliente.
        - status: Código HTTP asociado al error (por defecto 400).
        - code: Código interno opcional para identificar el tipo de error
                (útil para frontend, logging o métricas).

        Diseño:
        - Se hereda de Exception para compatibilidad total
          con el manejo estándar de errores en Python.

        Args:
            message: Mensaje principal del error.
            status: Código HTTP asociado a la respuesta.
            code: Código interno opcional de clasificación.

        Returns:
            None.
        """
        super().__init__(message)

        # Mensaje principal del error (user-facing)
        self.message = message

        # Código HTTP que debe devolver la API
        self.status = status

        # Código interno opcional para clasificación del error
        self.code = code
