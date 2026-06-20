"""
Proyecto: YELIA4AP
Archivo: backend/nlp/config.py
Descripción: Configuración central del backend (credenciales, variables de entorno y constantes).

Revisión: 2026-02-10
"""
from __future__ import annotations

"""Config
Archivo del backend del sistema YELIA4AP.

Responsabilidad:
- Implementa la lógica asociada a este módulo.
"""

#
# Archivo: backend/nlp/config.py
# Rol: Módulo del backend (Flask) de YELIA4AP.


# =====================================
# Imports
# =====================================

import os
from dotenv import load_dotenv
from cachetools import TTLCache
import structlog

# ------------------------------------------------------
# Cargar variables de entorno
# ------------------------------------------------------
# Se carga `.env` (si existe) al entorno del proceso. Esto habilita `os.getenv(...)`
# sin que el resto de módulos necesite conocer la ruta del archivo.

# =====================================
# Configuración / Constantes
# =====================================
load_dotenv()

# ------------------------------------------------------
# Logging estructurado
# ------------------------------------------------------
logger = structlog.get_logger(__name__)

# ------------------------------------------------------
# Cache global NLP
# ------------------------------------------------------
# Caché con:
# - `maxsize`: número máximo de entradas.
# - `ttl`: tiempo de vida por entrada (segundos).
# Ambos se parametrizan por entorno para ajuste sin cambios de código.
NLP_CACHE = TTLCache(
    maxsize=int(os.getenv("NLP_CACHE_MAXSIZE", 256)),
    ttl=int(os.getenv("NLP_CACHE_TTL_S", 300)),
)

# ------------------------------------------------------
# Timeout global para LLMs
# ------------------------------------------------------
# Timeouts (segundos) por proveedor, para evitar bloqueos por latencia/red.
GROQ_TIMEOUT_S = int(os.getenv("GROQ_TIMEOUT_S", 20))
DEEPSEEK_TIMEOUT_S = int(os.getenv("DEEPSEEK_TIMEOUT_S", 20))
OPENAI_TIMEOUT_S = int(os.getenv("OPENAI_TIMEOUT_S", 20))
GEMINI_TIMEOUT_S = int(os.getenv("GEMINI_TIMEOUT_S", 20))

# ------------------------------------------------------
# ================= GROQ ===============================
# ------------------------------------------------------
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

if GROQ_API_KEY:
    logger.info("Groq configurado", model=GROQ_MODEL)
else:
    logger.warning("GROQ_API_KEY no configurada")

# ------------------------------------------------------
# ================ DEEPSEEK =============================
# ------------------------------------------------------
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_BASE_URL = os.getenv(
    "DEEPSEEK_BASE_URL",
    "https://api.deepseek.com/v1"
)
DEEPSEEK_MODEL = os.getenv(
    "DEEPSEEK_MODEL",
    "deepseek-chat"
)

if DEEPSEEK_API_KEY:
    logger.info(
        "DeepSeek configurado",
        model=DEEPSEEK_MODEL,
        base_url=DEEPSEEK_BASE_URL,
    )
else:
    logger.warning("DEEPSEEK_API_KEY no configurada")

# ------------------------------------------------------
# ================= GEMINI (Google) ====================
# ------------------------------------------------------
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv(
    "GEMINI_MODEL",
    "gemini-2.0-flash",
)

if GEMINI_API_KEY:
    logger.info("Gemini configurado", model=GEMINI_MODEL)
else:
    logger.warning("GEMINI_API_KEY no configurada")

# ------------------------------------------------------
# ================= OPENAI (respaldo) ==================
# ------------------------------------------------------
# Proveedor opcional (puede estar vacío sin afectar el flujo).
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "")

if OPENAI_API_KEY:
    logger.info("OpenAI configurado", model=OPENAI_MODEL)
else:
    logger.info("OPENAI_API_KEY no configurada (respaldo)")

# ------------------------------------------------------
# Flags de disponibilidad (clave para el orquestador)
# ------------------------------------------------------
# `PROVIDERS_AVAILABLE` guía la selección de proveedor según credenciales presentes.
PROVIDERS_AVAILABLE = {
    "groq": bool(GROQ_API_KEY),
    "deepseek": bool(DEEPSEEK_API_KEY),
    "gemini": bool(GEMINI_API_KEY),
    "openai": bool(OPENAI_API_KEY),
    # (Ollama removido)
}

# ------------------------------------------------------
# Compatibilidad defensiva (evita ImportError legacy)
# ------------------------------------------------------
# Se conserva como símbolo para código antiguo/pruebas. No se usa dentro del módulo.
client = None
