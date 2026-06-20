"""
Proyecto: YELIA4AP
Archivo: backend/nlp/history_utils.py
Descripción: Funciones auxiliares reutilizables (utilities) para el backend.

Revisión: 2026-02-10
"""
from __future__ import annotations

"""
Archivo: backend/nlp/history_utils.py
Proyecto: YELIA4AP
Última revisión: 2026-02-10

Componentes de procesamiento de lenguaje natural (NLU/NLP) del backend.

Convenciones:
- Funciones pequeñas, nombres descriptivos y manejo de errores explícito.
- Evitar prints en producción: usar logging si aplica.
"""


#
# Archivo: backend/nlp/history_utils.py
# Rol: Módulo del backend (Flask) de YELIA4AP.


"""History Utils
Archivo del backend del sistema YELIA4AP.

Responsabilidad:
- Implementa la lógica asociada a este módulo.

backend/nlp/history_utils.py

Backend Flask — YELIA (módulo de servidor)

Propósito:
    Este archivo pertenece al backend (Flask) de YELIA. Contiene lógica de servidor
    y/o utilidades que soportan rutas, servicios, persistencia y orquestación NLP.
    En particular, este módulo maneja la normalización, limpieza y resumen
    del historial conversacional del estudiante para mejorar la coherencia y
    eficiencia en las interacciones con el modelo de lenguaje.
"""


# =========================================================
# CONFIGURACIÓN DE HISTORIAL (Continuidad de chat)
# ---------------------------------------------------------
# Ajustes recomendados para balancear memoria vs. tokens.
# - NORMALIZE_LIMIT: cuántos items se aceptan como entrada (front/BD).
# - CONTEXT_*: cuántos mensajes se convierten en contexto para el prompt.
# =========================================================
NORMALIZE_LIMIT: int = 20
CONTEXT_CHAT_MESSAGES: int = 6
CONTEXT_LEGACY_PAIRS: int = 4
CONTEXT_ITEM_MAX_CHARS: int = 700


# backend/nlp/history_utils.py
# ============================================================
# PROPÓSITO:
#   Utilidades para manejar, limpiar y resumir el historial
#   conversacional del estudiante.
#
# QUÉ RESUELVE ESTE MÓDULO:
#   - Normaliza distintos formatos de historial (legacy y actual)
#   - Reduce ruido y limita tamaño del historial
#   - Construye un contexto textual compacto para el prompt
#   - Extrae "pistas" recientes para cache y coherencia
#   - Genera hashes cortos para claves de cache
#
# ENFOQUE PROFESIONAL:
#   El historial NO se envía completo al modelo.
#   Se filtra, resume y estructura para:
#   - Mejor rendimiento
#   - Menos tokens
#   - Respuestas más coherentes
# ============================================================


from typing import List, Dict, Any
import hashlib


def normalizar_historial(historial: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Normaliza el historial recibido desde el frontend o la base de datos.

    Soporta dos formatos:
    1) Formato nuevo (chat):
       { "remitente": "user|bot", "contenido": "texto" }
    2) Formato legacy:
       { "pregunta": "...", "respuesta": "..." }

    Reglas:
    - Si el historial no es una lista, se ignora.
    - Se limita a los últimos NORMALIZE_LIMIT elementos (control de tamaño).
    - Se eliminan mensajes vacíos o mal formados.

    Retorna:
    - Lista de mensajes normalizados y listos para análisis/contexto.

    Args:
        historial: Historial de conversación.

    Returns:
        Valor retornado por la función.
    """
    if not isinstance(historial, list):
        return []

    normalizado: List[Dict[str, Any]] = []

    # Se recorren solo los últimos 20 elementos para evitar prompts largos
    for item in historial[-NORMALIZE_LIMIT:]:
        if not isinstance(item, dict):
            continue

        # Formato moderno (chat continuo)
        if "remitente" in item and "contenido" in item:
            contenido = (item.get("contenido") or "").strip()
            if contenido:
                normalizado.append({
                    "remitente": item.get("remitente"),
                    "contenido": contenido
                })

        # Formato legacy (pregunta / respuesta)
        else:
            preg = (item.get("pregunta") or "").strip()
            resp = (item.get("respuesta") or "").strip()
            if preg or resp:
                normalizado.append({
                    "pregunta": preg,
                    "respuesta": resp
                })

    return normalizado


def construir_contexto_desde_historial(historial: List[Dict[str, Any]]) -> str:
    """Construye un resumen textual del historial reciente.

    Objetivo:
    - Generar un contexto breve y legible para incluirlo en el prompt
      del modelo (system prompt).

    Estrategia:
    - Si el historial es tipo legacy (pregunta/respuesta):
        • Usa los últimos CONTEXT_LEGACY_PAIRS pares
    - Si es tipo chat (user/bot):
        • Usa los últimos CONTEXT_CHAT_MESSAGES mensajes
    - Se etiqueta cada línea para claridad semántica

    Retorna:
    - String con formato de lista
    - O 'Sin historial previo.' si no hay contenido útil

    Args:
        historial: Historial de conversación.

    Returns:
        Valor tipo str.
    """
    if not historial:
        return "Sin historial previo."

    def _compactar(texto: str) -> str:
        texto = (texto or "").strip()
        if len(texto) <= CONTEXT_ITEM_MAX_CHARS:
            return texto
        return texto[:CONTEXT_ITEM_MAX_CHARS].rstrip() + " [...]"

    lineas: List[str] = []

    # Detecta si el historial es de tipo pregunta/respuesta (legacy)
    tiene_pr = any(("pregunta" in h or "respuesta" in h) for h in historial)

    if tiene_pr:
        # Historial legacy: pares pregunta-respuesta
        for h in historial[-CONTEXT_LEGACY_PAIRS:]:
            preg = _compactar(h.get("pregunta") or "")
            resp = _compactar(h.get("respuesta") or "")
            if preg or resp:
                lineas.append(f"- Pregunta: {preg}\n  Respuesta: {resp}")
    else:
        # Historial tipo chat (user/bot)
        for h in historial[-CONTEXT_CHAT_MESSAGES:]:
            remitente = h.get("remitente")
            texto = _compactar(h.get("contenido") or "")
            if not texto:
                continue

            if remitente == "user":
                lineas.append(f"- Estudiante: {texto}")
            elif remitente == "bot":
                lineas.append(f"- YELIA: {texto}")
            else:
                lineas.append(f"- Mensaje: {texto}")

    return "\n".join(lineas) if lineas else "Sin historial previo."


def extraer_ultima_pista_historial(historial: List[Dict[str, Any]]) -> str:
    """Extrae una 'pista' corta del último mensaje del historial.

    Uso principal:
    - Diferenciar contextos similares en el sistema de cache
    - Evitar reutilizar respuestas cuando el contexto cambió ligeramente

    Regla:
    - Prioriza 'contenido' (chat)
    - Si no existe, usa 'pregunta' (legacy)
    - Limita a 140 caracteres para estabilidad

    Args:
        historial: Historial de conversación.

    Returns:
        Valor tipo str.
    """
    if not historial:
        return ""

    last = historial[-1] or {}

    texto = (last.get("contenido") or "").strip()
    if not texto:
        texto = (last.get("pregunta") or "").strip()

    return texto[:140]


def hash_texto_corto(texto: str, n: int = 16) -> str:
    """Genera un hash corto (SHA-256 truncado) de un texto.

    Uso:
    - Crear claves de cache compactas y reproducibles
    - Evitar guardar texto completo en la key (eficiencia y privacidad)

    Parámetros:
    - texto: string de entrada
    - n: longitud del hash final (por defecto 16)

    Retorna:
    - Hash hexadecimal truncado

    Args:
        texto: Texto de entrada.
        n: Parámetro de entrada.

    Returns:
        Hash corto determinista del texto.
    """
    texto = (texto or "").strip()
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()[:n]


def extraer_ultimo_tema_relevante(historial: List[Dict[str, Any]]) -> str:
    """Intenta extraer una pista de 'tema' desde el historial reciente.

    Caso que resuelve:
    - El estudiante escribe: "sí", "quiero saber más", "continúa"
    - Ese mensaje por sí solo no contiene keywords de dominio
    - Por tanto, necesitamos rescatar el tema anterior (UML, clases, etc.)

    Estrategia (simple y explicable para tesis):
    - Recorre desde el final buscando el último mensaje con contenido "sustancioso"
    - Evita frases meta tipo "¿Te quedó claro?" o reacciones.
    - Devuelve el texto encontrado (máx. 220 chars) como pista.

    Args:
        historial: Historial de conversación.

    Returns:
        Valor tipo str.
    """
    if not historial:
        return ""

    # Palabras/frases que no aportan tema (ruido común en UI)
    ruido = {
        "te quedo claro",
        "¿te quedo claro?",
        "te quedo claro?",
        "te quedó claro",
        "¿te quedó claro?",
        "👍",
        "👎",
        "copiar",
    }

    def _es_util(t: str) -> bool:
        """_es_util.

        Args:
            t (str): TODO: Describe this parameter.

        Returns:
            bool: TODO: Describe the return value."""
        t = (t or "").strip()
        if len(t) < 6:
            return False
        tl = t.lower()
        for r in ruido:
            if r in tl:
                return False
        return True

    # Busca desde el final: prioriza preguntas del estudiante, luego respuestas del bot
    for item in reversed(historial[-NORMALIZE_LIMIT:]):
        if not isinstance(item, dict):
            continue

        # Formato chat
        if "contenido" in item:
            t = (item.get("contenido") or "").strip()
            if _es_util(t):
                return t[:220]

        # Formato legacy
        preg = (item.get("pregunta") or "").strip()
        if _es_util(preg):
            return preg[:220]
        resp = (item.get("respuesta") or "").strip()
        if _es_util(resp):
            return resp[:220]

    return ""
