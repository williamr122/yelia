"""
Proyecto: YELIA4AP
Archivo: backend/routes/chat_routes_chat.py
Descripción: Módulo del backend para la lógica asociada a esta carpeta/funcionalidad.

Revisión: 2026-02-10
"""
"""Chat Routes Chat
Archivo del backend del sistema YELIA4AP.

Responsabilidad:
- Implementa la lógica asociada a este módulo.
"""

#
# Archivo: backend/routes/chat_routes_chat.py
# Rol: Módulo del backend (Flask) de YELIA4AP.

"""backend/routes/chat_routes_chat.py

Backend Flask — YELIA (módulo de servidor)

Propósito:
    Este archivo pertenece al backend (Flask) de YELIA. Contiene lógica de servidor
    y/o utilidades que soportan rutas, servicios, persistencia y orquestación NLP.

NOTA (FIX PRO):
    - Antes se guardaban adjuntos en PRIVATE_UPLOAD_DIR, pero el análisis/lectura
      buscaba en static/uploads, causando "Archivo no encontrado".
    - Ahora se resuelve la ruta del adjunto buscando primero en PRIVATE_UPLOAD_DIR
      y, por compatibilidad, en static/uploads (si existen adjuntos antiguos).
"""

# ============================================================================
# IMPORTS
# ============================================================================
import os
import time
import hashlib
import io
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from backend.config import MAX_HISTORY  # Límite de historial (demo/hosting)

import structlog
from flask import jsonify, request, send_file, session
from werkzeug.utils import secure_filename

from backend.db.session import (
    db_session,
    crear_conversacion,
    obtener_foco_conversacion,
    actualizar_foco_conversacion,
    obtener_memoria_conversacion,
    get_or_create_usuario,
    registrar_interaccion,
)
from backend.routes.chat_routes_conversations import (
    _allowed_attachment_ext,
    _allowed_attachment_mime,
    _magic_bytes_ok,
)

from backend.services.chat_service import procesar_mensaje_chat
from backend.services.memory_summary_service import update_memory_summary_if_needed
from backend.services.progreso_service import actualizar_progreso
from backend.services.tutor_pro_service import build_tutor_additions
from backend.services.recommendation_service import (
    build_recommendations,
    recommendations_to_suggestions,
)
from backend.services.emotion_service import detect_emotion
from backend.services.personalized_feedback_service import build_personalized_feedback
from backend.services.adaptive_profile_service import update_adaptive_profile
from backend.services.adaptive_content_service import build_adaptive_plan, save_adaptive_plan
from backend.services.structured_quiz_service import (
    build_structured_quiz,
    canonical_topic,
    close_structured_quiz,
    format_grade_for_chat,
    format_quiz_for_chat,
    get_active_quiz,
    grade_structured_quiz,
    parse_student_answers,
    requested_count,
    save_structured_quiz,
)
from backend.nlp.intent import detectar_intencion_semantica, detectar_modo_interaccion
from backend.repositories.attachments_repo import (
    get_attachment,
    save_attachment_analysis,
    get_attachment_analysis,
)
from backend.repositories.student_profile_repo import get_profile
from backend.repositories.metrics_repo import log_recommendations, log_adaptive_feedback
from backend.services.attachment_analyzer import extract_text_from_file

from .chat_routes import (
    _validate_chat_payload,
    chat_bp,
    limiter,
    _ok,
    _err,
    obtener_usuario_actual,
    log_event,
    log_perf,
    save_attachment,
)

logger = structlog.get_logger()

# Fallback de adjuntos para que el chat no se caiga si la tabla attachments falla.
# Se usa solo como respaldo temporal durante la sesión del servidor.
_FALLBACK_ATTACHMENTS = {}
_FALLBACK_NEXT_ATT_ID = -1


# ============================================================================
# HELPERS (Fase 2 adaptativa)
# ============================================================================
_ONLINE_RESOURCE_TERMS = (
    "recomienda",
    "recomiendas",
    "recomendacion",
    "recomendaciones",
    "recurso",
    "recursos",
    "fuente",
    "fuentes",
    "link",
    "links",
    "enlace",
    "enlaces",
    "web",
    "internet",
    "tutorial",
    "tutoriales",
    "documentacion",
    "documentación",
)


def _wants_online_resources(text: str) -> bool:
    t = (text or "").strip().lower()
    return any(term in t for term in _ONLINE_RESOURCE_TERMS)


def _append_web_resources_to_reply_direct(
    reply: str,
    user_text: str,
    recommendations: List[Dict[str, Any]],
) -> str:
    if not _wants_online_resources(user_text):
        return reply

    web_items = [
        rec for rec in (recommendations or [])
        if rec.get("type") == "web_resource" and rec.get("url")
    ]
    if not web_items:
        return reply

    existing = reply or ""
    lines = []
    for rec in web_items[:3]:
        url = str(rec.get("url") or "").strip()
        if not url or url in existing:
            continue
        title = str(rec.get("title") or "Recurso web").strip()
        explanation = str(rec.get("explanation") or rec.get("reason") or "").strip()
        reason = str(rec.get("reason") or "").strip()
        level = str(rec.get("level_used") or "intermedio").strip()
        emotion = str(rec.get("emotion_used") or "neutral").strip()
        topic = str(rec.get("topic_used") or "Programacion Avanzada").strip()
        lines.extend([
            f"- **{title}**",
            f"  Enlace directo: {url}",
            f"  Por que te sirve: {explanation or reason}",
            f"  Nivel usado: {level} | Emocion detectada: {emotion} | Tema: {topic}",
        ])

    if not lines:
        return reply

    section = "Recursos web recomendados:\n" + "\n".join(lines)
    return (existing.strip() + "\n\n" + section).strip()


def _append_history_recommendations_to_reply(reply: str, recommendations: List[Dict[str, Any]]) -> str:
    history_items = [rec for rec in (recommendations or []) if rec.get("history_based")]
    if not history_items:
        return reply

    existing = reply or ""
    lines = []
    for rec in history_items[:2]:
        title = str(rec.get("title") or "Recomendacion por historial").strip()
        explanation = str(rec.get("explanation") or "").strip()
        reason = str(rec.get("history_reason") or rec.get("reason") or "").strip()
        action = str(rec.get("message") or "").strip()
        lines.extend([
            f"- **{title}**",
            f"  Motivo: {explanation or reason}",
            f"  Accion sugerida: {action}",
        ])

    if not lines:
        return reply

    section = "Recomendacion por historial:\n" + "\n".join(lines)
    if section in existing:
        return reply
    return (existing.strip() + "\n\n" + section).strip()


def _avatar_contract(
    *,
    emotion: Dict[str, Any],
    mode: str,
    intent: str,
    interaction_mode: str,
    has_reply: bool,
) -> Dict[str, Any]:
    emotion_name = str((emotion or {}).get("emotion") or "neutral").strip().lower() or "neutral"
    expression = str((emotion or {}).get("avatar_expression") or emotion_name).strip().lower() or "neutral"
    try:
        intensity = float((emotion or {}).get("intensity") or 0)
    except Exception:
        intensity = 0.0
    intensity = max(0.0, min(1.0, intensity))

    mode = (mode or "").strip().lower()
    intent = (intent or "").strip().lower()
    interaction_mode = (interaction_mode or "").strip().lower()

    state = "speaking" if has_reply else "idle"
    if mode in {"error"}:
        state = "error"
        expression = "concerned"
    elif interaction_mode in {"quiz", "quiz_grade"} or intent in {"quiz", "evaluacion_respuesta"}:
        expression = "curious" if expression in {"neutral", ""} else expression
    elif emotion_name in {"confused", "frustrated", "anxious"}:
        expression = "supportive" if expression in {"neutral", ""} else expression

    if intent in {"quiz", "evaluacion_respuesta"}:
        gesture = "point"
    elif emotion_name in {"confused", "frustrated", "anxious"}:
        gesture = "reassure"
    elif intent in {"explicar", "teoria", "debug"}:
        gesture = "explain"
    else:
        gesture = "none"

    return {
        "version": "avatar.v1",
        "state": state,
        "emotion": emotion_name,
        "expression": expression,
        "gesture": gesture,
        "intensity": intensity,
        "speaking": state == "speaking",
        "mouth_shape": "talk" if state == "speaking" else "small" if state == "error" else "closed",
    }


@chat_bp.route("/api/voice/tts", methods=["POST"])
@limiter.limit(os.getenv("RATE_LIMIT_TTS", "30 per minute"))
def api_voice_tts():
    """Genera audio MP3 con gTTS como proveedor Google TTS opcional."""
    data = request.get_json(silent=True) or {}
    text = str(data.get("text") or "").strip()
    lang = str(data.get("lang") or "es").strip().lower()[:8] or "es"
    max_len = int(os.getenv("TTS_MAX_TEXT_LEN", "1200"))

    if not text:
        return _err("Falta texto para sintetizar voz.", 400)
    if len(text) > max_len:
        text = text[:max_len]

    try:
        from gtts import gTTS

        audio = io.BytesIO()
        gTTS(text=text, lang=lang).write_to_fp(audio)
        audio.seek(0)
        return send_file(
            audio,
            mimetype="audio/mpeg",
            as_attachment=False,
            download_name="yelia-tts.mp3",
            max_age=0,
        )
    except Exception as exc:
        logger.warning("No se pudo generar TTS con gTTS", error=str(exc))
        return _err("No se pudo generar audio TTS.", 503)


def _adaptive_profile_context(profile: Dict[str, Any]) -> str:
    adaptive = (profile or {}).get("adaptive") or {}
    summary = (profile or {}).get("adaptive_summary") or {}
    weak = adaptive.get("weak_topics") or summary.get("weak_topics") or []
    mastered = adaptive.get("mastered_topics") or summary.get("mastered_topics") or []
    recent = adaptive.get("recent_recommendations") or []
    lines = [
        "PERFIL ADAPTATIVO DEL ESTUDIANTE:",
        f"- Nivel actual: {(profile or {}).get('level_current') or adaptive.get('last_level') or 'basico'}",
        f"- Estado de aprendizaje: {adaptive.get('learning_state') or summary.get('learning_state') or 'active'}",
        f"- Ultima emocion: {adaptive.get('last_emotion') or summary.get('last_emotion') or 'neutral'}",
        f"- Ultimo tema: {adaptive.get('last_topic') or summary.get('last_topic') or 'Programacion Avanzada'}",
        f"- Siguiente mejor accion: {adaptive.get('next_best_action') or summary.get('next_best_action') or 'recommend_next_resource'}",
    ]
    if weak:
        lines.append(f"- Temas debiles: {', '.join(str(x) for x in weak[:5])}")
    if mastered:
        lines.append(f"- Temas dominados: {', '.join(str(x) for x in mastered[:5])}")
    if recent:
        titles = [str(item.get("title") or item.get("type") or "") for item in recent[:3] if isinstance(item, dict)]
        if titles:
            lines.append(f"- Recomendaciones recientes: {', '.join(titles)}")
    lines.append("Usa este perfil para adaptar dificultad, ejemplos, practica y retroalimentacion.")
    return "\n".join(lines)


def _normalize_recommendation_emotion(raw: Any, user_text: str) -> Dict[str, Any]:
    if isinstance(raw, dict):
        emotion = str(raw.get("emotion") or raw.get("key") or "neutral").strip() or "neutral"
        return {
            **raw,
            "emotion": emotion,
            "label": raw.get("label") or emotion,
        }
    if isinstance(raw, str) and raw.strip():
        emotion = raw.strip().lower()
        return {
            "emotion": emotion,
            "label": emotion,
            "confidence": 0.6,
            "intensity": 0.0,
            "signals": [],
        }
    return detect_emotion(user_text)


@chat_bp.route("/api/recommendations", methods=["POST"])
@limiter.limit(os.getenv("RATE_LIMIT_RECOMMENDATIONS", "60 per hour"))
def api_recommendations():
    """Genera recomendaciones de recursos como mejora aislada de fase 2.

    Este endpoint no llama a proveedores de IA. Usa reglas explicables,
    perfil adaptativo del estudiante y catalogo curado para responder rapido
    y registrar evidencia en metrics_recommendations.
    """
    usuario = obtener_usuario_actual()
    data = request.get_json(silent=True) or {}

    user_text = str(
        data.get("message")
        or data.get("query")
        or data.get("text")
        or data.get("prompt")
        or ""
    ).strip()
    if not user_text:
        return _err("El campo 'message' o 'query' es obligatorio.", 400, code="VALIDATION_ERROR")

    topic = str(data.get("topic") or data.get("tema") or "Programacion Avanzada").strip()
    level = str(data.get("level") or data.get("nivel") or "intermedio").strip()
    intent = str(data.get("intent") or data.get("intencion") or detectar_intencion_semantica(user_text.lower())).strip()

    conversation_id = data.get("conversation_id")
    try:
        conversation_id = int(conversation_id) if conversation_id not in (None, "", "null", "undefined") else None
    except Exception:
        conversation_id = None

    emotion = _normalize_recommendation_emotion(data.get("emotion"), user_text)

    try:
        profile = get_profile(usuario)
    except Exception:
        profile = {}

    recommendations = build_recommendations(
        user_text=user_text,
        topic=topic,
        level=level,
        emotion=emotion,
        intent=intent,
        history_profile=profile,
    )
    suggestions = recommendations_to_suggestions(recommendations)

    evidence_logged = False
    if data.get("log", True) is not False:
        try:
            log_recommendations(
                usuario=usuario,
                conversation_id=conversation_id,
                recommendations=recommendations,
            )
            evidence_logged = bool(recommendations)
        except Exception:
            evidence_logged = False

    return _ok({
        "contract_version": "recommendations.v1",
        "usuario": usuario,
        "conversation_id": conversation_id,
        "topic": topic,
        "level": level,
        "intent": intent,
        "emotion": emotion,
        "recommendations": recommendations,
        "suggestions": suggestions,
        "evidence": {
            "logged": evidence_logged,
            "table": "metrics_recommendations",
            "count": len(recommendations),
        },
    })


@chat_bp.route("/api/personalized-feedback", methods=["POST"])
@limiter.limit(os.getenv("RATE_LIMIT_PERSONALIZED_FEEDBACK", "60 per hour"))
def api_personalized_feedback():
    """Genera retroalimentacion personalizada como mejora aislada de fase 2."""
    usuario = obtener_usuario_actual()
    data = request.get_json(silent=True) or {}

    user_text = str(
        data.get("message")
        or data.get("answer")
        or data.get("response")
        or data.get("text")
        or ""
    ).strip()
    if not user_text:
        return _err("El campo 'message' o 'answer' es obligatorio.", 400, code="VALIDATION_ERROR")

    topic = str(data.get("topic") or data.get("tema") or "Programacion Avanzada").strip()
    level = str(data.get("level") or data.get("nivel") or "intermedio").strip()
    intent = str(data.get("intent") or data.get("intencion") or detectar_intencion_semantica(user_text.lower())).strip()
    mode = str(data.get("mode") or data.get("modo") or detectar_modo_interaccion(user_text)).strip()
    emotion = _normalize_recommendation_emotion(data.get("emotion"), user_text)

    conversation_id = data.get("conversation_id")
    try:
        conversation_id = int(conversation_id) if conversation_id not in (None, "", "null", "undefined") else None
    except Exception:
        conversation_id = None

    feedback = build_personalized_feedback(
        user_text=user_text,
        topic=topic,
        level=level,
        emotion=emotion,
        intent=intent,
        mode=mode,
    )

    if not feedback:
        feedback = {
            "contract_version": "personalized_feedback.v1",
            "detected": False,
            "kind": "no_signal",
            "status": "no_action",
            "score_delta": 0,
            "topic": topic,
            "level": level,
            "emotion": emotion.get("emotion") or "neutral",
            "summary": "Sin senal suficiente para retroalimentacion personalizada",
            "action": "Continuar con una pregunta o practica corta.",
            "reason": "El mensaje no expresa comprension, confusion, practica ni solicitud de revision.",
            "next_action": "continue_learning",
            "recommendation": "Mantener seguimiento sin modificar el perfil.",
            "append_markdown": "",
            "evidence_tags": ["no_signal", topic, level],
        }

    profile_summary = None
    if data.get("update_profile", True) is not False:
        try:
            profile = update_adaptive_profile(
                student_id=usuario,
                topic=topic,
                level=level,
                emotion=emotion,
                intent=intent,
                recommendations=[],
                personalized_feedback=feedback if feedback.get("detected") else None,
            )
            profile_summary = (profile or {}).get("adaptive_summary")
        except Exception:
            profile_summary = None

    evidence_logged = False
    if data.get("log", True) is not False and feedback.get("detected"):
        try:
            log_adaptive_feedback(
                usuario=usuario,
                conversation_id=conversation_id,
                feedback=feedback,
            )
            evidence_logged = True
        except Exception:
            evidence_logged = False

    return _ok({
        "contract_version": "personalized_feedback.v1",
        "usuario": usuario,
        "conversation_id": conversation_id,
        "topic": topic,
        "level": level,
        "intent": intent,
        "mode": mode,
        "emotion": emotion,
        "personalized_feedback": feedback,
        "adaptive_profile": profile_summary,
        "evidence": {
            "logged": evidence_logged,
            "table": "metrics_adaptive_feedback",
            "detected": bool(feedback.get("detected")),
        },
    })


@chat_bp.route("/api/adaptive-plan", methods=["POST"])
@limiter.limit(os.getenv("RATE_LIMIT_ADAPTIVE_PLAN", "60 per hour"))
def api_adaptive_plan():
    """Calcula personalizacion adaptativa sin reemplazar el flujo del chat."""
    usuario = obtener_usuario_actual()
    data = request.get_json(silent=True) or {}

    user_text = str(
        data.get("message")
        or data.get("query")
        or data.get("text")
        or ""
    ).strip()
    topic = str(data.get("topic") or data.get("tema") or "Programacion Avanzada").strip()
    level = str(data.get("level") or data.get("nivel") or "").strip()
    intent = str(data.get("intent") or data.get("intencion") or detectar_intencion_semantica(user_text.lower())).strip()
    emotion = _normalize_recommendation_emotion(data.get("emotion"), user_text)

    try:
        profile = get_profile(usuario)
    except Exception:
        profile = {}

    personalized_feedback = data.get("personalized_feedback")
    if personalized_feedback is not None and not isinstance(personalized_feedback, dict):
        personalized_feedback = None

    plan = build_adaptive_plan(
        profile=profile,
        topic=topic,
        requested_level=level or None,
        emotion=emotion,
        intent=intent,
        personalized_feedback=personalized_feedback,
    )

    persisted = False
    if data.get("persist", True) is not False:
        try:
            save_adaptive_plan(usuario, plan)
            persisted = True
        except Exception:
            persisted = False

    return _ok({
        "contract_version": "adaptive_personalization.v1",
        "usuario": usuario,
        "topic": topic,
        "intent": intent,
        "emotion": emotion,
        "adaptive_plan": plan,
        "evidence": {
            "persisted": persisted,
            "profile_source": "student_profiles.profile_json",
        },
    })



# ============================================================================
# HELPERS (Adjuntos)
# ============================================================================
def _private_upload_dir() -> Path:
    """Directorio privado (preferido) para adjuntos."""
    return Path(os.getenv("PRIVATE_UPLOAD_DIR", "private_uploads"))


def _legacy_static_upload_dir() -> Path:
    """Directorio legado (por compatibilidad) si antes guardabas en /static/uploads."""
    base_dir = Path(__file__).resolve().parents[2]
    return base_dir / "static" / "uploads"


def _resolve_attachment_path(stored_name: str) -> Optional[Path]:
    """Resuelve la ruta física de un adjunto.

    Orden:
      1) PRIVATE_UPLOAD_DIR (nuevo, seguro)
      2) static/uploads (legado, por compatibilidad)
    """
    if not stored_name:
        return None

    # 1) privado
    pvt = _private_upload_dir() / str(stored_name)
    if pvt.exists() and pvt.is_file():
        return pvt

    # 2) legado
    legacy = _legacy_static_upload_dir() / str(stored_name)
    if legacy.exists() and legacy.is_file():
        return legacy

    return None


# ============================================================================
# ENDPOINTS
# ============================================================================
@chat_bp.route("/api/chat", methods=["POST"])
@limiter.limit(os.getenv("RATE_LIMIT_MESSAGES", "100 per hour"))
@limiter.limit(
    os.getenv("RATE_LIMIT_UPLOADS", "20 per hour"),
    deduct_when=lambda response: bool(getattr(request, "files", None))
    and len(request.files) > 0,
)
def api_chat():
    """
    Endpoint principal del chat:
    - Valida payload
    - Reconstruye historial (limitado)
    - Pasa todo por chat_service (orquestación limpia)
    - Persiste mensajes (user/bot) y actualiza progreso
    """
    usuario = obtener_usuario_actual()
    data = request.get_json(silent=True) or {}

    val = _validate_chat_payload(data)
    if not val.get("ok"):
        return _err(val.get("error", "Payload inválido."), 400)

    mensaje: str = val["message"]
    raw_user_message: str = mensaje
    requested_topic = str(data.get("topic") or data.get("tema") or "").strip()

    conv_id: Optional[int] = val["conversation_id"]
    titulo: Optional[str] = val["titulo"]

    # ----------------------------------------------------
    # (NUEVO) Continuidad: si el usuario se refiere a "ese/eso/anterior",
    # inyectamos el último foco (adjuntos/tema) aunque el frontend no mande ids.
    # ----------------------------------------------------
    def _is_reference_or_continuation(text: str) -> bool:
        t = (text or "").strip().lower()
        if not t:
            return False
        keys = [
            "ese",
            "eso",
            "anterior",
            "archivo",
            "adjunto",
            "documento",
            "imagen",
            "pdf",
            "código",
            "codigo",
            "del archivo",
            "del adjunto",
            "explica",
            "explicame",
            "profundizar",
            "profundiza",
            "continua",
            "continúa",
            "seguir",
            "que mas",
            "qué más",
            "mejorar",
            "aumentar",
            "agregar",
            "recomienda",
            "recomiendas",
            "recomendacion",
            "recomendaciones",
            "recurso",
            "recursos",
            "fuente",
            "fuentes",
            "link",
            "links",
            "enlace",
            "enlaces",
            "web",
            "internet",
            "tutorial",
            "tutoriales",
            "documentacion",
            "documentación",
        ]
        return any(k in t for k in keys) or len(t.split()) <= 6

    wants_focus = bool(conv_id and _is_reference_or_continuation(mensaje))
    focus_topic_local: Optional[str] = None
    memory_summary_local: Optional[str] = None
    if wants_focus and conv_id is not None:
        try:
            foco = obtener_foco_conversacion(int(conv_id), usuario)
            focus_topic_local = foco.get("focus_topic")
            focus_ids = foco.get("focus_attachment_ids") or []
            # Si el frontend no envió attachment_ids, usamos el foco persistido.
            if not (data.get("attachment_ids") or data.get("attachments")) and focus_ids:
                data["attachment_ids"] = focus_ids
        except Exception:
            pass

    # ----------------------------------------------------
    # (NUEVO) Memory summary: pequeña "memoria" del hilo
    # ----------------------------------------------------
    if conv_id is not None:
        try:
            mem = obtener_memoria_conversacion(int(conv_id), usuario)
            ms = (mem.get("memory_summary") or "").strip()
            memory_summary_local = ms or None
        except Exception:
            memory_summary_local = None

    # ----------------------------------------------------
    # (NUEVO) Contexto desde adjuntos
    # ----------------------------------------------------
    attachment_ids = data.get("attachment_ids") or data.get("attachments") or []
    attachment_context_parts: List[str] = []
    if isinstance(attachment_ids, list) and attachment_ids:
        try:
            for raw_id in attachment_ids[:3]:  # límite de seguridad: 3 adjuntos
                try:
                    att_id = int(raw_id)
                except Exception:
                    continue

                meta = get_attachment(att_id)
                if not meta:
                    continue

                stored_name = meta.get("stored_name")
                original_name = meta.get("original_name") or stored_name
                if not stored_name:
                    continue

                # ✅ FIX: resolver en PRIVATE_UPLOAD_DIR (y fallback a static/uploads si hay adjuntos antiguos)
                path = _resolve_attachment_path(str(stored_name))
                if not path:
                    continue

                r = extract_text_from_file(path)
                if r.ok and (r.text or "").strip():
                    attachment_context_parts.append(
                        f"[ADJUNTO: {original_name} | id={att_id}]\n{r.text.strip()}\n"
                    )
                elif r.error:
                    attachment_context_parts.append(
                        f"[ADJUNTO: {original_name} | id={att_id}]\n(No se pudo extraer texto: {r.error})\n"
                    )
        except Exception:
            # Best-effort: no romper el chat si falla el análisis
            attachment_context_parts = []

    if attachment_context_parts:
        contexto_adjuntos = "\n\n".join(attachment_context_parts)
        encabezado = "Tengo estos adjuntos como contexto. Úsalos para responder la consulta del usuario."
        if memory_summary_local:
            encabezado = f"MEMORIA (resumen del hilo):\n{memory_summary_local}\n\n" + encabezado
        if wants_focus and focus_topic_local:
            encabezado = f"FOCO ACTUAL: {focus_topic_local}\n" + encabezado
        mensaje = encabezado + "\n\n" + contexto_adjuntos + "\n\n---\n\n" + mensaje
    else:
        pref = ""
        if memory_summary_local:
            pref += f"MEMORIA (resumen del hilo):\n{memory_summary_local}\n\n"
        if wants_focus and focus_topic_local:
            pref += f"FOCO ACTUAL: {focus_topic_local}\n\n"
        if pref:
            mensaje = pref + mensaje

    try:
        adaptive_context = _adaptive_profile_context(get_profile(usuario))
        if adaptive_context:
            mensaje = adaptive_context + "\n\n" + mensaje
    except Exception:
        pass

    # ----------------------------------------------------
    # PERF (Métricas PRO)
    # ----------------------------------------------------
    perf_start = time.perf_counter()

    try:
        log_event(
            usuario=usuario,
            conversation_id=val.get("conversation_id"),
            event_type="message_received",
        )
    except Exception:
        pass

    modo_interaccion: Optional[str] = None
    intencion: Optional[str] = None
    tema: Optional[str] = None
    structured_quiz_payload: Optional[Dict[str, Any]] = None
    structured_grade_payload: Optional[Dict[str, Any]] = None

    try:
        # ----------------------------------------------------
        # 1) Validar pertenencia de conversation_id
        # ----------------------------------------------------
        if conv_id:
            with db_session(write=False) as conn:
                cur = conn.cursor()
                cur.execute(
                    "SELECT id FROM conversaciones WHERE id = ? AND usuario = ?;",
                    (conv_id, usuario),
                )
                if cur.fetchone() is None:
                    logger.warning(
                        "conversation_id inválido/no pertenece; se creará nueva",
                        usuario=usuario,
                        conv_id=conv_id,
                    )
                    conv_id = None

        # ----------------------------------------------------
        # 2) Construir historial (limitado) para el NLP
        # ----------------------------------------------------
        historial: List[Dict[str, Any]] = []
        if conv_id:
            max_hist = int(os.getenv("CHAT_HISTORY_LIMIT", str(MAX_HISTORY)))
            with db_session(write=False) as conn:
                cur = conn.cursor()
                cur.execute(
                    "SELECT remitente, contenido FROM messages WHERE conv_id = ? AND usuario = ? ORDER BY id DESC LIMIT ?;",
                    (conv_id, usuario, max_hist),
                )
                filas = list(reversed(cur.fetchall()))
                historial = [
                    {"remitente": r["remitente"], "contenido": r["contenido"]} for r in filas
                ]
                try:
                    logger.info(
                        "Historial cargado",
                        usuario=usuario,
                        conv_id=conv_id,
                        count=len(historial),
                        max_hist=max_hist,
                    )
                except Exception:
                    pass

        # ----------------------------------------------------
        # 3) Perfil opcional (override) enviado por el frontend
        # ----------------------------------------------------
        profile = data.get("profile") or {}
        ciclo_override = profile.get("ciclo_academico") or profile.get("ciclo") or None
        estado_override = profile.get("estado_materia") or profile.get("estado") or None
        nivel_override = (
            profile.get("nivel_materia")
            or profile.get("nivel")
            or data.get("nivel_materia")
            or data.get("nivel_explicacion")
            or None
        )

        detected_mode = detectar_modo_interaccion(raw_user_message.lower())
        detected_intent = detectar_intencion_semantica(raw_user_message.lower())
        active_quiz = get_active_quiz(int(conv_id), usuario) if conv_id else None
        generic_topics = {"programacion avanzada", "programación avanzada"}
        requested_topic_seed = "" if requested_topic.strip().lower() in generic_topics else requested_topic
        effective_topic = canonical_topic(
            requested_topic_seed or focus_topic_local or (active_quiz or {}).get("tema") or "",
            raw_user_message,
        )

        quiz_answers = parse_student_answers(raw_user_message) if active_quiz else {}
        if active_quiz and (detected_intent == "evaluacion_respuesta" or quiz_answers):
            structured_grade_payload = grade_structured_quiz(active_quiz, raw_user_message)
            resultado_chat = {
                "respuesta": format_grade_for_chat(structured_grade_payload),
                "tema": structured_grade_payload.get("topic") or active_quiz.get("tema") or effective_topic,
                "modo": "structured",
                "web_search": False,
                "modo_interaccion": "quiz_grade",
                "intencion": "evaluacion_respuesta",
                "profile_used": None,
                "emotion": {"emotion": "focused", "avatar_expression": "explain"},
            }
        elif detected_mode == "quiz" or detected_intent == "quiz":
            quiz_count = requested_count(raw_user_message, default=3)
            structured_quiz_payload = build_structured_quiz(
                effective_topic,
                count=quiz_count,
                request_text=raw_user_message,
            )
            resultado_chat = {
                "respuesta": format_quiz_for_chat(structured_quiz_payload),
                "tema": structured_quiz_payload.get("topic") or effective_topic,
                "modo": "structured",
                "web_search": False,
                "modo_interaccion": "quiz",
                "intencion": "quiz",
                "profile_used": None,
                "emotion": {"emotion": "focused", "avatar_expression": "curious"},
            }
        else:
            resultado_chat = procesar_mensaje_chat(
                usuario=usuario,
                mensaje=mensaje,
                historial=historial,
                nivel_explicacion=(nivel_override or "basica"),
                ciclo_academico=ciclo_override,
                estado_materia=estado_override,
            )

        # ----------------------------------------------------
        # 4) Normalización de la respuesta del servicio
        # ----------------------------------------------------
        texto_respuesta = (resultado_chat.get("respuesta") or "").strip()
        tema = resultado_chat.get("tema") or "Programación Avanzada"
        modo = resultado_chat.get("modo") or "groq"
        if requested_topic and requested_topic.strip().lower() not in {"programacion avanzada", "programación avanzada"}:
            tema = requested_topic
        web_search = bool(resultado_chat.get("web_search", False))
        modo_interaccion = resultado_chat.get("modo_interaccion") or "normal"
        intencion = resultado_chat.get("intencion") or "otro"
        profile_used = resultado_chat.get("profile_used")
        emotion_payload = resultado_chat.get("emotion") or {}
        provider_failures = list(
            resultado_chat.get("provider_failures")
            or resultado_chat.get("proveedores_fallidos")
            or []
        )

        if not texto_respuesta:
            texto_respuesta = "Ocurrió un error al procesar tu consulta. Intenta nuevamente."
            modo = "error"
            modo_interaccion = "normal"
            intencion = "otro"
            provider_failures = provider_failures or ["empty_response"]

        texto_respuesta_principal = texto_respuesta

        # ----------------------------------------------------
        # (NUEVO) TUTOR PRO: nivel automático + ejercicios personalizados
        # ----------------------------------------------------
        tutor_payload = None
        try:
            code_context_for_level = None
            if attachment_context_parts:
                code_context_for_level = "\n\n".join(attachment_context_parts)
                if len(code_context_for_level) > 1500:
                    code_context_for_level = code_context_for_level[:1500] + "\n..."

            additions = build_tutor_additions(
                student_id=usuario,
                user_text=raw_user_message,
                focus_topic=(tema or "Programación Avanzada"),
                code_context=code_context_for_level,
                emotion=emotion_payload,
                intent=intencion,
            )
            tutor_payload = additions.get("tutor") or {
                k: v for k, v in additions.items() if k in {"profile", "level"}
            }
            append_md = (additions.get("append_markdown") or "").strip()
            append_tutor_in_reply = os.getenv("APPEND_TUTOR_ADDONS_IN_REPLY", "0") == "1"
            if append_tutor_in_reply and append_md and intencion not in {"evaluacion_respuesta"} and modo_interaccion not in {"quiz"}:
                texto_respuesta = (texto_respuesta + "\n\n" + append_md).strip()
        except Exception:
            tutor_payload = None

        # ----------------------------------------------------
        # Recomendaciones, retroalimentacion y perfil adaptativo
        # ----------------------------------------------------
        recommendations_payload = []
        suggestion_payload = []
        personalized_feedback_payload = None
        adaptive_profile_payload = None
        adaptive_plan_payload = None
        try:
            nivel_recomendacion = nivel_override or "intermedio"
            if isinstance(tutor_payload, dict):
                nivel_recomendacion = nivel_override or tutor_payload.get("level") or nivel_recomendacion
            history_profile = get_profile(usuario)
            recommendations_payload = build_recommendations(
                user_text=raw_user_message,
                topic=(tema or "Programacion Avanzada"),
                level=nivel_recomendacion,
                emotion=emotion_payload,
                intent=intencion,
                history_profile=history_profile,
            )
            suggestion_payload = recommendations_to_suggestions(recommendations_payload)
            append_recommendations = (
                os.getenv("APPEND_RECOMMENDATIONS_IN_REPLY", "1") == "1"
                and intencion not in {"evaluacion_respuesta"}
                and modo_interaccion not in {"quiz"}
            )
            if append_recommendations:
                texto_respuesta = _append_history_recommendations_to_reply(
                    texto_respuesta,
                    recommendations_payload,
                )
                texto_respuesta = _append_web_resources_to_reply_direct(
                    texto_respuesta,
                    raw_user_message,
                    recommendations_payload,
                )
            personalized_feedback_payload = build_personalized_feedback(
                user_text=raw_user_message,
                topic=(tema or "Programacion Avanzada"),
                level=nivel_recomendacion,
                emotion=emotion_payload,
                intent=intencion,
                mode=modo_interaccion,
            )
            if personalized_feedback_payload:
                append_feedback = (personalized_feedback_payload.get("append_markdown") or "").strip()
                append_feedback_allowed = (
                    os.getenv("APPEND_FEEDBACK_IN_REPLY", "1") == "1"
                    and intencion not in {"evaluacion_respuesta"}
                    and modo_interaccion not in {"quiz"}
                )
                if append_feedback_allowed and append_feedback and append_feedback not in texto_respuesta:
                    texto_respuesta = (texto_respuesta + "\n\n" + append_feedback).strip()
            adaptive_profile_payload = update_adaptive_profile(
                student_id=usuario,
                topic=(tema or "Programacion Avanzada"),
                level=nivel_recomendacion,
                emotion=emotion_payload,
                intent=intencion,
                recommendations=recommendations_payload,
                personalized_feedback=personalized_feedback_payload,
            )
            adaptive_plan_payload = build_adaptive_plan(
                profile=adaptive_profile_payload or history_profile,
                topic=(tema or "Programacion Avanzada"),
                requested_level=nivel_recomendacion,
                emotion=emotion_payload,
                intent=intencion,
                personalized_feedback=personalized_feedback_payload,
            )
            save_adaptive_plan(usuario, adaptive_plan_payload)
        except Exception:
            recommendations_payload = []
            suggestion_payload = []
            personalized_feedback_payload = None
            adaptive_profile_payload = None
            adaptive_plan_payload = None

        # ----------------------------------------------------
        # Persistir foco del hilo (tema + adjuntos recientes)
        # ----------------------------------------------------
        try:
            if conv_id:
                ids = []
                if isinstance(attachment_ids, list) and attachment_ids:
                    for x in attachment_ids[:3]:
                        try:
                            ids.append(int(x))
                        except Exception:
                            continue
                actualizar_foco_conversacion(
                    int(conv_id),
                    usuario,
                    focus_topic=(tema or "Programación Avanzada"),
                    focus_attachment_ids=(ids or None),
                )
        except Exception:
            pass

        # ----------------------------------------------------
        # 5) Persistencia en BD (transacción única)
        # ----------------------------------------------------
        bot_message_id: Optional[int] = None
        with db_session(write=True) as conn:

            cur = conn.cursor()

            if not conv_id:
                cur.execute(
                    "INSERT INTO conversaciones (usuario, titulo) VALUES (?, ?);",
                    (usuario, (titulo or raw_user_message[:60])),
                )
                lastrowid = cur.lastrowid
                if lastrowid is not None:
                    conv_id = int(lastrowid)
                else:
                    raise RuntimeError("No se pudo obtener el lastrowid para la nueva conversación.")

            cur.execute(
                "INSERT INTO messages (conv_id, usuario, remitente, contenido, tema) VALUES (?, ?, 'user', ?, ?);",
                (conv_id, usuario, raw_user_message, tema),
            )
            cur.execute(
                """
                INSERT INTO messages (conv_id, usuario, remitente, contenido, tema, proveedor, response_ms)
                VALUES (?, ?, 'bot', ?, ?, ?, ?);
                """,
                (conv_id, usuario, texto_respuesta, tema, modo, round((time.perf_counter() - perf_start) * 1000.0)),
            )
            if cur.lastrowid is not None:
                bot_message_id = int(cur.lastrowid)
            
            try:
                usuario_id = get_or_create_usuario(usuario)
                registrar_interaccion(
                    usuario_id=usuario_id,
                    pregunta=raw_user_message,
                    respuesta=texto_respuesta,
                    tema=tema,
                )
            except Exception as inter_err:
                logger.warning(
                    "No se pudo registrar interacción legacy",
                    error=str(inter_err),
                    usuario=usuario,
                    conv_id=conv_id,
                )

        try:
            if structured_quiz_payload and conv_id:
                quiz_id = save_structured_quiz(
                    conv_id=int(conv_id),
                    usuario=usuario,
                    tema=tema or structured_quiz_payload.get("topic") or "Programacion Avanzada",
                    quiz=structured_quiz_payload,
                    source_message_id=bot_message_id,
                )
                structured_quiz_payload["id"] = quiz_id
            if structured_grade_payload and structured_grade_payload.get("complete"):
                close_structured_quiz(
                    int(structured_grade_payload.get("quiz_id") or 0),
                    int(structured_grade_payload.get("score") or 0),
                    int(structured_grade_payload.get("quiz_total") or structured_grade_payload.get("total") or 0),
                )
        except Exception as quiz_err:
            logger.warning("No se pudo persistir/cerrar quiz estructurado", error=str(quiz_err), usuario=usuario)

        # Garantizar foco también en conversaciones recién creadas
        try:
            ids = []
            if isinstance(attachment_ids, list) and attachment_ids:
                for x in attachment_ids[:3]:
                    try:
                        ids.append(int(x))
                    except Exception:
                        continue
            actualizar_foco_conversacion(
                int(conv_id),
                usuario,
                focus_topic=(tema or "Programación Avanzada"),
                focus_attachment_ids=(ids or None),
            )
        except Exception:
            pass

        # ----------------------------------------------------
        # Memory summary: actualizar cada N mensajes
        # ----------------------------------------------------
        try:
            if conv_id:
                update_memory_summary_if_needed(usuario=usuario, conv_id=int(conv_id))
        except Exception:
            pass

        # ----------------------------------------------------
        # 6) Progreso (tolerante a fallos)
        # ----------------------------------------------------
        try:
            if structured_grade_payload:
                puntos_delta = 1 + int(structured_grade_payload.get("score") or 0)
            elif structured_quiz_payload:
                puntos_delta = 1
            else:
                puntos_delta = 3 if intencion in ("quiz", "evaluacion_respuesta") else 1
            if isinstance(personalized_feedback_payload, dict):
                puntos_delta += int(personalized_feedback_payload.get("score_delta") or 0)
            progreso = actualizar_progreso(usuario, tema_nuevo=tema, puntos_delta=puntos_delta)
        except Exception as prog_err:
            logger.error("Error actualizando progreso", error=str(prog_err), usuario=usuario)
            progreso = None

        try:
            if isinstance(personalized_feedback_payload, dict):
                log_event(
                    usuario=usuario,
                    conversation_id=conv_id,
                    event_type="personalized_feedback",
                    modo_interaccion=modo_interaccion,
                    intencion=personalized_feedback_payload.get("kind") or intencion,
                    tema=tema,
                    confusion_detectada=(personalized_feedback_payload.get("status") == "needs_help"),
                )
        except Exception:
            pass

        try:
            log_recommendations(
                usuario=usuario,
                conversation_id=conv_id,
                recommendations=recommendations_payload,
            )
            log_adaptive_feedback(
                usuario=usuario,
                conversation_id=conv_id,
                feedback=personalized_feedback_payload,
            )
        except Exception:
            pass

        # ----------------------------------------------------
        # 7) Respuesta al frontend (contrato estable)
        # ----------------------------------------------------
        response_ms = round((time.perf_counter() - perf_start) * 1000.0)
        avatar_payload = _avatar_contract(
            emotion=emotion_payload,
            mode=modo,
            intent=intencion,
            interaction_mode=modo_interaccion,
            has_reply=bool(texto_respuesta),
        )
        return _ok(
            {
                "contract_version": "chat.v1",
                "conversation_id": conv_id,
                "response": texto_respuesta_principal,
                "reply": texto_respuesta_principal,
                "answer": texto_respuesta_principal,
                "enriched_reply": texto_respuesta,
                "tema": tema,
                "topic": tema,
                "progreso": progreso,
                "modo": modo,
                "provider": modo,
                "proveedor": modo,
                "response_ms": response_ms,
                "web_search": web_search,
                "modo_interaccion": modo_interaccion,
                "intencion": intencion,
                "profile_used": profile_used,
                "tutor": tutor_payload,
                "emotion": emotion_payload,
                "personalized_feedback": personalized_feedback_payload,
                "adaptive_profile": (adaptive_profile_payload or {}).get("adaptive_summary"),
                "adaptive_plan": adaptive_plan_payload,
                "recommendations": recommendations_payload,
                "suggestions": suggestion_payload,
                "structured_quiz": structured_quiz_payload,
                "structured_grade": structured_grade_payload,
                "avatar": avatar_payload,
                "diagnostics": {
                    "provider": modo,
                    "provider_failures": provider_failures,
                    "web_search": web_search,
                    "response_ms": response_ms,
                },
            }
        )

    except Exception as e:
        logger.error("Error en /api/chat", error=str(e), usuario=usuario)
        return _err("No se pudo procesar el mensaje.", 500)

    finally:
        try:
            latency_ms = round((time.perf_counter() - perf_start) * 1000.0, 1)
            log_perf(
                usuario=usuario,
                conversation_id=conv_id,
                endpoint="/api/chat",
                latency_ms=latency_ms,
            )
            log_event(
                usuario=usuario,
                conversation_id=conv_id,
                event_type="message_replied",
                modo_interaccion=modo_interaccion,
                intencion=intencion,
                tema=tema,
            )
        except Exception:
            pass


# ---------------------------
# API: Adjuntos
# ---------------------------
@chat_bp.route("/api/attachments/upload", methods=["POST"])
@limiter.limit(os.getenv("RATE_LIMIT_ATTACH", "20 per minute"))
def upload_attachment():
    if "file" not in request.files:
        return jsonify({"ok": False, "error": "No se recibió el archivo (field: file)."}), 400

    f = request.files["file"]

    max_mb = int(os.getenv("MAX_ATTACHMENT_MB", "10"))
    max_bytes = max_mb * 1024 * 1024

    if request.content_length and request.content_length > max_bytes:
        return _err(f"El archivo supera el límite ({max_mb} MB).", 413, code="FILE_TOO_LARGE")

    if not f or not f.filename:
        return _err("Archivo inválido.", 400)

    original_name = f.filename

    if not _allowed_attachment_ext(original_name):
        return _err("Tipo de archivo no permitido.", 400)

    ext = original_name.rsplit(".", 1)[-1].lower() if "." in original_name else ""

    if not _allowed_attachment_mime(ext, getattr(f, "mimetype", None)):
        return _err("Tipo MIME no permitido.", 400)

    safe_name = secure_filename(original_name)
    stored_name = f"{uuid.uuid4().hex}_{safe_name}"

    private_dir = _private_upload_dir()
    private_dir.mkdir(parents=True, exist_ok=True)
    out_path = private_dir / stored_name

    f.save(str(out_path))

    try:
        size_bytes = out_path.stat().st_size
    except Exception:
        size_bytes = 0

    if size_bytes > max_bytes:
        try:
            out_path.unlink(missing_ok=True)
        except Exception:
            pass
        return _err(f"El archivo supera el límite ({max_mb} MB).", 413, code="FILE_TOO_LARGE")

    if not _magic_bytes_ok(ext, out_path):
        try:
            out_path.unlink(missing_ok=True)
        except Exception:
            pass
        return _err(
            "El archivo no coincide con el tipo esperado (firma inválida).",
            400,
            code="FILE_SIGNATURE_INVALID",
        )

    mime = getattr(f, "mimetype", None)

    sha256 = None
    try:
        h = hashlib.sha256()
        with open(out_path, "rb") as fp:
            for chunk in iter(lambda: fp.read(1024 * 1024), b""):
                h.update(chunk)
        sha256 = h.hexdigest()
    except Exception:
        sha256 = None

    conversation_id = request.form.get("conversation_id")
    try:
        conversation_id = int(conversation_id) if conversation_id not in (None, "", "null", "undefined") else None
    except Exception:
        conversation_id = None

    try:
        usuario = session.get("usuario") or session.get("user") or session.get("username") or "anonimo"
    except Exception:
        usuario = "anonimo"

    url = f"/api/uploads/{stored_name}"

    global _FALLBACK_NEXT_ATT_ID

    attachment_meta = {
        "usuario": usuario,
        "conv_id": conversation_id,
        "conversation_id": conversation_id,
        "original_name": original_name,
        "stored_name": stored_name,
        "mime": mime,
        "size_bytes": size_bytes,
        "sha256": sha256,
        "url": url,
        "file_path": str(out_path),
        "filename": original_name,
    }

    try:
        att_saved = save_attachment(
            usuario=usuario,
            conv_id=conversation_id,
            original_name=original_name,
            stored_name=stored_name,
            mime=mime,
            size_bytes=size_bytes,
            sha256=sha256,
            url=url,
            file_path=str(out_path),
            filename=original_name,
        )

        if isinstance(att_saved, dict):
            att_id = att_saved.get("id") or att_saved.get("attachment_id")
        else:
            att_id = att_saved

        if att_id is None:
            raise RuntimeError("save_attachment no devolvió id")

        att_id = int(att_id)

    except Exception as e:
        logger.error("No se pudo guardar metadata de adjunto; usando fallback en memoria", error=str(e))
        att_id = _FALLBACK_NEXT_ATT_ID
        _FALLBACK_NEXT_ATT_ID -= 1

    attachment_meta["id"] = int(att_id)

    # CLAVE DEL ARREGLO:
    # Siempre guardamos fallback en memoria, incluso si la BD respondió.
    # Así analyze puede encontrar el adjunto inmediatamente sin recargar.
    _FALLBACK_ATTACHMENTS[int(att_id)] = attachment_meta

    return jsonify(
        {
            "ok": True,
            "data": {
                "conversation_id": conversation_id,
                "attachment": {
                    "id": int(att_id),
                    "original_name": original_name,
                    "stored_name": stored_name,
                    "mime": mime,
                    "size_bytes": size_bytes,
                    "url": url,
                },
            },
        }
    ), 200


@chat_bp.route("/api/attachments/analyze", methods=["POST"])
@limiter.limit(os.getenv("RATE_LIMIT_ATTACH_ANALYZE", "60 per minute"))
def analyze_attachment():
    """
    Analiza un adjunto previamente subido y devuelve el texto extraído.

    FIX:
    - Busca primero en BD.
    - Si la BD no responde o no devuelve metadata, usa _FALLBACK_ATTACHMENTS.
    - Resuelve la ruta usando PRIVATE_UPLOAD_DIR y, si hace falta, file_path.
    - Genera auto_reply para que YELIA responda automáticamente al PDF.
    - Devuelve payload de avatar para activar animación de habla en frontend.
    """
    data = request.get_json(silent=True) or {}
    raw_id = data.get("id") or data.get("attachment_id")

    if raw_id is None:
        return _err("Falta 'id' de adjunto para analizar.", 400)

    try:
        att_id = int(raw_id)
    except Exception:
        return _err("'id' de adjunto inválido para analizar.", 400)

    # 1) Buscar metadata del adjunto
    meta = None
    try:
        meta = get_attachment(att_id)
    except Exception as e:
        logger.error("Error consultando adjunto en DB", error=str(e), att_id=att_id)
        meta = None

    # Fallback inmediato para evitar "Adjunto no encontrado" después de subir
    if not meta:
        meta = _FALLBACK_ATTACHMENTS.get(int(att_id))

    if not meta:
        return _err("Adjunto no encontrado.", 404)

    stored_name = meta.get("stored_name")
    if not stored_name:
        return _err("Adjunto inválido (sin stored_name).", 400)

    # 2) Resolver archivo físico
    path = _resolve_attachment_path(str(stored_name))

    # Fallback adicional: si la metadata trae ruta absoluta/relativa guardada
    if not path:
        file_path = meta.get("file_path")
        if file_path:
            candidate = Path(file_path)
            if candidate.exists() and candidate.is_file():
                path = candidate

    if not path:
        return _err("Archivo no encontrado en el servidor.", 404)

    # 3) Extraer texto
    r = extract_text_from_file(path)

    if not r.ok:
        return jsonify(
            {
                "ok": False,
                "error": r.error or "No se pudo extraer texto.",
                "data": {
                    "id": att_id,
                    "original_name": meta.get("original_name"),
                    "mime": meta.get("mime"),
                    "meta": r.meta,
                    "avatar": {
                        "state": "idle",
                        "emotion": "neutral",
                        "gesture": "none",
                    },
                },
            }
        ), 200

    extracted_text = (r.text or "").strip()

    # 4) Persistir análisis, si se puede
    try:
        save_attachment_analysis(att_id, extracted_text=extracted_text, extracted_meta=r.meta or {})
    except Exception as e:
        logger.error("No se pudo guardar análisis del adjunto", error=str(e), att_id=att_id)

    # 5) Actualizar foco de conversación para que botones como "Explicar mejor" usen este PDF
    try:
        conv_id = meta.get("conv_id") or meta.get("conversation_id")
        usuario_meta = meta.get("usuario") or obtener_usuario_actual() or "anonimo"

        if conv_id:
            try:
                prev = obtener_foco_conversacion(int(conv_id), usuario_meta)
                prev_ids = prev.get("focus_attachment_ids") or []
            except Exception:
                prev_ids = []

            new_ids = [int(att_id)]
            for item in prev_ids:
                try:
                    item_id = int(item)
                    if item_id != int(att_id):
                        new_ids.append(item_id)
                except Exception:
                    continue

            new_ids = new_ids[:3]
            focus_topic = f"Adjunto: {meta.get('original_name') or stored_name}"

            actualizar_foco_conversacion(
                int(conv_id),
                usuario_meta,
                focus_topic=focus_topic,
                focus_attachment_ids=new_ids,
            )
    except Exception as e:
        logger.error("No se pudo actualizar foco de adjunto", error=str(e), att_id=att_id)

    # 6) Respuesta automática de YELIA
    auto_reply = None
    suggestions = None

    if bool(data.get("auto_explain")):
        try:
            original_name = meta.get("original_name") or stored_name
            pregunta = (
                "Eres YELIA, una tutora virtual de Programación Avanzada. "
                f"El estudiante acaba de subir el archivo '{original_name}'. "
                "Lee el contenido y responde directamente al estudiante. "
                "Explica qué contiene el archivo, qué debe hacer, los conceptos importantes "
                "y da una guía clara paso a paso. No digas que no encontraste el archivo."
            )

            texto_para_ia = extracted_text
            if len(texto_para_ia) > 12000:
                texto_para_ia = texto_para_ia[:12000] + "\n\n[Contenido recortado por longitud.]"

            resp = procesar_mensaje_chat(
                usuario=meta.get("usuario") or obtener_usuario_actual() or "anonimo",
                mensaje=f"[CONTENIDO DEL ARCHIVO]\n{texto_para_ia}\n\n[PREGUNTA]\n{pregunta}",
                historial=[],
            )

            auto_reply = (resp.get("respuesta") or "").strip() or None

            if not auto_reply:
                auto_reply = (
                    "Ya leí tu archivo. Veo que contiene contenido relacionado con Programación Avanzada. "
                    "Puedo ayudarte a explicarlo paso a paso, resolver el ejercicio o mejorarlo."
                )

            suggestions = [
                "Explicar adjunto",
                "Paso a paso",
                "Mejorar código",
                "Casos de prueba",
                "Quiz",
            ]

        except Exception as e:
            logger.error("Error generando auto_reply de adjunto", error=str(e), att_id=att_id)
            auto_reply = (
                "Ya leí tu archivo. Puedo ayudarte a explicarlo paso a paso, "
                "mejorarlo o resolver el ejercicio según lo que necesites."
            )
            suggestions = [
                "Explicar adjunto",
                "Paso a paso",
                "Mejorar código",
                "Casos de prueba",
                "Quiz",
            ]

    return jsonify(
        {
            "ok": True,
            "data": {
                "id": att_id,
                "original_name": meta.get("original_name"),
                "mime": meta.get("mime"),
                "extracted_text": extracted_text,
                "meta": r.meta,
                "auto_reply": auto_reply,
                "suggestions": suggestions,
                "avatar": {
                    "state": "speaking",
                    "emotion": "neutral",
                    "gesture": "talk",
                    "intensity": 1,
                },
            },
        }
    ), 200
