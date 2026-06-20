"""
Proyecto: YELIA4AP
Archivo: backend/services/nlp_service.py
Descripción: Módulo del backend para la lógica asociada a esta carpeta/funcionalidad.

Revisión: 2026-02-10
"""
from __future__ import annotations

"""
Archivo: backend/services/nlp_service.py
Proyecto: YELIA4AP
Última revisión: 2026-02-10

Módulo de backend en Python.

Convenciones:
- Funciones pequeñas, nombres descriptivos y manejo de errores explícito.
- Evitar prints en producción: usar logging si aplica.
"""


#
# Archivo: backend/services/nlp_service.py
# Rol: Módulo del backend (Flask) de YELIA4AP.


"""Nlp Service
Archivo del backend del sistema YELIA4AP.

Responsabilidad:
- Implementa la lógica asociada a este módulo.

backend/services/nlp_service.py

Backend Flask — YELIA (módulo de servidor)

Propósito:
    Este archivo pertenece al backend (Flask) de YELIA. Contiene lógica de servidor
    y/o utilidades que soportan rutas, servicios, persistencia y orquestación NLP.
Rol de este archivo:
    Proveer un servicio de alto nivel para generar respuestas educativas
    utilizando el motor NLP subyacente.
Motivación del diseño:
    - Actuar como una capa de abstracción entre las rutas HTTP y el núcleo NLP.
    - Evitar que las rutas importen directamente el core NLP.
    - Mantener estabilidad de imports existentes.
    - Facilitar futuros cambios sin tocar las rutas.
Enfoque profesional:
    Este wrapper no agrega lógica adicional. Su existencia refuerza la arquitectura
    por capas y mejora la mantenibilidad del código.
"""


# backend/services/nlp_service.py
# ============================================================
# PROPÓSITO:
#   Exponer un servicio de alto nivel para generar respuestas
#   educativas a través del motor NLP.
#
# ROL DE ESTE ARCHIVO:
#   Actúa como una capa de abstracción (service layer) entre:
#   - routes (HTTP / Blueprints)
#   - y el núcleo NLP (backend.nlp.core)
#
# MOTIVACIÓN DEL DISEÑO:
#   - Evitar que las rutas importen directamente el core NLP
#   - Mantener estabilidad de imports existentes
#   - Facilitar futuros cambios sin tocar las rutas
#
# ENFOQUE PROFESIONAL:
#   Este wrapper no agrega lógica adicional.
#   Su existencia refuerza la arquitectura por capas.
# ============================================================


from typing import List, Dict, Any, Optional

# Función principal del motor NLP
from backend.nlp.core import procesar_consulta_educativa


def generar_respuesta_educativa(
    usuario: str,
    pregunta: str,
    historial: Optional[List[Dict[str, Any]]] = None,
    *,
    nivel_explicacion: str = "basica",
    ciclo_academico: Optional[str] = None,
    estado_materia: Optional[str] = None,
) -> Dict[str, Any]:
    """Servicio de generación de respuesta educativa.

    Parámetros:
    - usuario: identificador del estudiante
    - pregunta: texto de la consulta
    - historial: historial conversacional previo (opcional)
    - nivel_explicacion: nivel deseado de detalle (básica / avanzada)
    - ciclo_academico: ciclo o semestre del estudiante (opcional)
    - estado_materia: relación del estudiante con la materia (opcional)

    Comportamiento:
    - Normaliza el historial si no se envía
    - Delegates completamente la lógica al motor NLP
    - Devuelve una respuesta estructurada (dict)

    Nota de compatibilidad:
    - Este wrapper se mantiene para no romper imports
      existentes en rutas o controladores.

    Args:
        usuario: Parámetro de entrada.
        pregunta: Parámetro de entrada.
        historial: Historial de conversación.

    Returns:
        Valor retornado por la función.
    """
    # Garantiza que historial siempre sea una lista
    historial = historial or []

    # Delegación directa al núcleo NLP
    return procesar_consulta_educativa(
        pregunta=pregunta,
        historial=historial,
        nivel_explicacion=nivel_explicacion,
        usuario=usuario,
        ciclo_academico=ciclo_academico,
        estado_materia=estado_materia,
    )
