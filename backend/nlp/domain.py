"""
Proyecto: YELIA4AP
Archivo: backend/nlp/domain.py
Descripción: Módulo del backend para la lógica asociada a esta carpeta/funcionalidad.

Revisión: 2026-02-10
"""
from __future__ import annotations

"""
Archivo: backend/nlp/domain.py
Proyecto: YELIA4AP
Última revisión: 2026-02-10

Componentes de procesamiento de lenguaje natural (NLU/NLP) del backend.

Convenciones:
- Funciones pequeñas, nombres descriptivos y manejo de errores explícito.
- Evitar prints en producción: usar logging si aplica.
"""


#
# Archivo: backend/nlp/domain.py
# Rol: Módulo del backend (Flask) de YELIA4AP.


"""Domain
Archivo del backend del sistema YELIA4AP.

Responsabilidad:
- Implementa la lógica asociada a este módulo.

backend/nlp/domain.py

Backend Flask — YELIA (módulo de servidor)

Propósito:
    Este archivo pertenece al backend (Flask) de YELIA. Contiene lógica de servidor
    y/o utilidades que soportan rutas, servicios, persistencia y orquestación NLP.
Clasificación de dominio académico de preguntas estudiantiles
-----------------------------------------------------------------------------------
Funcionalidad:
    Proporciona funciones para clasificar preguntas de estudiantes en dominios
    académicos específicos ("core", "ext", "off") basándose en reglas y heurísticas
    definidas. Esto ayuda a mantener las respuestas de YELIA enfocadas en el
    contenido del curso y evita desviaciones.
"""


# ============================================================
# PROPÓSITO:
#   Clasificar la pregunta del estudiante por "dominio" académico para
#   controlar el enfoque de YELIA y evitar desvíos.
#
# DOMINIOS:
#   - "core": contenidos del sílabo oficial (Programación Avanzada)
#   - "ext" : contenidos complementarios que ayudan a entender el core
#   - "off" : fuera del dominio (se redirige al estudiante)
#
# NOTA PROFESIONAL:
#   Este filtro es una capa determinística (reglas/heurísticas) que:
#   - reduce alucinaciones del LLM,
#   - mejora consistencia de respuestas,
#   - y protege el objetivo pedagógico (mantenerse en la materia).
# ============================================================


import re
from typing import Dict, List, Set, Tuple


def norm(s: str) -> str:
    """Normaliza texto para comparar contra diccionarios de dominio.

    Pasos:
    - Convierte a minúsculas
    - Remueve tildes/diacríticos comunes (español)
    - Sustituye caracteres no alfanuméricos por espacio
    - Compacta espacios múltiples

    Beneficio:
    - Hace que la detección por keywords/phrases sea más robusta,
      evitando fallos por acentos, signos o puntuación.

    Args:
        s: Texto de entrada.

    Returns:
        Valor tipo str.
    """
    s = (s or "").lower()
    s = (
        s.replace("á", "a").replace("é", "e").replace("í", "i")
         .replace("ó", "o").replace("ú", "u").replace("ü", "u")
         .replace("ñ", "n")
    )
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


# ============================================================
# 1) FRASES (MATCH DE SUBCADENA)
# ------------------------------------------------------------
# CORE_PHRASES:
# - Señales fuertes del sílabo: si aparecen en el texto, es "core".
#
# EXT_PHRASES:
# - Tópicos complementarios (Android, SOLID, patrones).
# - Se consideran "ext" solo si no se clasificó como core primero.
# ============================================================

CORE_PHRASES: List[str] = [
    'programacion orientada a objetos',
    'poo',
    'uml',
    'diagrama de clases',
    'diagrama de secuencia',
    'casos de uso',
    'mvc',
    'modelo vista controlador',
    'base de datos',
    'orm',
    'acceso a archivos',
    'clases abstractas',
    'interfaces',
    'herencia',
    'polimorfismo',
    'encapsulamiento',
    'getter',
    'setter',
    'buenas practicas',
    'pruebas',
    'programacion concurrente',
    'concurrencia',
    'programacion distribuida',
    'distribuida',
]

EXT_PHRASES: List[str] = [
    'solid',
    'patrones de diseno',
    'singleton',
    'factory',
    'observer',
    'android',
    'activity',
    'fragment',
    'retrofit',
    'room',
    'viewmodel',
    'lifecycle',
    'ciclo de vida',
]


# ============================================================
# 2) KEYWORDS (MATCH POR TOKENS)
# ------------------------------------------------------------
# CORE_KEYWORDS:
# - Vocabulario asociado al núcleo de la materia.
# - Se usa intersección (tokens del texto ∩ set de keywords).
#
# EXT_KEYWORDS:
# - Vocabulario complementario (arquitecturas, Android, REST, etc.)
#
# Ventaja:
# - Funciona incluso cuando el estudiante no escribe frases exactas,
#   sino palabras sueltas relacionadas.
# ============================================================

CORE_KEYWORDS: Set[str] = {
    'abstractas', 'accede', 'acceso', 'aplicacion', 'archivos', 'atributos',
    'base', 'bases', 'buenas', 'calidad', 'capacidad', 'clase', 'clases',
    'codigo', 'combina', 'combinan', 'completos', 'comportamiento',
    'comportarse', 'comunes', 'concurrente', 'continua', 'contratos',
    'controlado', 'controlador', 'datos', 'deben', 'definen', 'definir',
    'desde', 'detalles', 'diagramas', 'diferentes', 'dise', 'distribuida',
    'documentar', 'encapsulamiento', 'escribir', 'especificar', 'estandar',
    'estructura', 'formas', 'frameworks', 'fundamentos', 'getters',
    'graficamente', 'herede', 'herencia', 'hibernate', 'hilos', 'implementar',
    'incluye', 'incompletos', 'instancias', 'integracion', 'interfaces',
    'interfaz', 'internos', 'introduccion', 'java', 'jdbc', 'leer',
    'lenguaje', 'logica', 'maquinas', 'mediante', 'metodo', 'metodos',
    'modelado', 'modelo', 'moldes', 'multiples', 'mvc', 'objeto', 'objetos',
    'oculta', 'organiza', 'orientacion', 'orientada', 'orm', 'otra', 'patron',
    'patrones', 'permite', 'permitiendo', 'persistencia', 'persistentes',
    'polimorfismo', 'poo', 'practicas', 'probadas', 'problemas',
    'programacion', 'pruebas', 'representan', 'reutilizando', 'separa',
    'setters', 'sistema', 'sistemas', 'sobrecarga', 'sobreescritura',
    'software', 'soluciones', 'son', 'torno', 'uml', 'unidad', 'unificado',
    'unitarias', 'vista', 'visualizar',
}

EXT_KEYWORDS: Set[str] = {
    'abstrae', 'activity', 'algoritmo', 'android', 'anotaciones', 'apis',
    'aplicacion', 'architecture', 'arquitectura', 'arquitecturas',
    'avanzados', 'biblioteca', 'buenas', 'cambia', 'cambiar', 'capas',
    'centraliza', 'ciclo', 'clean', 'comparacion', 'concentricas', 'conjunto',
    'consumo', 'contexto', 'creacion', 'cuando', 'datos', 'delega',
    'desacopla', 'desacoplar', 'desarrollo', 'describe', 'dinamicamente',
    'directamente', 'dise', 'dominio', 'estado', 'estados', 'etc',
    'evitando', 'extensible', 'facilita', 'factory', 'forma', 'fragments',
    'http', 'infraestructura', 'interfaces', 'introduce', 'limpio',
    'llamadas', 'logica', 'manejan', 'mantenible', 'modernas', 'modulares',
    'movil', 'multiples', 'mvc', 'mvp', 'mvvm', 'new', 'notifica', 'objetos',
    'observer', 'oncreate', 'onresume', 'onstart', 'orm', 'otro', 'pantalla',
    'pasa', 'patron', 'patrones', 'permite', 'permiten', 'persistencia',
    'persistente', 'practicas', 'presentador', 'principios', 'promueven',
    'rest', 'retrofit', 'room', 'separa', 'solid', 'sqlite', 'strategy',
    'unidad', 'usado', 'usando', 'usar', 'vida', 'viewmodel', 'viewmodels',
}


# ============================================================
# 3) HEURÍSTICAS DE "SEÑALES DE CÓDIGO"
# ------------------------------------------------------------
# CODE_HINTS:
# - Detecta patrones típicos de código/errores.
# - Se usa para "rescatar" preguntas que podrían parecer off-topic
#   pero realmente son de la materia (por ejemplo, pegar un error).
# ============================================================

CODE_HINTS: Tuple[str, ...] = (
    'public ', 'class ', 'static ', 'void ', 'system.out', 'println',
    'nullpointerexception', 'exception', 'traceback', '{', '}', ';', 'import ',
)


# ============================================================
# 4) PALABRAS "FUERTES" DEL CURSO
# ------------------------------------------------------------
# COURSE_STRONG:
# - Tokens con alta probabilidad de pertenecer al curso.
# - Útil para mejorar "recall" y no dejar afuera preguntas válidas.
# ============================================================

COURSE_STRONG: Set[str] = {
    'abstraccion', 'abstract', 'api', 'archivo', 'archivos', 'atributo',
    'atributos', 'base', 'bd', 'casos', 'clase', 'clases', 'cliente',
    'compilar', 'compile', 'constructor', 'datos', 'debug', 'depurar',
    'diagrama', 'diagramas', 'encapsulacion', 'encapsulamiento', 'error',
    'herencia', 'hibernate', 'http', 'interface', 'interfaz', 'java', 'jdbc',
    'json', 'metodo', 'metodos', 'mvc', 'objeto', 'objetos', 'oop', 'orm',
    'override', 'patron', 'patrones', 'polimorfismo', 'poo', 'pruebas',
    'secuencia', 'servidor', 'sobrecarga', 'sobreescritura', 'socket',
    'solid', 'sql', 'sqlite', 'tcp', 'test', 'udp', 'uml', 'unitarias', 'uso',
}


# ============================================================
# 5) TÉRMINOS AMBIGUOS
# ------------------------------------------------------------
# AMBIGUOS:
# - Palabras que pueden significar cosas fuera de programación.
# - Ej:
#   * "clase" puede ser de "historia" o "social"
#   * "java" puede ser "isla" o "café"
#
# Objetivo:
# - Reducir falsos positivos (evitar clasificar como materia algo que no lo es).
# ============================================================

AMBIGUOS: Dict[str, List[str]] = {
    'clase': ['social', 'economica', 'económica', 'historia', 'biologia', 'biología'],
    'java': ['isla', 'indonesia', 'cafe', 'café'],
}


def match_domain(text_raw: str) -> str:
    """Clasifica el texto en 'core', 'ext' u 'off'.

    Estrategia:
    1) CORE primero (prioridad máxima, por sílabo)
       - match por frases CORE_PHRASES
       - o match por al menos 2 keywords
       - o si el mensaje es corto (<=4 tokens) con al menos 1 keyword core
    2) EXT después (complementario)
       - match por frases EXT_PHRASES o >=2 keywords ext
    3) Si no matchea, se considera off-topic.

    Args:
        text_raw: Parámetro de entrada.

    Returns:
        Valor tipo str.
    """
    t = norm(text_raw)
    tokens = set(t.split())

    # 1) CORE primero (sílabo)
    if (
        any(ph in t for ph in CORE_PHRASES)
        or (len(tokens & CORE_KEYWORDS) >= 2)
        or (len(tokens) <= 4 and len(tokens & CORE_KEYWORDS) >= 1)
    ):
        return "core"

    # 2) EXT (complementario)
    if any(ph in t for ph in EXT_PHRASES) or (len(tokens & EXT_KEYWORDS) >= 2):
        return "ext"

    return "off"


def tiene_senal_materia(texto: str) -> bool:
    """Heurística rápida para detectar si el texto "huele a programación/materia".

    Se considera señal positiva si:
    - Contiene pistas de código/error (CODE_HINTS)
    - Contiene tokens fuertes del curso (COURSE_STRONG)
    - Contiene la palabra "programacion"

    Args:
        texto: Texto de entrada.

    Returns:
        Valor tipo bool.
    """
    t = norm(texto)
    if any(h in t for h in CODE_HINTS):
        return True
    toks = set(t.split())
    if toks & COURSE_STRONG:
        return True
    if "programacion" in t:
        return True
    return False


def es_ambigua_pero_probable_materia(texto: str) -> bool:
    """Detecta casos donde hay términos ambiguos que podrían ser del curso.

    Regla:
    - Si aparece un término ambiguo (ej: "clase", "java"),
      entonces:
        * Si también aparecen pistas NO-programación => NO es materia.
        * Si NO aparecen pistas no-programación => probable que SÍ sea materia.

    Uso:
    - Sirve como "rescate" cuando match_domain() dio off,
      pero todavía hay probabilidad de que sea una consulta válida.

    Args:
        texto: Texto de entrada.

    Returns:
        Valor tipo bool.
    """
    t = norm(texto)
    toks = set(t.split())
    for term, pistas_no_prog in AMBIGUOS.items():
        if term in toks:
            # Si incluye pista no-programación, no lo tratamos como materia
            if any(norm(p) in t for p in pistas_no_prog):
                return False
            return True
    return False
