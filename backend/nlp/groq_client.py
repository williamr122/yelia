"""
Proyecto: YELIA4AP
Archivo: backend/nlp/groq_client.py
Descripción: Módulo del backend para la lógica asociada a esta carpeta/funcionalidad.

Revisión: 2026-02-10
"""
from __future__ import annotations

"""
Archivo: backend/nlp/groq_client.py
Proyecto: YELIA4AP
Última revisión: 2026-02-10

Componentes de procesamiento de lenguaje natural (NLU/NLP) del backend.

Convenciones:
- Funciones pequeñas, nombres descriptivos y manejo de errores explícito.
- Evitar prints en producción: usar logging si aplica.
"""


#
# Archivo: backend/nlp/groq_client.py
# Rol: Módulo del backend (Flask) de YELIA4AP.


"""Groq Client
Archivo del backend del sistema YELIA4AP.

Responsabilidad:
- Implementa la lógica asociada a este módulo.

backend/nlp/groq_client.py

Cliente Groq — YELIA4AP

Problema típico en entornos académicos:
- No siempre están instalados `groq` o `structlog`.
- El backend no debería "romper" por eso: si falta el SDK o la API key,
  simplemente se deshabilita Groq y se usa el fallback (p. ej. proveedor local).

Este módulo:
- Importa Groq de forma segura.
- Usa logging estándar si no existe `structlog`.
- Implementa reintentos simples sin depender de `retrying`.
- Expone `llamar_groq(...)` que retorna "" si Groq no está disponible.

Nota de tipado (VSCode/Pylance):
- A veces subraya `.chat.completions.create` porque `_client` es Optional.
  Para que el type-narrowing funcione, copiamos `_client` a una variable local
  dentro de `llamar_groq`.
"""
# =====================================
# Imports
# =====================================


import time
import logging
from typing import Optional, Any, Callable, TypeVar


# =====================================
# Configuración / Constantes
# =====================================
from .config import GROQ_API_KEY, GROQ_MODEL, GROQ_TIMEOUT_S

# ------------------------------------------------------
# Logger: structlog opcional (fallback a logging)
# ------------------------------------------------------
try:
    import structlog  # type: ignore[import-not-found]

    _slogger = structlog.get_logger(__name__)
# =====================================
# Funciones / Clases
# =====================================


    def _log_info(msg: str, **kw: Any) -> None:
        _slogger.info(msg, **kw)

    def _log_warning(msg: str, **kw: Any) -> None:
        _slogger.warning(msg, **kw)

    def _log_error(msg: str, **kw: Any) -> None:
        _slogger.error(msg, **kw)

except Exception:
    _logger = logging.getLogger(__name__)

    def _log_info(msg: str, **kw: Any) -> None:
        _logger.info("%s | %s", msg, kw if kw else "")

    def _log_warning(msg: str, **kw: Any) -> None:
        _logger.warning("%s | %s", msg, kw if kw else "")

    def _log_error(msg: str, **kw: Any) -> None:
        _logger.error("%s | %s", msg, kw if kw else "")


# ------------------------------------------------------
# SDK Groq opcional
# ------------------------------------------------------
try:
    from groq import Groq  # type: ignore[import-not-found]
except Exception:  # pragma: no cover
    Groq = None  # type: ignore[assignment]


_client: Optional[Any] = None
_enabled: bool = False

if GROQ_API_KEY and Groq is not None:
    try:
        _client = Groq(api_key=GROQ_API_KEY)
        _enabled = True
        _log_info("Cliente Groq inicializado", model=GROQ_MODEL)
    except Exception as e:  # pragma: no cover
        _client = None
        _enabled = False
        _log_warning("No se pudo inicializar Groq; se deshabilita", error=str(e))
else:
    _client = None
    _enabled = False
    if not GROQ_API_KEY:
        _log_info("Groq deshabilitado (API key ausente)")
    else:
        _log_info("Groq deshabilitado (SDK 'groq' no instalado)")


def _should_retry(exc: Exception) -> bool:
    """Decide si una excepción amerita reintento."""
    msg = (str(exc) or "").lower()
    # No reintentar auth
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


def llamar_groq(
    prompt_system: str,
    pregunta_user: str,
    max_tokens: int,
    temperature: float = 0.3,
) -> str:
    """Envía una consulta al modelo Groq y devuelve el texto generado.

    Retorna "" (cadena vacía) si:
    - Groq no está disponible (sin SDK o sin API key), o
    - ocurre un error definitivo.
    """
    if not _enabled or _client is None:
        return ""

    # ✅ type-narrowing para VSCode/Pylance
    client = _client

    def _do_call() -> Any:
        # Algunos SDKs aceptan `timeout`, otros no.
        try:
            return client.chat.completions.create(
                model=GROQ_MODEL,
                messages=[
                    {"role": "system", "content": prompt_system},
                    {"role": "user", "content": pregunta_user},
                ],
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=0.9,
                timeout=GROQ_TIMEOUT_S,
            )
        except TypeError:
            return client.chat.completions.create(
                model=GROQ_MODEL,
                messages=[
                    {"role": "system", "content": prompt_system},
                    {"role": "user", "content": pregunta_user},
                ],
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=0.9,
            )

    try:
        response = _retry_call(_do_call, attempts=2, wait_s=0.8)
    except Exception as e:
        # Log explícito para diagnosticar por qué se activa la respuesta local.
        # No se lanza la excepción para no romper el chat; el router probará otros proveedores.
        _log_error("Error al llamar a Groq", error=str(e), error_type=type(e).__name__, model=GROQ_MODEL)
        return ""

    choices = getattr(response, "choices", None)
    if not choices:
        return ""

    # Parse defensivo (objeto o dict)
    first = choices[0]
    if isinstance(first, dict):
        content = (((first.get("message") or {}).get("content")) or "").strip()
        return content

    message = getattr(first, "message", None)
    content = getattr(message, "content", "") if message else ""
    return (content or "").strip()
