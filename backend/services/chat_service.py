"""
Proyecto: YELIA4AP
Archivo: backend/services/chat_service.py
Descripción: Módulo del backend para la lógica asociada a esta carpeta/funcionalidad.

Revisión: 2026-02-10
"""
from __future__ import annotations

"""
Archivo: backend/services/chat_service.py
Proyecto: YELIA4AP
Última revisión: 2026-02-10

Interacciones del chat: envío, recepción y render de mensajes.

Convenciones:
- Funciones pequeñas, nombres descriptivos y manejo de errores explícito.
- Evitar prints en producción: usar logging si aplica.
"""


#
# Archivo: backend/services/chat_service.py
# Rol: Módulo del backend (Flask) de YELIA4AP.


"""Chat Service
Archivo del backend del sistema YELIA4AP.

Responsabilidad:
- Implementa la lógica asociada a este módulo.

backend/services/chat_service.py

Backend Flask — YELIA (módulo de servidor)

Propósito:
    Este archivo pertenece al backend (Flask) de YELIA. Contiene lógica de servidor
    y/o utilidades que soportan rutas, servicios, persistencia y orquestación NLP.
    En particular, este módulo implementa la lógica de negocio del chat educativo.
    Actúa como intermediario entre las rutas HTTP y el servicio NLP, gestionando
    la validación y normalización de datos, así como el ajuste del nivel de explicación
    según el feedback previo del usuario.
"""


# backend/services/chat_service.py
# ============================================================
# PROPÓSITO:
#   Implementar la lógica de negocio del chat educativo.
#
# ROL DE ESTE SERVICIO:
#   - Actúa como intermediario entre routes y NLP
#   - Valida y normaliza datos de entrada
#   - Ajusta el nivel de explicación según feedback previo
#   - Devuelve una respuesta estructurada y consistente
#
# ENFOQUE PROFESIONAL:
#   Este archivo concentra decisiones de negocio del chat,
#   NO lógica HTTP ni acceso directo a base de datos.
# ============================================================


from typing import List, Dict, Any, Optional

# Servicio NLP de alto nivel
from backend.services.nlp_service import generar_respuesta_educativa

# Repositorio de métricas (feedback de claridad)
from backend.repositories.metrics_repo import get_latest_clarity_for_user



def _normalizar_nivel_explicacion(nivel: str) -> str:
    """
    Normaliza niveles que pueden venir desde UI.

    Acepta: "Básico", "Intermedio", "Avanzado", "Sin conocimientos", "basica", "avanzada".
    Retorna solo: "basica" | "avanzada".
    """
    n = (nivel or "").strip().lower()
    if not n:
        return "basica"
    if n in {"avanzada", "avanzado", "advanced"}:
        return "avanzada"
    # Intermedio y Sin conocimientos se tratan como "basica" internamente
    if n in {"intermedio", "medio", "sin conocimientos", "sin_conocimientos", "ninguno", "cero"}:
        return "basica"
    if n in {"basica", "básica", "basico", "básico", "basic"}:
        return "basica"
    return "basica"
def _ajustar_nivel_por_feedback(nivel_actual: str, clarity: Optional[int]) -> str:
    """Ajusta automáticamente el nivel de explicación según feedback previo.

    Regla actual:
    - clarity == 0 (👎) → bajar el nivel a 'basica'
    - cualquier otro caso → mantener el nivel actual

    Nota:
    - Esta lógica es simple por diseño.
    - Permite mejorar la experiencia sin intervención del usuario.

    Args:
        nivel_actual: Parámetro de entrada.
        clarity: Parámetro de entrada.

    Returns:
        Valor tipo str.
    """
    # clarity=0 (👎) -> baja a basica
    if clarity == 0:
        return "basica"
    return nivel_actual


def procesar_mensaje_chat(
    *,
    usuario: str,
    mensaje: str,
    historial: Optional[List[Dict[str, Any]]] = None,
    nivel_explicacion: str = "basica",
    ciclo_academico: Optional[str] = None,
    estado_materia: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Procesa un mensaje del chat y genera una respuesta educativa.

    Parámetros:
    - usuario: identificador del estudiante
    - mensaje: texto enviado por el usuario
    - historial: historial conversacional previo (opcional)
    - nivel_explicacion: nivel inicial solicitado
    - ciclo_academico / estado_materia: contexto académico opcional

    Retorna:
    - Diccionario estructurado con la respuesta del chat
    """

    # --------------------------------------------------------
    # 1) Normalización básica de entrada
    # --------------------------------------------------------
    historial = historial or []
    usuario = (usuario or "guest").strip()
    mensaje = (mensaje or "").strip()

    # Caso borde: mensaje vacío
    if not mensaje:
        return {
            "ok": False,
            "usuario": usuario,
            "pregunta": "",
            "respuesta": "Escríbeme tu duda de Programación Avanzada 😊",
            "tema": "Programación Avanzada",
            "nivel": nivel_explicacion,
            "modo": "error",
            "modo_interaccion": "normal",
            "intencion": "otro",
        }

        # Normaliza nivel (puede venir como etiqueta desde UI)
    nivel_explicacion = _normalizar_nivel_explicacion(nivel_explicacion)

# --------------------------------------------------------
    # 2) Nivel 3 – Ajuste automático por feedback previo
    # --------------------------------------------------------
    # Se consulta el último feedback del usuario (si existe).
    # Si ocurre un error, se ignora para no romper el flujo.
    clarity = None
    try:
        clarity = get_latest_clarity_for_user(usuario)
    except Exception:
        clarity = None

    nivel_final = _ajustar_nivel_por_feedback(nivel_explicacion, clarity)

    # --------------------------------------------------------
    # 3) Generación de respuesta educativa (NLP)
    # --------------------------------------------------------
    resultado = generar_respuesta_educativa(
        usuario=usuario,
        pregunta=mensaje,
        historial=historial,
        nivel_explicacion=nivel_final,
        ciclo_academico=ciclo_academico,
        estado_materia=estado_materia,
    )

    # --------------------------------------------------------
    # 4) Construcción de la respuesta final del chat
    # --------------------------------------------------------
    return {
        "ok": True,
        "usuario": usuario,
        "pregunta": mensaje,
        "respuesta": resultado.get("respuesta", ""),
        "tema": resultado.get("tema") or "Programación Avanzada",
        "nivel": resultado.get("nivel", nivel_final),
        "modo": resultado.get("modo", "error"),
        "modo_interaccion": resultado.get("modo_interaccion", "normal"),
        "intencion": resultado.get("intencion", "otro"),

        # Información adicional útil para depuración y analítica
        "profile_used": {
            "nivel_explicacion": nivel_final,
            "clarity": clarity
        },
    }
