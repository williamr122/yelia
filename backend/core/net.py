"""
Proyecto: YELIA4AP
Archivo: backend/core/net.py
Descripción: Módulo del backend para la lógica asociada a esta carpeta/funcionalidad.

Revisión: 2026-02-10
"""
from __future__ import annotations

"""
Archivo: backend/core/net.py
Proyecto: YELIA4AP
Última revisión: 2026-02-10

Utilidades base del backend (helpers, red, configuración).

Convenciones:
- Funciones pequeñas, nombres descriptivos y manejo de errores explícito.
- Evitar prints en producción: usar logging si aplica.
"""


#
# Archivo: backend/core/net.py
# Rol: Módulo del backend (Flask) de YELIA4AP.


"""Net
Archivo del backend del sistema YELIA4AP.

Responsabilidad:
- Implementa la lógica asociada a este módulo.

backend/core/net.py

Backend Flask — YELIA (módulo de servidor)

Propósito:
    Este archivo pertenece al backend (Flask) de YELIA. Contiene lógica de servidor
    y/o utilidades que soportan rutas, servicios, persistencia y orquestación NLP.
    En particular, este módulo ofrece utilidades de red.
"""
# =====================================
# Imports
# =====================================



import socket



# =====================================
# Configuración / Constantes
# =====================================
# =====================================
# Funciones / Clases
# =====================================

def has_internet(host: str = "1.1.1.1", port: int = 53, timeout: float = 1.2) -> bool:
    """Verifica si existe conectividad a internet (chequeo rápido por socket).

    Se intenta abrir un socket TCP hacia un endpoint típico de DNS público.
    Si el socket conecta, se asume conectividad general.

    Args:
        host: Host a probar. Por defecto "1.1.1.1".
        port: Puerto a probar. Por defecto 53.
        timeout: Tiempo máximo de espera en segundos.

    Returns:
        True si se logra conectar, False si no hay conectividad.

    Raises:
        No lanza excepciones hacia arriba; cualquier error retorna False.
    """
    try:
        socket.setdefaulttimeout(timeout)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((host, port))
        sock.close()
        return True
    except OSError:
        return False
