"""
Proyecto: YELIA4AP
Archivo: backend/services/temas_service.py
Descripción: Módulo del backend para la lógica asociada a esta carpeta/funcionalidad.

Revisión: 2026-02-10
"""
"""Temas Service
Archivo del backend del sistema YELIA4AP.

Responsabilidad:
- Implementa la lógica asociada a este módulo.
"""

#
# Archivo: backend/services/temas_service.py
# Rol: Módulo del backend (Flask) de YELIA4AP.

"""backend/services/temas_service.py

Backend Flask — YELIA (módulo de servidor)

Propósito:
    Este archivo pertenece al backend (Flask) de YELIA. Contiene lógica de servidor
    y/o utilidades que soportan rutas, servicios, persistencia y orquestación NLP.
Responsabilidades:
    - Gestionar el catálogo de temas académicos (temas.json)
    - Proveer funciones para identificar temas desde texto de usuario
    - Mantener un caché en memoria para eficiencia
Notas:
    - Este módulo NO genera respuestas del chatbot.
    - Su función es únicamente clasificar / sugerir un tema
      para guiar el flujo pedagógico del NLP.
"""

# ============================================
# backend/services/temas_service.py
# --------------------------------------------
# PROPÓSITO DEL MÓDULO:
#   Administrar el catálogo de temas académicos (temas.json)
#   que utiliza YELIA para orientar la conversación educativa.
#
# RESPONSABILIDADES CLAVE:
#   1) Cargar los temas desde un archivo JSON externo
#   2) Aplanar la estructura jerárquica (Unidades → Temas)
#   3) Mantener un caché en memoria para eficiencia
#   4) Detectar el tema más probable a partir del texto del usuario
#
# IMPORTANTE:
#   - Este módulo NO genera respuestas del chatbot.
#   - Su función es únicamente clasificar / sugerir un tema
#     para guiar el flujo pedagógico del NLP.
#
# ENFOQUE PROFESIONAL:
#   El diseño prioriza:
#   - Simplicidad
#   - Explicabilidad (ideal para tesis)
#   - Bajo costo computacional
# ============================================

import json
import os
from typing import List, Dict, Any
import structlog

logger = structlog.get_logger()

# ------------------------------------------------------------
# SECCIÓN 1: RUTAS Y UBICACIÓN DEL PROYECTO
# ------------------------------------------------------------
# BASE_DIR apunta al directorio raíz del proyecto (yelia/)
#
# __file__  -> ruta de este archivo (backend/services/temas_service.py)
# ".."      -> sube un nivel (backend → yelia)
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# Ruta absoluta al archivo temas.json (yelia/temas.json)
TEMAS_PATH = os.path.join(BASE_DIR, "temas.json")

# ------------------------------------------------------------
# SECCIÓN 2: ESTADO EN MEMORIA (CACHÉ)
# ------------------------------------------------------------
# Lista plana de temas disponibles.
# Cada elemento contiene información suficiente para orientar al NLP.
TEMAS_DISPONIBLES: List[Dict[str, Any]] = []

# Flags de control de caché:
# - _TEMAS_CARGADOS: indica si ya se realizó la carga inicial
# - _TEMAS_MTIME: fecha de última modificación del archivo temas.json
#   Se usa para detectar cambios y recargar solo cuando es necesario.
_TEMAS_CARGADOS: bool = False
_TEMAS_MTIME: float = 0.0

# Índice auxiliar para búsqueda rápida de nombres de temas:
#   clave  -> nombre normalizado (minúsculas, sin espacios)
#   valor  -> nombre real del tema
#
# Permite detección eficiente cuando el usuario menciona
# explícitamente el nombre de un tema.
_TEMAS_NOMBRES_IDX: Dict[str, str] = {}


# ------------------------------------------------------------
# SECCIÓN 3: UTILIDADES INTERNAS
# ------------------------------------------------------------
def _normalizar(s: str) -> str:
    """Normaliza texto para comparaciones rápidas.

    Transformaciones:
    - Elimina espacios al inicio y fin
    - Convierte a minúsculas
    - Elimina espacios internos

    Ejemplo:
    "Clases y Objetos" → "clasesyobjetos"

    Beneficio:
    - Comparaciones robustas sin depender del formato del texto.

    Args:
        s: Texto de entrada.

    Returns:
        Valor tipo str.
    """
    return (s or "").strip().lower().replace(" ", "")


def _reconstruir_indices() -> None:
    """
    Reconstruye los índices internos a partir de TEMAS_DISPONIBLES.

    Construye:
    - _TEMAS_NOMBRES_IDX: { nombre_normalizado : nombre_real }

    Uso:
    - Permite detectar coincidencias exactas o parciales
      sin recorrer estructuras complejas cada vez.
    """
    global _TEMAS_NOMBRES_IDX
    _TEMAS_NOMBRES_IDX = {}

    for t in TEMAS_DISPONIBLES:
        if not isinstance(t, dict):
            continue

        nombre = (t.get("nombre") or "").strip()
        if not nombre:
            continue

        key = _normalizar(nombre)

        # Si hay colisiones de normalización,
        # se conserva el primer tema encontrado
        if key and key not in _TEMAS_NOMBRES_IDX:
            _TEMAS_NOMBRES_IDX[key] = nombre


# ------------------------------------------------------------
# SECCIÓN 4: CARGA DE TEMAS DESDE temas.json
# ------------------------------------------------------------
def cargar_temas(force: bool = False) -> None:
    """Carga los temas desde temas.json hacia memoria.

    ESTRUCTURA ESPERADA DEL JSON:
    {
      "Unidades": [
        {
          "nombre": "...",
          "temas": [
            {"nombre": "...", "nivel": "...", "definición": "...", "ejemplo": "..."}
          ]
        }
      ]
    }

    OPTIMIZACIÓN (CACHE POR MTIME):
    - Si el archivo no cambió desde la última carga,
      no se vuelve a leer (a menos que force=True).

    Args:
        force: Parámetro de entrada.

    Returns:
        Valor retornado por la función.
    """
    global TEMAS_DISPONIBLES, _TEMAS_CARGADOS, _TEMAS_MTIME

    # 4.1) Si el archivo no existe, el sistema no falla
    if not os.path.exists(TEMAS_PATH):
        logger.warning("No se encontró temas.json", path=TEMAS_PATH)
        TEMAS_DISPONIBLES.clear()
        _TEMAS_CARGADOS = False
        _TEMAS_MTIME = 0.0
        _reconstruir_indices()
        return

    # 4.2) Obtener fecha de modificación del archivo
    try:
        mtime = os.path.getmtime(TEMAS_PATH)
    except Exception:
        mtime = 0.0

    # 4.3) Evitar recarga innecesaria si no hubo cambios
    if (
        not force
        and _TEMAS_CARGADOS
        and mtime
        and _TEMAS_MTIME
        and mtime == _TEMAS_MTIME
        and TEMAS_DISPONIBLES
    ):
        return

    # 4.4) Leer y parsear el archivo JSON
    try:
        with open(TEMAS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        logger.error("Error al leer temas.json", error=str(e), path=TEMAS_PATH)
        TEMAS_DISPONIBLES.clear()
        _TEMAS_CARGADOS = False
        _TEMAS_MTIME = 0.0
        _reconstruir_indices()
        return

    # 4.5) Aplanar estructura jerárquica (Unidades → Temas)
    temas_list: List[Dict[str, Any]] = []

    unidades = data.get("Unidades", [])
    if not isinstance(unidades, list):
        unidades = []

    for unidad in unidades:
        if not isinstance(unidad, dict):
            continue

        nombre_unidad = unidad.get("nombre", "Unidad sin nombre")
        temas = unidad.get("temas", [])

        if not isinstance(temas, list):
            temas = []

        for tema in temas:
            if not isinstance(tema, dict):
                continue

            temas_list.append(
                {
                    "unidad": nombre_unidad,
                    "nombre": tema.get("nombre"),
                    "nivel": tema.get("nivel", "basica"),
                    "definicion": tema.get("definición") or tema.get("definicion"),
                    "definición": tema.get("definición") or tema.get("definicion"),
                    "ejemplo": tema.get("ejemplo"),
                    "ventajas": tema.get("ventajas") or [],
                    "pasos": tema.get("pasos") or [],
                }
            )

    TEMAS_DISPONIBLES.clear()
    TEMAS_DISPONIBLES.extend(temas_list)
    _TEMAS_CARGADOS = True
    _TEMAS_MTIME = mtime or _TEMAS_MTIME
    _reconstruir_indices()

    logger.info("Temas cargados en memoria", count=len(TEMAS_DISPONIBLES))


# ------------------------------------------------------------
# SECCIÓN 5: IDENTIFICACIÓN DE TEMA DESDE TEXTO
# ------------------------------------------------------------
def identificar_tema_desde_texto(pregunta: str) -> str:
    """Identifica el tema académico más probable a partir del texto del usuario.

    Estrategia:
    1) Validación básica
    2) Mapeo manual por palabras clave
    3) Coincidencias con temas.json (exactas o parciales)
    4) Fallback a tema por defecto

    Args:
        pregunta: Parámetro de entrada.

    Returns:
        Valor tipo str.
    """
    if not pregunta:
        return "Introducción a la Programación Orientada a Objetos"

    # Garantiza que los temas estén cargados
    global _TEMAS_CARGADOS
    if not _TEMAS_CARGADOS:
        cargar_temas(force=False)

    pregunta_lower = pregunta.lower()

    # Mapeo manual de palabras clave a temas
    # Simple, explicable y controlable (ideal para tesis)
    mapeo_manual = {
        "poo": "Introducción a la Programación Orientada a Objetos",
        "orientada a objetos": "Introducción a la Programación Orientada a Objetos",
        "clase": "Clases y Objetos",
        "clases": "Clases y Objetos",
        "objeto": "Clases y Objetos",
        "objetos": "Clases y Objetos",
        "herencia": "Herencia",
        "polimorfismo": "Polimorfismo",
        "encapsulamiento": "Encapsulamiento",
        "encapsulación": "Encapsulamiento",
        "abstract": "Clases abstractas e interfaces",
        "interfaz": "Interfaces en Java",
        "mvc": "Arquitectura MVC",
        "patrón": "Patrones de Diseño en POO",
        "dao": "Patrón DAO",
        "uml": "Diagramas UML",
        "jdbc": "Conexión a bases de datos en Java",
        "persistencia": "Persistencia con ORM",
        "room": "Persistencia con Room / ORM",
    }

    # 5.1) Búsqueda por substring (rápida y prioritaria)
    for palabra, tema in mapeo_manual.items():
        if palabra in pregunta_lower:
            return tema

    # 5.2) Búsqueda usando los nombres reales de temas.json
    compact = _normalizar(pregunta)

    if _TEMAS_NOMBRES_IDX:
        # Coincidencia exacta
        if compact in _TEMAS_NOMBRES_IDX:
            return _TEMAS_NOMBRES_IDX[compact]

        # Coincidencia parcial (nombre del tema dentro del texto)
        for key, nombre_real in _TEMAS_NOMBRES_IDX.items():
            if key and key in compact:
                return nombre_real

    # 5.3) Fallback final
    return "Introducción a la Programación Orientada a Objetos"
