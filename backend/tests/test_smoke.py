"""
Proyecto: YELIA4AP
Archivo: backend/tests/test_smoke.py
Descripción: Módulo del backend para la lógica asociada a esta carpeta/funcionalidad.

Revisión: 2026-02-10
"""
"""
Pruebas de humo del backend.

Este archivo valida que los endpoints básicos del sistema
respondan correctamente y que la aplicación se inicie sin errores.
"""
# =====================================
# Funciones / Clases
# =====================================



def test_health(client):
    """Verifica el endpoint de estado general."""
    res = client.get("/health")
    assert res.status_code in (200, 204)


def test_api_health(client):
    """Verifica el estado del backend a través de la API."""
    res = client.get("/api/health")
    assert res.status_code == 200

    body = res.get_json()
    assert body["ok"] is True


def test_api_history_paging(client):
    """Verifica la paginación básica del historial."""
    res = client.get("/api/history?limit=5&offset=0")
    assert res.status_code == 200

    body = res.get_json()
    assert "paging" in body
