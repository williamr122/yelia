"""Official course content loaded from the thesis academic base."""

from __future__ import annotations

import json
import re
import unicodedata
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List


CONTENT_PATH = Path(__file__).resolve().parents[1] / "content" / "course_content.json"


TOPICS_BY_UNIT: Dict[int, List[str]] = {
    1: ["Introduccion a POO", "Clases y Objetos", "Atributos y metodos", "Encapsulamiento"],
    2: ["Herencia", "Polimorfismo", "Sobrecarga y sobrescritura", "Interfaces"],
    3: ["Diagramas UML", "Casos de uso", "Secuencia y actividad", "MVC"],
    4: ["Acceso a archivos", "Bases de Datos y ORM", "Integracion POO/MVC/Datos", "Pruebas"],
}


def _norm(text: str | None) -> str:
    raw = (text or "").strip().lower()
    raw = "".join(c for c in unicodedata.normalize("NFD", raw) if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", raw)


def _infer_topic(question: str, unit_id: int = 0) -> str:
    text = _norm(question)
    checks = [
        ("Encapsulamiento", ("encapsul", "private", "getter", "setter", "proteger")),
        ("Clases y Objetos", ("clase", "class", "objeto", "instancia", "poo", "programacion orientada")),
        ("Atributos y metodos", ("atributo", "metodo", "constructor", "caracteristica")),
        ("Herencia", ("herencia", "padre", "hija", "extends", "superclase", "subclase")),
        ("Polimorfismo", ("polimorf", "sobrecarga", "sobrescritura", "misma accion")),
        ("Interfaces", ("interfaz", "interface", "abstract")),
        ("Diagramas UML", ("uml", "diagrama", "caso de uso", "secuencia", "actividad")),
        ("MVC", ("mvc", "modelo", "vista", "controlador")),
        ("Bases de Datos y ORM", ("base de datos", "sql", "ddl", "orm", "jdbc", "tabla")),
        ("Acceso a archivos", ("archivo", "file", "leer", "guardar")),
        ("Pruebas", ("prueba", "test", "junit")),
    ]
    for topic, keywords in checks:
        if any(keyword in text for keyword in keywords):
            return topic
    return (TOPICS_BY_UNIT.get(unit_id) or ["Programacion Avanzada"])[0]


def _level_for(kind: str, unit_id: int) -> str:
    if kind == "diagnostic":
        return "Diagnostico"
    if unit_id <= 1:
        return "Basico"
    if unit_id in {2, 3}:
        return "Intermedio"
    return "Avanzado"


@lru_cache(maxsize=1)
def load_course_content() -> Dict[str, Any]:
    if not CONTENT_PATH.exists():
        return {}
    with CONTENT_PATH.open("r", encoding="utf-8-sig") as fh:
        return json.load(fh)


def _normalize_question(raw: Dict[str, Any], *, fallback_unit: int, kind: str) -> Dict[str, Any]:
    unit_id = int(raw.get("unit_id") or fallback_unit or 0)
    question = str(raw.get("question") or "").strip()
    options = [str(option).strip() for option in (raw.get("options") or []) if str(option).strip()]
    try:
        answer = int(raw.get("answer"))
    except Exception:
        answer = -1
    return {
        "id": str(raw.get("id") or f"{kind}-{unit_id}-{raw.get('number', 0)}"),
        "topic": raw.get("topic") or _infer_topic(question, unit_id),
        "level": raw.get("level") or _level_for(kind, unit_id),
        "question": question,
        "options": options,
        "answer": answer,
        "source": raw.get("source"),
        "unit_id": unit_id,
    }


def diagnostic_question_bank() -> List[Dict[str, Any]]:
    content = load_course_content()
    questions = content.get("diagnostic_questions") or []
    return [
        _normalize_question(item, fallback_unit=0, kind="diagnostic")
        for item in questions
        if item.get("question") and len(item.get("options") or []) >= 2
    ]


def course_units() -> List[Dict[str, Any]]:
    content = load_course_content()
    units = []
    for item in content.get("units") or []:
        try:
            unit_id = int(item.get("id"))
        except Exception:
            continue
        units.append({
            "id": unit_id,
            "title": str(item.get("title") or f"Unidad {unit_id}"),
            "subtitle": _unit_subtitle(unit_id, item),
            "topics": TOPICS_BY_UNIT.get(unit_id, []),
            "resources": item.get("resources") or [],
            "lesson_questions_count": len(item.get("lesson_questions") or []),
            "unit_exam_questions_count": len(item.get("unit_exam_questions") or []),
        })
    return units


def _unit_subtitle(unit_id: int, item: Dict[str, Any]) -> str:
    topics = TOPICS_BY_UNIT.get(unit_id) or []
    if topics:
        return ", ".join(topics) + "."
    return str(item.get("title") or f"Unidad {unit_id}")


def unit_question_bank(kind: str = "unit_exam") -> Dict[int, List[Dict[str, Any]]]:
    content = load_course_content()
    key = "lesson_questions" if kind == "lesson" else "unit_exam_questions"
    bank: Dict[int, List[Dict[str, Any]]] = {}
    for unit in content.get("units") or []:
        try:
            unit_id = int(unit.get("id"))
        except Exception:
            continue
        questions = [
            _normalize_question(item, fallback_unit=unit_id, kind=kind)
            for item in unit.get(key) or []
            if item.get("question") and len(item.get("options") or []) >= 2
        ]
        if questions:
            bank[unit_id] = questions
    return bank


def final_question_bank(total: int = 10) -> List[Dict[str, Any]]:
    """Build a balanced final exam from the official unit exams.

    The ZIP currently has unit exams but no independent final exam document.
    This derived final keeps the source traceable until a final-exam file exists.
    """
    bank = unit_question_bank("unit_exam")
    questions: List[Dict[str, Any]] = []
    per_unit = max(1, total // 4)
    for unit_id in range(1, 5):
        for item in bank.get(unit_id, [])[:per_unit]:
            clone = dict(item)
            clone["id"] = clone["id"].replace(f"u{unit_id}-exam", "final")
            clone["kind"] = "final_exam"
            questions.append(clone)
    extra_index = per_unit
    while len(questions) < total:
        added = False
        for unit_id in range(1, 5):
            unit_questions = bank.get(unit_id, [])
            if extra_index < len(unit_questions):
                clone = dict(unit_questions[extra_index])
                clone["id"] = clone["id"].replace(f"u{unit_id}-exam", "final")
                clone["kind"] = "final_exam"
                questions.append(clone)
                added = True
                if len(questions) >= total:
                    break
        if not added:
            break
        extra_index += 1
    return questions[:total]


def resources_for_topic(topic: str | None = None, limit: int = 3) -> List[Dict[str, Any]]:
    content = load_course_content()
    topic_norm = _norm(topic)
    preferred_unit = 0
    for unit_id, topics in TOPICS_BY_UNIT.items():
        if any(_norm(item) in topic_norm or topic_norm in _norm(item) for item in topics if topic_norm):
            preferred_unit = unit_id
            break

    resources: List[Dict[str, Any]] = []
    for unit in content.get("units") or []:
        try:
            unit_id = int(unit.get("id"))
        except Exception:
            continue
        if preferred_unit and unit_id != preferred_unit:
            continue
        for resource in unit.get("resources") or []:
            resources.append({
                "unit_id": unit_id,
                "unit_title": unit.get("title") or f"Unidad {unit_id}",
                "type": resource.get("type") or "unit_content",
                "title": resource.get("title") or f"Recurso Unidad {unit_id}",
                "source": resource.get("source"),
                "text_preview": resource.get("text_preview"),
            })

    if not resources and preferred_unit:
        return resources_for_topic(None, limit=limit)
    return resources[:max(1, int(limit or 3))]


def unit_content(unit_id: int) -> Dict[str, Any]:
    content = load_course_content()
    safe_unit = max(1, min(4, int(unit_id or 1)))
    unit = next(
        (item for item in content.get("units") or [] if int(item.get("id") or 0) == safe_unit),
        {},
    )
    return {
        "unit": {
            "id": safe_unit,
            "title": unit.get("title") or f"Unidad {safe_unit}",
            "subtitle": _unit_subtitle(safe_unit, unit),
            "topics": TOPICS_BY_UNIT.get(safe_unit, []),
        },
        "resources": unit.get("resources") or [],
        "lesson_questions": [
            _normalize_question(item, fallback_unit=safe_unit, kind="lesson")
            for item in unit.get("lesson_questions") or []
            if item.get("question") and len(item.get("options") or []) >= 2
        ],
        "unit_exam_questions_count": len(unit.get("unit_exam_questions") or []),
        "lesson_questions_count": len(unit.get("lesson_questions") or []),
    }
