from __future__ import annotations

"""
Proyecto: YELIA4AP
Archivo: backend/core/utils.py
Descripción: Funciones auxiliares reutilizables (utilities) para el backend.

Revisión: 2026-02-10
"""
"""Utils
Archivo del backend del sistema YELIA4AP.

Responsabilidad:
- Implementa la lógica asociada a este módulo.
"""

#
# Archivo: backend/core/utils.py
# Rol: Módulo del backend (Flask) de YELIA4AP.

"""backend/core/utils.py

Backend Flask — YELIA (módulo de servidor)

Propósito:
    Este archivo pertenece al backend (Flask) de YELIA. Contiene lógica de servidor
    y/o utilidades que soportan rutas, servicios, persistencia y orquestación NLP.
    En particular, este módulo estandariza las respuestas HTTP de la API del backend.
"""

# ============================================================
# PROPÓSITO:
#   Definir utilidades comunes para estandarizar las respuestas
#   HTTP (JSON) de la API del backend.
#
# QUÉ PROBLEMA RESUELVE:
#   - Evita respuestas inconsistentes entre endpoints
#   - Facilita el manejo de errores en frontend
#   - Simplifica la lectura y el mantenimiento del código
#
# ENFOQUE PROFESIONAL:
#   Todas las respuestas de la API siguen un mismo contrato:
#   - ok: True  -> respuesta exitosa
#   - ok: False -> respuesta de error
#
#   Esto permite que el frontend maneje resultados
#   sin depender del endpoint específico.
# ============================================================

#
# Utilidades comunes para respuestas HTTP.
#
# Este módulo estandariza las respuestas JSON de la API,
# manteniendo una estructura clara y consistente.

from flask import jsonify, g

# ============================================================
# Respuestas estándar de API
# ============================================================
# Contrato unificado (para TODOS los endpoints /api/*):
#   {
#     "ok": true|false,
#     "data": <obj|null>,
#     "error": <str|null>,
#     "code": <str>,
#     "request_id": <str|null>,
#     ... (extra)
#   }
# ============================================================


def ok(payload: dict | None = None, status: int = 200, code: str = "OK", **extra):
    """Respuesta exitosa estándar."""
    rid = getattr(g, "request_id", None)
    data = payload
    body = {
        "ok": True,
        "data": data,
        "error": None,
        "code": code,
        "request_id": rid,
    }
    if extra:
        body.update(extra)
    return jsonify(body), status


def err(message: str, status: int = 400, code: str = "ERROR", **extra):
    """Respuesta de error estándar."""
    rid = getattr(g, "request_id", None)
    body = {
        "ok": False,
        "data": None,
        "error": message,
        "code": code,
        "request_id": rid,
    }
    if extra:
        body.update(extra)
    return jsonify(body), status
