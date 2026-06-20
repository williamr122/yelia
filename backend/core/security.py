"""
Proyecto: YELIA4AP
Archivo: backend/core/security.py
Descripción: Utilidades de seguridad: validaciones, sanitización y helpers relacionados.

Revisión: 2026-02-10
"""
"""Security
Archivo del backend del sistema YELIA4AP.

Responsabilidad:
- Implementa la lógica asociada a este módulo.
"""

#
# Archivo: backend/core/security.py
# Rol: Módulo del backend (Flask) de YELIA4AP.

"""backend/core/security.py

Backend Flask — YELIA (módulo de servidor)

Propósito:
    Este archivo pertenece al backend (Flask) de YELIA. Contiene lógica de servidor
    y/o utilidades que soportan rutas, servicios, persistencia y orquestación NLP.
    En particular, este módulo centraliza funciones básicas de seguridad y control
    de acceso del backend.
"""

# ============================================================
# PROPÓSITO:
#   Centralizar funciones básicas de seguridad y control de acceso
#   del backend.
#
# QUÉ PROBLEMA RESUELVE:
#   - Protege endpoints sensibles (admin / métricas / mantenimiento)
#   - Evita exponer operaciones críticas sin autorización
#
# ENFOQUE PROFESIONAL:
#   Este módulo implementa validaciones simples pero efectivas,
#   adecuadas para prototipos, proyectos académicos y servicios
#   internos sin un sistema de autenticación completo.
# ============================================================

#
# Funciones de seguridad y control de acceso.
#
# Este módulo centraliza validaciones relacionadas con permisos
# y tokens sensibles del sistema.

import os
from flask import request


def require_admin_token() -> bool:
    """
    Valida el token de administrador del sistema.

    Mecanismos soportados (recomendado):
    - Header HTTP: X-Admin-Token
    - Header estándar: Authorization: Bearer <token>

    Compatibilidad (solo DEV / opcional):
    - Query parameter: ?token=XXXX
      (puede habilitarse en desarrollo con ALLOW_ADMIN_TOKEN_QUERY=1)

    El valor recibido se compara contra la variable de entorno ADMIN_TOKEN.

    Retorna:
    - True  → token válido (acceso permitido)
    - False → token inválido o no proporcionado
    """

    admin = (os.getenv("ADMIN_TOKEN") or "").strip()
    if not admin:
        return False

    # 1) Header dedicado
    header = (request.headers.get("X-Admin-Token") or "").strip()
    if header and header == admin:
        return True

    # 2) Authorization: Bearer <token>
    auth = (request.headers.get("Authorization") or "").strip()
    if auth:
        parts = auth.split(None, 1)
        if len(parts) == 2 and parts[0].lower() == "bearer":
            if parts[1].strip() == admin:
                return True

    # 3) Compatibilidad: token por query string SOLO en desarrollo (y opcional)
    env = (os.getenv("FLASK_ENV") or os.getenv("ENV") or "production").lower()
    allow_qs = (os.getenv("ALLOW_ADMIN_TOKEN_QUERY", "0") or "0").strip() == "1"
    if env in ("development", "dev", "local", "test", "testing") and allow_qs:
        token_qs = (request.args.get("token") or "").strip()
        return bool(token_qs) and token_qs == admin

    return False


from flask import session

def has_staff_session() -> bool:
    """Indica si existe una sesión válida de personal (admin/docente).

    Se considera sesión de personal cuando cualquiera de estos keys está presente:
    - admin_role (panel admin)
    - teacher_role (panel docente)
    - role (fallback)

    Valores aceptados:
    - admin
    - teacher
    - docente
    """
    role = (session.get("admin_role") or session.get("teacher_role") or session.get("role") or "").strip().lower()
    return role in ("admin", "teacher", "docente")


def require_staff_or_token() -> bool:
    """Permite acceso a endpoints internos (staff) por:
    1) Sesión de admin/docente, o
    2) ADMIN_TOKEN (útil en dev/local y pruebas automatizadas)

    Nota:
        En producción, se recomienda deshabilitar el token por querystring y usar
        solamente headers / sesión (ver require_admin_token()).
    """
    return has_staff_session() or require_admin_token()


def get_current_role() -> str:
    """Obtiene el rol actual desde la sesión (normalizado)."""
    try:
        role = (session.get("admin_role") or session.get("teacher_role") or session.get("role") or "").strip().lower()
        return role
    except Exception:
        return ""


def require_roles(*roles: str, allow_token: bool = True) -> bool:
    """Valida acceso por rol (sesión) y opcionalmente por ADMIN_TOKEN."""
    allowed = {r.strip().lower() for r in roles if r and r.strip()}
    role = get_current_role()
    if role and role in allowed:
        return True
    return require_admin_token() if allow_token else False
