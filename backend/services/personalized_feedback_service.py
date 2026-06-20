"""Retroalimentacion personalizada para aprendizaje adaptativo.

Este modulo interpreta senales simples del estudiante despues de una explicacion,
quiz o practica. No intenta reemplazar al LLM: genera una capa estable y medible
para la tesis, el perfil adaptativo y las metricas.
"""
from __future__ import annotations

import re
import unicodedata
from typing import Any, Dict, Optional


def _norm(text: Optional[str]) -> str:
    raw = (text or "").strip().lower()
    raw = "".join(c for c in unicodedata.normalize("NFD", raw) if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", raw)


def _contains_any(text: str, terms: tuple[str, ...]) -> bool:
    return any(term in text for term in terms)


def _contract(payload: Dict[str, Any], *, summary: str, action: str, reason: str) -> Dict[str, Any]:
    """Completa el contrato usado por Next, metricas y tesis."""
    payload = dict(payload or {})
    payload.setdefault("contract_version", "personalized_feedback.v1")
    payload.setdefault("summary", summary)
    payload.setdefault("action", action)
    payload.setdefault("reason", reason)
    payload.setdefault("evidence_tags", [
        payload.get("kind") or "feedback",
        payload.get("status") or "unknown",
        payload.get("topic") or "Programacion Avanzada",
        payload.get("level") or "intermedio",
    ])
    return payload


def build_personalized_feedback(
    *,
    user_text: str,
    topic: str,
    level: str,
    emotion: Dict[str, Any],
    intent: str,
    mode: str,
) -> Optional[Dict[str, Any]]:
    """Devuelve retroalimentacion personalizada si el mensaje trae una senal util."""
    text = _norm(user_text)
    if not text:
        return None

    topic_label = topic or "Programacion Avanzada"
    level_label = level or "intermedio"
    emotion_key = _norm((emotion or {}).get("emotion") or "neutral") or "neutral"

    positive = _contains_any(text, (
        "entendi", "ya entendi", "me quedo claro", "esta claro", "si entiendo",
        "comprendi", "perfecto", "gracias ya", "me sirvio",
    ))
    negative = _contains_any(text, (
        "no entendi", "no entiendo", "sigo sin entender", "me confunde",
        "estoy confundido", "no me queda claro", "explica mas simple",
        "mas simple", "desde cero", "me perdi",
    ))
    asks_review = _contains_any(text, (
        "mi respuesta", "esta bien", "esta correcta", "corrige", "revisa",
        "la respuesta es", "respondo", "opcion a", "opcion b", "opcion c", "opcion d",
    ))
    asks_practice = _contains_any(text, (
        "practicar", "ejercicio", "dame un ejercicio", "hacer practica", "actividad",
    ))

    if negative:
        return _contract({
            "detected": True,
            "kind": "needs_reinforcement",
            "status": "needs_help",
            "score_delta": -1,
            "topic": topic_label,
            "level": level_label,
            "emotion": emotion_key,
            "message": "Detecte que el estudiante aun necesita refuerzo.",
            "next_action": "explain_simpler",
            "recommendation": "Bajar la dificultad, usar analogia y cerrar con una pregunta de comprobacion.",
            "append_markdown": (
                "Retroalimentacion personalizada:\n"
                f"- Estado: necesitas refuerzo en {topic_label}.\n"
                f"- Accion: lo explicare mas simple y con un ejemplo corto.\n"
                f"- Nivel usado: {level_label} | Emocion detectada: {emotion_key}."
            ),
        }, summary=f"Necesita refuerzo en {topic_label}", action=f"Explicame {topic_label} mas simple, con una analogia y un ejemplo corto.", reason="El mensaje contiene senales de confusion o dificultad.")

    if positive:
        return _contract({
            "detected": True,
            "kind": "understood",
            "status": "progress",
            "score_delta": 2,
            "topic": topic_label,
            "level": level_label,
            "emotion": emotion_key,
            "message": "Detecte comprension del estudiante.",
            "next_action": "practice_or_quiz",
            "recommendation": "Subir un paso: practica corta o mini quiz.",
            "append_markdown": (
                "Retroalimentacion personalizada:\n"
                f"- Estado: vas bien con {topic_label}.\n"
                "- Accion: ahora conviene practicar o resolver un mini quiz.\n"
                f"- Nivel usado: {level_label} | Emocion detectada: {emotion_key}."
            ),
        }, summary=f"Progreso positivo en {topic_label}", action=f"Dame una practica corta o mini quiz de {topic_label}.", reason="El estudiante reporta comprension o utilidad.")

    if asks_review or intent == "evaluacion_respuesta":
        return _contract({
            "detected": True,
            "kind": "answer_review",
            "status": "pending_review",
            "score_delta": 1,
            "topic": topic_label,
            "level": level_label,
            "emotion": emotion_key,
            "message": "El estudiante esta pidiendo revision de una respuesta.",
            "next_action": "review_answer",
            "recommendation": "Comparar la respuesta con el concepto, indicar acierto parcial y corregir el punto debil.",
            "append_markdown": (
                "Retroalimentacion personalizada:\n"
                f"- Estado: respuesta enviada para revision sobre {topic_label}.\n"
                "- Accion: revisare si tu idea coincide con el concepto y marcare que mejorar.\n"
                f"- Nivel usado: {level_label} | Emocion detectada: {emotion_key}."
            ),
        }, summary=f"Respuesta lista para revision sobre {topic_label}", action=f"Revisa mi respuesta sobre {topic_label} y dime que debo mejorar.", reason="El estudiante solicita correccion o validacion.")

    if asks_practice or intent == "ejercicio" or mode == "quiz":
        return _contract({
            "detected": True,
            "kind": "practice_requested",
            "status": "practice",
            "score_delta": 1,
            "topic": topic_label,
            "level": level_label,
            "emotion": emotion_key,
            "message": "El estudiante pidio practicar o evaluarse.",
            "next_action": "guided_practice",
            "recommendation": "Proponer una actividad breve con criterio de revision.",
            "append_markdown": (
                "Retroalimentacion personalizada:\n"
                f"- Estado: listo para practicar {topic_label}.\n"
                "- Accion: usare una actividad corta y luego revisare tu respuesta.\n"
                f"- Nivel usado: {level_label} | Emocion detectada: {emotion_key}."
            ),
        }, summary=f"Practica recomendada para {topic_label}", action=f"Dame una actividad guiada de {topic_label} y revisa mi respuesta.", reason="El estudiante pidio practica o evaluacion.")

    return None
