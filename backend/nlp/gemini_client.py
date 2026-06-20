"""
Proyecto: YELIA4AP
Archivo: backend/nlp/gemini_client.py
Descripción: Módulo del backend para la lógica asociada a esta carpeta/funcionalidad.

Revisión: 2026-02-10
"""
from __future__ import annotations

"""
Archivo: backend/nlp/gemini_client.py
Proyecto: YELIA4AP
Última revisión: 2026-02-10

Componentes de procesamiento de lenguaje natural (NLU/NLP) del backend.

Convenciones:
- Funciones pequeñas, nombres descriptivos y manejo de errores explícito.
- Evitar prints en producción: usar logging si aplica.
"""


#
# Archivo: backend/nlp/gemini_client.py
# Rol: Módulo del backend (Flask) de YELIA4AP.


"""Gemini Client
Archivo del backend del sistema YELIA4AP.

Responsabilidad:
- Implementa la lógica asociada a este módulo.

backend/nlp/gemini_client.py

Cliente Gemini (Google) — YELIA

Objetivo:
- Soportar 2 SDKs distintos (porque en PCs / labs a veces hay uno u otro):
  1) SDK NUEVO:   google-genai     -> from google import genai; client.models.generate_content(...)
  2) SDK CLÁSICO: google-generativeai -> import google.generativeai as genai; GenerativeModel(...).generate_content(...)

- Si no hay SDK o no hay API key, retorna "" (cadena vacía) para que el router use fallback.
"""
# =====================================
# Imports
# =====================================


import logging
from typing import Optional, Any


# =====================================
# Configuración / Constantes
# =====================================
from .config import GEMINI_API_KEY, GEMINI_MODEL

_logger = logging.getLogger(__name__)

# Flags de disponibilidad
_enabled: bool = False
_mode: str = "none"  # "google-genai" | "google-generativeai" | "none"

# Cliente / modelo (dependiendo del SDK)
_client: Optional[Any] = None
_model_obj: Optional[Any] = None

# ------------------------------------------------------
# Intento 1: SDK NUEVO (google-genai)
# ------------------------------------------------------
try:
    # Requiere: pip install google-genai
    from google import genai  # type: ignore
    from google.genai import types  # type: ignore

    if GEMINI_API_KEY:
        _client = genai.Client(api_key=GEMINI_API_KEY)
        _enabled = True
        _mode = "google-genai"
        _logger.info("Gemini listo (google-genai) | model=%s", GEMINI_MODEL)
    else:
        _logger.info("Gemini deshabilitado (GEMINI_API_KEY ausente)")

except Exception:
    # Si falla import o algo del SDK nuevo, probamos el clásico
    _client = None

# ------------------------------------------------------
# Intento 2: SDK CLÁSICO (google-generativeai)
# ------------------------------------------------------
if not _enabled:
    try:
        # Requiere: pip install google-generativeai
        import google.generativeai as genai_old  # type: ignore

        if GEMINI_API_KEY:
            genai_old.configure(api_key=GEMINI_API_KEY)
            _model_obj = genai_old.GenerativeModel(GEMINI_MODEL)
            _enabled = True
            _mode = "google-generativeai"
            _logger.info("Gemini listo (google-generativeai) | model=%s", GEMINI_MODEL)
        else:
            _logger.info("Gemini deshabilitado (GEMINI_API_KEY ausente)")

    except Exception:
        _model_obj = None
# =====================================
# Funciones / Clases
# =====================================



def llamar_gemini(
    prompt_system: str,
    pregunta_user: str,
    max_tokens: int,
    temperature: float = 0.3,
) -> str:
    """
    Retorna texto generado por Gemini.
    Devuelve "" si:
    - no está disponible Gemini (sin SDK o sin API key), o
    - hubo error al llamar al proveedor.
    """
    if not _enabled:
        return ""

    # Unimos system + user para el SDK clásico, o usamos config/system_instruction en el nuevo
    try:
        if _mode == "google-genai":
            # SDK NUEVO
            from google.genai import types  # type: ignore

            if _client is None:
                return ""

            resp = _client.models.generate_content(
                model=GEMINI_MODEL,
                contents=pregunta_user,
                config=types.GenerateContentConfig(
                    system_instruction=prompt_system,
                    temperature=float(temperature),
                    max_output_tokens=int(max_tokens),
                    top_p=0.9,
                ),
            )

            # resp.text suele venir listo
            text = getattr(resp, "text", "") or ""
            return str(text).strip()

        # SDK CLÁSICO
        if _model_obj is None:
            return ""

        prompt = f"{prompt_system}\n\nUsuario:\n{pregunta_user}".strip()
        resp = _model_obj.generate_content(
            prompt,
            generation_config={
                "temperature": float(temperature),
                "max_output_tokens": int(max_tokens),
                "top_p": 0.9,
            },
        )

        # resp.text en google-generativeai
        text = getattr(resp, "text", "") or ""
        return str(text).strip()

    except Exception as e:
        _logger.exception("Error llamando Gemini | mode=%s | err=%s", _mode, str(e))
        return ""
