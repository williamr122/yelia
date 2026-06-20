"""
Proyecto: YELIA4AP
Archivo: backend/nlp/local_provider.py
Descripción: Módulo del backend para la lógica asociada a esta carpeta/funcionalidad.

Revisión: 2026-02-10
"""
from __future__ import annotations

"""
Archivo: backend/nlp/local_provider.py
Proyecto: YELIA4AP
Última revisión: 2026-02-10

Componentes de procesamiento de lenguaje natural (NLU/NLP) del backend.

Convenciones:
- Funciones pequeñas, nombres descriptivos y manejo de errores explícito.
- Evitar prints en producción: usar logging si aplica.
"""


#
# Archivo: backend/nlp/local_provider.py
# Rol: Módulo del backend (Flask) de YELIA4AP.


"""Local Provider
Archivo del backend del sistema YELIA4AP.

Responsabilidad:
- Implementa la lógica asociada a este módulo.

backend/nlp/local_provider.py

Backend Flask — YELIA (módulo de servidor)

Propósito:
    Proveedor NLP local (offline). Responde consultas educativas usando un índice
    construido a partir de ``temas.json``. Está pensado como respaldo cuando no
    se desea (o no se puede) llamar a proveedores externos.
"""
# =====================================
# Imports
# =====================================


import json
import os
import re
import logging
from typing import Any, Dict, List


# =====================================
# Configuración / Constantes
# =====================================
logger = logging.getLogger(__name__)

_CACHE: Dict[str, Any] | None = None
_INDEX: List[Dict[str, Any]] | None = None
# =====================================
# Funciones / Clases
# =====================================



def _normalize(text: str) -> str:
    """Normaliza texto para comparación simple.

    Realiza una normalización "suave" (lowercase, recorte, eliminación de tildes,
    caracteres no alfanuméricos y espacios repetidos). Se usa para construir claves
    de búsqueda y evitar falsos negativos por diferencias de formato.

    Args:
        text (str): Texto de entrada.

    Returns:
        str: Texto normalizado.
    """
    t = (text or "").lower().strip()
    t = (
        t.replace("á", "a").replace("é", "e").replace("í", "i")
         .replace("ó", "o").replace("ú", "u").replace("ñ", "n")
    )
    t = re.sub(r"[^a-z0-9\s]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def _temas_path() -> str:
    """Obtiene la ruta efectiva para ``temas.json``.

    Prioriza ``TEMAS_JSON_PATH`` (variable de entorno) y luego busca en rutas
    típicas del proyecto. Si no se encuentra, retorna cadena vacía.

    Returns:
        str: Ruta válida de ``temas.json`` o ``""`` si no existe.
    """
    # 1) si lo configuras por ENV
    p = os.getenv("TEMAS_JSON_PATH")
    if p and os.path.isfile(p):
        return p

    # 2) rutas típicas del proyecto
    base = os.getcwd()
    candidates = [
        os.path.join(base, "temas.json"),
        os.path.join(base, "backend", "temas.json"),
        os.path.join(base, "backend", "data", "temas.json"),
        os.path.join(base, "backend", "nlp", "temas.json"),
    ]
    for c in candidates:
        if os.path.isfile(c):
            return c

    return ""


def _load_temas() -> Dict[str, Any]:
    """Carga ``temas.json`` con cache en memoria.

    Si el archivo no existe o falla la lectura, se retorna una estructura mínima
    para mantener el flujo del sistema (sin lanzar error).

    Returns:
        Dict[str, Any]: Contenido del JSON (al menos ``{"Unidades": []}``).
    """
    global _CACHE
    if _CACHE is not None:
        return _CACHE

    path = _temas_path()
    if not path:
        logger.warning("No se encontró temas.json. Configura TEMAS_JSON_PATH.")
        _CACHE = {"Unidades": []}
        return _CACHE

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        logger.info("temas.json cargado", extra={"path": path})
        if not isinstance(data, dict):
            data = {"Unidades": []}
        if "Unidades" not in data:
            data["Unidades"] = []
        _CACHE = data
        return _CACHE
    except Exception as e:
        logger.exception("Error leyendo temas.json", extra={"error": str(e), "path": path})
        _CACHE = {"Unidades": []}
        return _CACHE


def _build_index() -> List[Dict[str, Any]]:
    """Construye (y cachea) el índice local de temas.

    Aplana la estructura por unidades/temas para facilitar búsqueda por puntaje.
    Se guardan claves normalizadas (``k`` y ``ku``) para comparación.

    Returns:
        List[Dict[str, Any]]: Lista de entradas indexadas.
    """
    global _INDEX
    if _INDEX is not None:
        return _INDEX

    data = _load_temas()
    unidades = data.get("Unidades") or []
    idx: List[Dict[str, Any]] = []

    for u in unidades:
        unidad_nombre = u.get("nombre") or ""
        for t in (u.get("temas") or []):
            nombre = t.get("nombre") or ""
            nivel_tema = (t.get("nivel") or "").lower().strip()
            definicion = t.get("definición") or t.get("definicion") or ""
            ventajas = t.get("ventajas") or []
            ejemplo = t.get("ejemplo") or ""

            idx.append({
                "unidad": unidad_nombre,
                "tema": nombre,
                "nivel": nivel_tema,
                "definicion": definicion,
                "ventajas": ventajas,
                "ejemplo": ejemplo,
                "k": _normalize(nombre),
                "ku": _normalize(unidad_nombre),
            })

    _INDEX = idx
    logger.info("Indice local construido", extra={"count": len(idx)})
    return _INDEX


def _nivel_ok(nivel_usuario: str, nivel_tema: str) -> bool:
    """Determina si un tema aplica para el nivel del usuario.

    La regla es deliberadamente permisiva: si el tema no declara nivel, se acepta.
    "avanzada" acepta todo; "intermedia" acepta básica e intermedia; "básica"
    acepta solo básica.

    Args:
        nivel_usuario (str): Nivel declarado por el usuario.
        nivel_tema (str): Nivel configurado en el tema.

    Returns:
        bool: ``True`` si se permite el tema para ese nivel.
    """
    nu = (nivel_usuario or "").lower().strip()
    nt = (nivel_tema or "").lower().strip()

    mapping = {
        "basico": "basica",
        "básico": "basica",
        "basica": "basica",
        "básica": "basica",
        "intermedio": "intermedia",
        "intermedia": "intermedia",
        "avanzado": "avanzada",
        "avanzada": "avanzada",
        "sin conocimientos": "basica",
        "sin_conocimientos": "basica",
    }

    nu_norm = mapping.get(nu, "basica")
    nt_norm = mapping.get(nt, nt)

    if not nt_norm:
        return True
    if nu_norm == "avanzada":
        return True
    if nu_norm == "intermedia":
        return nt_norm in ("basica", "intermedia")
    if nu_norm == "basica":
        return nt_norm in ("basica",)
    return True


# ------------------------------------------------------------
# INTENCIÓN LOCAL (OFFLINE)
# ------------------------------------------------------------
_INTENT_PATTERNS = {
    "definicion": [r"\bque es\b", r"\bqué es\b", r"\bdefin", r"\bconcepto\b", r"\bsignifica\b"],
    "pasos": [r"\bpasos\b", r"\bcomo\b", r"\bcómo\b", r"\bhacer\b", r"\bprocedimiento\b"],
    "ejemplo": [r"\bejemplo\b", r"\bcodigo\b", r"\bcódigo\b", r"\bjava\b", r"\bplantuml\b"],
    "proyecto": [r"\bproyecto\b", r"\bcaso\s+real\b", r"\bavance\b", r"\btrabajo\b"],
    "comparacion": [r"\bvs\b", r"\bdiferencia\b", r"\bcompar\b"],
    "quiz": [r"\bquiz\b", r"\bpreguntas\b", r"\bevalu\b"],
    "debug": [r"\berror\b", r"\bexcep\b", r"\bbug\b", r"\bstack\b", r"\bno funciona\b"],
}


def _detectar_intent(q: str) -> str:
    """Clasifica una consulta en una intención simple por patrones.

    No intenta ser NLP avanzado: únicamente busca coincidencias regex para
    orientar el tipo de respuesta (definición, pasos, ejemplo, etc.).

    Args:
        q (str): Consulta original del usuario.

    Returns:
        str: Nombre de la intención detectada o ``"general"``.
    """
    q = (q or "").lower()
    for intent, pats in _INTENT_PATTERNS.items():
        for p in pats:
            if re.search(p, q):
                return intent
    return "general"


def _score(qn: str, it: Dict[str, Any]) -> int:
    """Calcula un puntaje de coincidencia entre consulta normalizada e item.

    El puntaje combina:
    - coincidencia exacta,
    - contención (tema dentro de la consulta o viceversa),
    - intersección de tokens (tema y unidad).

    Args:
        qn (str): Consulta ya normalizada.
        it (Dict[str, Any]): Item del índice local.

    Returns:
        int: Puntaje (mayor es mejor).
    """
    tk = it.get("k", "")
    uk = it.get("ku", "")
    if not qn:
        return 0
    if qn == tk:
        return 100

    s = 0
    if tk and tk in qn:
        s += 70
    if qn in tk:
        s += 60

    q_tokens = set(qn.split())
    t_tokens = set(tk.split())
    u_tokens = set(uk.split())

    s += len(q_tokens & t_tokens) * 12
    s += len(q_tokens & u_tokens) * 4
    return s


def responder_local_temas(
    pregunta_user: str,
    nivel: str = "",
    modo_interaccion: str = "",
) -> str:
    """Responde una consulta usando el catálogo local de temas.

    Flujo general:
    1) Normaliza la pregunta y detecta intención.
    2) Puntúa cada tema del índice (filtrando por nivel si aplica).
    3) Si hay coincidencia suficiente, arma una respuesta con definición,
       ventajas y/o plantillas guiadas por intención.

    Args:
        pregunta_user (str): Pregunta ingresada por el usuario.
        nivel (str): Nivel académico (básica/intermedia/avanzada).
        modo_interaccion (str): Ajuste de salida (por ejemplo: ``quiz`` o ``debug``).

    Returns:
        str: Respuesta formateada. Si no hay match, retorna cadena vacía.
    """
    qn = _normalize(pregunta_user or "")
    if not qn:
        return ""

    intent = _detectar_intent(pregunta_user)

    idx = _build_index()

    best_sc = 0
    best_it: Dict[str, Any] | None = None

    for it in idx:
        if not _nivel_ok(nivel, it.get("nivel", "")):
            continue
        sc = _score(qn, it)
        if sc > best_sc:
            best_sc = sc
            best_it = it

    if not best_it or best_sc < 30:
        return ""

    tema = best_it.get("tema", "")
    unidad = best_it.get("unidad", "")
    definicion = (best_it.get("definicion") or "").strip()
    ventajas = best_it.get("ventajas") or []
    ejemplo = (best_it.get("ejemplo") or "").strip()

    parts: List[str] = []
    parts.append(f"**{tema}**")
    if unidad:
        parts.append(f"Unidad: {unidad}")

    if definicion:
        # Para offline: siempre ancla con una definición corta (controlada) del tema
        parts.append(f"\n{definicion}")

    # --------------------------------------------------------
    # Respuestas guiadas por intención (sin inventar)
    # --------------------------------------------------------
    # Si el tema no trae 'pasos' específicos, damos un guion reutilizable.
    pasos = best_it.get("pasos") if isinstance(best_it, dict) else None
    if intent in ("pasos", "proyecto") and not pasos:
        pasos = [
            "1) Define el objetivo (qué problema resuelve).",
            "2) Identifica actores/entidades principales.",
            "3) Modela (UML/Clases) antes de programar.",
            "4) Implementa en Java por módulos.",
            "5) Prueba con casos (incluye 2-3 escenarios).",
            "6) Documenta: diagrama + explicación + conclusiones.",
        ]

    if intent == "pasos" and pasos:
        if isinstance(pasos, list):
            parts.append("\n**Pasos (guía):**\n" + "\n".join([f"- {p}" for p in pasos[:10]]))
        else:
            parts.append(f"\n**Pasos (guía):**\n{pasos}")

    if intent == "proyecto":
        # Plantilla corta para que el estudiante pueda avanzar sin internet
        parts.append(
            "\n**Plantilla de mini-proyecto (offline):**\n"
            "- Contexto: describe en 3 líneas un caso real (ej: biblioteca, veterinaria, residencial).\n"
            "- Alcance: 5–7 funcionalidades.\n"
            "- Entregables: (1) Casos de uso, (2) Diagrama de clases, (3) 1 diagrama de secuencia, (4) explicación.\n"
            "- Reglas: usa nombres claros, relaciones y multiplicidades.\n"
            "- Extra: agrega validaciones y manejo de errores."
        )

    if intent == "comparacion":
        parts.append("\nSi quieres comparar, dime exactamente: **A vs B** (ej: interfaz vs clase abstracta).")

    if isinstance(ventajas, list) and ventajas:
        bullets = "\n".join([f"- {v}" for v in ventajas[:6]])
        parts.append(f"\n**Ventajas:**\n{bullets}")

    if ejemplo:
        if "\n" in ejemplo or "class " in ejemplo or "def " in ejemplo:
            parts.append(f"\n**Ejemplo:**\n```java\n{ejemplo}\n```")
        else:
            parts.append(f"\n**Ejemplo:** {ejemplo}")

    if modo_interaccion == "quiz":
        parts.append("\n¿Quieres que te haga 3 preguntas tipo quiz de este tema?")
    elif modo_interaccion == "debug":
        parts.append("\nSi me pegas tu código/error, te ayudo a corregirlo paso a paso.")

    return "\n".join(parts).strip()
