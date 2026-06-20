"""
Proyecto: YELIA4AP
Archivo: backend/services/memory_summary_service.py
Descripción: Módulo del backend para la lógica asociada a esta carpeta/funcionalidad.

Revisión: 2026-02-10
"""
from __future__ import annotations

"""
Archivo: backend/services/memory_summary_service.py
Proyecto: YELIA4AP
Última revisión: 2026-02-10

Módulo de backend en Python.

Convenciones:
- Funciones pequeñas, nombres descriptivos y manejo de errores explícito.
- Evitar prints en producción: usar logging si aplica.
"""


#
# Archivo: backend/services/memory_summary_service.py
# Rol: Módulo del backend (Flask) de YELIA4AP.


"""Memory Summary Service
Archivo del backend del sistema YELIA4AP.

Responsabilidad:
- Implementa la lógica asociada a este módulo.

backend/services/memory_summary_service.py

Backend Flask — YELIA (módulo de servidor)

Propósito:
    Proveer un mecanismo de **resumen automático del hilo (memory summary)** para
    mejorar la continuidad de conversación cuando el historial enviado al LLM es
    corto (por límites de tokens / hosting).

Idea (estilo ChatGPT):
    - Cada N mensajes guardados en `messages`, se recalcula un resumen breve.
    - Se guarda en la tabla `conversaciones` (columnas: memory_summary,
      memory_msg_count, memory_updated_at).
    - En el siguiente turno, el backend puede inyectar este resumen como contexto
      adicional, evitando que el modelo “olvide” el hilo.

Notas:
    - Es *best-effort*: si falla el resumen (sin internet/API), no debe romper el chat.
    - Mantener el resumen corto: 8–14 líneas, con tareas actuales y decisiones.
"""
# =====================================
# Imports
# =====================================


from typing import Any, Dict, List, Optional

import structlog

from backend.db.session import (

# =====================================
# Configuración / Constantes
# =====================================
    db_session,
    obtener_memoria_conversacion,
    actualizar_memoria_conversacion,
)
from backend.nlp.provider_router import seleccionar_proveedor

logger = structlog.get_logger()


DEFAULT_EVERY_N_MESSAGES: int = 8
DEFAULT_MAX_MESSAGES_FOR_SUMMARY: int = 24
# =====================================
# Funciones / Clases
# =====================================



def _count_messages(conv_id: int, usuario: str) -> int:
    """Cuenta mensajes de una conversación."""
    with db_session(write=False) as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT COUNT(1) AS c FROM messages WHERE conv_id = ? AND usuario = ?;",
            (int(conv_id), usuario),
        )
        row = cur.fetchone()
        return int(row["c"] or 0) if row else 0


def _fetch_recent_messages(conv_id: int, usuario: str, limit: int) -> List[Dict[str, str]]:
    """Trae los últimos mensajes (user/bot) en orden cronológico."""
    with db_session(write=False) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT remitente, contenido
            FROM messages
            WHERE conv_id = ? AND usuario = ?
            ORDER BY id DESC
            LIMIT ?;
            """,
            (int(conv_id), usuario, int(limit)),
        )
        rows = list(reversed(cur.fetchall()))

    out: List[Dict[str, str]] = []
    for r in rows:
        out.append({
            "role": "user" if (r["remitente"] == "user") else "assistant",
            "content": (r["contenido"] or "").strip(),
        })
    return out


def _build_summary_prompt(
    *,
    usuario: str,
    existing_summary: Optional[str],
    recent_msgs: List[Dict[str, str]],
) -> Dict[str, str]:
    """Construye el prompt para resumir manteniendo continuidad."""

    # Convertimos mensajes recientes a formato legible
    turns: List[str] = []
    for m in recent_msgs:
        who = "ESTUDIANTE" if m["role"] == "user" else "YELIA"
        txt = (m["content"] or "").strip()
        if not txt:
            continue
        # recorta por seguridad
        if len(txt) > 900:
            txt = txt[:900] + "..."
        turns.append(f"- {who}: {txt}")

    transcript = "\n".join(turns) if turns else "(sin mensajes recientes)"

    sys = (
        "Eres un sistema que crea un **resumen de memoria** para un tutor virtual llamado YELIA.\n"
        "Objetivo: que la IA NO pierda contexto aunque el historial sea corto.\n\n"
        "Reglas del resumen:\n"
        "- Escribe en ESPAÑOL.\n"
        "- Máximo 14 líneas.\n"
        "- Incluye: (1) tema/objetivo actual, (2) qué se explicó ya, (3) dudas pendientes, "
        "(4) archivos/adjuntos relevantes si se mencionan.\n"
        "- No inventes información. Si algo no está, escribe 'no especificado'.\n"
        "- Formato recomendado:\n"
        "  • Contexto: ...\n"
        "  • Progreso: ...\n"
        "  • Pendiente: ...\n"
        "  • Adjuntos: ...\n"
    )

    user = (
        f"Usuario: {usuario}\n\n"
        f"RESUMEN ANTERIOR (si existe):\n{(existing_summary or '—')}\n\n"
        "MENSAJES RECIENTES:\n"
        f"{transcript}\n\n"
        "Ahora genera el NUEVO RESUMEN (reemplaza/actualiza el anterior)."
    )

    return {"system": sys, "user": user}


def recompute_memory_summary(
    *,
    usuario: str,
    conv_id: int,
    existing_summary: Optional[str] = None,
    max_recent_messages: int = DEFAULT_MAX_MESSAGES_FOR_SUMMARY,
) -> str:
    """Genera un nuevo resumen usando el proveedor NLP disponible."""

    recent = _fetch_recent_messages(conv_id, usuario, max_recent_messages)
    p = _build_summary_prompt(usuario=usuario, existing_summary=existing_summary, recent_msgs=recent)

    out = seleccionar_proveedor(
        p["system"],
        p["user"],
        max_tokens=450,
        modo_interaccion="normal",
        nivel="basica",
    )

    summary = (out.get("respuesta") or out.get("reply") or "").strip()
    # Guardrail: si quedó demasiado largo, recortamos.
    if len(summary) > 2200:
        summary = summary[:2200] + "..."
    return summary


def update_memory_summary_if_needed(
    *,
    usuario: str,
    conv_id: int,
    every_n_messages: int = DEFAULT_EVERY_N_MESSAGES,
) -> Optional[str]:
    """Actualiza el resumen si el hilo creció lo suficiente.

    Retorna:
        - El resumen actualizado si se recalculó.
        - None si no era necesario o si ocurrió un fallo.
    """
    usuario = (usuario or "anonimo").strip() or "anonimo"

    try:
        mem = obtener_memoria_conversacion(int(conv_id), usuario)
        existing = (mem.get("memory_summary") or "").strip() or None
        last_count = int(mem.get("memory_msg_count") or 0)

        total = _count_messages(int(conv_id), usuario)
        if total <= 0:
            return None

        # Si no han pasado N mensajes desde el último resumen, no hacemos nada.
        if (total - last_count) < int(every_n_messages):
            return None

        new_summary = recompute_memory_summary(
            usuario=usuario,
            conv_id=int(conv_id),
            existing_summary=existing,
        )
        if not new_summary:
            return None

        actualizar_memoria_conversacion(
            int(conv_id),
            usuario,
            memory_summary=new_summary,
            memory_msg_count=total,
        )

        try:
            logger.info(
                "Memory summary actualizado",
                usuario=usuario,
                conv_id=int(conv_id),
                total_messages=total,
                prev_count=last_count,
            )
        except Exception:
            pass

        return new_summary

    except Exception as e:
        # Best-effort: jamás romper el chat por esto.
        try:
            logger.warning("No se pudo actualizar memory summary", usuario=usuario, conv_id=int(conv_id), error=str(e))
        except Exception:
            pass
        return None
