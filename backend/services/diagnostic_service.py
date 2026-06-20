"""Diagnostic question bank and scoring for YELIA4AP."""

from __future__ import annotations

import random
from typing import Any, Dict, Iterable, List


QUESTION_BANK: List[Dict[str, Any]] = [
    {
        "id": "poo-01",
        "topic": "Clases y Objetos",
        "level": "Sin conocimientos",
        "question": "Que representa una clase en programacion orientada a objetos?",
        "options": ["Un molde para crear objetos", "Un error del programa", "Una base de datos", "Un archivo comprimido"],
        "answer": 0,
    },
    {
        "id": "poo-02",
        "topic": "Clases y Objetos",
        "level": "Basico",
        "question": "Que es un objeto?",
        "options": ["Una instancia de una clase", "Una carpeta del sistema", "Un tipo de comentario", "Una consulta SQL"],
        "answer": 0,
    },
    {
        "id": "poo-03",
        "topic": "Metodos",
        "level": "Basico",
        "question": "Para que sirve un metodo dentro de una clase?",
        "options": ["Para definir comportamientos", "Para borrar la clase", "Para cambiar el sistema operativo", "Para ocultar todos los datos"],
        "answer": 0,
    },
    {
        "id": "poo-04",
        "topic": "Atributos",
        "level": "Basico",
        "question": "Que describe un atributo?",
        "options": ["Una caracteristica o dato del objeto", "La contrasena del usuario", "Un servidor externo", "Una excepcion"],
        "answer": 0,
    },
    {
        "id": "poo-05",
        "topic": "Encapsulamiento",
        "level": "Basico",
        "question": "Que busca el encapsulamiento?",
        "options": ["Proteger datos y controlar su acceso", "Duplicar codigo", "Eliminar constructores", "Evitar usar objetos"],
        "answer": 0,
    },
    {
        "id": "poo-06",
        "topic": "Constructores",
        "level": "Basico",
        "question": "Cuando se ejecuta normalmente un constructor?",
        "options": ["Al crear un objeto", "Al cerrar el programa", "Al escribir un comentario", "Al importar una imagen"],
        "answer": 0,
    },
    {
        "id": "poo-07",
        "topic": "Herencia",
        "level": "Intermedio",
        "question": "Que permite la herencia?",
        "options": ["Reutilizar y especializar miembros de una clase base", "Convertir Java en SQL", "Quitar todos los metodos", "Crear tablas automaticamente"],
        "answer": 0,
    },
    {
        "id": "poo-08",
        "topic": "Polimorfismo",
        "level": "Intermedio",
        "question": "Que idea describe mejor el polimorfismo?",
        "options": ["Un mismo metodo puede comportarse distinto segun el objeto", "Un objeto no puede cambiar", "Todo debe ser privado", "Solo existe una clase"],
        "answer": 0,
    },
    {
        "id": "poo-09",
        "topic": "Abstraccion",
        "level": "Intermedio",
        "question": "Que ventaja tiene la abstraccion?",
        "options": ["Oculta detalles complejos y muestra lo esencial", "Obliga a copiar todo el codigo", "Elimina la necesidad de pruebas", "Convierte objetos en archivos"],
        "answer": 0,
    },
    {
        "id": "poo-10",
        "topic": "Interfaces",
        "level": "Intermedio",
        "question": "Que define principalmente una interfaz?",
        "options": ["Un contrato de metodos que una clase debe cumplir", "Una tabla con datos", "Un valor constante de sistema", "Un tipo de excepcion"],
        "answer": 0,
    },
    {
        "id": "poo-11",
        "topic": "Sobrecarga",
        "level": "Intermedio",
        "question": "Que es la sobrecarga de metodos?",
        "options": ["Tener metodos con el mismo nombre y parametros distintos", "Repetir una clase dos veces", "Eliminar parametros", "Convertir un metodo en atributo"],
        "answer": 0,
    },
    {
        "id": "poo-12",
        "topic": "Sobrescritura",
        "level": "Intermedio",
        "question": "Que es sobrescribir un metodo?",
        "options": ["Redefinir en una subclase un metodo heredado", "Cambiar el nombre del proyecto", "Crear una base de datos", "Borrar el constructor"],
        "answer": 0,
    },
    {
        "id": "poo-13",
        "topic": "Excepciones",
        "level": "Basico",
        "question": "Para que sirve try/catch?",
        "options": ["Para manejar errores en tiempo de ejecucion", "Para crear objetos visuales", "Para ordenar clases alfabeticamente", "Para guardar contrasenas"],
        "answer": 0,
    },
    {
        "id": "poo-14",
        "topic": "Colecciones",
        "level": "Basico",
        "question": "Que estructura permite guardar varios elementos en orden en Java?",
        "options": ["ArrayList", "private", "extends", "throw"],
        "answer": 0,
    },
    {
        "id": "poo-15",
        "topic": "MVC",
        "level": "Intermedio",
        "question": "En MVC, que parte gestiona la logica y datos principales?",
        "options": ["Modelo", "Vista", "Color", "Paquete"],
        "answer": 0,
    },
    {
        "id": "poo-16",
        "topic": "MVC",
        "level": "Intermedio",
        "question": "En MVC, que parte atiende eventos y coordina modelo/vista?",
        "options": ["Controlador", "Constructor", "Variable local", "Excepcion"],
        "answer": 0,
    },
    {
        "id": "poo-17",
        "topic": "UML",
        "level": "Basico",
        "question": "Para que sirve un diagrama de clases UML?",
        "options": ["Para visualizar clases, atributos, metodos y relaciones", "Para ejecutar codigo", "Para instalar dependencias", "Para cifrar archivos"],
        "answer": 0,
    },
    {
        "id": "poo-18",
        "topic": "UML",
        "level": "Intermedio",
        "question": "Que relacion UML indica que una clase hija hereda de una clase padre?",
        "options": ["Generalizacion", "Composicion de texto", "Consulta", "Despliegue"],
        "answer": 0,
    },
    {
        "id": "poo-19",
        "topic": "Patrones",
        "level": "Avanzado",
        "question": "Que patron asegura normalmente una sola instancia compartida?",
        "options": ["Singleton", "Factory inexistente", "Loop", "Array"],
        "answer": 0,
    },
    {
        "id": "poo-20",
        "topic": "Patrones",
        "level": "Avanzado",
        "question": "Que problema resuelve Factory Method?",
        "options": ["Crear objetos sin acoplarse a clases concretas", "Sumar dos numeros", "Cambiar el fondo del IDE", "Leer solo archivos PDF"],
        "answer": 0,
    },
    {
        "id": "poo-21",
        "topic": "SOLID",
        "level": "Avanzado",
        "question": "Que propone el principio de responsabilidad unica?",
        "options": ["Una clase debe tener una razon principal para cambiar", "Una clase debe hacerlo todo", "No usar metodos", "Evitar paquetes"],
        "answer": 0,
    },
    {
        "id": "poo-22",
        "topic": "SOLID",
        "level": "Avanzado",
        "question": "Que busca la inversion de dependencias?",
        "options": ["Depender de abstracciones y no de implementaciones concretas", "Depender siempre de clases finales", "Evitar interfaces", "Eliminar pruebas"],
        "answer": 0,
    },
    {
        "id": "poo-23",
        "topic": "Bases de Datos y ORM",
        "level": "Intermedio",
        "question": "Que hace un ORM?",
        "options": ["Mapea objetos del programa con tablas de base de datos", "Compila imagenes", "Cambia el idioma del navegador", "Dibuja UML automaticamente siempre"],
        "answer": 0,
    },
    {
        "id": "poo-24",
        "topic": "JDBC",
        "level": "Intermedio",
        "question": "Para que se usa JDBC en Java?",
        "options": ["Para conectar una aplicacion Java con bases de datos", "Para disenar iconos", "Para crear clases abstractas", "Para ordenar paquetes"],
        "answer": 0,
    },
    {
        "id": "poo-25",
        "topic": "Capas",
        "level": "Intermedio",
        "question": "Que ventaja tiene separar la app en capas?",
        "options": ["Mejora mantenimiento, orden y pruebas", "Hace imposible depurar", "Elimina la necesidad de clases", "Obliga a usar una sola funcion"],
        "answer": 0,
    },
    {
        "id": "poo-26",
        "topic": "Pruebas",
        "level": "Avanzado",
        "question": "Que verifica una prueba unitaria?",
        "options": ["Una unidad pequena de codigo de forma aislada", "Todo el servidor fisico", "El color del editor", "La conexion del monitor"],
        "answer": 0,
    },
    {
        "id": "poo-27",
        "topic": "Genericos",
        "level": "Avanzado",
        "question": "Que ventaja aportan los genericos?",
        "options": ["Mayor seguridad de tipos y reutilizacion", "Menos compilacion", "Eliminar clases", "Evitar colecciones"],
        "answer": 0,
    },
    {
        "id": "poo-28",
        "topic": "Streams",
        "level": "Avanzado",
        "question": "Que permite la API Stream de Java?",
        "options": ["Procesar colecciones con operaciones como filter/map/reduce", "Crear ventanas graficas obligatorias", "Reiniciar el equipo", "Evitar objetos"],
        "answer": 0,
    },
    {
        "id": "poo-29",
        "topic": "Composicion",
        "level": "Intermedio",
        "question": "Que expresa la composicion?",
        "options": ["Un objeto esta formado por otros objetos", "Una clase no tiene atributos", "Un metodo no retorna", "Un paquete externo"],
        "answer": 0,
    },
    {
        "id": "poo-30",
        "topic": "Buenas practicas",
        "level": "Avanzado",
        "question": "Por que conviene bajo acoplamiento?",
        "options": ["Facilita cambios, pruebas y mantenimiento", "Hace que todo dependa de todo", "Impide reutilizar codigo", "Obliga a no usar interfaces"],
        "answer": 0,
    },
]

try:
    from backend.services.course_content_service import diagnostic_question_bank

    _official_questions = diagnostic_question_bank()
    if _official_questions:
        QUESTION_BANK = _official_questions
except Exception:
    pass


def random_questions(count: int = 5) -> List[Dict[str, Any]]:
    safe_count = max(1, min(int(count or 5), len(QUESTION_BANK)))
    selected = random.sample(QUESTION_BANK, safe_count)
    return [public_question(item) for item in selected]


def public_question(item: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": item["id"],
        "topic": item["topic"],
        "level": item["level"],
        "question": item["question"],
        "options": list(item["options"]),
    }


def score_answers(answers: Dict[str, int] | Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    if not isinstance(answers, dict):
        answers = {str(item.get("id")): item.get("answer") for item in answers if isinstance(item, dict)}

    by_id = {item["id"]: item for item in QUESTION_BANK}
    details = []
    score = 0
    topics_missed: Dict[str, int] = {}
    topics_ok: Dict[str, int] = {}

    for question_id, selected in answers.items():
        item = by_id.get(str(question_id))
        if not item:
            continue
        try:
            selected_index = int(selected)
        except Exception:
            selected_index = -1
        correct = selected_index == int(item["answer"])
        if correct:
            score += 1
            topics_ok[item["topic"]] = topics_ok.get(item["topic"], 0) + 1
        else:
            topics_missed[item["topic"]] = topics_missed.get(item["topic"], 0) + 1
        details.append({
            "id": item["id"],
            "topic": item["topic"],
            "correct": correct,
            "selected": selected_index,
            "answer": int(item["answer"]),
        })

    total = len(details)
    level = detected_level(score, total)
    return {
        "score": score,
        "total": total,
        "level": level,
        "level_label": level,
        "details": details,
        "topics_ok": topics_ok,
        "topics_missed": topics_missed,
        "feedback": feedback_for_level(level, score, total, topics_missed),
        "recommendations": recommendations_for_level(level, topics_missed),
    }


def detected_level(score: int, total: int) -> str:
    if total <= 0:
        return "Sin conocimientos"
    ratio = score / total
    if ratio <= 0.20:
        return "Sin conocimientos"
    if ratio <= 0.45:
        return "Basico"
    if ratio <= 0.75:
        return "Intermedio"
    return "Avanzado"


def feedback_for_level(level: str, score: int, total: int, topics_missed: Dict[str, int]) -> str:
    weak = ", ".join(sorted(topics_missed.keys())[:3])
    base = f"Se detecto un nivel {level} en Programacion Avanzada ({score}/{total})."
    if weak:
        return f"{base} Conviene reforzar: {weak}."
    return f"{base} Puedes avanzar con practica guiada y retos progresivos."


def recommendations_for_level(level: str, topics_missed: Dict[str, int]) -> List[Dict[str, str]]:
    weak_topics = sorted(topics_missed.keys())[:3] or ["Clases y Objetos", "Programacion Avanzada"]
    if level == "Sin conocimientos":
        action = "Empezar desde cero con conceptos, ejemplos cortos y ejercicios basicos."
    elif level == "Basico":
        action = "Practicar con ejemplos guiados y preguntas de repaso por unidad."
    elif level == "Intermedio":
        action = "Resolver casos aplicados, UML y pequenas implementaciones."
    else:
        action = "Trabajar retos tecnicos, patrones y explicaciones mas precisas."
    return [{"topic": topic, "action": action} for topic in weak_topics]
