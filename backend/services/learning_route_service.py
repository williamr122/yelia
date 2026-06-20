"""Learning route persistence and unit quizzes for YELIA4AP."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict, List

from backend.db.session import db_session
from backend.services.course_content_service import course_units, final_question_bank, unit_question_bank
from backend.services.progreso_service import actualizar_progreso


UNITS: List[Dict[str, Any]] = [
    {
        "id": 1,
        "title": "Fundamentos de POO",
        "subtitle": "Introduccion, clases, objetos, atributos, metodos y encapsulamiento.",
        "topics": ["Introduccion a POO", "Clases y Objetos", "Atributos y metodos", "Encapsulamiento"],
    },
    {
        "id": 2,
        "title": "Herencia, polimorfismo e interfaces",
        "subtitle": "Clases base y derivadas, sobrecarga, sobrescritura, clases abstractas e interfaces.",
        "topics": ["Herencia", "Polimorfismo", "Sobrecarga y sobrescritura", "Interfaces"],
    },
    {
        "id": 3,
        "title": "UML y patron MVC",
        "subtitle": "Diagramas UML, casos de uso, secuencia, actividad y patron MVC.",
        "topics": ["Diagramas UML", "Casos de uso", "Secuencia y actividad", "MVC"],
    },
    {
        "id": 4,
        "title": "Archivos, base de datos y buenas practicas",
        "subtitle": "Archivos, base de datos, ORM, integracion POO/MVC/datos, pruebas y buenas practicas.",
        "topics": ["Acceso a archivos", "Bases de Datos y ORM", "Integracion POO/MVC/Datos", "Pruebas"],
    },
]


QUIZ_BANK: Dict[int, List[Dict[str, Any]]] = {
    1: [
        {"id": "u1-01", "topic": "Clases y Objetos", "question": "Que representa una clase en POO?", "options": ["Un molde para crear objetos", "Un error del sistema", "Una tabla SQL", "Un archivo"], "answer": 0},
        {"id": "u1-02", "topic": "Clases y Objetos", "question": "Que es un objeto?", "options": ["Una instancia de una clase", "Un comentario", "Un diagrama", "Una carpeta"], "answer": 0},
        {"id": "u1-03", "topic": "Atributos y metodos", "question": "Que describe un atributo?", "options": ["Un dato o caracteristica del objeto", "Un permiso del navegador", "Una excepcion", "Un paquete"], "answer": 0},
        {"id": "u1-04", "topic": "Atributos y metodos", "question": "Para que sirve un metodo?", "options": ["Para definir comportamientos", "Para borrar objetos siempre", "Para instalar Java", "Para crear tablas"], "answer": 0},
        {"id": "u1-05", "topic": "Encapsulamiento", "question": "Que busca el encapsulamiento?", "options": ["Proteger datos y controlar acceso", "Duplicar codigo", "Evitar clases", "Quitar constructores"], "answer": 0},
    ],
    2: [
        {"id": "u2-01", "topic": "Herencia", "question": "Que permite la herencia?", "options": ["Reutilizar y especializar una clase base", "Eliminar atributos", "Cambiar SQL por Java", "Crear iconos"], "answer": 0},
        {"id": "u2-02", "topic": "Polimorfismo", "question": "Que describe mejor el polimorfismo?", "options": ["Un mismo metodo puede comportarse distinto", "Una clase sin objetos", "Un atributo privado", "Un paquete externo"], "answer": 0},
        {"id": "u2-03", "topic": "Sobrecarga y sobrescritura", "question": "Que es sobrecarga de metodos?", "options": ["Mismo nombre con parametros distintos", "Borrar un metodo heredado", "Crear una base", "Cambiar el IDE"], "answer": 0},
        {"id": "u2-04", "topic": "Sobrecarga y sobrescritura", "question": "Que es sobrescritura?", "options": ["Redefinir en una subclase un metodo heredado", "Duplicar un archivo", "Ordenar paquetes", "Evitar interfaces"], "answer": 0},
        {"id": "u2-05", "topic": "Interfaces", "question": "Que define principalmente una interfaz?", "options": ["Un contrato de metodos", "Una tabla con datos", "Un color de vista", "Un comentario"], "answer": 0},
    ],
    3: [
        {"id": "u3-01", "topic": "Diagramas UML", "question": "Para que sirve un diagrama de clases?", "options": ["Visualizar clases, atributos, metodos y relaciones", "Ejecutar codigo", "Crear contrasenas", "Instalar librerias"], "answer": 0},
        {"id": "u3-02", "topic": "Casos de uso", "question": "Que muestra un caso de uso?", "options": ["Interacciones entre actor y sistema", "Solo codigo Java", "Tablas de base", "Errores del compilador"], "answer": 0},
        {"id": "u3-03", "topic": "Secuencia y actividad", "question": "Que enfatiza un diagrama de secuencia?", "options": ["El orden de mensajes entre objetos", "El color de una clase", "La instalacion del IDE", "Un registro SQL"], "answer": 0},
        {"id": "u3-04", "topic": "MVC", "question": "En MVC, que parte gestiona datos y reglas principales?", "options": ["Modelo", "Vista", "Color", "Paquete"], "answer": 0},
        {"id": "u3-05", "topic": "MVC", "question": "En MVC, que parte coordina modelo y vista?", "options": ["Controlador", "Constructor", "Atributo", "Archivo"], "answer": 0},
    ],
    4: [
        {"id": "u4-01", "topic": "Acceso a archivos", "question": "Para que sirve manejar archivos desde POO?", "options": ["Leer y guardar informacion persistente", "Cambiar el monitor", "Eliminar clases", "Evitar objetos"], "answer": 0},
        {"id": "u4-02", "topic": "Bases de Datos y ORM", "question": "Que hace un ORM?", "options": ["Mapea objetos con tablas de base de datos", "Dibuja iconos", "Cambia idioma", "Borra pruebas"], "answer": 0},
        {"id": "u4-03", "topic": "Integracion POO/MVC/Datos", "question": "Que ventaja tiene separar en capas?", "options": ["Mejora mantenimiento, orden y pruebas", "Hace imposible depurar", "Elimina clases", "Evita metodos"], "answer": 0},
        {"id": "u4-04", "topic": "Pruebas", "question": "Que verifica una prueba unitaria?", "options": ["Una unidad pequena de codigo", "Todo el servidor fisico", "El color del editor", "La red electrica"], "answer": 0},
        {"id": "u4-05", "topic": "Pruebas", "question": "Por que conviene bajo acoplamiento?", "options": ["Facilita cambios, pruebas y mantenimiento", "Hace todo dependiente", "Impide reutilizar", "Evita interfaces"], "answer": 0},
    ],
}


FINAL_QUIZ_BANK: List[Dict[str, Any]] = [
    {"id": "final-01", "topic": "Clases y Objetos", "question": "Que relacion hay entre una clase y un objeto?", "options": ["La clase es el molde y el objeto es una instancia", "Son lo mismo", "El objeto crea la clase", "La clase solo existe en SQL"], "answer": 0},
    {"id": "final-02", "topic": "Encapsulamiento", "question": "Por que se usa encapsulamiento?", "options": ["Para proteger datos y controlar acceso", "Para eliminar metodos", "Para evitar constructores", "Para no usar objetos"], "answer": 0},
    {"id": "final-03", "topic": "Herencia", "question": "Que ventaja aporta la herencia?", "options": ["Reutilizar y especializar codigo", "Duplicar todo el proyecto", "Quitar atributos", "Evitar subclases"], "answer": 0},
    {"id": "final-04", "topic": "Polimorfismo", "question": "Que permite el polimorfismo?", "options": ["Que un comportamiento tenga distintas implementaciones", "Que no existan metodos", "Que una tabla sea una clase", "Que un archivo compile solo"], "answer": 0},
    {"id": "final-05", "topic": "UML", "question": "Para que ayuda UML en un proyecto?", "options": ["Para visualizar estructura e interacciones antes de programar", "Para reemplazar toda la base de datos", "Para instalar Java", "Para borrar dependencias"], "answer": 0},
    {"id": "final-06", "topic": "MVC", "question": "Que busca el patron MVC?", "options": ["Separar datos, interfaz y control", "Mezclar todo en una clase", "Evitar modelos", "Crear solo vistas"], "answer": 0},
    {"id": "final-07", "topic": "Bases de Datos y ORM", "question": "Que hace un ORM?", "options": ["Relaciona objetos del codigo con tablas", "Dibuja diagramas UML", "Lee voces", "Hace preguntas del quiz"], "answer": 0},
    {"id": "final-08", "topic": "Pruebas", "question": "Por que son utiles las pruebas?", "options": ["Ayudan a verificar comportamiento y evitar regresiones", "Reemplazan el aprendizaje", "Bloquean el sistema", "Ocultan errores"], "answer": 0},
]

try:
    _official_units = course_units()
    _official_unit_exams = unit_question_bank("unit_exam")
    _official_final_exam = final_question_bank(total=10)
    if _official_units:
        UNITS = _official_units
    if _official_unit_exams:
        QUIZ_BANK = _official_unit_exams
    if _official_final_exam:
        FINAL_QUIZ_BANK = _official_final_exam
except Exception:
    pass


def _now() -> str:
    return datetime.utcnow().isoformat(timespec="seconds") + "Z"


def _ensure_table() -> None:
    with db_session(write=True) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS learning_routes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario TEXT NOT NULL UNIQUE,
                route_json TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
        )


def _default_route() -> Dict[str, Any]:
    return {
        "currentUnit": 1,
        "units": {
            "1": {"status": "active", "progress": 25, "quiz": None, "practice_started": False},
            "2": {"status": "locked", "progress": 0, "quiz": None, "practice_started": False},
            "3": {"status": "locked", "progress": 0, "quiz": None, "practice_started": False},
            "4": {"status": "locked", "progress": 0, "quiz": None, "practice_started": False},
        },
        "final_evaluation": None,
        "route_completed": False,
        "updated_at": _now(),
    }


def _normalize_route(data: Dict[str, Any] | None) -> Dict[str, Any]:
    route = _default_route()
    if isinstance(data, dict):
        route.update({k: v for k, v in data.items() if k != "units"})
        incoming_units = data.get("units") if isinstance(data.get("units"), dict) else {}
        for key, value in incoming_units.items():
            if str(key) in route["units"] and isinstance(value, dict):
                route["units"][str(key)].update(value)
    return route


def _save_route(usuario: str, route: Dict[str, Any]) -> Dict[str, Any]:
    _ensure_table()
    route["updated_at"] = _now()
    raw = json.dumps(route, ensure_ascii=False)
    with db_session(write=True) as conn:
        cur = conn.cursor()
        cur.execute("SELECT id FROM learning_routes WHERE usuario = ?;", (usuario,))
        row = cur.fetchone()
        if row:
            cur.execute(
                "UPDATE learning_routes SET route_json = ?, updated_at = CURRENT_TIMESTAMP WHERE usuario = ?;",
                (raw, usuario),
            )
        else:
            cur.execute(
                "INSERT INTO learning_routes (usuario, route_json) VALUES (?, ?);",
                (usuario, raw),
            )
    return route


def get_route(usuario: str) -> Dict[str, Any]:
    _ensure_table()
    with db_session(write=False) as conn:
        cur = conn.cursor()
        cur.execute("SELECT route_json FROM learning_routes WHERE usuario = ?;", (usuario,))
        row = cur.fetchone()
    if not row:
        return _save_route(usuario, _default_route())
    try:
        return _normalize_route(json.loads(row["route_json"] or "{}"))
    except Exception:
        return _save_route(usuario, _default_route())


def mark_practice(usuario: str, unit_id: int) -> Dict[str, Any]:
    route = get_route(usuario)
    key = str(max(1, min(4, int(unit_id or 1))))
    unit = route["units"][key]
    if unit.get("status") == "locked":
        unit["status"] = "active"
    unit["practice_started"] = True
    unit["progress"] = max(int(unit.get("progress") or 0), 50)
    route["currentUnit"] = int(key)
    return _save_route(usuario, route)


def public_quiz(unit_id: int) -> Dict[str, Any]:
    unit_id = max(1, min(4, int(unit_id or 1)))
    questions = [
        {k: v for k, v in item.items() if k != "answer"}
        for item in QUIZ_BANK[unit_id]
    ]
    return {"unit": UNITS[unit_id - 1], "questions": questions, "passing_score": 70}


def public_final_quiz() -> Dict[str, Any]:
    questions = [
        {k: v for k, v in item.items() if k != "answer"}
        for item in FINAL_QUIZ_BANK
    ]
    return {"title": "Evaluacion final de Programacion Avanzada", "questions": questions, "passing_score": 70}


def grade_quiz(usuario: str, unit_id: int, answers: Dict[str, Any]) -> Dict[str, Any]:
    unit_id = max(1, min(4, int(unit_id or 1)))
    route = get_route(usuario)
    by_id = {item["id"]: item for item in QUIZ_BANK[unit_id]}
    details = []
    score = 0
    missed_topics: Dict[str, int] = {}
    ok_topics: Dict[str, int] = {}

    for qid, item in by_id.items():
        try:
            selected = int(answers.get(qid, -1))
        except Exception:
            selected = -1
        correct = selected == int(item["answer"])
        if correct:
            score += 1
            ok_topics[item["topic"]] = ok_topics.get(item["topic"], 0) + 1
        else:
            missed_topics[item["topic"]] = missed_topics.get(item["topic"], 0) + 1
        details.append({"id": qid, "topic": item["topic"], "correct": correct, "selected": selected, "answer": int(item["answer"])})

    total = len(by_id)
    percent = round((score / total) * 100) if total else 0
    passed = percent >= 70
    key = str(unit_id)
    unit_state = route["units"][key]
    unit_state["quiz"] = {
        "score": score,
        "total": total,
        "percent": percent,
        "passed": passed,
        "topics_ok": ok_topics,
        "topics_missed": missed_topics,
        "details": details,
        "created_at": _now(),
    }
    unit_state["progress"] = 100 if passed else max(int(unit_state.get("progress") or 0), percent)
    unit_state["status"] = "done" if passed else "active"
    route["currentUnit"] = unit_id

    if passed and unit_id < 4:
        next_state = route["units"][str(unit_id + 1)]
        if next_state.get("status") == "locked":
            next_state["status"] = "active"
            next_state["progress"] = max(int(next_state.get("progress") or 0), 25)
        route["currentUnit"] = unit_id + 1

    if passed:
        for topic in UNITS[unit_id - 1]["topics"]:
            actualizar_progreso(usuario, tema_nuevo=topic, puntos_delta=2)
    else:
        for topic in missed_topics:
            actualizar_progreso(usuario, tema_nuevo=topic, puntos_delta=0)

    saved = _save_route(usuario, route)
    feedback = _feedback(unit_id, percent, passed, missed_topics)
    return {"result": unit_state["quiz"], "route": saved, "feedback": feedback, "next_unit": saved.get("currentUnit")}


def final_unlocked(route: Dict[str, Any]) -> bool:
    units = route.get("units", {})
    return all((units.get(str(unit["id"]), {}) or {}).get("status") == "done" for unit in UNITS)


def grade_final_quiz(usuario: str, answers: Dict[str, Any]) -> Dict[str, Any]:
    route = get_route(usuario)
    if not final_unlocked(route):
        raise ValueError("La evaluacion final aun esta bloqueada.")

    by_id = {item["id"]: item for item in FINAL_QUIZ_BANK}
    details = []
    score = 0
    missed_topics: Dict[str, int] = {}

    for qid, item in by_id.items():
        try:
            selected = int(answers.get(qid, -1))
        except Exception:
            selected = -1
        correct = selected == int(item["answer"])
        if correct:
            score += 1
        else:
            missed_topics[item["topic"]] = missed_topics.get(item["topic"], 0) + 1
        details.append({"id": qid, "topic": item["topic"], "correct": correct, "selected": selected, "answer": int(item["answer"])})

    total = len(by_id)
    percent = round((score / total) * 100) if total else 0
    passed = percent >= 70
    route["final_evaluation"] = {
        "score": score,
        "total": total,
        "percent": percent,
        "passed": passed,
        "topics_missed": missed_topics,
        "details": details,
        "created_at": _now(),
    }
    route["route_completed"] = passed

    if passed:
        actualizar_progreso(usuario, tema_nuevo="Evaluacion final de Programacion Avanzada", puntos_delta=5)
    else:
        for topic in missed_topics:
            actualizar_progreso(usuario, tema_nuevo=topic, puntos_delta=0)

    saved = _save_route(usuario, route)
    if passed:
        feedback = f"Aprobaste la evaluacion final con {percent}%. Ya tienes cierre de ruta y puedes revisar tu mapa de calor."
    else:
        weak = ", ".join(missed_topics.keys()) or "las unidades anteriores"
        feedback = f"Obtuviste {percent}%. Refuerza {weak} y vuelve a intentar la evaluacion final."
    return {"result": route["final_evaluation"], "route": saved, "feedback": feedback}


def _feedback(unit_id: int, percent: int, passed: bool, missed_topics: Dict[str, int]) -> str:
    unit = UNITS[unit_id - 1]
    if passed:
        if unit_id < 4:
            return f"Aprobaste la Unidad {unit_id} con {percent}%. Puedes avanzar a la siguiente unidad."
        return f"Aprobaste la Unidad 4 con {percent}%. Ya puedes preparar la evaluacion final."
    weak = ", ".join(missed_topics.keys()) or unit["title"]
    return f"Obtuviste {percent}%. Refuerza {weak} antes de avanzar."
