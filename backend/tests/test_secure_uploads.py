"""
Proyecto: YELIA4AP
Archivo: backend/tests/test_secure_uploads.py
Descripción: Módulo del backend para la lógica asociada a esta carpeta/funcionalidad.

Revisión: 2026-02-10
"""
"""Test Secure Uploads
Archivo del backend del sistema YELIA4AP.

Responsabilidad:
- Implementa la lógica asociada a este módulo.
"""

#
# Archivo: backend/tests/test_secure_uploads.py
# Rol: Módulo del backend (Flask) de YELIA4AP.

"""Tests automatizados: test_secure_uploads.py.

Archivo de pruebas para validar comportamientos básicos del backend.
"""

# =====================================
# Imports
# =====================================
from pathlib import Path


# =====================================
# Configuración / Constantes
# =====================================
# =====================================
# Funciones / Clases
# =====================================

def test_download_requires_auth_by_default(client, tmp_path, monkeypatch):
    monkeypatch.setenv("PRIVATE_UPLOAD_DIR", str(tmp_path))
    # Crear archivo simulado
    f = tmp_path / "file.txt"
    f.write_text("hola", encoding="utf-8")

    res = client.get("/api/uploads/file.txt")
    assert res.status_code in (401, 403)

def test_download_bad_extension(client):
    res = client.get("/api/uploads/evil.exe")
    assert res.status_code in (400, 401, 403, 404)
