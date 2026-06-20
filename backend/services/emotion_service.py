"""Detección emocional ligera para adaptar la tutoría de YELIA."""
from __future__ import annotations

import re
import unicodedata
from typing import Any, Dict


def _norm(text: str) -> str:
    text = (text or "").strip().lower()
    text = "".join(
        ch for ch in unicodedata.normalize("NFD", text)
        if unicodedata.category(ch) != "Mn"
    )
    return re.sub(r"\s+", " ", text)


_EMOTION_RULES = {
    "frustrated": {
        "label": "frustración",
        "strategy": "validar la dificultad, bajar la carga cognitiva y guiar paso a paso",
        "avatar_expression": "error",
        "keywords": [
            "no puedo", "no me sale", "me sale error", "odio", "me frustra",
            "estoy frustrado", "estoy frustrada", "ya no puedo", "me rindo",
            "no funciona", "siempre falla", "estoy perdido", "estoy perdida",
        ],
    },
    "confused": {
        "label": "confusión",
        "strategy": "explicar desde una idea base, usar ejemplo corto y confirmar comprensión",
        "avatar_expression": "curious",
        "keywords": [
            "no entiendo", "no entendi", "no comprendo", "confundido",
            "confundida", "me confunde", "explicame mejor", "explica mejor",
            "desde cero", "que significa", "que es", "como asi",
        ],
    },
    "anxious": {
        "label": "ansiedad académica",
        "strategy": "dar calma, ordenar prioridades y proponer una tarea pequeña alcanzable",
        "avatar_expression": "curious",
        "keywords": [
            "tengo miedo", "me preocupa", "estoy nervioso", "estoy nerviosa",
            "me va mal", "voy a reprobar", "no llego", "urgente",
            "examen", "parcial", "no me alcanza el tiempo",
        ],
    },
    "curious": {
        "label": "curiosidad",
        "strategy": "ampliar con una conexión práctica y proponer reto opcional",
        "avatar_expression": "happy",
        "keywords": [
            "quiero saber", "me interesa", "por que", "por qué",
            "que pasaria", "que más", "que mas", "profundiza",
            "dame mas", "dame más", "curioso", "curiosa",
        ],
    },
    "confident": {
        "label": "confianza",
        "strategy": "subir ligeramente la dificultad y sugerir práctica aplicada",
        "avatar_expression": "happy",
        "keywords": [
            "ya entendi", "ya entendí", "facil", "fácil", "lo logre",
            "lo hice", "quiero algo mas dificil", "mas dificil", "más difícil",
            "reto", "avanzado",
        ],
    },
    "bored": {
        "label": "desinterés",
        "strategy": "hacer la respuesta más breve, práctica y orientada a un reto concreto",
        "avatar_expression": "neutral",
        "keywords": [
            "aburrido", "aburrida", "me aburre", "no me interesa",
            "muy largo", "resumelo", "resúmelo", "hazlo corto",
        ],
    },
}

_EMOTION_ACTIONS = {
    "frustrated": ["Explicar mas simple", "Revisar error paso a paso", "Practicar con guia"],
    "confused": ["Explicar desde cero", "Dar ejemplo", "Hacer quiz corto"],
    "anxious": ["Ordenar prioridades", "Practicar una parte", "Resumen rapido"],
    "curious": ["Profundizar", "Dame un reto", "Ver aplicacion real"],
    "confident": ["Subir dificultad", "Reto aplicado", "Quiz avanzado"],
    "bored": ["Version rapida", "Ejemplo practico", "Reto corto"],
    "neutral": ["Dar ejemplo", "Practicar", "Hacer quiz"],
}

_EMOTION_TONE = {
    "frustrated": "calmado, empatico y paso a paso",
    "confused": "claro, basico y comprobando comprension",
    "anxious": "tranquilo, ordenado y con una tarea pequena",
    "curious": "motivador, ampliando con conexiones practicas",
    "confident": "retador y tecnico sin perder claridad",
    "bored": "breve, directo y aplicado",
    "neutral": "claro, cercano y pedagogico",
}

_EMOTION_RESPONSE_POLICY = {
    "frustrated": (
        "Respuesta breve y contenida: valida la dificultad en 1 linea, divide la solucion "
        "en 3 pasos maximo y evita explicaciones largas. Cierra con una accion pequena."
    ),
    "confused": (
        "Respuesta corta y guiada: 1 definicion simple, 1 analogia, 1 mini ejemplo y "
        "1 pregunta de comprobacion. No uses una explicacion extensa salvo que el usuario la pida."
    ),
    "anxious": (
        "Respuesta calmada: ordena prioridades, explica solo lo esencial y propone una tarea "
        "alcanzable de menos de 5 minutos."
    ),
    "curious": (
        "Respuesta ampliada moderada: conecta el tema con un caso practico y ofrece una ruta "
        "para profundizar sin saturar."
    ),
    "confident": (
        "Respuesta con mayor desafio: resume la base, sube un poco la dificultad y propone "
        "un reto verificable."
    ),
    "bored": (
        "Respuesta muy breve: ve directo al uso practico, evita teoria larga y ofrece un reto corto."
    ),
    "neutral": (
        "Respuesta clara y equilibrada: explica, ejemplifica y pregunta si desea practicar."
    ),
}


def detect_emotion(text: str) -> Dict[str, Any]:
    """Clasifica emoción del estudiante a partir del mensaje escrito.

    Es una heurística explicable, rápida y sin costo de API. Devuelve un contrato
    estable para recomendaciones y avatar.
    """
    clean = _norm(text)
    if not clean:
        return {
            "emotion": "neutral",
            "label": "neutral",
            "confidence": 0.5,
            "intensity": 0.0,
            "strategy": "responder con tono claro y cercano",
            "avatar_expression": "neutral",
            "tone": _EMOTION_TONE["neutral"],
            "suggested_actions": _EMOTION_ACTIONS["neutral"],
            "response_policy": _EMOTION_RESPONSE_POLICY["neutral"],
            "signals": [],
        }

    scores: Dict[str, list[str]] = {}
    for emotion, rule in _EMOTION_RULES.items():
        hits = [kw for kw in rule["keywords"] if kw in clean]
        if hits:
            scores[emotion] = hits

    punctuation_boost = 0.08 if any(mark in text for mark in ("!!!", "???")) else 0.0
    question_boost = 0.05 if "?" in text or "¿" in text else 0.0

    if not scores:
        return {
            "emotion": "neutral",
            "label": "neutral",
            "confidence": 0.55,
            "intensity": min(0.35, question_boost),
            "strategy": "responder con tono claro y cercano",
            "avatar_expression": "explain",
            "tone": _EMOTION_TONE["neutral"],
            "suggested_actions": _EMOTION_ACTIONS["neutral"],
            "response_policy": _EMOTION_RESPONSE_POLICY["neutral"],
            "signals": [],
        }

    emotion = max(scores, key=lambda key: len(scores[key]))
    hits = scores[emotion]
    rule = _EMOTION_RULES[emotion]
    confidence = min(0.95, 0.58 + (0.12 * len(hits)) + punctuation_boost + question_boost)
    intensity = min(1.0, 0.35 + (0.16 * len(hits)) + punctuation_boost)

    return {
        "emotion": emotion,
        "label": rule["label"],
        "confidence": round(confidence, 2),
        "intensity": round(intensity, 2),
        "strategy": rule["strategy"],
        "avatar_expression": rule["avatar_expression"],
        "tone": _EMOTION_TONE.get(emotion, _EMOTION_TONE["neutral"]),
        "suggested_actions": _EMOTION_ACTIONS.get(emotion, _EMOTION_ACTIONS["neutral"]),
        "response_policy": _EMOTION_RESPONSE_POLICY.get(emotion, _EMOTION_RESPONSE_POLICY["neutral"]),
        "signals": hits[:5],
    }
