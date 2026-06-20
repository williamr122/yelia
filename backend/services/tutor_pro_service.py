"""
Proyecto: YELIA4AP
Archivo: backend/services/tutor_pro_service.py
Descripción: Extras pedagógicos del tutor sin romper el flujo principal del chat.

Revisión: 2026-03-29
"""
from __future__ import annotations

import os
from typing import Any, Dict, Optional

from backend.repositories.student_profile_repo import get_profile, save_profile
from backend.services.level_detector_service import detect_level
from backend.services.exercise_generator_service import generate_exercises, generate_glossary


def _wants_personalized_practice(user_text: str) -> bool:
    t = (user_text or "").lower()
    keys = [
        "profundizar", "profundiza", "más ejercicios", "mas ejercicios", "practicar",
        "ejercicio", "ejercicios", "quiz", "reto", "taller", "rúbrica", "rubrica",
        "glosario", "proyecto", "parcial", "aumentar", "mejorar", "qué más", "que más",
        "subir nivel", "subir dificultad",
    ]
    return any(k in t for k in keys)


def _bump_counter(container: Dict[str, Any], key: str, amount: int = 1) -> None:
    """Incrementa un contador dentro de un dict sin romper si el valor previo no es int."""
    if not key:
        return
    try:
        container[key] = int(container.get(key, 0)) + amount
    except Exception:
        container[key] = amount


def _normalize_topic_key(topic: Optional[str]) -> str:
    topic = (topic or "Programacion Avanzada").strip()
    return topic[:80] or "Programacion Avanzada"


def _update_adaptive_trace(
    profile: Dict[str, Any],
    *,
    focus_topic: Optional[str],
    level: str,
    emotion: Optional[Dict[str, Any]],
    intent: Optional[str],
) -> None:
    """Guarda senales pedagogicas para personalizacion adaptativa.

    Se guarda en el JSON flexible de student_profiles para no tocar el esquema.
    """
    metrics = profile.setdefault("metrics", {})
    adaptive = profile.setdefault("adaptive", {})

    emotion_key = ((emotion or {}).get("emotion") or "neutral").strip().lower()
    intent_key = (intent or "otro").strip().lower()
    topic_key = _normalize_topic_key(focus_topic)

    metrics.setdefault("emotions", {})
    metrics.setdefault("intents", {})
    metrics.setdefault("topics", {})
    _bump_counter(metrics["emotions"], emotion_key)
    _bump_counter(metrics["intents"], intent_key)
    _bump_counter(metrics["topics"], topic_key)

    adaptive["last_emotion"] = emotion_key
    adaptive["last_emotion_label"] = (emotion or {}).get("label") or "neutral"
    adaptive["last_intent"] = intent_key
    adaptive["last_topic"] = topic_key
    adaptive["last_level"] = level
    adaptive["support_mode"] = emotion_key in {"confused", "frustrated", "anxious"}

    if adaptive["support_mode"]:
        _bump_counter(metrics, "support_needed")
    if emotion_key in {"curious", "confident"}:
        _bump_counter(metrics, "challenge_ready")


def _build_append_markdown(
    level: str,
    topic: Optional[str],
    user_text: str,
    profile: Dict[str, Any],
) -> Optional[str]:
    blocks: list[str] = []

    if "glosario" in (user_text or "").lower():
        glossary = generate_glossary(topic)
        if glossary:
            blocks.append("\n\n---\n\n## Glosario breve de apoyo")
            for item in glossary[:5]:
                blocks.append(
                    f"- **{item.get('concepto', 'Concepto')}**: {item.get('definicion', '')}"
                )

    if _wants_personalized_practice(user_text):
        mistakes = profile.get("mistakes") or []
        exercises = generate_exercises(focus_topic=topic, level=level, mistakes=mistakes)
        if exercises:
            blocks.append("\n\n## Actividades sugeridas según tu nivel")
            blocks.append(f"**Nivel detectado:** `{level}`")
            for i, item in enumerate(exercises[:2], start=1):
                blocks.append(
                    f"\n### Opción {i}: {item.get('title', 'Actividad')}\n{item.get('prompt', '')}"
                )
                rubric = item.get("rubric") or []
                if rubric:
                    blocks.append("\n**Criterios de evaluación:**")
                    for r in rubric:
                        blocks.append(f"- {r}")
                tips = item.get("tips") or []
                if tips:
                    blocks.append("\n**Tips:**")
                    for tip in tips:
                        blocks.append(f"- {tip}")
            blocks.append("\nResponde con **1** o **2** si quieres que te lo desarrolle paso a paso.")

    return "\n".join(blocks) if blocks else None


def build_tutor_additions(
    *,
    student_id: str,
    user_text: str,
    focus_topic: Optional[str] = None,
    code_context: Optional[str] = None,
    emotion: Optional[Dict[str, Any]] = None,
    intent: Optional[str] = None,
) -> Dict[str, Any]:
    if os.getenv("ENABLE_TUTOR_PRO", "1") != "1":
        return {}
    if not student_id:
        return {}

    profile = get_profile(student_id)

    det = detect_level(user_text, code_context)
    level = det.get("level") or profile.get("level_current") or "intermedio"
    profile["level_current"] = level
    profile["level_confidence"] = det.get("confidence", profile.get("level_confidence", 0.5))

    profile.setdefault("metrics", {})
    profile["metrics"]["messages_total"] = int(profile["metrics"].get("messages_total", 0)) + 1
    if focus_topic:
        profile["last_topic"] = focus_topic
    _update_adaptive_trace(
        profile,
        focus_topic=focus_topic,
        level=level,
        emotion=emotion,
        intent=intent,
    )

    append_md = _build_append_markdown(level, focus_topic, user_text, profile)
    save_profile(student_id, profile)

    out: Dict[str, Any] = {"profile": profile, "level": level}
    if append_md:
        out["append_markdown"] = append_md
    return out
