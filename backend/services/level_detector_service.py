"""
Proyecto: YELIA4AP
Archivo: backend/services/level_detector_service.py
Descripción: Módulo del backend para la lógica asociada a esta carpeta/funcionalidad.

Revisión: 2026-02-10
"""
from __future__ import annotations

"""
Archivo: backend/services/level_detector_service.py
Proyecto: YELIA4AP
Última revisión: 2026-02-10

Módulo de backend en Python.

Convenciones:
- Funciones pequeñas, nombres descriptivos y manejo de errores explícito.
- Evitar prints en producción: usar logging si aplica.
"""


#
# Archivo: backend/services/level_detector_service.py
# Rol: Módulo del backend (Flask) de YELIA4AP.


"""Level Detector Service
Archivo del backend del sistema YELIA4AP.

Responsabilidad:
- Implementa la lógica asociada a este módulo.

backend/services/level_detector_service.py

Backend Flask — YELIA (módulo de servidor)

Propósito:
    Detectar automáticamente el nivel del estudiante (basico/intermedio/avanzado)
    usando señales ligeras (heurísticas) y opcionalmente una clasificación con LLM.

Principios:
    - No romper el chat: si falla, se devuelve un nivel por defecto.
    - Evitar latencia extra: el LLM es opcional y se controla por env.
"""
# =====================================
# Imports
# =====================================


import os
import re
from typing import Any, Dict, Optional

import structlog

from backend.nlp.provider_router import seleccionar_proveedor


# =====================================
# Configuración / Constantes
# =====================================
logger = structlog.get_logger()


_LEVELS = ("basico", "intermedio", "avanzado")
# =====================================
# Funciones / Clases
# =====================================



def _heuristic_level(user_text: str, code_context: Optional[str] = None) -> Dict[str, Any]:
    """Heurística simple y rápida para estimar nivel."""
    t = (user_text or "").lower().strip()
    code = (code_context or "")

    # Señales de básico
    basic_markers = [
        "no entiendo",
        "explicame",
        "explícame",
        "que es",
        "qué es",
        "desde cero",
        "paso a paso",
        "ayuda",
    ]

    # Señales de avanzado
    advanced_markers = [
        "complejidad",
        "big o",
        "patron",
        "patrón",
        "refactor",
        "pruebas",
        "junit",
        "mvc",
        "uml",
        "solid",
        "dao",
        "orm",
        "arquitectura",
    ]

    score_basic = sum(1 for m in basic_markers if m in t)
    score_adv = sum(1 for m in advanced_markers if m in t)

    # Señales de intermedio: debugging, "por qué falla", etc.
    score_mid = 0
    mid_markers = ["error", "falla", "bug", "no funciona", "corrige", "completa", "mejorar", "optimizar"]
    score_mid += sum(1 for m in mid_markers if m in t)

    # Si el usuario pega código con estructuras más complejas, sube a intermedio
    if code and any(k in code for k in ["class ", "public static", "for (", "while (", "try {", "catch ("]):
        score_mid += 1

    # Regex para ver si hay métodos / firmas
    if code and re.search(r"\b(static|public|private)\s+\w+\s+\w+\s*\(", code):
        score_mid += 1

    # Decisión
    if score_adv >= 2:
        return {"level": "avanzado", "confidence": 0.72, "reason": "Señales de diseño/mejora/pruebas."}
    if score_basic >= 2 and score_adv == 0:
        return {"level": "basico", "confidence": 0.70, "reason": "Señales de explicación desde cero/paso a paso."}
    if score_mid >= 2:
        return {"level": "intermedio", "confidence": 0.65, "reason": "Señales de depuración/mejora de código."}

    # Por defecto
    return {"level": "intermedio", "confidence": 0.55, "reason": "Señales mixtas o insuficientes."}


def detect_level(user_text: str, code_context: Optional[str] = None) -> Dict[str, Any]:
    """Detecta nivel; usa LLM opcionalmente y cae a heurística si algo falla.

    Env:
        ENABLE_LEVEL_DETECTOR_LLM=1 para usar LLM además de heurística.

    Returns:
        dict: {level, confidence, reason, source}
    """
    h = _heuristic_level(user_text, code_context)

    if os.getenv("ENABLE_LEVEL_DETECTOR_LLM", "0") != "1":
        h["source"] = "heuristic"
        return h

    # LLM opcional (si tu router lo soporta)
    try:
        prompt = (
            "Clasifica el nivel del estudiante segun su mensaje y (si existe) el codigo. "
            "Responde SOLO con una palabra: basico, intermedio o avanzado.\n\n"
            f"MENSAJE:\n{user_text}\n\n"
            f"CODIGO (opcional):\n{code_context or ''}"
        )
        r = seleccionar_proveedor(prompt_system="Eres un clasificador de nivel académico. Responde solo: basico, intermedio o avanzado.", pregunta_user=prompt, max_tokens=8, modo_interaccion="normal", nivel="basica")
        raw = (r.get("respuesta") or "").strip().lower()
        # normalizar
        raw = re.sub(r"[^a-záéíóúñ]", "", raw)
        if raw in _LEVELS:
            return {
                "level": raw,
                "confidence": max(float(h.get("confidence", 0.55)), 0.72),
                "reason": "Clasificación LLM + heurística.",
                "source": "llm",
            }
    except Exception as e:
        logger.warning("Fallo level detector LLM, usando heurística", error=str(e))

    h["source"] = "heuristic_fallback"
    return h
