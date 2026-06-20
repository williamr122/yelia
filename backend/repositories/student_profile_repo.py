"""
Proyecto: YELIA4AP
Archivo: backend/repositories/student_profile_repo.py
Descripción: Módulo del backend para la lógica asociada a esta carpeta/funcionalidad.

Revisión: 2026-02-10
"""
from __future__ import annotations

"""
Archivo: backend/repositories/student_profile_repo.py
Proyecto: YELIA4AP
Última revisión: 2026-02-10

Módulo de backend en Python.

Convenciones:
- Funciones pequeñas, nombres descriptivos y manejo de errores explícito.
- Evitar prints en producción: usar logging si aplica.
"""


#
# Archivo: backend/repositories/student_profile_repo.py
# Rol: Módulo del backend (Flask) de YELIA4AP.


"""Student Profile Repo
Archivo del backend del sistema YELIA4AP.

Responsabilidad:
- Implementa la lógica asociada a este módulo.

backend/repositories/student_profile_repo.py

Backend Flask — YELIA (módulo de servidor)

Propósito:
    Persistir y recuperar el "perfil avanzado" del estudiante (JSON) para:
      - seguimiento de progreso por habilidades (skills)
      - nivel detectado (basico/intermedio/avanzado)
      - errores frecuentes (mistakes)
      - metas (goals)

Diseño:
    - Se guarda como JSON para flexibilidad y para no romper el esquema existente.
    - Operaciones best-effort: si algo falla, el chat no debe caerse.
"""
# =====================================
# Imports
# =====================================


import datetime
import json
from typing import Any, Dict, Optional

import structlog

from backend.db.session import db_session


# =====================================
# Configuración / Constantes
# =====================================
logger = structlog.get_logger()
# =====================================
# Funciones / Clases
# =====================================



def _default_profile(student_id: str) -> Dict[str, Any]:
    """Crea un perfil inicial seguro."""
    return {
        "student_id": student_id,
        # Nombre corto opcional para personalizar la UI y el tutor.
        # Se guarda aquí (JSON) para no tocar el esquema de DB.
        "nickname": None,
        "level_current": "basico",
        "level_confidence": 0.5,
        "course": None,
        "tags": [],
        "notes": "",
        "skills": {},
        "mistakes": [],
        "goals": [],
        "stats": {"messages": 0, "quizzes": 0, "exercises": 0},
        "last_topic": None,
        "updated_at": datetime.datetime.now().isoformat(timespec="seconds"),
    }


def get_profile(student_id: str) -> Dict[str, Any]:
    """Obtiene perfil del estudiante. Si no existe, devuelve uno por defecto."""
    if not student_id:
        return _default_profile("unknown")

    try:
        with db_session(write=False) as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT profile_json FROM student_profiles WHERE student_id = ? LIMIT 1;",
                (student_id,),
            )
            row = cur.fetchone()
        if not row:
            return _default_profile(student_id)

        raw = row["profile_json"] or "{}"
        try:
            data = json.loads(raw)
            if not isinstance(data, dict):
                return _default_profile(student_id)
        except Exception:
            return _default_profile(student_id)

        # Normalización mínima
        data.setdefault("student_id", student_id)
        data.setdefault("skills", {})
        data.setdefault("mistakes", [])
        data.setdefault("goals", [])
        data.setdefault("stats", {"messages": 0, "quizzes": 0, "exercises": 0})
        data.setdefault("level_current", "basico")
        data.setdefault("level_confidence", 0.5)
        data.setdefault("last_topic", None)
        data.setdefault("nickname", None)
        return data

    except Exception as e:
        logger.warning("No se pudo leer student_profiles; usando perfil por defecto", error=str(e))
        return _default_profile(student_id)


def save_profile(student_id: str, profile: Dict[str, Any]) -> None:
    """Crea o actualiza el perfil del estudiante (upsert)."""
    if not student_id:
        return

    profile = dict(profile or {})
    profile["student_id"] = student_id
    profile["updated_at"] = datetime.datetime.now().isoformat(timespec="seconds")

    try:
        payload = json.dumps(profile, ensure_ascii=False)
    except Exception:
        payload = json.dumps(_default_profile(student_id), ensure_ascii=False)

    try:
        with db_session(write=True) as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO student_profiles (student_id, profile_json, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(student_id) DO UPDATE SET
                    profile_json = excluded.profile_json,
                    updated_at = excluded.updated_at;
                """,
                (student_id, payload, profile["updated_at"]),
            )
    except Exception as e:
        # Best-effort: no romper el chat por fallo de persistencia
        logger.warning("No se pudo guardar student_profile", error=str(e), student_id=student_id)


def set_nickname(student_id: str, nickname: Optional[str]) -> None:
    """Guarda/actualiza el nickname del estudiante dentro del perfil JSON.

    - No requiere migraciones: se mantiene el esquema actual.
    - Best-effort: si falla, no rompe el chat.
    """
    if not student_id:
        return

    try:
        nick = (nickname or "").strip()
        if not nick:
            # Permite limpiar nickname si llega vacío
            profile = get_profile(student_id)
            profile["nickname"] = None
            save_profile(student_id, profile)
            return

        # Hard limits (anti-abuso / payload)
        nick = nick[:24]
        profile = get_profile(student_id)
        profile["nickname"] = nick
        save_profile(student_id, profile)

    except Exception as e:
        logger.warning("No se pudo guardar nickname", error=str(e), student_id=student_id)
