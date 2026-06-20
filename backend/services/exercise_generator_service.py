"""
Proyecto: YELIA4AP
Archivo: backend/services/exercise_generator_service.py
Descripción: Generador de ejercicios alineados al sílabo de Programación Avanzada.

Revisión: 2026-03-29
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List, Optional


def _normalize_level(level: Optional[str]) -> str:
    lvl = (level or "intermedio").strip().lower()
    if lvl in {"basica", "básica", "basico", "básico", "sin conocimientos", "sin_conocimientos"}:
        return "basico"
    if lvl in {"avanzada", "avanzado"}:
        return "avanzado"
    if lvl not in {"basico", "intermedio", "avanzado"}:
        return "intermedio"
    return lvl


def _normalize_topic(topic: Optional[str]) -> str:
    t = (topic or "").strip().lower()
    if not t:
        return "general"
    mapping = {
        "poo": ["poo", "clase", "objeto", "encapsulamiento", "getter", "setter"],
        "uml": ["uml", "diagrama", "casos de uso", "clases", "secuencia", "actividad"],
        "mvc": ["mvc", "modelo", "vista", "controlador"],
        "archivos_bd": ["archivo", "archivos", "base de datos", "bd", "orm", "jdbc", "sqlite", "pruebas"],
        "herencia_polimorfismo": ["herencia", "polimorfismo", "interfaz", "abstracta", "sobrecarga", "sobreescritura"],
    }
    for normalized, keys in mapping.items():
        if any(k in t for k in keys):
            return normalized
    return "general"


_BANK: Dict[str, Dict[str, List[Dict[str, Any]]]] = {
    "poo": {
        "basico": [
            {
                "title": "Clase y objeto básicos",
                "prompt": "Crea una clase `Estudiante` con atributos privados `nombre` y `edad`, más sus getters y setters. Luego instancia un objeto y muestra sus datos.",
                "rubric": ["Usa encapsulamiento.", "La clase compila.", "Se crea un objeto y se imprime información."],
                "tips": ["Primero define atributos, luego constructor opcional y finalmente getters/setters."],
            },
            {
                "title": "Explicación guiada de encapsulamiento",
                "prompt": "Explica con tus palabras por qué se usan atributos privados y luego modifica un ejemplo para que use `setEdad()` y `getEdad()`.",
                "rubric": ["Define encapsulamiento correctamente.", "Relaciona teoría con código."],
            },
        ],
        "intermedio": [
            {
                "title": "Modelado de clases",
                "prompt": "Diseña las clases `Curso`, `Docente` y `Estudiante`. Indica atributos, métodos y relación entre ellas. Después implementa una de esas clases en Java.",
                "rubric": ["Identifica correctamente atributos y métodos.", "La implementación coincide con el diseño."],
                "tips": ["Piensa primero en sustantivos y luego en acciones del dominio."],
            },
            {
                "title": "Refactor POO",
                "prompt": "Toma un programa procedural corto y reorganízalo en una clase con responsabilidades claras. Justifica por qué mejora el mantenimiento.",
                "rubric": ["Separa responsabilidades.", "Explica la mejora en mantenibilidad."],
            },
        ],
        "avanzado": [
            {
                "title": "Mini taller POO",
                "prompt": "Resuelve un mini taller: modela un sistema de matrícula con al menos 3 clases, constructor, encapsulamiento y un método que valide cupos. Después propone 3 casos de prueba.",
                "rubric": ["POO correcta.", "Hay validaciones.", "Incluye casos de prueba."],
            },
            {
                "title": "Rúbrica de revisión POO",
                "prompt": "Evalúa un diseño orientado a objetos usando esta rúbrica: encapsulamiento, cohesión, nombres, reutilización y claridad. Asigna una puntuación de 1 a 5 por criterio.",
                "rubric": ["Usa criterios claros.", "Justifica cada puntuación."],
            },
        ],
    },
    "herencia_polimorfismo": {
        "basico": [
            {
                "title": "Herencia simple",
                "prompt": "Crea una clase `Persona` y una clase `Estudiante` que herede de ella. Agrega un atributo propio a `Estudiante` y demuestra el uso de la herencia.",
                "rubric": ["Usa `extends` correctamente.", "Distingue atributos heredados y propios."],
            },
            {
                "title": "Sobrecarga vs sobreescritura",
                "prompt": "Escribe un ejemplo corto que muestre sobrecarga y otro que muestre sobreescritura. Después explica la diferencia.",
                "rubric": ["Diferencia ambos conceptos correctamente."],
            },
        ],
        "intermedio": [
            {
                "title": "Interfaces y clases abstractas",
                "prompt": "Modela un sistema con una interfaz `Animal` y una clase abstracta `Figura`. Explica cuándo conviene usar cada una.",
                "rubric": ["Implementa correctamente interfaz y clase abstracta.", "Explica su uso."],
            },
            {
                "title": "Mini quiz de polimorfismo",
                "prompt": "Genera 5 preguntas tipo quiz sobre herencia, polimorfismo, interfaces y clases abstractas, cada una con 4 opciones.",
                "rubric": ["Preguntas claras.", "Opciones plausibles."],
            },
        ],
        "avanzado": [
            {
                "title": "Jerarquía robusta",
                "prompt": "Diseña una jerarquía de clases para un sistema académico. Incluye al menos una interfaz, una clase abstracta y un caso real de polimorfismo. Justifica cada decisión.",
                "rubric": ["Diseño coherente.", "Polimorfismo bien aplicado.", "Justificación sólida."],
            },
            {
                "title": "Depuración de herencia",
                "prompt": "Analiza un caso donde una subclase sobrescribe un método incorrectamente. Explica el error, corrígelo y define 3 pruebas manuales.",
                "rubric": ["Detecta el error.", "Corrige la jerarquía.", "Incluye pruebas."],
            },
        ],
    },
    "uml": {
        "basico": [
            {
                "title": "Casos de uso básicos",
                "prompt": "Propón un diagrama de casos de uso para un sistema de biblioteca con actores y funcionalidades principales.",
                "rubric": ["Identifica actores.", "Delimita funcionalidades."],
            },
            {
                "title": "Diagrama de clases simple",
                "prompt": "Construye un diagrama de clases para un sistema de notas con `Estudiante`, `Materia` y `Calificación`.",
                "rubric": ["Incluye clases, atributos y relaciones."],
            },
        ],
        "intermedio": [
            {
                "title": "Secuencia + actividad",
                "prompt": "Diseña un diagrama de secuencia para el login y un diagrama de actividades para el proceso de matrícula.",
                "rubric": ["Respeta el propósito de cada diagrama.", "El flujo es entendible."],
            },
            {
                "title": "Relaciones UML",
                "prompt": "Explica con ejemplos asociación, agregación y composición. Luego aplícalas a un dominio académico.",
                "rubric": ["Distingue correctamente las relaciones.", "Ejemplos coherentes."],
            },
        ],
        "avanzado": [
            {
                "title": "Proyecto UML completo",
                "prompt": "Plantea un mini proyecto con: casos de uso, diagrama de clases, secuencia de un caso crítico y diagrama de actividades. Añade una rúbrica breve de evaluación.",
                "rubric": ["Incluye los 4 entregables.", "Mantiene coherencia entre diagramas."],
            },
            {
                "title": "Corrección de modelado",
                "prompt": "Revisa un diagrama UML y detecta al menos 5 errores comunes: atributos ambiguos, relaciones incorrectas, multiplicidades ausentes o nombres poco claros.",
                "rubric": ["Identifica errores reales.", "Propone correcciones."],
            },
        ],
    },
    "mvc": {
        "basico": [
            {
                "title": "Identificar capas MVC",
                "prompt": "Dado un ejemplo de sistema de login, identifica qué corresponde al Modelo, la Vista y el Controlador.",
                "rubric": ["Ubica bien cada responsabilidad."],
            },
            {
                "title": "Mapa conceptual MVC",
                "prompt": "Explica el patrón MVC en un mapa conceptual breve con funciones de cada capa.",
                "rubric": ["Explica flujo y responsabilidad."],
            },
        ],
        "intermedio": [
            {
                "title": "Aplicar MVC",
                "prompt": "Diseña una estructura MVC para una app de gestión de tareas. Menciona clases o archivos principales por capa.",
                "rubric": ["Separa capas correctamente.", "No mezcla lógica de presentación con datos."],
            },
            {
                "title": "Comparación diseño vs implementación",
                "prompt": "Relaciona un diagrama de clases con una implementación MVC. Explica qué parte del diagrama termina en Modelo, Vista y Controlador.",
                "rubric": ["Relaciona diseño y código."],
            },
        ],
        "avanzado": [
            {
                "title": "Mini proyecto MVC",
                "prompt": "Propón un mini proyecto académico con patrón MVC, base de datos y pruebas básicas. Divide el trabajo en tareas de taller, exposición y evaluación.",
                "rubric": ["Arquitectura coherente.", "Plan de trabajo claro."],
            },
            {
                "title": "Revisión crítica de MVC",
                "prompt": "Analiza errores típicos al implementar MVC: controladores gigantes, vistas con lógica, acceso directo a BD desde la UI. Propón mejoras.",
                "rubric": ["Detecta fallos de arquitectura.", "Propone mejoras viables."],
            },
        ],
    },
    "archivos_bd": {
        "basico": [
            {
                "title": "Lectura de archivos",
                "prompt": "Escribe un programa que lea un archivo de texto línea por línea y muestre el contenido. Después explica dónde se aplicaría en un sistema real.",
                "rubric": ["Lee el archivo correctamente.", "Explica su utilidad."],
            },
            {
                "title": "Conexión simple a BD",
                "prompt": "Explica la diferencia entre guardar datos en un archivo y en una base de datos. Luego muestra un ejemplo corto de consulta JDBC.",
                "rubric": ["Distingue archivo vs BD.", "Incluye ejemplo técnico."],
            },
        ],
        "intermedio": [
            {
                "title": "ORM y buenas prácticas",
                "prompt": "Define qué es un ORM, compáralo con SQL directo y plantea 4 buenas prácticas para acceso a datos.",
                "rubric": ["Explica ORM claramente.", "Incluye buenas prácticas reales."],
            },
            {
                "title": "Taller de integración",
                "prompt": "Diseña un ejercicio donde una aplicación use POO + MVC + acceso a datos. Indica qué parte sería Modelo, cómo se persiste y cómo se prueba.",
                "rubric": ["Integra correctamente conceptos de la unidad 4."],
            },
        ],
        "avanzado": [
            {
                "title": "Mini proyecto BD/ORM",
                "prompt": "Propón un mini proyecto con entidad, repositorio/DAO, servicio y pruebas. Incluye una rúbrica corta para evaluar calidad de código, persistencia y pruebas.",
                "rubric": ["Arquitectura por capas.", "Persistencia clara.", "Incluye pruebas y rúbrica."],
            },
            {
                "title": "Casos de prueba para acceso a datos",
                "prompt": "Define pruebas para lectura/escritura de archivos, validación de datos y operaciones de BD. Incluye casos felices y errores.",
                "rubric": ["Cubre errores y casos borde."],
            },
        ],
    },
    "general": {
        "basico": [
            {
                "title": "Glosario guiado",
                "prompt": "Elabora un glosario corto con 5 conceptos de Programación Avanzada y escribe una definición sencilla para cada uno.",
                "rubric": ["Definiciones claras y correctas."],
            },
            {
                "title": "Mini quiz general",
                "prompt": "Crea 5 preguntas de opción múltiple sobre POO, UML, MVC y base de datos.",
                "rubric": ["Las preguntas cubren varias unidades."],
            },
        ],
        "intermedio": [
            {
                "title": "Taller integrador",
                "prompt": "Diseña un taller corto que combine POO, UML y MVC. Divide el trabajo en pasos y agrega criterios de evaluación.",
                "rubric": ["Integra los conceptos principales.", "Incluye criterios de evaluación."],
            },
            {
                "title": "Rúbrica de exposición",
                "prompt": "Construye una rúbrica breve para evaluar una exposición sobre un tema de Programación Avanzada: dominio conceptual, claridad, ejemplo y defensa técnica.",
                "rubric": ["Rúbrica clara y usable."],
            },
        ],
        "avanzado": [
            {
                "title": "Mini proyecto por unidades",
                "prompt": "Plantea un mini proyecto final que evidencie las 4 unidades oficiales del sílabo. Incluye entregables, cronograma corto y rúbrica.",
                "rubric": ["Cubre las 4 unidades.", "Entregables viables.", "Rúbrica coherente."],
            },
            {
                "title": "Plan de evaluación",
                "prompt": "Elabora una propuesta de evaluación con glosario, quiz, taller, exposición y proyecto, alineada a Programación Avanzada.",
                "rubric": ["Alinea actividades y aprendizaje."],
            },
        ],
    },
}


def generate_personalized_exercises(*, level: str, focus_topic: Optional[str], mistakes: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    lvl = _normalize_level(level)
    topic = _normalize_topic(focus_topic)
    bank = deepcopy(_BANK.get(topic) or _BANK["general"])
    exercises = (bank.get(lvl) or [])[:2]
    mistakes = [m.strip() for m in (mistakes or []) if isinstance(m, str) and m.strip()]
    if mistakes:
        tip = f"Cuidado con este error frecuente: {mistakes[0]}."
        for item in exercises:
            tips = item.get("tips") or []
            if not isinstance(tips, list):
                tips = [str(tips)]
            tips.append(tip)
            item["tips"] = tips
    return exercises


def generate_glossary(topic: Optional[str] = None) -> List[Dict[str, str]]:
    norm = _normalize_topic(topic)
    glossaries = {
        "poo": [
            {"concepto": "Clase", "definicion": "Molde que define atributos y métodos de un objeto."},
            {"concepto": "Objeto", "definicion": "Instancia concreta de una clase."},
            {"concepto": "Encapsulamiento", "definicion": "Protección del estado interno mediante acceso controlado."},
        ],
        "uml": [
            {"concepto": "Caso de uso", "definicion": "Funcionalidad vista desde el actor o usuario."},
            {"concepto": "Diagrama de clases", "definicion": "Representa clases, atributos, métodos y relaciones."},
            {"concepto": "Multiplicidad", "definicion": "Cantidad de instancias involucradas en una relación."},
        ],
    }
    return glossaries.get(norm, [
        {"concepto": "MVC", "definicion": "Patrón que separa modelo, vista y controlador."},
        {"concepto": "ORM", "definicion": "Mapeo objeto-relacional para persistencia de datos."},
        {"concepto": "Prueba unitaria", "definicion": "Verifica de forma aislada una parte del código."},
    ])


generate_exercises = generate_personalized_exercises
