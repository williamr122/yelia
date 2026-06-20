"""
Proyecto: YELIA4AP
Archivo: backend/tests/test_student_auth.py
Descripción: Módulo del backend para la lógica asociada a esta carpeta/funcionalidad.

Revisión: 2026-02-10
"""
"""Test Student Auth
Archivo del backend del sistema YELIA4AP.

Responsabilidad:
- Implementa la lógica asociada a este módulo.
"""

#
# Archivo: backend/tests/test_student_auth.py
# Rol: Módulo del backend (Flask) de YELIA4AP.

"""Tests automatizados: test_student_auth.py.

Archivo de pruebas para validar comportamientos básicos del backend.
"""

# =====================================
# Imports
# =====================================
import os


# =====================================
# Configuración / Constantes
# =====================================
# =====================================
# Funciones / Clases
# =====================================

def test_student_code_min_len(client, monkeypatch):
    monkeypatch.setenv("STUDENT_CODE_MIN_LEN", "4")
    res = client.post("/api/auth/login", json={"student_code": "ab"})
    assert res.status_code == 200  # cae a guest
    body = res.get_json()
    assert body["ok"] is True

def test_student_code_strict_blocks(client, monkeypatch):
    monkeypatch.setenv("STUDENT_AUTH_STRICT", "1")
    monkeypatch.setenv("STUDENT_CODES_ALLOWLIST", "ABCD,ZZZZ")
    monkeypatch.setenv("STUDENT_AUTH_FAIL_OPEN", "0")
    res = client.post("/api/auth/login", json={"student_code": "NOPE"})
    assert res.status_code == 403


def test_guest_id_login_is_stable(client):
    res = client.post("/api/auth/login", json={"guest_id": "abc-123"})
    assert res.status_code == 200
    data = res.get_json()["data"]
    assert data["usuario"] == "GUEST-abc-123"
    assert data["mode"] == "guest"

    who = client.get("/api/auth/whoami")
    assert who.status_code == 200
    assert who.get_json()["data"]["usuario"] == "GUEST-abc-123"
