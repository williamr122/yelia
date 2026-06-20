"""
Proyecto: YELIA4AP
Archivo: backend/routes/upload_routes_secure.py
Descripción: Módulo del backend para la lógica asociada a esta carpeta/funcionalidad.

Revisión: 2026-02-10
"""
from __future__ import annotations

"""
Archivo: backend/routes/upload_routes_secure.py
Proyecto: YELIA4AP
Última revisión: 2026-02-10

Módulo de backend en Python.

Convenciones:
- Funciones pequeñas, nombres descriptivos y manejo de errores explícito.
- Evitar prints en producción: usar logging si aplica.
"""


#
# Archivo: backend/routes/upload_routes_secure.py
# Rol: Módulo del backend (Flask) de YELIA4AP.


"""Upload Routes Secure
Archivo del backend del sistema YELIA4AP.

Responsabilidad:
- Implementa la lógica asociada a este módulo.

backend/routes/upload_routes_secure.py

Endpoint seguro para descargar adjuntos sin exponer /static/uploads.

Ruta:
  GET /api/uploads/<stored_name>

Seguridad:
- Validación de nombre + extensión (allowlist)
- Bloqueo de path traversal
- Requiere sesión (student/admin/teacher) cuando REQUIRE_AUTH_UPLOADS=1
"""
# =====================================
# Imports
# =====================================


import os
from pathlib import Path
from flask import Blueprint, jsonify, send_file, abort, session
from werkzeug.utils import secure_filename


# =====================================
# Configuración / Constantes
# =====================================
secure_uploads_bp = Blueprint("secure_uploads", __name__)

PRIVATE_UPLOAD_DIR = os.getenv("PRIVATE_UPLOAD_DIR", "private_uploads")
MAX_FILENAME_LEN = int(os.getenv("UPLOAD_MAX_FILENAME_LEN", "140"))
ALLOWED_EXTENSIONS = {
    ext.strip().lower()
    for ext in os.getenv("UPLOAD_ALLOWED_EXTENSIONS", "txt,pdf,png,jpg,jpeg").split(",")
    if ext.strip()
}

REQUIRE_AUTH = os.getenv("REQUIRE_AUTH_UPLOADS", "1") == "1"
# =====================================
# Funciones / Clases
# =====================================



def _is_allowed_user() -> bool:
    # Compatibilidad con las sesiones reales del proyecto
    from backend.core.security import has_staff_session
    return bool(
        session.get("usuario")
        or session.get("admin_username")
        or session.get("teacher_username")
        or has_staff_session()
    )


def _safe_path(filename: str) -> Path:
    name = secure_filename(filename)[:MAX_FILENAME_LEN]
    if not name:
        raise ValueError("Nombre inválido")

    if "." not in name:
        raise ValueError("Extensión inválida")

    ext = name.rsplit(".", 1)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError("Extensión no permitida")

    root = Path(PRIVATE_UPLOAD_DIR).resolve()
    full = (root / name).resolve()

    # Evita ../ traversal
    if root not in full.parents and full != root:
        raise ValueError("Ruta inválida")

    return full


@secure_uploads_bp.route("/api/uploads/<path:filename>", methods=["GET"])
def download_upload(filename: str):
    # Auth opcional por env para no romper demo si lo desactivas
    if REQUIRE_AUTH and not _is_allowed_user():
        return jsonify({"ok": False, "error": "No autenticado"}), 401

    try:
        path = _safe_path(filename)
    except ValueError as e:
        return jsonify({"ok": False, "error": str(e)}), 400

    if not path.exists() or not path.is_file():
        abort(404)

    return send_file(path, as_attachment=True)
