"""
Proyecto: YELIA4AP
Archivo: backend/routes/chat_routes_conversations.py
Descripción: Módulo del backend para la lógica asociada a esta carpeta/funcionalidad.

Revisión: 2026-02-10
"""
"""Chat Routes Conversations
Archivo del backend del sistema YELIA4AP.

Responsabilidad:
- Implementa la lógica asociada a este módulo.
"""

#
# Archivo: backend/routes/chat_routes_conversations.py
# Rol: Módulo del backend (Flask) de YELIA4AP.

"""backend/routes/chat_routes_conversations.py

Backend Flask — YELIA (módulo de servidor)

Propósito:
    Este archivo pertenece al backend (Flask) de YELIA. Contiene lógica de servidor
    y/o utilidades que soportan rutas, servicios, persistencia y orquestación NLP.
"""

# ============================================================================
# IMPORTS
# ============================================================================
import os
from pathlib import Path
import structlog
from flask import request

from backend.services.progreso_service import actualizar_perfil_usuario, cargar_progreso
from backend.db.session import (
    db_session,
    obtener_conversaciones_usuario,
    obtener_mensajes_conversacion,
)

from .chat_routes import (
    chat_bp,
    limiter,
    _ok,
    _err,
    obtener_usuario_actual,
)

logger = structlog.get_logger()


# ============================================================================
# ENDPOINTS
# ============================================================================
@chat_bp.route("/api/history", methods=["GET"])
@limiter.limit(os.getenv("RATE_LIMIT_CONVERSATIONS", "60 per minute"))
def api_history():
    """
    Lista conversaciones del usuario actual.
    Se limita para evitar scraping/abuso del historial.
    """
    usuario = obtener_usuario_actual()
    try:
                # Paginación: /api/history?limit=20&offset=0
        try:
            limit = int(request.args.get("limit", 20))
        except Exception:
            limit = 20
        try:
            offset = int(request.args.get("offset", 0))
        except Exception:
            offset = 0
        limit = max(1, min(limit, 200))
        offset = max(0, offset)

        conversaciones = obtener_conversaciones_usuario(usuario, limite=limit, offset=offset)
        convs = conversaciones
        has_more = len(convs) > limit
        convs = convs[:limit]
        convs = [
            {"id": c["id"], "titulo": c["titulo"] or f"Conversación {c['id']}", "created_at": c["created_at"]}
            for c in convs
        ]
        return _ok({"conversations": convs, "paging": {"limit": limit, "offset": offset, "has_more": has_more}})
    except Exception as e:
        logger.error("Error en /api/history", error=str(e), usuario=usuario)
        return _err("No se pudo obtener el historial.", 500)


@chat_bp.route("/api/history", methods=["DELETE"])
@limiter.limit(os.getenv("RATE_LIMIT_DELETE_HISTORY", "5 per hour"))
def api_delete_history():
    """Elimina todas las conversaciones del usuario actual."""
    usuario = obtener_usuario_actual()
    try:
        with db_session(write=True) as conn:
            cur = conn.cursor()
            cur.execute("SELECT id FROM conversaciones WHERE usuario = ?;", (usuario,))
            conv_ids = [int(row["id"]) for row in cur.fetchall()]
            if conv_ids:
                placeholders = ",".join("?" for _ in conv_ids)
                cur.execute(f"DELETE FROM messages WHERE conv_id IN ({placeholders});", tuple(conv_ids))
                cur.execute(f"DELETE FROM conversaciones WHERE id IN ({placeholders});", tuple(conv_ids))

        return _ok({"deleted": len(conv_ids)})
    except Exception as e:
        logger.error("Error al eliminar historial", error=str(e), usuario=usuario)
        return _err("No se pudo eliminar el historial.", 500)


@chat_bp.route("/api/conversation/<int:conv_id>", methods=["GET"])
@limiter.limit(os.getenv("RATE_LIMIT_CONVERSATION", "60 per hour"))
def api_conversation(conv_id: int):
    """Devuelve una conversación específica:

    - valida pertenencia al usuario (seguridad)
    - permite limit por query param (acotado a 500)

    Args:
        conv_id: Parámetro de entrada.

    Returns:
        Resultado de la operación.
    """
    usuario = obtener_usuario_actual()
    try:
        # Validación de pertenencia: evita acceso cruzado entre usuarios
        with db_session(write=False) as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT usuario, titulo FROM conversaciones WHERE id = ? AND usuario = ?;",
                (conv_id, usuario),
            )
            cabecera = cur.fetchone()
            if not cabecera:
                return _err("Conversación no encontrada (puede que ya fue eliminada).", 200)

        # Límite de mensajes retornados (protección de payload)
        lim = request.args.get("limit", "200")
        try:
            lim_int = max(1, min(int(lim), 500))
        except Exception:
            lim_int = 200

        mensajes = obtener_mensajes_conversacion(conv_id, limite=lim_int, ascendente=True)
        return _ok({
            "conversation": {
                "id": conv_id,
                "usuario": cabecera["usuario"],
                "titulo": cabecera["titulo"],
                "messages": mensajes
            }
        })
    except Exception as e:
        logger.error("Error en /api/conversation", error=str(e), usuario=usuario)
        return _err("No se pudo obtener la conversación.", 500)


@chat_bp.route("/api/update-profile", methods=["POST"])
@limiter.limit(os.getenv("RATE_LIMIT_PROFILE", "20 per hour"))
def api_update_profile():
    """
    Actualiza datos académicos del perfil del usuario.
    Sirve para personalizar respuestas (ciclo, estado de materia).
    """
    usuario = obtener_usuario_actual()
    data = request.get_json(silent=True) or {}
    ciclo = data.get("ciclo_academico")
    estado = data.get("estado_materia")
    nivel_materia = data.get("nivel_materia")
    nickname = data.get("nickname")

    try:
        actualizar_perfil_usuario(usuario, ciclo_academico=ciclo, estado_materia=estado, nivel_materia=nivel_materia)
        # Nickname se guarda en perfil JSON (no requiere migraciones)
        try:
            from backend.repositories.student_profile_repo import set_nickname
            set_nickname(usuario, nickname)
        except Exception:
            pass
        return _ok({"usuario": usuario})
    except Exception as e:
        logger.error("Error en /api/update-profile", error=str(e), usuario=usuario)
        return _err("No se pudo actualizar el perfil.", 500)


@chat_bp.route("/api/progreso", methods=["GET"])
@limiter.limit(os.getenv("RATE_LIMIT_PROGRESO", "60 per hour"))
def api_progreso():
    """
    Devuelve el progreso del usuario (puntos, temas, etc.).
    """
    usuario = obtener_usuario_actual()
    try:
        progreso = cargar_progreso(usuario)
        teacher_actions = []
        try:
            from backend.repositories.student_profile_repo import get_profile
            profile = get_profile(usuario) or {}
            teacher_actions = list(profile.get("teacher_actions") or [])[-5:]
        except Exception:
            teacher_actions = []
        return _ok({"progreso": progreso, "teacher_actions": teacher_actions})
    except Exception as e:
        logger.error("Error en /api/progreso", error=str(e), usuario=usuario)
        return _err("No se pudo obtener el progreso.", 500)


@chat_bp.route("/api/conversation/<int:conv_id>/rename", methods=["POST"])
@limiter.limit(os.getenv("RATE_LIMIT_RENAME", "20 per hour"))
def api_rename_conversation(conv_id: int):
    """Permite renombrar una conversación (solo si pertenece al usuario).

    Args:
        conv_id: Parámetro de entrada.

    Returns:
        Resultado de la operación.
    """
    usuario = obtener_usuario_actual()
    data = request.get_json(silent=True) or {}
    nuevo_titulo = (data.get("titulo") or "").strip()
    if not nuevo_titulo:
        return _err("El título no puede estar vacío.", 400)

    try:
        with db_session(write=True) as conn:
            cur = conn.cursor()
            cur.execute(
                "UPDATE conversaciones SET titulo = ? WHERE id = ? AND usuario = ?;",
                (nuevo_titulo, conv_id, usuario),
            )
            if cur.rowcount == 0:
                return _err("Conversación no encontrada (puede que ya fue eliminada).", 200)
        return _ok({"id": conv_id, "titulo": nuevo_titulo})
    except Exception as e:
        logger.error("Error al renombrar conversación", error=str(e), usuario=usuario)
        return _err("No se pudo renombrar la conversación.", 500)


@chat_bp.route("/api/conversation/<int:conv_id>", methods=["DELETE"])
@limiter.limit(os.getenv("RATE_LIMIT_DELETE", "10 per hour"))
def api_delete_conversation(conv_id: int):
    """Elimina una conversación y sus mensajes asociados.

    Se limita fuertemente por rate limit (acción destructiva).

    Args:
        conv_id: Parámetro de entrada.

    Returns:
        Resultado de la operación.
    """
    usuario = obtener_usuario_actual()
    try:
        with db_session(write=True) as conn:
            cur = conn.cursor()
            cur.execute("SELECT id FROM conversaciones WHERE id = ? AND usuario = ?;", (conv_id, usuario))
            if not cur.fetchone():
                return _err("Conversación no encontrada (puede que ya fue eliminada).", 200)

            cur.execute("DELETE FROM messages WHERE conv_id = ?;", (conv_id,))
            cur.execute("DELETE FROM conversaciones WHERE id = ?;", (conv_id,))

        return _ok({})
    except Exception as e:
        logger.error("Error al eliminar conversación", error=str(e), usuario=usuario)
        return _err("No se pudo eliminar la conversación.", 500)


# ============================================================================
# VALIDACIÓN DE ADJUNTOS — EXTENSIÓN (Whitelist)
# ============================================================================
def _allowed_attachment_ext(filename: str) -> bool:
    """Valida extensión permitida para adjuntos (whitelist).

    Args:
        filename: Parámetro de entrada.

    Returns:
        Valor tipo bool.
    """
    allowed = {"pdf", "png", "jpg", "jpeg", "txt", "docx"}
    ext = (filename.rsplit(".", 1)[-1].lower() if "." in filename else "")
    return ext in allowed


# ============================================================================
# VALIDACIÓN DE ADJUNTOS — FIRMA (MAGIC BYTES)
# ============================================================================
def _magic_bytes_ok(ext: str, file_path: "Path") -> bool:
    """Valida la firma real del archivo (magic bytes) según extensión.

    Nota:
    - El mimetype puede ser falsificado por el cliente/navegador.
    - Esta verificación es un control adicional de seguridad.
    - Para TXT se permite cualquier contenido.
    - Para DOCX se valida que sea ZIP (comienza con 'PK'), que es el contenedor típico.

    Args:
        ext: Parámetro de entrada.
        file_path: Parámetro de entrada.

    Returns:
        Valor tipo bool.
    """
    try:
        ext = (ext or "").lower()
        from pathlib import Path
        p = Path(file_path)
        if not p.is_file():
            return False

        with p.open("rb") as f:
            head = f.read(16)

        if ext == "pdf":
            return head.startswith(b"%PDF")
        if ext == "png":
            return head.startswith(b"\x89PNG\r\n\x1a\n")
        if ext in ("jpg", "jpeg"):
            return head.startswith(b"\xff\xd8\xff")
        if ext == "docx":
            return head.startswith(b"PK")  # ZIP container
        if ext == "txt":
            return True

        # Si no está mapeado, se rechaza por defecto
        return False
    except Exception:
        return False

# ============================================================================
# VALIDACIÓN DE ADJUNTOS — MIME TYPE
# ============================================================================
def _allowed_attachment_mime(ext: str, mimetype: str | None) -> bool:
    """Valida el mimetype reportado por el navegador/cliente contra la extensión.

    Args:
        ext: Parámetro de entrada.
        mimetype: Parámetro de entrada.

    Returns:
        Valor tipo bool.
    """
    if not mimetype:
        return False

    ext = (ext or "").lower()
    mimetype = (mimetype or "").lower().split(";", 1)[0].strip()

    allowed_map = {
        "pdf": {"application/pdf"},
        "png": {"image/png"},
        "jpg": {"image/jpeg"},
        "jpeg": {"image/jpeg"},
        "txt": {"text/plain"},
        "docx": {"application/vnd.openxmlformats-officedocument.wordprocessingml.document"},
    }

    return mimetype in allowed_map.get(ext, set())
