"""Structured quiz engine for exact evaluation in YELIA."""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional

from backend.db.session import db_session
from backend.services.course_content_service import unit_question_bank


TOPIC_ALIASES = {
    "mvc": "Arquitectura MVC",
    "modelo vista controlador": "Arquitectura MVC",
    "arquitectura mvc": "Arquitectura MVC",
    "clase": "Clases y Objetos",
    "objeto": "Clases y Objetos",
    "poo": "Clases y Objetos",
    "herencia": "Herencia y Polimorfismo",
    "polimorfismo": "Herencia y Polimorfismo",
    "interface": "Herencia y Polimorfismo",
    "interfaz": "Herencia y Polimorfismo",
    "uml": "Diagramas UML",
    "diagrama": "Diagramas UML",
    "base de datos": "Bases de Datos y ORM",
    "sql": "Bases de Datos y ORM",
    "jdbc": "Bases de Datos y ORM",
    "orm": "Bases de Datos y ORM",
}

UNIT_TOPIC_ALIASES = {
    1: "Unidad 1: Introduccion a la Programacion Orientada a Objetos",
    2: "Unidad 2: Lenguaje de Modelado Unificado",
    3: "Unidad 3: Aplicacion de la Programacion Orientada a Objetos",
    4: "Unidad 4: Acceso a Archivos y Base de Datos",
}


QUESTION_BANK: Dict[str, List[Dict[str, Any]]] = {
    "Arquitectura MVC": [
        {
            "question": "En MVC, que componente contiene la logica de datos y reglas principales del dominio?",
            "options": {
                "a": "Vista",
                "b": "Modelo",
                "c": "Controlador",
                "d": "Router visual",
            },
            "answer": "b",
            "explanation": "El Modelo representa datos, reglas y operaciones del dominio.",
        },
        {
            "question": "Cual es una senal de mal diseno MVC?",
            "options": {
                "a": "El controlador coordina entre vista y modelo",
                "b": "La vista solo muestra informacion",
                "c": "La vista contiene consultas SQL y reglas de negocio",
                "d": "El modelo valida datos importantes",
            },
            "answer": "c",
            "explanation": "La vista no debe mezclar persistencia ni reglas de negocio.",
        },
        {
            "question": "Que funcion cumple principalmente el Controlador?",
            "options": {
                "a": "Recibir eventos o peticiones y coordinar la respuesta",
                "b": "Guardar directamente todos los estilos visuales",
                "c": "Ser la base de datos",
                "d": "Reemplazar al modelo",
            },
            "answer": "a",
            "explanation": "El controlador interpreta la entrada y coordina modelo/vista.",
        },
    ],
    "Clases y Objetos": [
        {
            "question": "En POO, que representa una clase?",
            "options": {
                "a": "Una instancia concreta",
                "b": "Un metodo especial",
                "c": "Una plantilla para crear objetos",
                "d": "Un valor primitivo",
            },
            "answer": "c",
            "explanation": "Una clase define atributos y comportamientos que tendran sus objetos.",
        },
        {
            "question": "Que representa un objeto?",
            "options": {
                "a": "Una instancia concreta de una clase",
                "b": "Una plantilla sin datos",
                "c": "Un comentario de codigo",
                "d": "Un paquete de Java",
            },
            "answer": "a",
            "explanation": "El objeto es la entidad creada a partir de una clase.",
        },
        {
            "question": "Que principio protege atributos internos usando metodos publicos?",
            "options": {
                "a": "Herencia",
                "b": "Polimorfismo",
                "c": "Abstraccion",
                "d": "Encapsulamiento",
            },
            "answer": "d",
            "explanation": "El encapsulamiento oculta datos internos y controla el acceso.",
        },
    ],
    "Herencia y Polimorfismo": [
        {
            "question": "Que permite la herencia en Programacion Orientada a Objetos?",
            "options": {
                "a": "Reutilizar y extender atributos o metodos de una clase padre",
                "b": "Eliminar todos los constructores",
                "c": "Convertir una base de datos en interfaz",
                "d": "Evitar la creacion de objetos",
            },
            "answer": "a",
            "explanation": "La herencia permite que una subclase reutilice y especialice comportamiento de una superclase.",
        },
        {
            "question": "Que describe mejor el polimorfismo?",
            "options": {
                "a": "Un atributo privado sin getter",
                "b": "Una misma operacion que puede comportarse distinto segun el objeto real",
                "c": "Un diagrama sin relaciones",
                "d": "Una tabla SQL con clave primaria",
            },
            "answer": "b",
            "explanation": "El polimorfismo permite invocar una misma interfaz/metodo y obtener comportamientos especificos por tipo.",
        },
        {
            "question": "En Java, que palabra clave se usa para indicar que una clase implementa una interfaz?",
            "options": {
                "a": "extends",
                "b": "new",
                "c": "implements",
                "d": "private",
            },
            "answer": "c",
            "explanation": "La palabra clave implements conecta una clase concreta con una interfaz.",
        },
    ],
    "Diagramas UML": [
        {
            "question": "Que diagrama UML muestra clases, atributos, metodos y relaciones?",
            "options": {
                "a": "Diagrama de clases",
                "b": "Diagrama de actividades",
                "c": "Diagrama de despliegue",
                "d": "Diagrama de estados",
            },
            "answer": "a",
            "explanation": "El diagrama de clases representa la estructura estatica del sistema.",
        },
        {
            "question": "Que relacion indica que una clase contiene partes con ciclo de vida dependiente?",
            "options": {
                "a": "Asociacion",
                "b": "Composicion",
                "c": "Dependencia simple",
                "d": "Implementacion",
            },
            "answer": "b",
            "explanation": "En composicion, la parte depende fuertemente del todo.",
        },
        {
            "question": "Que diagrama ayuda a ver el orden de mensajes entre objetos?",
            "options": {
                "a": "Casos de uso",
                "b": "Secuencia",
                "c": "Clases",
                "d": "Paquetes",
            },
            "answer": "b",
            "explanation": "El diagrama de secuencia muestra interacciones en el tiempo.",
        },
    ],
    "Bases de Datos y ORM": [
        {
            "question": "Que ventaja principal aporta un ORM?",
            "options": {
                "a": "Permite mapear objetos a tablas",
                "b": "Elimina toda necesidad de validar datos",
                "c": "Reemplaza al lenguaje Java",
                "d": "Solo sirve para diseno grafico",
            },
            "answer": "a",
            "explanation": "Un ORM conecta objetos del codigo con registros/tablas de la base de datos.",
        },
        {
            "question": "En una arquitectura ordenada, donde conviene ubicar consultas a la base de datos?",
            "options": {
                "a": "Directamente en la vista",
                "b": "En el HTML",
                "c": "En repositorios/DAO o capa de acceso a datos",
                "d": "En comentarios",
            },
            "answer": "c",
            "explanation": "Repositorio o DAO separa la persistencia de la interfaz y la logica visual.",
        },
        {
            "question": "Que significa CRUD?",
            "options": {
                "a": "Create, Read, Update, Delete",
                "b": "Class, Route, User, Data",
                "c": "Compile, Run, Use, Debug",
                "d": "Code, Render, Upload, Design",
            },
            "answer": "a",
            "explanation": "CRUD resume las operaciones basicas sobre datos.",
        },
    ],
}


def canonical_topic(topic: str = "", fallback_text: str = "") -> str:
    request_text = (fallback_text or "").lower()
    for key, value in TOPIC_ALIASES.items():
        if key in request_text:
            return value

    haystack = f"{topic} {fallback_text}".lower()
    for key, value in TOPIC_ALIASES.items():
        if key in haystack:
            return value
    return topic.strip() or "Programacion Avanzada"


def requested_unit(text: str = "") -> Optional[int]:
    haystack = (text or "").lower()
    match = re.search(r"\bunidad\s*([1-4])\b", haystack)
    if match:
        return int(match.group(1))
    return None


def requested_count(text: str = "", default: int = 3) -> int:
    haystack = (text or "").lower()
    match = re.search(r"\b(\d{1,2})\s+preguntas?\b", haystack)
    if match:
        return max(1, min(10, int(match.group(1))))
    if "autoevalu" in haystack or "examen" in haystack:
        return 10
    return default


def _official_question_to_structured(raw: Dict[str, Any], index: int) -> Dict[str, Any]:
    options = list(raw.get("options") or [])
    letters = ("a", "b", "c", "d")
    option_map = {
        letter: str(options[pos]).strip()
        for pos, letter in enumerate(letters)
        if pos < len(options)
    }
    answer_index = int(raw.get("answer") or 0)
    answer_letter = letters[answer_index] if 0 <= answer_index < len(letters) else "a"
    question_text = str(raw.get("question") or "").strip()
    if int(raw.get("unit_id") or 0) == 1 and "ddl" in question_text.lower():
        question_text = "¿Qué método especial se ejecuta al crear un objeto de una clase?"
        option_map = {
            "a": "Constructor",
            "b": "Getter",
            "c": "Setter",
            "d": "Paquete",
        }
        answer_letter = "a"
        explanation = "El constructor inicializa el objeto cuando se crea una instancia de la clase."
    else:
        explanation = str(raw.get("explanation") or raw.get("topic") or "Revisa el concepto de la unidad.").strip()

    return {
        "id": index,
        "question": question_text,
        "options": option_map,
        "answer": answer_letter,
        "explanation": explanation,
    }


def build_structured_quiz(topic: str, count: int = 3, request_text: str = "") -> Dict[str, Any]:
    unit_id = requested_unit(f"{topic} {request_text}")
    if unit_id:
        official_bank = unit_question_bank("unit_exam").get(unit_id) or []
        selected = official_bank[: max(1, min(count, len(official_bank) or count))]
        questions = [
            _official_question_to_structured(item, index)
            for index, item in enumerate(selected, start=1)
            if item.get("question") and len(item.get("options") or []) >= 2
        ]
        if questions:
            topic_label = UNIT_TOPIC_ALIASES.get(unit_id) or f"Unidad {unit_id}"
            return {"topic": topic_label, "unit_id": unit_id, "questions": questions, "total": len(questions)}

    canonical = canonical_topic(topic, request_text)
    bank = QUESTION_BANK.get(canonical) or QUESTION_BANK["Clases y Objetos"]
    questions = []
    for index, item in enumerate(bank[: max(1, min(count, len(bank)))], start=1):
        questions.append(
            {
                "id": index,
                "question": item["question"],
                "options": item["options"],
                "answer": item["answer"],
                "explanation": item["explanation"],
            }
        )
    return {"topic": canonical, "questions": questions, "total": len(questions)}


def format_quiz_for_chat(quiz: Dict[str, Any]) -> str:
    lines = [
        f"Mini quiz de {quiz.get('topic') or 'Programacion Avanzada'}",
        "",
        "Responde con el formato `1a, 2b, 3c` para corregirte con precision.",
        "",
    ]
    for question in quiz.get("questions", []):
        lines.append(f"{question['id']}. {question['question']}")
        options = question.get("options") or {}
        for key in ("a", "b", "c", "d"):
            if key in options:
                lines.append(f"{key}) {options[key]}")
        lines.append("")
    return "\n".join(lines).strip()


def parse_student_answers(text: str) -> Dict[int, str]:
    answers: Dict[int, str] = {}
    normalized = (text or "").lower()
    for match in re.finditer(r"(?:pregunta\s*)?(\d+)\s*[:.)-]?\s*([abcd])\b", normalized):
        answers[int(match.group(1))] = match.group(2)
    if answers:
        return answers
    compact = re.findall(r"\b([abcd])\b", normalized)
    return {index: value for index, value in enumerate(compact, start=1)}


def save_structured_quiz(
    *,
    conv_id: int,
    usuario: str,
    tema: str,
    quiz: Dict[str, Any],
    source_message_id: Optional[int] = None,
) -> int:
    with db_session(write=True) as conn:
        cur = conn.cursor()
        cur.execute(
            "UPDATE structured_quizzes SET status = 'closed', updated_at = CURRENT_TIMESTAMP WHERE conv_id = ? AND usuario = ? AND status = 'active';",
            (int(conv_id), usuario),
        )
        cur.execute(
            """
            INSERT INTO structured_quizzes (conv_id, usuario, tema, source_message_id, quiz_json, status)
            VALUES (?, ?, ?, ?, ?, 'active');
            """,
            (int(conv_id), usuario, tema, source_message_id, json.dumps(quiz, ensure_ascii=False)),
        )
        return int(cur.lastrowid)


def get_active_quiz(conv_id: int, usuario: str) -> Optional[Dict[str, Any]]:
    with db_session(write=False) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, tema, quiz_json
            FROM structured_quizzes
            WHERE conv_id = ? AND usuario = ? AND status = 'active'
            ORDER BY id DESC
            LIMIT 1;
            """,
            (int(conv_id), usuario),
        )
        row = cur.fetchone()
    if not row:
        return None
    try:
        quiz = json.loads(row["quiz_json"] or "{}")
    except Exception:
        return None
    return {"id": int(row["id"]), "tema": row["tema"], "quiz": quiz}


def close_structured_quiz(quiz_id: int, score: int, total: int) -> None:
    with db_session(write=True) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE structured_quizzes
            SET status = 'graded',
                last_score = ?,
                total_questions = ?,
                answered_at = CURRENT_TIMESTAMP,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?;
            """,
            (int(score), int(total), int(quiz_id)),
        )


def grade_structured_quiz(active: Dict[str, Any], answer_text: str) -> Dict[str, Any]:
    quiz = active.get("quiz") or {}
    answers = parse_student_answers(answer_text)
    results = []
    score = 0
    questions = quiz.get("questions") or []
    answered_ids = {int(key) for key in answers.keys()}
    for question in questions:
        qid = int(question.get("id") or 0)
        if qid not in answered_ids:
            continue
        chosen = answers.get(qid)
        correct = str(question.get("answer") or "").lower()
        ok = bool(chosen and chosen == correct)
        if ok:
            score += 1
        results.append(
            {
                "id": qid,
                "chosen": chosen,
                "correct": correct,
                "ok": ok,
                "question": question.get("question"),
                "explanation": question.get("explanation"),
            }
        )
    next_question = None
    for question in questions:
        qid = int(question.get("id") or 0)
        if qid not in answered_ids:
            next_question = qid
            break
    answered_count = len(results)
    quiz_total = len(questions)
    complete = bool(quiz_total and answered_count >= quiz_total)
    return {
        "quiz_id": active["id"],
        "topic": quiz.get("topic"),
        "score": score,
        "total": answered_count,
        "quiz_total": quiz_total,
        "answered_count": answered_count,
        "complete": complete,
        "next_question": next_question,
        "results": results,
    }


def format_grade_for_chat(grade: Dict[str, Any]) -> str:
    score = int(grade.get("score") or 0)
    total = int(grade.get("total") or 0)
    quiz_total = int(grade.get("quiz_total") or total)
    complete = bool(grade.get("complete"))
    lines = ["Resultado"]
    if complete:
        lines.append(f"Obtuviste {score}/{quiz_total}.")
    else:
        answered = int(grade.get("answered_count") or total)
        lines.append(f"Respuesta registrada: {score}/{total}. Llevas {answered}/{quiz_total} preguntas respondidas.")
    lines.extend(["", "Correccion breve"])
    for item in grade.get("results", []):
        chosen = (item.get("chosen") or "sin respuesta").upper()
        correct = (item.get("correct") or "").upper()
        status = "Correcta" if item.get("ok") else "Incorrecta"
        lines.append(f"- Pregunta {item['id']}: {status} | Tu respuesta: {chosen} | Correcta: {correct}")
    lines.extend(["", "Por que"])
    for item in grade.get("results", []):
        if not item.get("ok"):
            lines.append(f"- Pregunta {item['id']}: {item.get('explanation')}")
    if complete and score == quiz_total:
        lines.append("- Dominaste este mini quiz. Ya puedes pasar a un reto un poco mas aplicado.")
    if complete:
        lines.extend([
            "",
            "Siguiente paso",
            "Quieres que te ponga una practica guiada del mismo tema o subimos la dificultad?",
        ])
    elif grade.get("next_question"):
        lines.extend([
            "",
            "Siguiente paso",
            f"Responde la pregunta {grade.get('next_question')} cuando estes lista/o.",
        ])
    return "\n".join(lines).strip()
