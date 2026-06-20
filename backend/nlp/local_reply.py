"""
Proyecto: YELIA4AP
Archivo: backend/nlp/local_reply.py
Descripción: Módulo del backend para la lógica asociada a esta carpeta/funcionalidad.

Revisión: 2026-02-10
"""
from __future__ import annotations

"""Local Reply
Archivo del backend del sistema YELIA4AP.

Responsabilidad:
- Implementa la lógica asociada a este módulo.
"""

#
# Archivo: backend/nlp/local_reply.py
# Rol: Módulo del backend (Flask) de YELIA4AP.


# =====================================
# Imports
# =====================================

from typing import Optional, Dict, Any



# =====================================
# Configuración / Constantes
# =====================================
# =====================================
# Funciones / Clases
# =====================================

class LocalResponses:
    """Clase que agrupa todas las respuestas locales estáticas o semi-dinámicas.

    Facilita:
    - Centralizar mensajes y traducciones futuras
    - Agregar lógica condicional sin ensuciar funciones sueltas
    - Testear fácilmente cada respuesta
    - Extender con nuevos patrones sin tocar el core del router
    """

    DEFAULT_USER_EMOJI = "👋"
    APP_NAME = "YELIA4AP"
    FOCUS = "Programación Avanzada"

    @staticmethod
    def greeting(usuario: Optional[str] = None) -> str:
        """Saludo inicial amigable y personalizado."""
        nombre = usuario.strip() if usuario and usuario.strip() else LocalResponses.DEFAULT_USER_EMOJI
        return (
            f"¡Hola {nombre}! 😊\n\n"
            f"¡Bienvenid@ a **{LocalResponses.APP_NAME}**!\n"
            f"Estoy aquí para ayudarte con **{LocalResponses.FOCUS}**.\n\n"
            "Puedes pedirme:\n"
            "• Explicaciones paso a paso\n"
            "• Ejemplos de código comentados\n"
            "• Depuración de errores\n"
            "• Ejercicios personalizados según tu nivel\n\n"
            "Dime el tema o simplemente empieza a preguntar:\n"
            "POO • Clases y objetos • Herencia • Polimorfismo • UML/MVC • Archivos • BD/ORM • Pruebas"
        )

    @staticmethod
    def empty_message() -> str:
        """Respuesta cuando el usuario envía mensaje vacío o solo espacios."""
        return (
            "Parece que no escribiste nada... 😅\n\n"
            "¿En qué tema de Programación Avanzada te ayudo hoy?"
        )

    @staticmethod
    def too_short() -> str:
        """Para mensajes muy cortos que no justifican LLM (ej: 'hola', 'ok')."""
        return (
            "¡Ey! 😄 Ya estamos conectados.\n"
            "¿Quieres que hablemos de algún tema en concreto?"
        )

    @staticmethod
    def fallback_error() -> str:
        """Respuesta cuando falla el proveedor LLM y no hay respuesta generada."""
        return (
            "Ups... parece que mi cerebro IA está tomando un café ☕\n\n"
            "Mientras vuelve, ¿me cuentas qué necesitas? Estoy 100% aquí para ayudarte.\n"
            "Puedes repetir tu pregunta o probar con otro tema."
        )


# Interfaz pública del módulo (lo que deberían importar otros archivos)
def get_local_response(
    mensaje: str,
    usuario: Optional[str] = None,
    contexto: Optional[Dict[str, Any]] = None,
) -> Optional[str]:
    """Función principal de entrada para decidir si responder localmente.

    Args:
        mensaje: texto limpio enviado por el usuario
        usuario: nombre/alias del usuario (opcional)
        contexto: diccionario con info adicional (conv_id, tema detectado, etc.)

    Returns:
        str | None: respuesta local si aplica, None si debe pasar al LLM
    """
    mensaje = (mensaje or "").strip().lower()

    if not mensaje:
        return LocalResponses.empty_message()

    if len(mensaje) <= 5 and mensaje in {"hola", "buenas", "hey", "que tal"}:
        return LocalResponses.greeting(usuario)

    if len(mensaje) <= 8:  # mensajes muy cortos → fast-path
        return LocalResponses.too_short()

    # Aquí se pueden agregar más reglas en el futuro
    # Ejemplos:
    # if "ayuda" in mensaje or "help" in mensaje:
    #     return LocalResponses.help_menu()
    # if mensaje == "reset":
    #     return LocalResponses.reset_conversation()

    # Si no matchea ninguna regla local → None → ir al LLM
    return None


# Para compatibilidad con el código existente (mínimo cambio necesario)
def respuesta_saludo_local(usuario: Optional[str] = None) -> str:
    """Función legacy / de compatibilidad con el código actual.
    Se recomienda migrar a get_local_response() en el futuro.
    """
    return LocalResponses.greeting(usuario)


if __name__ == "__main__":
    # Pruebas rápidas al ejecutar el archivo directamente
    print("=== Pruebas local_reply ===")
    print("Saludo con nombre:")
    print(respuesta_saludo_local("Erick"))
    print("\nSaludo sin nombre:")
    print(respuesta_saludo_local())
    print("\nMensaje vacío:")
    print(get_local_response("   "))
    print("\nMensaje corto:")
    print(get_local_response("hola"))
    print("\nMensaje que pasa a LLM:")
    print(get_local_response("Explicame que es un decorador en Python"))
