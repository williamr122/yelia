"""Actualizacion del perfil academico adaptativo de YELIA."""
from __future__ import annotations

import datetime
from typing import Any, Dict, List, Optional

from backend.repositories.student_profile_repo import get_profile, save_profile


def _bump(container: Dict[str, Any], key: str, amount: int = 1) -> None:
    if not key:
        return
    try:
        container[key] = int(container.get(key, 0)) + amount
    except Exception:
        container[key] = amount


def _clean_topic(topic: Optional[str]) -> str:
    topic = (topic or "Programacion Avanzada").strip()
    return topic[:80] or "Programacion Avanzada"


def _unique_keep_recent(values: List[str], value: str, limit: int = 8) -> List[str]:
    cleaned = [str(v).strip() for v in values or [] if str(v).strip() and str(v).strip() != value]
    if value:
        cleaned.insert(0, value)
    return cleaned[:limit]


def _recommendation_summary(recommendations: List[Dict[str, Any]], limit: int = 5) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for rec in recommendations or []:
        out.append({
            "type": rec.get("type"),
            "title": rec.get("title"),
            "source": rec.get("source"),
            "url": rec.get("url"),
            "topic": rec.get("topic_used"),
            "reason": rec.get("reason"),
        })
        if len(out) >= limit:
            break
    return out


def _derive_next_action(feedback: Optional[Dict[str, Any]], emotion_key: str, intent_key: str) -> str:
    if isinstance(feedback, dict) and feedback.get("next_action"):
        return str(feedback["next_action"])
    if emotion_key in {"confused", "frustrated", "anxious"}:
        return "explain_simpler"
    if intent_key in {"quiz", "evaluacion_respuesta"}:
        return "review_answer"
    if intent_key in {"ejercicio"}:
        return "guided_practice"
    return "recommend_next_resource"


def update_adaptive_profile(
    *,
    student_id: str,
    topic: str,
    level: str,
    emotion: Optional[Dict[str, Any]],
    intent: str,
    recommendations: Optional[List[Dict[str, Any]]] = None,
    personalized_feedback: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Actualiza el perfil del estudiante y devuelve el perfil resultante."""
    profile = get_profile(student_id)
    topic_key = _clean_topic(topic)
    level_key = (level or profile.get("level_current") or "basico").strip().lower()
    emotion_key = ((emotion or {}).get("emotion") or "neutral").strip().lower()
    intent_key = (intent or "otro").strip().lower()

    profile["level_current"] = level_key
    profile["last_topic"] = topic_key

    stats = profile.setdefault("stats", {"messages": 0, "quizzes": 0, "exercises": 0})
    _bump(stats, "messages")
    if intent_key == "quiz":
        _bump(stats, "quizzes")
    if intent_key in {"ejercicio", "evaluacion_respuesta"}:
        _bump(stats, "exercises")

    metrics = profile.setdefault("metrics", {})
    metrics.setdefault("emotions", {})
    metrics.setdefault("intents", {})
    metrics.setdefault("topics", {})
    metrics.setdefault("feedback", {})
    _bump(metrics, "messages_total")
    _bump(metrics["emotions"], emotion_key)
    _bump(metrics["intents"], intent_key)
    _bump(metrics["topics"], topic_key)

    adaptive = profile.setdefault("adaptive", {})
    adaptive["last_topic"] = topic_key
    adaptive["last_level"] = level_key
    adaptive["last_emotion"] = emotion_key
    adaptive["last_emotion_label"] = (emotion or {}).get("label") or emotion_key
    adaptive["last_intent"] = intent_key
    adaptive["support_mode"] = emotion_key in {"confused", "frustrated", "anxious"}
    adaptive["next_best_action"] = _derive_next_action(personalized_feedback, emotion_key, intent_key)
    adaptive["recent_recommendations"] = _recommendation_summary(recommendations or [])
    adaptive["updated_at"] = datetime.datetime.now().isoformat(timespec="seconds")

    weak_topics = adaptive.setdefault("weak_topics", [])
    mastered_topics = adaptive.setdefault("mastered_topics", [])

    feedback_kind = (personalized_feedback or {}).get("kind") if isinstance(personalized_feedback, dict) else None
    feedback_status = (personalized_feedback or {}).get("status") if isinstance(personalized_feedback, dict) else None
    if feedback_kind:
        _bump(metrics["feedback"], str(feedback_kind))

    if feedback_status == "needs_help" or adaptive["support_mode"]:
        adaptive["learning_state"] = "needs_reinforcement"
        adaptive["weak_topics"] = _unique_keep_recent(weak_topics, topic_key)
        adaptive["mastered_topics"] = [t for t in mastered_topics if t != topic_key]
    elif feedback_status == "progress" or feedback_kind == "understood":
        adaptive["learning_state"] = "progressing"
        adaptive["mastered_topics"] = _unique_keep_recent(mastered_topics, topic_key)
        adaptive["weak_topics"] = [t for t in weak_topics if t != topic_key]
    elif feedback_status == "practice":
        adaptive["learning_state"] = "practicing"
    elif feedback_status == "pending_review":
        adaptive["learning_state"] = "reviewing_answer"
    else:
        adaptive.setdefault("learning_state", "active")

    profile["adaptive_summary"] = {
        "learning_state": adaptive.get("learning_state"),
        "next_best_action": adaptive.get("next_best_action"),
        "weak_topics": adaptive.get("weak_topics", [])[:5],
        "mastered_topics": adaptive.get("mastered_topics", [])[:5],
        "last_topic": topic_key,
        "last_level": level_key,
        "last_emotion": emotion_key,
    }

    save_profile(student_id, profile)
    return profile
