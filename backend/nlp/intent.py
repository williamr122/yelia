"""
Proyecto: YELIA4AP
Archivo: backend/nlp/intent.py
Descripción: Módulo del backend para la lógica asociada a esta carpeta/funcionalidad.

Revisión: 2026-02-10
"""
from __future__ import annotations

"""
Archivo: backend/nlp/intent.py
Proyecto: YELIA4AP
Última revisión: 2026-02-10

Componentes de procesamiento de lenguaje natural (NLU/NLP) del backend.

Convenciones:
- Funciones pequeñas, nombres descriptivos y manejo de errores explícito.
- Evitar prints en producción: usar logging si aplica.
"""


#
# Archivo: backend/nlp/intent.py
# Rol: Módulo del backend (Flask) de YELIA4AP.


"""Intent
Archivo del backend del sistema YELIA4AP.

Responsabilidad:
- Implementa la lógica asociada a este módulo.

backend/nlp/intent.py

Backend Flask — YELIA (módulo de servidor)

Propósito:
    Este archivo pertenece al backend (Flask) de YELIA. Contiene lógica de servidor
    y/o utilidades que soportan rutas, servicios, persistencia y orquestación NLP.
    En particular, este módulo implementa la detección de intención del estudiante
    mediante reglas determinísticas, para mejorar la coherencia y control pedagógico.
"""


# ============================================================
# PROPÓSITO:
#   Detectar cómo y con qué intención se comunica el estudiante.
#
# DIFERENCIA CLAVE:
#   - modo_interaccion → define CÓMO debe responder YELIA
#     (quiz, debug, intro, tarea_directa, normal)
#
#   - intencion_semantica → define QUÉ tipo de contenido busca
#     (saludo, teoría, código, ejercicio, evaluación, etc.)
#
# ENFOQUE PROFESIONAL:
#   Estas detecciones NO dependen del modelo LLM.
#   Son reglas determinísticas que permiten:
#   - respuestas más coherentes
#   - control pedagógico
#   - evitar entregar soluciones directas cuando no corresponde
#
# CORRECCIÓN APLICADA (bug real observado):
#   - Cuando el estudiante responde con una opción del menú UI (ej: "definición rápida"),
#     ese texto suelto podía caer en off-topic (por falta de contexto).
#   - Solución: detectar opciones del menú y tratarlas como "continuacion" para heredar el tema anterior.
# ============================================================


import re


# ------------------------------------------------------------
# NORMALIZACIÓN (liviana, para reglas)
# ------------------------------------------------------------
# - Se usa en triggers cortos (continuación/menú)
# - Es deliberadamente simple para ser rápida y estable
# ------------------------------------------------------------

def _norm_basic(s: str) -> str:
    """Normalización liviana para reglas (tildes + signos + espacios).

    Args:
        s: Texto de entrada.

    Returns:
        Valor tipo str.
    """
    s = (s or "").lower().strip()
    s = (
        s.replace("á","a").replace("é","e").replace("í","i")
         .replace("ó","o").replace("ú","u").replace("ü","u")
         .replace("ñ","n")
    )
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


# ------------------------------------------------------------
# ------------------------------------------------------------
# Objetivo:
# - Detectar mensajes tipo: "sí", "ok", "quiero saber más", "continúa"
# - Evitar que el filtro de dominio los marque como off-topic
# - Permitir que YELIA continúe el tema anterior sin pedir que el
#   estudiante repita la pregunta.
#
# Optimización (sin cambiar lógica):
# - Normalizamos el set una sola vez para no reconstruirlo por llamada.
# ------------------------------------------------------------

_CONTINUACION_TRIGGERS = {
    "si",
    "sí",
    "ok",
    "okay",
    "dale",
    "de una",
    "continua",
    "continúa",
    "sigue",
    "siga",
    "quiero saber mas",
    "quiero saber más",
    "explicame mas",
    "explícame más",
    "mas",
    "más",
    "cuentame mas",
    "cuéntame más",
    "amplia",
    "amplía",
    "profundiza",
}
# Set normalizado (evita recalcular en cada request)
_CONTINUACION_TRIGGERS_N = {_norm_basic(x) for x in _CONTINUACION_TRIGGERS}

def es_mensaje_de_continuacion(texto: str) -> bool:
    """True si el mensaje parece ser una continuación del tema anterior.

    Args:
        texto: Texto de entrada.

    Returns:
        Valor tipo bool.
    """
    t = _norm_basic(texto)

    # Match exacto (respuestas cortas)
    if t in _CONTINUACION_TRIGGERS_N:
        return True

    # Match por subcadena (frases cortas: "quiero saber mas de eso")
    if len(t) <= 60:
        for trig in _CONTINUACION_TRIGGERS_N:
            if trig in t:
                return True

    return False


# ------------------------------------------------------------
# OPCIONES DE MENÚ (FIX del caso "definición rápida")
# ------------------------------------------------------------
# Contexto real:
# - En UI, YELIA muestra opciones: "definición rápida", "ejemplo en Java", etc.
# - Esas respuestas pueden llegar al backend como texto suelto.
# - Sin contexto, domain.py podría marcarlas como off-topic.
#
# Solución:
# - Tratar estas opciones como una continuación guiada.
# - Aquí las detectamos y devolvemos intención "continuacion".
#
# Nota importante (mejora sin romper tu idea):
# - NO incluimos "ejemplo" o "definicion" sueltos porque podrían ser
#   una consulta nueva sin relación al tema anterior (evita falsos positivos).
# - Dejamos SOLO las frases típicas del menú UI.
#
# Optimización:
# - Normalizamos el set una sola vez.
# ------------------------------------------------------------

_MENU_TRIGGERS = {
    "definicion rapida",
    "definición rápida",
    "ejemplo en java",
    "pasos para un ejercicio",
    "depurar un error",
}
_MENU_TRIGGERS_N = {_norm_basic(x) for x in _MENU_TRIGGERS}

def es_opcion_menu(texto: str) -> bool:
    """True si el texto coincide con una opción corta típica del menú UI.

    Args:
        texto: Texto de entrada.

    Returns:
        Valor tipo bool.
    """
    t = _norm_basic(texto)
    return t in _MENU_TRIGGERS_N


def detectar_modo_interaccion(pregunta_lower: str) -> str:
    """Determina el modo de interacción esperado por el estudiante.

    El modo NO indica el contenido, sino la forma de ayuda solicitada.

    Modos posibles:
    - quiz           → el estudiante quiere ser evaluado
    - debug          → el estudiante tiene un error o problema técnico
    - tarea_directa  → intenta que el sistema resuelva por él
    - intro          → necesita explicación desde cero
    - normal         → explicación estándar

    Args:
        pregunta_lower: Parámetro de entrada.

    Returns:
        Valor tipo str.
    """
    pl = (pregunta_lower or "").lower()

    if "autoevalu" in pl:
        return "quiz"

    if any(x in pl for x in [
        "hazme un quiz","hazme un cuestionario","ponme preguntas","evalúame","evaluame",
        "pregúntame","preguntame","test de","preguntas de opción múltiple","preguntas de opcion multiple"
    ]):
        return "quiz"

    if any(x in pl for x in [
        "error","exception","traceback","no compila","no funciona",
        "me falla","se cae","crashea"
    ]):
        return "debug"

    if any(x in pl for x in [
        "hazme el código","hazme el codigo","hazme un código","hazme un codigo",
        "resuélveme","resuelveme","hazme la tarea","hazme el deber",
        "resuelve este ejercicio","examen","prueba"
    ]):
        return "tarea_directa"

    if any(x in pl for x in [
        "no entiendo nada","explícame desde cero","explicame desde cero",
        "enséñame desde cero","enseñame desde cero","empezar desde cero",
        "por dónde empiezo","por donde empiezo"
    ]):
        return "intro"

    return "normal"


def detectar_intencion_semantica(pregunta_lower: str) -> str:
    """Detecta la intención semántica principal del mensaje.

    Intenciones posibles:
    - continuacion
    - saludo
    - quiz
    - evaluacion_respuesta
    - teoria
    - codigo
    - ejercicio
    - otro

    Args:
        pregunta_lower: Parámetro de entrada.

    Returns:
        Valor tipo str.
    """
    pl = (pregunta_lower or "").lower()

    # 0) Opciones del menú (se tratan como continuación guiada)
    # FIX: evita "offtopic" cuando el estudiante solo presiona una opción del menú.
    if es_opcion_menu(pl):
        return "continuacion"

    # 1) Continuación conversacional (ej: "sí", "quiero saber más", "continúa")
    if es_mensaje_de_continuacion(pl):
        return "continuacion"

    if any(x in pl for x in ["hola", "buenas", "buen día", "buen dia", "hey yelia", "holi"]):
        return "saludo"

    if any(x in pl for x in ["quiz", "cuestionario", "test"]) or "autoevalu" in pl:
        return "quiz"

    if any(x in pl for x in [
        "mi respuesta está bien","mi respuesta esta bien","revisa mi respuesta",
        "corrige mi respuesta","dime si está bien","dime si esta bien"
    ]):
        return "evaluacion_respuesta"

    if any(x in pl for x in [
        "qué es","que es","explícame","explicame","definición","definicion","concepto de"
    ]):
        return "teoria"

    if any(x in pl for x in [
        "código","codigo","ejemplo en java","ejemplo en kotlin",
        "muestra un ejemplo","sintaxis"
    ]):
        return "codigo"

    if any(x in pl for x in [
        "ejercicio","aplicar","aplicación","aplicacion",
        "caso práctico","caso practico"
    ]):
        return "ejercicio"

    return "otro"


def clasificar_fuerza_consulta(pregunta: str, modo_interaccion: str, intencion_semantica: str) -> str:
    """Clasifica la consulta como:

    - 'fuerte'  -> requiere razonamiento/explicación profunda
    - 'simple'  -> respuesta rápida / conversacional

    Esta función NO llama IA. Solo reglas determinísticas.

    Args:
        pregunta: Parámetro de entrada.
        modo_interaccion: Parámetro de entrada.
        intencion_semantica: Parámetro de entrada.

    Returns:
        Valor tipo str.
    """
    t = (pregunta or "").strip().lower()

    if modo_interaccion in ("debug", "quiz"):
        return "fuerte"

    if modo_interaccion == "tarea_directa":
        return "fuerte"

    if intencion_semantica in ("teoria", "codigo", "ejercicio"):
        if len(t) >= 180:
            return "fuerte"
        if "```" in t:
            return "fuerte"
        if any(k in t for k in ("error", "exception", "traceback", "optimiza", "complejidad", "demuestra")):
            return "fuerte"

    # Menú/continuación suelen ser respuestas rápidas
    if intencion_semantica in ("saludo", "continuacion"):
        return "simple"

    if len(t) >= 350:
        return "fuerte"

    return "simple"
