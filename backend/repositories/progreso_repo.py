"""
Proyecto: YELIA4AP
Archivo: backend/repositories/progreso_repo.py
Descripción: Módulo del backend para la lógica asociada a esta carpeta/funcionalidad.

Revisión: 2026-02-10
"""
"""Progreso Repo
Archivo del backend del sistema YELIA4AP.

Responsabilidad:
- Implementa la lógica asociada a este módulo.
"""

#
# Archivo: backend/repositories/progreso_repo.py
# Rol: Módulo del backend (Flask) de YELIA4AP.

"""backend/repositories/progreso_repo.py

Backend Flask — YELIA (módulo de servidor)

Propósito:
    Este archivo pertenece al backend (Flask) de YELIA. Contiene lógica de servidor
    y/o utilidades que soportan rutas, servicios, persistencia y orquestación NLP.
    En particular, este módulo define el repositorio para la entidad 'progreso',
    encapsulando el acceso a datos relacionados con el progreso académico del estudiante.
"""

# ============================================================
# PROPÓSITO:
#   Repositorio destinado a encapsular el acceso a datos
#   relacionados con el progreso académico del estudiante.
#
# RELACIÓN CON EL SISTEMA ACTUAL:
#   - Actualmente, el acceso a la tabla 'progreso' se realiza
#     directamente desde backend/services/progreso_service.py.
#   - Este repositorio existe para formalizar el patrón
#     Repositorio y permitir una migración futura sin impactar
#     a la capa de servicios ni a las rutas/API.
#
# OBJETIVO A FUTURO (MIGRACIÓN CONTROLADA):
#   - Mover aquí las operaciones SQL realizadas hoy por:
#       • cargar_progreso()
#       • actualizar_progreso()
#       • actualizar_perfil_usuario()
#
# BENEFICIO ARQUITECTÓNICO:
#   - Desacopla lógica de negocio (service) de persistencia (repo)
#   - Facilita pruebas unitarias (mock del repo)
#   - Reduce repetición de SQL y concentra reglas de almacenamiento
#
#   - Este módulo NO implementa CRUD todavía.
#   - Contiene únicamente stubs (contrato) para documentar
#     las operaciones esperadas sin introducir comportamiento.
# ============================================================

from backend.db.session import db_session


class ProgresoRepository:
    """
    Repositorio de persistencia para la entidad 'progreso'.

    Responsabilidad:
      Encapsular el acceso a la tabla 'progreso' (SQLite/PostgreSQL)
      para operaciones de lectura y escritura relacionadas con
      puntos, temas aprendidos y perfil académico (ciclo/estado).

    Importante:
      Esta clase se define como contrato. La implementación real
      puede migrarse desde progreso_service.py en iteraciones futuras,
      sin cambiar las firmas públicas del servicio.
    """

    def __init__(self):
        """__init__.

        Returns:
            Any: TODO: Describe the return value.


        Returns:
            None.

        Args:
            (sin parámetros adicionales).
        """
        # Referencia al gestor de sesiones/conexiones de BD.
        self.db = db_session

    def get_progreso_row(self, usuario: str):
        """
        Obtiene la fila de progreso del usuario.

        Equivalente futuro al SELECT usado en cargar_progreso().

        Retorna:
          - Una fila (dict-like) con columnas relevantes, o None.
        """
        raise NotImplementedError("ProgresoRepository.get_progreso_row no implementado")

    def upsert_progreso(self, usuario: str, puntos: int, temas_aprendidos_json: str):
        """
        Crea o actualiza el progreso del usuario (puntos + temas).

        Equivalente futuro al UPDATE/INSERT de actualizar_progreso().

        Parámetros:
          usuario: identificador estable del estudiante
          puntos: puntaje acumulado
          temas_aprendidos_json: lista serializada JSON (texto)
        """
        raise NotImplementedError("ProgresoRepository.upsert_progreso no implementado")

    def upsert_perfil(self, usuario: str, ciclo_academico, estado_materia):
        """
        Crea o actualiza el perfil académico (ciclo + estado).

        Equivalente futuro a actualizar_perfil_usuario().

        Nota:
          - La lógica COALESCE y updated_at seguirá existiendo,
            pero su ubicación será este repositorio.
        """
        raise NotImplementedError("ProgresoRepository.upsert_perfil no implementado")
