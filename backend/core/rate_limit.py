"""
Proyecto: YELIA4AP
Archivo: backend/core/rate_limit.py
Descripción: Control de límites de uso (rate limiting) y reglas asociadas.

Revisión: 2026-02-10
"""
"""Rate Limit
Archivo del backend del sistema YELIA4AP.

Responsabilidad:
- Implementa la lógica asociada a este módulo.
"""

#
# Archivo: backend/core/rate_limit.py
# Rol: Módulo del backend (Flask) de YELIA4AP.

"""backend/core/rate_limit.py

Backend Flask — YELIA (módulo de servidor)

Propósito:
    Este archivo pertenece al backend (Flask) de YELIA. Contiene lógica de servidor
    y/o utilidades que soportan rutas, servicios, persistencia y orquestación NLP.
    Específicamente, este archivo configura y centraliza la limitación de solicitudes
    (Rate Limiting) para la API del backend.
    No contiene lógica de negocio, solo define un limitador reutilizable.
"""

# ============================================================
# PROPÓSITO:
#   Configurar y centralizar la limitación de solicitudes
#   (Rate Limiting) para la API del backend.
#
# QUÉ PROBLEMA RESUELVE:
#   - Protege la API contra abuso, spam o ataques automatizados
#   - Evita consumo excesivo de recursos
#   - Mantiene estabilidad del servicio
#
# ENFOQUE PROFESIONAL:
#   El rate limiting se define a nivel global y reutilizable,
#   para que pueda aplicarse fácilmente a rutas o blueprints.
# ============================================================

#
# Configuración de limitación de solicitudes (Rate Limiting).
#
# Este módulo protege la API contra abuso, spam o ataques,
# limitando la cantidad de peticiones que un cliente puede hacer.

import os
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address


def _key_func():
    """
    Función que define cómo identificar a un cliente para el rate limit.

    ✅ Ajuste de seguridad (prototipo):
    - NO se confía en headers del cliente como `X-User-Id` (puede ser falsificado).
    - Si existe una sesión válida con user_id (futuro login), se usa como clave.
    - En caso contrario, se usa la IP (get_remote_address).

    Esto mantiene compatibilidad con el prototipo actual (sin login) y
    deja la base lista para un futuro módulo de autenticación.
    """
    try:
        # Importación diferida: en tiempo de importación del módulo,
        # Flask puede no tener el contexto request/session listo.
        from flask import session

        uid = session.get("user_id") or session.get("uid")
        return f"s:{uid}" if uid else get_remote_address()
    except Exception:
        # Fallback seguro: ante cualquier error, limita por IP
        return get_remote_address()


# ------------------------------------------------------------
# INSTANCIA GLOBAL DEL LIMITER
# ------------------------------------------------------------
# Se define un limitador global reutilizable en la aplicación.
#
# default_limits:
# - Se obtiene desde variable de entorno para permitir
#   ajustes sin modificar el código.
# - Valor por defecto: 240 solicitudes por hora.
limiter = Limiter(
    key_func=_key_func,
    default_limits=[os.getenv("RATE_LIMIT_DEFAULT", "240 per hour")],
)
