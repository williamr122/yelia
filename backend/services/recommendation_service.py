"""Recomendaciones pedagogicas adaptadas por emocion, nivel, tema e internet.

Contrato de salida:
- type: web_resource | practice | quiz | example | glossary | support | challenge
- title: titulo visible
- label: texto corto para chip
- explanation: que aporta la recomendacion
- url: enlace opcional
- reason: motivo pedagogico
- emotion_used / level_used / topic_used: trazabilidad para tesis y metricas
- message: prompt accionable para que el frontend pueda enviarlo como chip
"""
from __future__ import annotations

import re
import unicodedata
from typing import Any, Dict, List, Optional, Tuple

from backend.core.net import has_internet
from backend.services.course_content_service import resources_for_topic
from backend.services.exercise_generator_service import generate_exercises, generate_glossary


_RESOURCES_BY_TOPIC = {
    "poo": [
        {
            "title": "Oracle Java Tutorials: Classes and Objects",
            "url": "https://docs.oracle.com/javase/tutorial/java/javaOO/",
            "source": "Oracle",
            "explanation": "Unidad 1 del pensum: clases, objetos, atributos, metodos y constructores en Java.",
            "syllabus_unit": "Unidad 1: Fundamentos de la Programacion Orientada a Objetos",
        },
        {
            "title": "Programiz: Java Inheritance",
            "url": "https://www.programiz.com/java-programming/inheritance",
            "source": "Programiz",
            "explanation": "Unidad 2 del pensum: herencia con ejemplos cortos y visuales.",
            "syllabus_unit": "Unidad 2: Herencia, Polimorfismo y UML",
        },
        {
            "title": "Ejercicios de POO con Java y UML",
            "url": "http://www.fadmon.unal.edu.co/fileadmin/user_upload/investigacion/centro_editorial/libros/ejercicios%20de%20programacion.pdf",
            "source": "Bibliografia complementaria del silabo",
            "explanation": "Libro de ejercicios citado en el silabo para practicar POO, Java y UML.",
            "syllabus_unit": "Unidades 1, 2 y 3",
        },
        {
            "title": "Java 17: programacion avanzada",
            "url": "https://elibro.net/es/lc/uguayaquil/titulos/222668",
            "source": "Bibliografia basica UG",
            "explanation": "Texto base del plan analitico para reforzar Programacion Avanzada.",
            "syllabus_unit": "Bibliografia basica",
        },
    ],
    "uml": [
        {
            "title": "UML Diagrams: Class Diagram",
            "url": "https://www.uml-diagrams.org/class-diagrams-overview.html",
            "source": "UML-Diagrams.org",
            "explanation": "Unidad 3 del pensum: diagramas de clases y relaciones UML.",
            "syllabus_unit": "Unidad 3: UML y patron MVC",
        },
        {
            "title": "Ejercicios de POO con Java y UML",
            "url": "http://www.fadmon.unal.edu.co/fileadmin/user_upload/investigacion/centro_editorial/libros/ejercicios%20de%20programacion.pdf",
            "source": "Bibliografia complementaria del silabo",
            "explanation": "Recurso citado en el silabo para practicar UML aplicado a POO.",
            "syllabus_unit": "Unidad 3: UML y patron MVC",
        },
    ],
    "mvc": [
        {
            "title": "MDN: MVC",
            "url": "https://developer.mozilla.org/en-US/docs/Glossary/MVC",
            "source": "MDN",
            "explanation": "Unidad 3 del pensum: conceptos de Modelo, Vista y Controlador.",
            "syllabus_unit": "Unidad 3: UML y patron MVC",
        },
    ],
    "bd": [
        {
            "title": "Oracle Java Tutorials: JDBC Basics",
            "url": "https://docs.oracle.com/javase/tutorial/jdbc/basics/",
            "source": "Oracle",
            "explanation": "Unidad 4 del pensum: integracion de POO, MVC y acceso a datos con Java.",
            "syllabus_unit": "Unidad 4: Acceso a archivos y base de datos",
        },
        {
            "title": "Manual de SQL",
            "url": "https://jorgesanchez.net/manuales/sql/intro-sql-sql2016.html",
            "source": "Sitio web del plan analitico",
            "explanation": "Recurso del plan analitico para repasar SQL y bases de datos relacionales.",
            "syllabus_unit": "Unidad 4: Acceso a archivos y base de datos",
        },
        {
            "title": "Java SE Development Kit",
            "url": "https://www.oracle.com/java/technologies/downloads/",
            "source": "Sitio web del plan analitico",
            "explanation": "Herramienta base del pensum para compilar y ejecutar ejercicios Java.",
            "syllabus_unit": "Recursos de software del plan",
        },
        {
            "title": "Apache NetBeans",
            "url": "https://netbeans.apache.org/",
            "source": "Sitio web del silabo",
            "explanation": "IDE recomendado en el silabo/plan para desarrollar proyectos Java.",
            "syllabus_unit": "Recursos de software del plan",
        },
    ],
}

_LEVEL_LABELS = {
    "sin conocimientos": "basico",
    "sin_conocimientos": "basico",
    "basico": "basico",
    "basica": "basico",
    "básico": "basico",
    "intermedio": "intermedio",
    "intermedia": "intermedio",
    "avanzado": "avanzado",
    "avanzada": "avanzado",
}

_TYPE_PRIORITY = {
    "support": 0,
    "foundation": 1,
    "example": 2,
    "history_review": 2,
    "history_practice": 2,
    "mastery_challenge": 2,
    "practice": 3,
    "quiz": 4,
    "glossary": 5,
    "challenge": 6,
    "advanced": 7,
    "short": 8,
    "course_resource": 1,
    "web_resource": 9,
}

_PRIORITY_LABEL = {
    0: "alta",
    1: "alta",
    2: "alta",
    3: "media",
    4: "media",
    5: "media",
    6: "media",
    7: "media",
    8: "alta",
    9: "baja",
}


def _norm(text: Optional[str]) -> str:
    raw = (text or "").strip().lower()
    raw = "".join(c for c in unicodedata.normalize("NFD", raw) if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", raw)


def _topic_key(topic: Optional[str], user_text: str = "") -> str:
    t = _norm(f"{topic or ''} {user_text or ''}")
    if any(k in t for k in ("uml", "diagrama", "clases uml", "caso de uso")):
        return "uml"
    if any(k in t for k in ("mvc", "modelo vista controlador", "controlador")):
        return "mvc"
    if any(k in t for k in ("base de datos", "bd", "orm", "jdbc", "sql", "archivo")):
        return "bd"
    return "poo"


def _level_key(level: Optional[str]) -> str:
    return _LEVEL_LABELS.get(_norm(level), "intermedio")


def _emotion_key(emotion: Dict[str, Any]) -> Tuple[str, str]:
    key = _norm((emotion or {}).get("emotion") or "neutral") or "neutral"
    label = (emotion or {}).get("label") or key
    return key, label


def _online_available() -> bool:
    try:
        return bool(has_internet())
    except Exception:
        return False


def _make_rec(
    *,
    type_: str,
    title: str,
    label: str,
    message: str,
    explanation: str,
    reason: str,
    emotion_used: str,
    level_used: str,
    topic_used: str,
    url: Optional[str] = None,
    source: Optional[str] = None,
    extra: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    rank = _TYPE_PRIORITY.get(type_, 50)
    rec: Dict[str, Any] = {
        "type": type_,
        "label": label,
        "title": title,
        "explanation": explanation,
        "reason": reason,
        "message": message,
        "url": url,
        "source": source,
        "emotion_used": emotion_used,
        "level_used": level_used,
        "topic_used": topic_used,
        "priority": _PRIORITY_LABEL.get(rank, "media"),
        "rank": rank,
    }
    if extra:
        rec.update(extra)
    return rec


def _base_recommendations(
    *,
    topic_label: str,
    level_key: str,
    emotion_key: str,
    emotion_label: str,
) -> List[Dict[str, str]]:
    if emotion_key in {"confused", "frustrated", "anxious"}:
        return [
            {
                "type": "support",
                "label": "Explicar mas simple",
                "title": "Explicacion guiada",
                "message": f"Explicame {topic_label} con una definicion simple, una analogia y una pregunta de comprobacion.",
                "explanation": "Reduce la carga cognitiva cuando el estudiante muestra dificultad emocional o conceptual.",
                "reason": f"Se detecto {emotion_label}; conviene bajar la complejidad antes de practicar.",
            },
            {
                "type": "example",
                "label": "Dar ejemplo",
                "title": "Ejemplo minimo",
                "message": f"Dame un ejemplo minimo y correcto de {topic_label} en Java, maximo 12 lineas.",
                "explanation": "Convierte el concepto abstracto en una situacion concreta y verificable.",
                "reason": "El estudiante necesita ver el concepto funcionando sin demasiada teoria.",
            },
        ]
    if emotion_key in {"curious", "confident"}:
        return [
            {
                "type": "challenge",
                "label": "Dame un reto",
                "title": "Reto adaptado",
                "message": f"Dame un reto practico de {topic_label} con dificultad un poco mayor y criterios de evaluacion.",
                "explanation": "Aprovecha la disposicion del estudiante para subir un nivel de dificultad.",
                "reason": "La emocion detectada indica apertura para profundizar o practicar.",
            }
        ]
    if emotion_key == "bored":
        return [
            {
                "type": "short",
                "label": "Version rapida",
                "title": "Resumen aplicado",
                "message": f"Resume {topic_label} en 5 lineas y dame un ejemplo practico corto.",
                "explanation": "Mantiene la atencion con una respuesta directa y aplicada.",
                "reason": "Se detecto bajo interes; conviene ir al uso practico.",
            }
        ]
    return []


def _resource_recommendations(
    *,
    topic_key: str,
    topic_label: str,
    emotion_key: str,
    level_key: str,
    force: bool = False,
) -> List[Dict[str, Any]]:
    online = _online_available()
    if not force:
        return []
    local_resources = resources_for_topic(topic_label, limit=2)
    local_recs = [
        _make_rec(
            type_="course_resource",
            label="Recurso oficial",
            title=resource.get("title") or "Recurso de la unidad",
            explanation=f"Material base de {resource.get('unit_title') or 'la ruta academica'} registrado en el ZIP academico.",
            source=resource.get("source"),
            message=f"Usa el recurso oficial de {resource.get('unit_title')}: {resource.get('title')}.",
            reason="El estudiante pidio recursos; se prioriza el material oficial cargado para la ruta de aprendizaje.",
            emotion_used=emotion_key,
            level_used=level_key,
            topic_used=topic_label,
            extra={
                "unit_id": resource.get("unit_id"),
                "resource_type": resource.get("type"),
                "course_based": True,
                "rank": 1,
                "priority": "alta",
            },
        )
        for resource in local_resources
    ]
    resources = list(_RESOURCES_BY_TOPIC.get(topic_key) or _RESOURCES_BY_TOPIC["poo"])
    topic_norm = _norm(topic_label)
    if topic_key == "poo" and not any(k in topic_norm for k in ("herencia", "inheritance")):
        resources = [
            item for item in resources
            if "inheritance" not in _norm(item.get("title")) and "inheritance" not in _norm(item.get("url"))
        ] or resources
    limit = 3 if force else 1
    recs: List[Dict[str, Any]] = list(local_recs)
    for resource in resources[:limit]:
        recs.append(_make_rec(
            type_="web_resource",
            label="Recurso web",
            title=resource["title"],
            explanation=resource["explanation"],
            url=resource["url"],
            source=resource.get("source"),
            message=f"Relaciona este recurso con {topic_label}: {resource['url']}",
            reason="El estudiante pidio recursos web; se recomienda una fuente externa confiable para complementar la explicacion.",
            emotion_used=emotion_key,
            level_used=level_key,
            topic_used=topic_label,
            extra={
                "online_available": online,
                "curated": True,
                "syllabus_unit": resource.get("syllabus_unit"),
                "rank": 2 if force else _TYPE_PRIORITY["web_resource"],
                "priority": "alta" if force else "baja",
            },
        ))
    return recs


def _wants_online_resource(user_text: str) -> bool:
    text = _norm(user_text)
    return any(
        term in text
        for term in (
            "recomienda",
            "recomendacion",
            "recomendaciones",
            "recurso",
            "recursos",
            "fuente",
            "fuentes",
            "link",
            "enlace",
            "internet",
            "web",
            "tutorial",
            "documentacion",
            "documentacion oficial",
        )
    )


def _profile_counts(profile: Optional[Dict[str, Any]], group: str) -> Dict[str, int]:
    try:
        data = (((profile or {}).get("metrics") or {}).get(group) or {})
        return {str(k): int(v or 0) for k, v in data.items()}
    except Exception:
        return {}


def _adaptive_lists(profile: Optional[Dict[str, Any]]) -> Tuple[List[str], List[str]]:
    adaptive = (profile or {}).get("adaptive") or {}
    summary = (profile or {}).get("adaptive_summary") or {}
    weak = adaptive.get("weak_topics") or summary.get("weak_topics") or []
    mastered = adaptive.get("mastered_topics") or summary.get("mastered_topics") or []
    return [str(x) for x in weak if str(x).strip()], [str(x) for x in mastered if str(x).strip()]


def _history_recommendations(
    *,
    topic_label: str,
    level_key: str,
    emotion_key: str,
    profile: Optional[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    if not profile:
        return []

    weak_topics, mastered_topics = _adaptive_lists(profile)
    topic_counts = _profile_counts(profile, "topics")
    feedback_counts = _profile_counts(profile, "feedback")
    topic_count = int(topic_counts.get(topic_label, 0))
    recs: List[Dict[str, Any]] = []

    if topic_label in weak_topics:
        recs.append(_make_rec(
            type_="history_review",
            label="Repasar debil",
            title=f"Repaso adaptativo de {topic_label}",
            message=f"Repasemos {topic_label} desde la base, con un ejemplo minimo y una pregunta de comprobacion.",
            explanation="El historial marca este tema como debil; conviene reforzarlo antes de avanzar.",
            reason="Recomendacion generada por historial adaptativo del estudiante.",
            emotion_used=emotion_key,
            level_used=level_key,
            topic_used=topic_label,
            extra={
                "history_based": True,
                "history_reason": "topic_in_weak_topics",
                "rank": 1,
                "priority": "alta",
            },
        ))

    if topic_count >= 3 or int(feedback_counts.get("needs_reinforcement", 0)) >= 2:
        recs.append(_make_rec(
            type_="history_practice",
            label="Practica guiada",
            title=f"Practica guiada por historial: {topic_label}",
            message=f"Dame una practica guiada de {topic_label}, paso a paso, y luego revisa mi respuesta.",
            explanation="El estudiante ha trabajado este tema varias veces; la practica guiada ayuda a consolidar.",
            reason="Recomendacion generada por frecuencia de consultas y necesidades previas de refuerzo.",
            emotion_used=emotion_key,
            level_used=level_key,
            topic_used=topic_label,
            extra={
                "history_based": True,
                "history_reason": "repeated_topic_or_reinforcement",
                "rank": 2,
                "priority": "alta",
            },
        ))

    if topic_label in mastered_topics and level_key in {"intermedio", "avanzado"}:
        recs.append(_make_rec(
            type_="mastery_challenge",
            label="Reto de avance",
            title=f"Reto para subir nivel: {topic_label}",
            message=f"Dame un reto aplicado de {topic_label} con criterios de evaluacion y retroalimentacion.",
            explanation="El historial indica dominio del tema; conviene subir dificultad de forma controlada.",
            reason="Recomendacion generada porque el tema aparece como dominado.",
            emotion_used=emotion_key,
            level_used=level_key,
            topic_used=topic_label,
            extra={
                "history_based": True,
                "history_reason": "topic_in_mastered_topics",
                "rank": 2,
                "priority": "alta",
            },
        ))

    return recs


def build_recommendations(
    *,
    user_text: str,
    topic: Optional[str],
    level: str,
    emotion: Dict[str, Any],
    intent: str = "otro",
    history_profile: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """Genera recomendaciones completas y ordenadas para chat, tesis y metricas."""
    emotion_key, emotion_label = _emotion_key(emotion)
    level_key = _level_key(level)
    topic_label = topic or "Programacion Avanzada"
    topic_key = _topic_key(topic_label, user_text)
    wants_resources = _wants_online_resource(user_text)
    recs: List[Dict[str, Any]] = []
    recs.extend(_history_recommendations(
        topic_label=topic_label,
        level_key=level_key,
        emotion_key=emotion_key,
        profile=history_profile,
    ))

    for item in _base_recommendations(
        topic_label=topic_label,
        level_key=level_key,
        emotion_key=emotion_key,
        emotion_label=emotion_label,
    ):
        recs.append(
            _make_rec(
                type_=item["type"],
                label=item["label"],
                title=item["title"],
                message=item["message"],
                explanation=item["explanation"],
                reason=item["reason"],
                emotion_used=emotion_key,
                level_used=level_key,
                topic_used=topic_label,
            )
        )

    if level_key == "basico":
        recs.append(
            _make_rec(
                type_="foundation",
                label="Base primero",
                title="Refuerzo de bases",
                message=f"Explicame los conceptos base de {topic_label} antes del ejemplo, como si estuviera empezando.",
                explanation="Refuerza vocabulario y conceptos previos para evitar saltos de dificultad.",
                reason="El nivel detectado requiere fundamentos antes de ejercicios extensos.",
                emotion_used=emotion_key,
                level_used=level_key,
                topic_used=topic_label,
            )
        )
    elif level_key == "avanzado":
        recs.append(
            _make_rec(
                type_="advanced",
                label="Profundizar",
                title="Profundizacion avanzada",
                message=f"Profundiza {topic_label} con buenas practicas, errores comunes y un caso aplicado.",
                explanation="Eleva el nivel con criterios de diseno y buenas practicas.",
                reason="El nivel detectado permite trabajar con mayor profundidad tecnica.",
                emotion_used=emotion_key,
                level_used=level_key,
                topic_used=topic_label,
            )
        )

    exercises = generate_exercises(focus_topic=topic_label, level=level_key, mistakes=[])
    if exercises:
        first = exercises[0]
        recs.append(
            _make_rec(
                type_="practice",
                label="Practicar",
                title=first.get("title") or "Actividad sugerida",
                message=first.get("prompt") or f"Dame un ejercicio de {topic_label}.",
                explanation="Permite aplicar el concepto y generar evidencia de aprendizaje.",
                reason="La practica ayuda a consolidar el tema actual.",
                emotion_used=emotion_key,
                level_used=level_key,
                topic_used=topic_label,
            )
        )

    if intent != "quiz":
        recs.append(
            _make_rec(
                type_="quiz",
                label="Hacer quiz",
                title="Mini quiz",
                message=f"Hazme un mini quiz de 3 preguntas sobre {topic_label}.",
                explanation="Comprueba comprension y permite retroalimentacion inmediata.",
                reason="Un quiz corto confirma si el estudiante ya puede reconocer el concepto.",
                emotion_used=emotion_key,
                level_used=level_key,
                topic_used=topic_label,
            )
        )

    glossary = generate_glossary(topic_label)
    if glossary:
        recs.append(
            _make_rec(
                type_="glossary",
                label="Glosario",
                title="Glosario breve",
                message=f"Dame un glosario breve de {topic_label} con ejemplos sencillos.",
                explanation="Aclara terminos clave para mejorar comprension antes de avanzar.",
                reason="El tema contiene vocabulario tecnico que puede bloquear el aprendizaje.",
                emotion_used=emotion_key,
                level_used=level_key,
                topic_used=topic_label,
            )
        )

    web_recs = _resource_recommendations(
        topic_key=topic_key,
        topic_label=topic_label,
        emotion_key=emotion_key,
        level_key=level_key,
        force=wants_resources,
    )
    recs.extend(web_recs)

    # Deduplicacion manteniendo el mejor orden. Los recursos web se distinguen por URL.
    seen: set[str] = set()
    unique: List[Dict[str, Any]] = []
    for rec in sorted(recs, key=lambda item: int(item.get("rank", 50))):
        kind = str(rec.get("type") or "")
        dedupe_key = f"{kind}:{rec.get('url')}" if kind == "web_resource" else kind
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)
        unique.append(rec)

    limited = unique[:6]
    if wants_resources and not any(item.get("type") == "web_resource" for item in limited):
        first_web = next((item for item in unique if item.get("type") == "web_resource"), None)
        if first_web:
            limited = limited[:5] + [first_web]

    return limited


def recommendations_to_suggestions(recommendations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Convierte recomendaciones completas al formato de chips del frontend."""
    suggestions: List[Dict[str, Any]] = []
    seen_labels: set[str] = set()
    for rec in recommendations or []:
        if rec.get("type") == "web_resource":
            label = rec.get("source") or rec.get("title") or "Recurso web"
        else:
            label = rec.get("label") or rec.get("title")
        message = rec.get("message") or rec.get("url")
        if not label or not message:
            continue
        label = str(label).strip()
        if label in seen_labels:
            continue
        seen_labels.add(label)
        suggestions.append({
            "label": label,
            "message": message,
            "actionKey": rec.get("type") or "recommendation",
            "title": rec.get("title"),
            "reason": rec.get("reason"),
        })
    return suggestions
