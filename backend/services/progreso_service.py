"""
Proyecto: YELIA4AP
Archivo: backend/services/progreso_service.py
Descripción: Módulo del backend para la lógica asociada a esta carpeta/funcionalidad.

Revisión: 2026-02-10
"""
"""Progreso Service
Archivo del backend del sistema YELIA4AP.

Responsabilidad:
- Implementa la lógica asociada a este módulo.
"""

#
# Archivo: backend/services/progreso_service.py
# Rol: Módulo del backend (Flask) de YELIA4AP.

"""backend/services/progreso_service.py

Backend Flask — YELIA (módulo de servidor)

Propósito:
    Este archivo pertenece al backend (Flask) de YELIA. Contiene lógica de servidor
    y/o utilidades que soportan rutas, servicios, persistencia y orquestación NLP.
    En particular, este módulo gestiona el progreso académico del estudiante
    dentro de YELIA, implementando un sistema ligero de gamificación para motivar
    el aprendizaje sin necesidad de autenticación formal.
"""

# ============================================================
# backend/services/progreso_service.py
# ------------------------------------------------------------
# PROPÓSITO DEL MÓDULO
# Este archivo se encarga de gestionar el progreso académico del
# estudiante dentro de YELIA. Su función principal es llevar un
# registro simple pero útil del avance del usuario a lo largo de
# sus interacciones con el chatbot.
#
# El enfoque es intencionalmente ligero (gamificación básica),
# pensado para motivar al estudiante sin introducir complejidad
# innecesaria ni depender de un sistema formal de autenticación.
#
# ¿QUÉ MANEJA ESTE MÓDULO?
# - Puntos acumulados por interacción y actividades.
# - Temas aprendidos, almacenados como lista en formato JSON.
# - Nivel simbólico del estudiante (Inicial, Intermedio, Avanzado),
#   calculado a partir de los puntos.
# - Información académica contextual:
#     • ciclo_academico
#     • estado_materia
#
# IDENTIFICACIÓN DEL USUARIO
# ✅ Fix importante:
# - Si la sesión/cookies NO persisten (Tracking Prevention),
#   el usuario cambiaba en cada request → por eso fallaban rename/delete.
# - Ahora: si no hay session["usuario"], se genera un ID estable
#   basado en IP + User-Agent (fallback determinístico).
#
# IMPORTANTE
# - Este mecanismo NO reemplaza autenticación real; se usa únicamente
#   para diferenciar estudiantes dentro del prototipo.
# - El frontend consume estos datos a través de los endpoints
#   /api/progreso y /api/update-profile definidos en routes.py.
# - La persistencia se realiza en SQLite usando db_session()
#   para garantizar cierres correctos y evitar bloqueos.
# ============================================================

import json
import hashlib
from typing import Dict, Any, Optional, List

from flask import session, request
import structlog

from backend.db import db_session  # asegura que conexión se cierre bien

logger = structlog.get_logger()


# -----------------------------------------------------------
# SECCIÓN 1: IDENTIFICADOR DE USUARIO (SESIÓN)
# -----------------------------------------------------------

def obtener_usuario_actual() -> str:
    """
    Devuelve el identificador del usuario.

    ✅ Objetivo: que el usuario sea *estable* incluso si el navegador bloquea
    cookies/almacenamiento ("Tracking Prevention").

    Estrategia:
    1) Si existe session["usuario"] → úsalo.
    2) Si no existe, usa fallback determinístico: hash(IP + User-Agent).
    """
    usuario = session.get("usuario")
    if usuario:
        return usuario

    # Fallback determinístico (no depende de cookies)
    ip = request.headers.get("X-Forwarded-For", request.remote_addr) or "0.0.0.0"
    # Si viene con múltiples IPs, tomar la primera
    if "," in ip:
        ip = ip.split(",")[0].strip()

    ua = request.headers.get("User-Agent", "unknown")
    base = f"{ip}|{ua}"
    digest = hashlib.sha1(base.encode("utf-8")).hexdigest()[:10]
    usuario = f"Anon-{digest}"

    # Intentar persistir en sesión (si el navegador lo permite)
    session["usuario"] = usuario
    session.modified = True

    logger.info("Creando usuario estable (fallback) por bloqueo de storage/cookies", usuario=usuario)
    return usuario


# -----------------------------------------------------------
# SECCIÓN 2: NIVEL (GAMIFICACIÓN SIMBÓLICA)
# -----------------------------------------------------------

def _calcular_nivel(puntos: int) -> str:
    """Calcula nivel simbólico según puntos.

    Reglas actuales:
    - < 10   → Inicial
    - < 30   → Intermedio
    - >= 30  → Avanzado

    Args:
        puntos: Parámetro de entrada.

    Returns:
        Valor tipo str.
    """
    if puntos < 10:
        return "Inicial"
    if puntos < 30:
        return "Intermedio"
    return "Avanzado"


# -----------------------------------------------------------
# SECCIÓN 3: NORMALIZACIÓN DE temas_aprendidos (JSON → lista)
# -----------------------------------------------------------

def _normalizar_temas_aprendidos(valor: Optional[str], usuario: str) -> List[str]:
    """Convierte temas_aprendidos (texto JSON) a lista segura de strings.

    Robustez:
    - None / "" → []
    - JSON inválido → []
    - JSON que no sea lista → []
    - si hay elementos no-string → se filtran

    Args:
        valor: Parámetro de entrada.
        usuario: Parámetro de entrada.

    Returns:
        Valor retornado por la función.
    """
    if not valor:
        return []

    try:
        temas = json.loads(valor)
        if not isinstance(temas, list):
            return []

        temas_limpios: List[str] = []
        for t in temas:
            if isinstance(t, str):
                t2 = t.strip()
                if t2:
                    temas_limpios.append(t2)

        return temas_limpios

    except json.JSONDecodeError:
        logger.warning(
            "Error al decodificar temas_aprendidos, se reinicia a lista vacía",
            usuario=usuario,
        )
        return []

    except Exception as e:
        logger.warning(
            "Fallo inesperado normalizando temas_aprendidos",
            error=str(e),
            usuario=usuario,
        )
        return []


# -----------------------------------------------------------
# SECCIÓN 4: CARGA (LECTURA) DEL PROGRESO DESDE BD
# -----------------------------------------------------------

def cargar_progreso(usuario: str) -> Dict[str, Any]:
    """Obtiene progreso del usuario desde la tabla 'progreso'.

    Retorna SIEMPRE:
    - usuario
    - puntos
    - temas_aprendidos (lista)
    - ciclo_academico
    - estado_materia
    - nivel (derivado de puntos)

    Casos:
    - Si no existe registro → estado inicial (puntos=0, temas=[]).
    - Si temas_aprendidos está corrupto → se normaliza.
    - Si falla algo → fallback seguro (no rompe el frontend).

    Args:
        usuario: Parámetro de entrada.

    Returns:
        Valor retornado por la función.
    """
    try:
        with db_session(write=False) as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT puntos, temas_aprendidos, ciclo_academico, estado_materia, nivel_materia
                FROM progreso
                WHERE usuario = ?
                """,
                (usuario,),
            )
            row = cur.fetchone()

        if not row:
            return {
                "usuario": usuario,
                "puntos": 0,
                "temas_aprendidos": [],
                "ciclo_academico": None,
                "estado_materia": None,
                "nivel_materia": None,
                "nivel": _calcular_nivel(0),
            }

        temas = _normalizar_temas_aprendidos(row["temas_aprendidos"], usuario)
        puntos = row["puntos"] or 0
        nivel = _calcular_nivel(puntos)

        data = dict(row)

        return {
            "usuario": usuario,
            "puntos": puntos,
            "temas_aprendidos": temas,
            "ciclo_academico": data.get("ciclo_academico"),
            "estado_materia": data.get("estado_materia"),
            "nivel_materia": data.get("nivel_materia"),
            "nivel": nivel,
        }

    except Exception as e:
        logger.error("Error al cargar progreso", error=str(e), usuario=usuario)
        return {
            "usuario": usuario,
            "puntos": 0,
            "temas_aprendidos": [],
            "ciclo_academico": None,
            "estado_materia": None,
            "nivel_materia": None,
            "nivel": _calcular_nivel(0),
        }


# -----------------------------------------------------------
# SECCIÓN 5: ACTUALIZACIÓN DE PROGRESO (puntos + tema)
# -----------------------------------------------------------

def actualizar_progreso(
    usuario: str,
    tema_nuevo: Optional[str] = None,
    puntos_delta: int = 1,
) -> Dict[str, Any]:
    """Actualiza progreso del usuario en BD y devuelve estado actualizado.

    Flujo:
    1) Buscar registro en progreso
    2) Cargar puntos y temas previos
    3) Sumar puntos_delta (sin permitir resultado negativo)
    4) Agregar tema_nuevo si es válido y no repetido
    5) UPDATE o INSERT
    6) Retornar dict actualizado (para UI inmediata)

    Args:
        usuario: Parámetro de entrada.
        tema_nuevo: Parámetro de entrada.
        puntos_delta: Parámetro de entrada.

    Returns:
        Valor retornado por la función.
    """
    try:
        with db_session(write=True) as conn:
            cur = conn.cursor()

            cur.execute(
                """
                SELECT puntos, temas_aprendidos, ciclo_academico, estado_materia
                FROM progreso
                WHERE usuario = ?
                """,
                (usuario,),
            )
            row = cur.fetchone()

            puntos = 0
            temas_aprendidos: List[str] = []
            ciclo_academico = None
            estado_materia = None

            if row:
                puntos = row["puntos"] or 0
                ciclo_academico = row["ciclo_academico"]
                estado_materia = row["estado_materia"]
                temas_aprendidos = _normalizar_temas_aprendidos(row["temas_aprendidos"], usuario)

            puntos = max(0, puntos + int(puntos_delta))

            if tema_nuevo:
                tema_nuevo = str(tema_nuevo).strip()
                if tema_nuevo and tema_nuevo not in temas_aprendidos:
                    temas_aprendidos.append(tema_nuevo)

            temas_json = json.dumps(temas_aprendidos, ensure_ascii=False)
            nivel = _calcular_nivel(puntos)

            if row:
                cur.execute(
                    """
                    UPDATE progreso
                    SET puntos = ?, temas_aprendidos = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE usuario = ?;
                    """,
                    (puntos, temas_json, usuario),
                )
            else:
                cur.execute(
                    """
                    INSERT INTO progreso (usuario, puntos, temas_aprendidos)
                    VALUES (?, ?, ?);
                    """,
                    (usuario, puntos, temas_json),
                )

        logger.info(
            "Progreso actualizado",
            usuario=usuario,
            puntos=puntos,
            temas_aprendidos=len(temas_aprendidos),
            nivel=nivel,
        )

        return {
            "usuario": usuario,
            "puntos": puntos,
            "temas_aprendidos": temas_aprendidos,
            "ciclo_academico": ciclo_academico,
            "estado_materia": estado_materia,
            "nivel": nivel,
        }

    except Exception as e:
        logger.error("Error al actualizar progreso", error=str(e), usuario=usuario)
        return {
            "usuario": usuario,
            "puntos": 0,
            "temas_aprendidos": [],
            "ciclo_academico": None,
            "estado_materia": None,
            "nivel": _calcular_nivel(0),
        }


# -----------------------------------------------------------
# SECCIÓN 6: PERFIL ACADÉMICO (ciclo + estado)
# -----------------------------------------------------------

def actualizar_perfil_usuario(
    usuario: str,
    ciclo_academico: Optional[str] = None,
    estado_materia: Optional[str] = None,
    nivel_materia: Optional[str] = None,
) -> None:
    """Actualiza campos académicos en la tabla 'progreso'.

    - Si existe registro: usa COALESCE para conservar datos anteriores
      si llega None.
    - Si no existe: crea registro nuevo.

    Args:
        usuario: Parámetro de entrada.
        ciclo_academico: Parámetro de entrada.
        estado_materia: Parámetro de entrada.
        nivel_materia: Parámetro de entrada.

    Returns:
        Valor retornado por la función.
    """
    try:
        with db_session(write=True) as conn:
            cur = conn.cursor()

            cur.execute(
                "SELECT id FROM progreso WHERE usuario = ?;",
                (usuario,),
            )
            row = cur.fetchone()

            if row:
                cur.execute(
                    """
                    UPDATE progreso
                    SET ciclo_academico = COALESCE(?, ciclo_academico),
                        estado_materia = COALESCE(?, estado_materia),
                        nivel_materia = COALESCE(?, nivel_materia),
                        updated_at = CURRENT_TIMESTAMP
                    WHERE usuario = ?;
                    """,
                    (ciclo_academico, estado_materia, nivel_materia, usuario),
                )
            else:
                cur.execute(
                    """
                    INSERT INTO progreso (usuario, ciclo_academico, estado_materia, nivel_materia)
                    VALUES (?, ?, ?, ?);
                    """,
                    (usuario, ciclo_academico, estado_materia, nivel_materia),
                )

        logger.info(
            "Perfil de usuario actualizado",
            usuario=usuario,
            ciclo_academico=ciclo_academico,
            estado_materia=estado_materia,
            nivel_materia=nivel_materia,
        )

    except Exception as e:
        logger.error("Error al actualizar perfil de usuario", error=str(e), usuario=usuario)
