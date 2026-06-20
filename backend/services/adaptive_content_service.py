"""Reglas de personalizacion adaptativa para YELIA.

Este servicio no reemplaza al chat ni al LLM. Calcula una decision pedagogica
explicable a partir del perfil, progreso y retroalimentacion del estudiante.
"""
from __future__ import annotations

import datetime
from typing import Any, Dict, Optional

from backend.repositories.student_profile_repo import get_profile, save_profile


LEVELS = ("basico", "intermedio", "avanzado")


def _clean(value: Optional[str], fallback: str) -> str:
    text = (value or fallback).strip()
    return text or fallback


def _level(value: Optional[str], fallback: str = "basico") -> str:
    value = _clean(value, fallback).lower()
    aliases = {
        "basica": "basico",
        "básico": "basico",
        "básica": "basico",
        "medio": "intermedio",
        "intermedia": "intermedio",
        "avanzada": "avanzado",
    }
    value = aliases.get(value, value)
    return value if value in LEVELS else fallback


def _step_level(level: str, delta: int) -> str:
    idx = LEVELS.index(_level(level))
    idx = max(0, min(len(LEVELS) - 1, idx + delta))
    return LEVELS[idx]


def _emotion_key(emotion: Optional[Dict[str, Any]]) -> str:
    return str((emotion or {}).get("emotion") or "neutral").strip().lower() or "neutral"


def _feedback_status(feedback: Optional[Dict[str, Any]]) -> str:
    if not isinstance(feedback, dict):
        return ""
    return str(feedback.get("status") or feedback.get("kind") or "").strip().lower()


def _contains_topic(values: Any, topic: str) -> bool:
    topic_norm = topic.strip().lower()
    return any(str(item).strip().lower() == topic_norm for item in (values or []))


def build_adaptive_plan(
    *,
    profile: Optional[Dict[str, Any]],
    topic: str,
    requested_level: Optional[str],
    emotion: Optional[Dict[str, Any]],
    intent: str,
    personalized_feedback: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Devuelve una decision adaptativa estable y trazable."""
    profile = dict(profile or {})
    adaptive = profile.get("adaptive") or {}
    summary = profile.get("adaptive_summary") or {}

    topic_label = _clean(topic, summary.get("last_topic") or adaptive.get("last_topic") or "Programacion Avanzada")
    current_level = _level(requested_level or profile.get("level_current") or adaptive.get("last_level") or summary.get("last_level"))
    intent_key = _clean(intent, adaptive.get("last_intent") or "otro").lower()
    emotion = emotion or {}
    emotion_name = _emotion_key(emotion)
    feedback_status = _feedback_status(personalized_feedback)

    weak_topics = adaptive.get("weak_topics") or summary.get("weak_topics") or []
    mastered_topics = adaptive.get("mastered_topics") or summary.get("mastered_topics") or []
    learning_state = adaptive.get("learning_state") or summary.get("learning_state") or "active"
    topic_is_weak = _contains_topic(weak_topics, topic_label)
    topic_is_mastered = _contains_topic(mastered_topics, topic_label)

    selected_level = current_level
    strategy = "continue_learning"
    next_action = adaptive.get("next_best_action") or summary.get("next_best_action") or "recommend_next_resource"
    rationale = "Se mantiene el nivel actual porque no hay senales fuertes de cambio."
    adjustments = {
        "pace": "normal",
        "examples": "mixed",
        "practice": "short",
        "check_understanding": True,
        "show_resources": True,
    }

    if (
        feedback_status in {"needs_help", "needs_reinforcement"}
        or emotion_name in {"confused", "frustrated", "anxious"}
        or topic_is_weak
        or learning_state == "needs_reinforcement"
    ):
        selected_level = _step_level(current_level, -1)
        strategy = "reinforce_foundations"
        next_action = "explain_simpler"
        rationale = "El perfil o la emocion indican que conviene reforzar antes de avanzar."
        adjustments.update({
            "pace": "slow",
            "examples": "concrete",
            "practice": "guided_micro",
            "check_understanding": True,
            "show_resources": True,
        })
    elif feedback_status in {"progress", "understood"} or topic_is_mastered:
        selected_level = _step_level(current_level, 1 if current_level != "avanzado" else 0)
        strategy = "increase_challenge"
        next_action = "practice_or_quiz"
        rationale = "El historial muestra progreso; se puede subir la dificultad con control."
        adjustments.update({
            "pace": "normal",
            "examples": "applied",
            "practice": "challenge",
            "check_understanding": True,
            "show_resources": True,
        })
    elif feedback_status in {"practice", "practice_requested"} or intent_key in {"ejercicio", "quiz"}:
        strategy = "guided_practice"
        next_action = "guided_practice"
        rationale = "El estudiante esta listo para practicar sin cambiar bruscamente de nivel."
        adjustments.update({
            "practice": "guided",
            "examples": "minimal_before_practice",
            "check_understanding": True,
        })
    elif feedback_status in {"pending_review", "answer_review"} or intent_key == "evaluacion_respuesta":
        strategy = "review_answer"
        next_action = "review_answer"
        rationale = "La prioridad es revisar la respuesta antes de introducir contenido nuevo."
        adjustments.update({
            "pace": "normal",
            "examples": "correction_based",
            "practice": "targeted",
            "check_understanding": True,
        })

    should_change_level = selected_level != current_level
    prompt_hint = (
        f"Personalizacion adaptativa: usa nivel {selected_level}, estrategia {strategy}, "
        f"accion {next_action}. Tema: {topic_label}. Ritmo: {adjustments['pace']}."
    )

    return {
        "contract_version": "adaptive_personalization.v1",
        "topic": topic_label,
        "current_level": current_level,
        "selected_level": selected_level,
        "should_change_level": should_change_level,
        "learning_state": learning_state,
        "strategy": strategy,
        "next_best_action": next_action,
        "rationale": rationale,
        "content_adjustments": adjustments,
        "prompt_hint": prompt_hint,
        "guardrails": [
            "No reemplaza login, rutas ni respuesta principal del chat.",
            "Solo ajusta nivel, ritmo y tipo de actividad.",
            "Debe aplicarse como contexto adicional y reversible.",
        ],
        "profile_snapshot": {
            "weak_topics": list(weak_topics or [])[:5],
            "mastered_topics": list(mastered_topics or [])[:5],
            "last_emotion": emotion_name,
            "last_intent": intent_key,
        },
        "evidence": {
            "source": "student_profiles.profile_json",
            "rules": ["emotion", "feedback", "weak_topics", "mastered_topics", "intent"],
        },
    }


def save_adaptive_plan(student_id: str, plan: Dict[str, Any]) -> None:
    """Guarda la ultima decision adaptativa dentro del perfil JSON."""
    if not student_id or not isinstance(plan, dict):
        return
    profile = get_profile(student_id)
    adaptive = profile.setdefault("adaptive", {})
    adaptive["last_plan"] = {
        "contract_version": plan.get("contract_version"),
        "topic": plan.get("topic"),
        "selected_level": plan.get("selected_level"),
        "strategy": plan.get("strategy"),
        "next_best_action": plan.get("next_best_action"),
        "updated_at": datetime.datetime.now().isoformat(timespec="seconds"),
    }
    profile["adaptive_summary"] = dict(profile.get("adaptive_summary") or {})
    profile["adaptive_summary"]["last_adaptive_strategy"] = plan.get("strategy")
    profile["adaptive_summary"]["last_selected_level"] = plan.get("selected_level")
    save_profile(student_id, profile)
