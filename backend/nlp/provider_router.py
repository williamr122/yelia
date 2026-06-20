"""
Proyecto: YELIA4AP
Archivo: backend/nlp/provider_router.py
Descripción: Módulo del backend para la lógica asociada a esta carpeta/funcionalidad.

Revisión: 2026-02-10
"""
from __future__ import annotations

"""
Archivo: backend/nlp/provider_router.py
Proyecto: YELIA4AP
Última revisión: 2026-02-10

Componentes de procesamiento de lenguaje natural (NLU/NLP) del backend.

Convenciones:
- Funciones pequeñas, nombres descriptivos y manejo de errores explícito.
- Evitar prints en producción: usar logging si aplica.
"""


#
# Archivo: backend/nlp/provider_router.py
# Rol: Módulo del backend (Flask) de YELIA4AP.


"""Provider Router
Archivo del backend del sistema YELIA4AP.

Responsabilidad:
- Implementa la lógica asociada a este módulo.

backend/nlp/provider_router.py

Backend Flask — YELIA (módulo de servidor)

Propósito:
    Este archivo pertenece al backend (Flask) de YELIA. Contiene lógica de servidor
    y/o utilidades que soportan rutas, servicios, persistencia y orquestación NLP.
"""
# =====================================
# Imports
# =====================================



import logging
import os
import time
import unicodedata
from typing import Any, Dict, List

from backend.core.net import has_internet


# =====================================
# Configuración / Constantes
# =====================================
from .groq_client import llamar_groq
from .deepseek_client import llamar_deepseek
from .gemini_client import llamar_gemini
from .local_provider import responder_local_temas  # ✅ NUEVO


# -----------------------------------------------------------------------------
# Normalización (acentos/alias) para decidir routing por nivel
# -----------------------------------------------------------------------------
# =====================================
# Funciones / Clases
# =====================================

def _norm(txt: str) -> str:
    txt = (txt or "").strip().lower()
    txt = "".join(c for c in unicodedata.normalize("NFD", txt) if unicodedata.category(c) != "Mn")
    return txt

logger = logging.getLogger(__name__)

# -----------------------------------------------------------------------------
# Heurísticas de complejidad (ligeras, sin dependencias)
# -----------------------------------------------------------------------------
_PALABRAS_PESADAS = (
    "optimiza", "refactor", "arquitectura", "escalable", "rendimiento",
    "big o", "complejidad", "demuestra", "prueba", "teorema",
    "caso borde", "edge case", "concurrencia", "multihilo", "async",
    "patrones", "solid", "clean architecture", "microservicios",
    "diseña", "diseño", "pipeline", "dataset", "entrenar", "fine-tuning",
    "rag", "embeddings", "vector", "retrieval", "documento", "pdf", "docx",
)

# -----------------------------------------------------------------------------
# Protección anti-reintento para Deep (errores no recuperables)
# -----------------------------------------------------------------------------
_DEEP_BLOCK_UNTIL_TS: float = 0.0
_DEEP_BLOCK_REASON: str = ""
_DEEP_BLOCK_SECONDS: int = 10 * 60  # 10 minutos
_MAX_PROMPT_CHARS: int = int(os.getenv("NLP_MAX_PROMPT_CHARS", "9000"))
_MAX_USER_CHARS: int = int(os.getenv("NLP_MAX_USER_CHARS", "6000"))


def _enabled_provider(name: str) -> bool:
    env_name = f"ENABLE_{name.upper()}"
    return os.getenv(env_name, "1").strip().lower() in {"1", "true", "yes", "on"}


def _trim_text(text: str, limit: int) -> str:
    text = text or ""
    if limit <= 0 or len(text) <= limit:
        return text
    keep_head = max(0, int(limit * 0.65))
    keep_tail = max(0, limit - keep_head - 80)
    return (
        text[:keep_head].rstrip()
        + "\n\n[... contexto recortado para evitar limite de tokens ...]\n\n"
        + text[-keep_tail:].lstrip()
    )


def _deep_esta_bloqueado() -> bool:
    """
    _deep_esta_bloqueado.

    Args:
        * (Ver firma): parámetros del método/función.

    Returns:
        Any: Resultado de la operación, según implementación.

    Raises:
        Exception: Errores relevantes propagados por dependencias.
    """
    return time.time() < _DEEP_BLOCK_UNTIL_TS


def _bloquear_deep(reason: str) -> None:
    """
    _bloquear_deep.

    Args:
        * (Ver firma): parámetros del método/función.

    Returns:
        Any: Resultado de la operación, según implementación.

    Raises:
        Exception: Errores relevantes propagados por dependencias.
    """
    global _DEEP_BLOCK_UNTIL_TS, _DEEP_BLOCK_REASON
    _DEEP_BLOCK_REASON = reason
    _DEEP_BLOCK_UNTIL_TS = time.time() + _DEEP_BLOCK_SECONDS
    logger.warning(
        "DeepSeek bloqueado temporalmente (cooldown)",
        extra={"seconds": _DEEP_BLOCK_SECONDS, "reason": reason},
    )


def _es_error_no_recuperable_deep(e: Exception) -> bool:
    """
    _es_error_no_recuperable_deep.

    Args:
        * (Ver firma): parámetros del método/función.

    Returns:
        Any: Resultado de la operación, según implementación.

    Raises:
        Exception: Errores relevantes propagados por dependencias.
    """
    msg = (str(e) or "").lower()
    return any(
        token in msg
        for token in (
            "402",
            "payment required",
            "insufficient balance",
            "quota",
            "billing",
        )
    )

# -----------------------------------------------------------------------------
# Heurísticas
# -----------------------------------------------------------------------------
def _contiene_mucho_codigo(texto: str) -> bool:
    """
    _contiene_mucho_codigo.

    Args:
        * (Ver firma): parámetros del método/función.

    Returns:
        Any: Resultado de la operación, según implementación.

    Raises:
        Exception: Errores relevantes propagados por dependencias.
    """
    if "```" in (texto or ""):
        return True

    lineas = (texto or "").splitlines()
    if len(lineas) >= 8:
        indicadores = (
            "def ", "class ", "import ", "from ",
            "{", "}", ";", "=>", "::",
            "#include", "SELECT ", "INSERT ",
        )
        hits = sum(1 for ln in lineas if any(tok in ln for tok in indicadores))
        return hits >= 3

    return False


def _es_consulta_fuerte(pregunta_user: str, modo_interaccion: str, nivel: str) -> bool:
    """
    _es_consulta_fuerte.

    Args:
        * (Ver firma): parámetros del método/función.

    Returns:
        Any: Resultado de la operación, según implementación.

    Raises:
        Exception: Errores relevantes propagados por dependencias.
    """
    q = (pregunta_user or "").lower().strip()

    if modo_interaccion in ("debug", "quiz", "tarea_directa"):
        return True
    if (nivel or "").lower() == "avanzada":
        return True
    if len(q) > 700:
        return True
    if _contiene_mucho_codigo(pregunta_user):
        return True
    if any(pal in q for pal in _PALABRAS_PESADAS):
        return True

        # opcional: “quiero paso a paso / completo”
    if any(x in q for x in (
        "paso a paso",
        "bien detallado", "muy detallado", "muy detallada",
        "muy completo", "hazlo completo",
        "no lo resumas", "no resumas", "sin resumir",
        "extenso", "extensa",
        "minimo", "mínimo", "1200 palabras", "1000 palabras",
        "secciones", "uml", "plantuml"
    )):
        return True

    return False

# -----------------------------------------------------------------------------
# Router principal
# -----------------------------------------------------------------------------
def seleccionar_proveedor(
    prompt_system: str,
    pregunta_user: str,
    max_tokens: int,
    modo_interaccion: str,
    nivel: str,
) -> Dict[str, Any]:

    """Selecciona y ejecuta el proveedor NLP más adecuado según la conectividad y el tipo de consulta.

El router prioriza una respuesta local cuando no hay internet. Con conectividad,
prueba proveedores en un orden distinto para consultas "fuertes" vs. "simples" y
devuelve metadatos útiles para trazabilidad (p. ej., proveedores fallidos).

Args:
    prompt_system (str): Instrucción base del sistema para el proveedor/modelo.
    pregunta_user (str): Consulta del usuario.
    max_tokens (int): Límite máximo de tokens para la generación.
    modo_interaccion (str): Modo de interacción (p. ej., 'debug', 'quiz').
    nivel (str): Nivel de profundidad esperado (p. ej., 'basica', 'avanzada').

Returns:
    Dict[str, Any]: Respuesta y metadatos del enrutamiento (proveedor usado, flags, etc.).

    """

    proveedores_fallidos: List[str] = []
    fuerte = _es_consulta_fuerte(pregunta_user, modo_interaccion, nivel)

    # -------------------------------------------------------------------------
    # 1) SIN INTERNET -> LOCAL (temas.json) directo
    #    (si local no encuentra match, core.py hará fallback mini-FAQ)
    # -------------------------------------------------------------------------
    if not has_internet():
        logger.info("Router NLP: sin internet.")
        r_local = responder_local_temas(pregunta_user, nivel=nivel, modo_interaccion=modo_interaccion)
        return {
            "respuesta": r_local or "",
            "proveedor": "local",
            "proveedores_fallidos": proveedores_fallidos,
            "fuerte": fuerte,
            "online": False,
        }

    # -------------------------------------------------------------------------
    # 2) CON INTERNET -> orden según fuerte/simple
    # -------------------------------------------------------------------------
    nivel_n = _norm(nivel)

    # ----------------------------------------------------------
    # Alias de nivel (UX): tratar "sin conocimientos" como básico
    # ----------------------------------------------------------
    # El frontend permite opciones como "Sin conocimientos".
    # Para que el routing sea consistente:
    #  - "sin conocimientos" => básico (Groq primero)
    #  - "novato"/"principiante" => básico
    if nivel_n in {"sin conocimientos", "sin conocimiento", "novato", "principiante", "principiante absoluto"}:
        nivel_n = "basico"


    # Orden por diseño:
    # - Intermedio/Avanzado (o fuerte=True): Deep -> Gemini -> Groq
    # - Básico/otros: Groq -> Deep -> Gemini
    if fuerte or nivel_n in {"intermedio", "intermedia", "avanzado", "avanzada"}:
        orden = ["deep", "gemini", "groq"]
    else:
        orden = ["groq", "gemini"]

    deep_enabled = _enabled_provider("deepseek")
    if _deep_esta_bloqueado():
        orden = [p for p in orden if p != "deep"]
        logger.info("DeepSeek omitido por cooldown", extra={"reason": _DEEP_BLOCK_REASON})
    if not deep_enabled:
        orden = [p for p in orden if p != "deep"]
        logger.info("DeepSeek omitido por configuracion ENABLE_DEEPSEEK=0")

    logger.info(
        "Router NLP: orden=%s (fuerte=%s, nivel=%s, modo=%s, len=%d)",
        "->".join(orden),
        fuerte,
        nivel,
        modo_interaccion,
        len(pregunta_user or ""),
    )

    prompt_system = _trim_text(prompt_system, _MAX_PROMPT_CHARS)
    pregunta_user = _trim_text(pregunta_user, _MAX_USER_CHARS)

    # -------------------------------------------------------------------------
    # 3) Intentar proveedores online en orden
    # -------------------------------------------------------------------------
    for prov in orden:
        try:
            logger.info("Router NLP: intentando proveedor=%s", prov)
            if prov == "groq":
                r = llamar_groq(prompt_system, pregunta_user, max_tokens)
                if r:
                    logger.info("Router NLP: proveedor_ok=%s", "groq")
                    return {"respuesta": r, "proveedor": "groq", "proveedores_fallidos": proveedores_fallidos, "fuerte": fuerte, "online": True}
                proveedores_fallidos.append("groq:empty")

            elif prov == "gemini":
                r = llamar_gemini(prompt_system, pregunta_user, max_tokens)
                if r:
                    logger.info("Router NLP: proveedor_ok=%s", "gemini")
                    return {"respuesta": r, "proveedor": "gemini", "proveedores_fallidos": proveedores_fallidos, "fuerte": fuerte, "online": True}
                proveedores_fallidos.append("gemini:empty")

            elif prov == "deep":
                r = llamar_deepseek(prompt_system, pregunta_user, max_tokens)
                if r:
                    logger.info("Router NLP: proveedor_ok=%s", "deep")
                    return {"respuesta": r, "proveedor": "deep", "proveedores_fallidos": proveedores_fallidos, "fuerte": fuerte, "online": True}
                proveedores_fallidos.append("deep:empty")

        except Exception as e:
            proveedores_fallidos.append(f"{prov}:{type(e).__name__}")
            logger.warning("Router NLP: %s falló: %s", prov, str(e))

            if prov == "deep" and _es_error_no_recuperable_deep(e):
                _bloquear_deep("402/Quota/Billing")

    # -------------------------------------------------------------------------
    # 4) SI CAEN LOS ONLINE -> fallback local real (temas.json)
    # -------------------------------------------------------------------------
    logger.warning("Router NLP: fallaron proveedores online, fallback a local (temas.json)...")
    r_local = responder_local_temas(pregunta_user, nivel=nivel, modo_interaccion=modo_interaccion)
    return {
        "respuesta": r_local or "",
        "proveedor": "local",
        "proveedores_fallidos": proveedores_fallidos,
        "fuerte": fuerte,
        "online": True,
    }
