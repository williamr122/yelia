"""
Proyecto: YELIA4AP
Archivo: backend/nlp/deepseek_client.py
Descripción: Módulo del backend para la lógica asociada a esta carpeta/funcionalidad.

Revisión: 2026-02-10
"""
from __future__ import annotations

"""
Archivo: backend/nlp/deepseek_client.py
Proyecto: YELIA4AP
Última revisión: 2026-02-10

Componentes de procesamiento de lenguaje natural (NLU/NLP) del backend.

Convenciones:
- Funciones pequeñas, nombres descriptivos y manejo de errores explícito.
- Evitar prints en producción: usar logging si aplica.
"""


#
# Archivo: backend/nlp/deepseek_client.py
# Rol: Módulo del backend (Flask) de YELIA4AP.


"""Deepseek Client
Archivo del backend del sistema YELIA4AP.

Responsabilidad:
- Implementa la lógica asociada a este módulo.

backend/nlp/deepseek_client.py

Cliente DeepSeek (OpenAI-compatible) — YELIA

✅ Objetivo de este módulo
- Inicializar DeepSeek de forma *robusta* (sin “falsos negativos”).
- Si DeepSeek no está disponible, devolver "" para que el router haga fallback
  (Gemini → Groq → Local) sin romper la app.

Problema que estabas viendo
- Tu app estaba mostrando mensajes tipo “openai no instalado” aunque SÍ lo tenías.
- La causa típica es un manejo de excepciones demasiado amplio en el import
  (captura cualquier error y asume que falta el paquete).

Este archivo:
- Distingue ModuleNotFoundError (no instalado) de otros errores (shadowing, rutas, etc.).
- Loguea *de forma útil* qué módulo `openai` se cargó (ruta/version) cuando falla.
- Soporta `base_url` de DeepSeek con el SDK `openai` moderno.

Variables (config.py):
- DEEPSEEK_API_KEY
- DEEPSEEK_BASE_URL (ej: https://api.deepseek.com/v1)
- DEEPSEEK_MODEL (ej: deepseek-chat)
- DEEPSEEK_TIMEOUT_S (opcional)
"""
# =====================================
# Imports
# =====================================


import os
import time
import logging
import importlib.util
from typing import Any, Callable, Optional, TypeVar


# =====================================
# Configuración / Constantes
# =====================================
from .config import (
    DEEPSEEK_API_KEY,
    DEEPSEEK_BASE_URL,
    DEEPSEEK_MODEL,
    DEEPSEEK_TIMEOUT_S,
)

logger = logging.getLogger(__name__)

OpenAI = None  # type: ignore[assignment]
_openai_import_error: Optional[str] = None
_openai_module_path: Optional[str] = None
_openai_version: Optional[str] = None
# =====================================
# Funciones / Clases
# =====================================



def _try_import_openai() -> None:
    """Importa OpenAI SDK y guarda metadata útil para debug."""
    global OpenAI, _openai_import_error, _openai_module_path, _openai_version

    spec = importlib.util.find_spec("openai")
    if spec is None:
        _openai_import_error = "ModuleNotFoundError: openai (find_spec returned None)"
        return

    try:
        import openai  # type: ignore
        _openai_module_path = getattr(openai, "__file__", None)
        _openai_version = getattr(openai, "__version__", None)

        # Import oficial (openai>=1.x/2.x)
        from openai import OpenAI as _OpenAI  # type: ignore

        OpenAI = _OpenAI
        _openai_import_error = None
    except ModuleNotFoundError as e:
        # Este caso es raro si find_spec ya encontró algo, pero lo distinguimos igual.
        _openai_import_error = f"ModuleNotFoundError: {e}"
    except Exception as e:
        # Cualquier otra cosa (shadowing, instalación corrupta, etc.)
        _openai_import_error = f"{type(e).__name__}: {e}"


_try_import_openai()

_client: Optional[Any] = None
_enabled: bool = False


def _debug_openai_hint() -> str:
    """Devuelve un string corto para el log cuando algo falla."""
    parts = []
    if _openai_version:
        parts.append(f"openai_version={_openai_version}")
    if _openai_module_path:
        parts.append(f"openai_path={_openai_module_path}")
    if _openai_import_error:
        parts.append(f"import_error={_openai_import_error}")
    return " | ".join(parts)


def _init_client() -> Optional[Any]:
    """Inicializa el cliente DeepSeek de manera defensiva."""
    if not DEEPSEEK_API_KEY:
        logger.warning("DeepSeek deshabilitado: DEEPSEEK_API_KEY vacío/no configurado")
        return None

    if OpenAI is None:
        logger.warning("DeepSeek deshabilitado: no se pudo importar OpenAI SDK. %s", _debug_openai_hint())
        return None

    # Camino moderno: OpenAI(api_key=..., base_url=...)
    try:
        return OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)
    except TypeError as e:
        # Fallback: constructor no acepta base_url (u otra firma)
        try:
            c = OpenAI(api_key=DEEPSEEK_API_KEY)
            # Intento best-effort de setear base_url
            try:
                setattr(c, "base_url", DEEPSEEK_BASE_URL)
            except Exception:
                pass
            logger.warning(
                "DeepSeek: OpenAI() no aceptó base_url (TypeError). Se usó fallback set base_url. err=%s | %s",
                str(e),
                _debug_openai_hint(),
            )
            return c
        except Exception as e2:
            logger.exception("DeepSeek: fallo inicializando cliente (fallback). %s", _debug_openai_hint())
            logger.warning("DeepSeek deshabilitado: %s", str(e2))
            return None
    except Exception:
        logger.exception("DeepSeek: error inesperado inicializando cliente. %s", _debug_openai_hint())
        return None


# Inicialización global (import-time)
_client = _init_client()
_enabled = _client is not None
if _enabled:
    logger.info("DeepSeek cliente listo | base_url=%s | model=%s", DEEPSEEK_BASE_URL, DEEPSEEK_MODEL)
else:
    # Útil para entender POR QUÉ se fue a fallback sin adivinar
    logger.warning("DeepSeek NO inicializado (fallback activo). %s", _debug_openai_hint())


def _should_retry(exc: Exception) -> bool:
    msg = (str(exc) or "").lower()
    # No reintentar errores de auth
    if any(x in msg for x in ("401", "403", "unauthorized", "invalid api key", "forbidden")):
        return False
    return True


T = TypeVar("T")


def _retry_call(
    fn: Callable[[], T],
    attempts: int = 2,
    wait_s: float = 0.8,
    retry_predicate: Callable[[Exception], bool] = _should_retry,
) -> T:
    last: Optional[Exception] = None
    attempts = max(1, attempts)
    for i in range(attempts):
        try:
            return fn()
        except Exception as e:
            last = e
            if i >= attempts - 1 or not retry_predicate(e):
                raise
            time.sleep(wait_s)
    assert last is not None
    raise last


def llamar_deepseek(
    prompt_system: str,
    pregunta_user: str,
    max_tokens: int,
    temperature: float = 0.3,
) -> str:
    """Llama a DeepSeek (chat completions). Retorna texto o "" si falla."""
    if not _enabled or _client is None:
        return ""

    client = _client  # type: ignore[assignment]

    def _do_call() -> Any:
        # DeepSeek es compatible con OpenAI Chat Completions.
        kwargs = dict(
            model=DEEPSEEK_MODEL,
            messages=[
                {"role": "system", "content": prompt_system},
                {"role": "user", "content": pregunta_user},
            ],
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=0.9,
        )
        # Algunas versiones aceptan timeout, otras no.
        if DEEPSEEK_TIMEOUT_S:
            kwargs["timeout"] = DEEPSEEK_TIMEOUT_S
        return client.chat.completions.create(**kwargs)

    attempts = int(os.getenv("DEEPSEEK_ATTEMPTS", "1") or "1")
    try:
        response = _retry_call(_do_call, attempts=attempts, wait_s=0.2)
    except Exception:
        logger.exception("DeepSeek: error al llamar. %s", _debug_openai_hint())
        raise

    choices = getattr(response, "choices", None)
    if not choices:
        return ""

    first = choices[0]
    if isinstance(first, dict):
        content = (((first.get("message") or {}).get("content")) or "").strip()
        return content

    message = getattr(first, "message", None)
    content = getattr(message, "content", "") if message else ""
    return (content or "").strip()
