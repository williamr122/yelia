"""
Proyecto: YELIA4AP
Archivo: backend/config.py
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
# Archivo: backend/config.py
# Rol: Módulo del backend (Flask) de YELIA4AP.



# ============================================================
# IMPORTACIONES
# ============================================================

import os
from functools import lru_cache

try:
    from groq import Groq  # type: ignore
except Exception:  # pragma: no cover
    Groq = None  # type: ignore

# ============================================================
# CONFIGURACIÓN OPERATIVA (DEMO / HOSTING)
# ============================================================

# Entorno y debug (útiles para demo/hosting)
ENV: str = os.getenv("ENV", "demo").strip().lower()
DEBUG: bool = os.getenv("DEBUG", "0").strip() == "1"

# Prefijo uniforme para endpoints API (evita rutas inconsistentes)
API_PREFIX: str = os.getenv("API_PREFIX", "/api").strip() or "/api"

# Límites del chat (estabilidad en demo)
MAX_HISTORY: int = int(os.getenv("MAX_HISTORY", "10"))
MAX_MESSAGE_LENGTH: int = int(os.getenv("MAX_MESSAGE_LENGTH", "20000"))

# Nivel de logs (si lo usas en app.py)
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").upper().strip()


# ============================================================
# CLIENTE GROQ (compatibilidad SIN romper arranque)
# ============================================================

# Si no existe GROQ_API_KEY, no inicializar para evitar crash al importar el módulo.
_groq_key = (os.getenv("GROQ_API_KEY") or "").strip()
client = Groq(api_key=_groq_key) if (_groq_key and Groq is not None) else None


# ============================================================
# CACHÉ / OPTIMIZACIÓN
# ============================================================

@lru_cache(maxsize=128)
def cache(prompt: str):
    """Retorna el `prompt` recibido, aprovechando un caché LRU.

    Importante (fidelidad al comportamiento real):
        Esta función NO genera respuestas ni ejecuta llamadas a modelos.
        En la implementación actual devuelve exactamente el texto de entrada.

    Args:
        prompt: Texto de entrada que se desea cachear.

    Returns:
        El mismo `prompt` recibido (sin modificar).
    """
    return prompt
