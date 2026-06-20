import os
import random
import pytest
from backend.db.session import db_session

def test_student_deletion_success(client, monkeypatch):
    # Setup admin token
    monkeypatch.setenv("ADMIN_TOKEN", "test-admin-token")
    headers = {"X-Admin-Token": "test-admin-token"}

    # Generate unique alias
    rand_suffix = str(random.randint(100000, 999999))
    student_alias = f"STU-teststudent-{rand_suffix}"

    # Seed data
    with db_session(write=True) as conn:
        cur = conn.cursor()
        
        # Clean up any potential leftover (should not exist but just in case)
        cur.execute("DELETE FROM usuarios WHERE alias = ?;", (student_alias,))
        cur.execute("DELETE FROM progreso WHERE usuario = ?;", (student_alias,))
        cur.execute("DELETE FROM student_profiles WHERE student_id = ?;", (student_alias,))
        
        # 1. Create a student in usuarios
        cur.execute(
            "INSERT INTO usuarios (alias, role, status) VALUES (?, ?, ?);",
            (student_alias, "student", "active")
        )
        student_id = cur.lastrowid
        
        # 2. Add an interaction referencing this student
        cur.execute(
            "INSERT INTO interacciones (usuario_id, pregunta, respuesta) VALUES (?, ?, ?);",
            (student_id, "Hola Yelia", "Hola, ¿en qué te ayudo?")
        )
        
        # 3. Add progress entry
        cur.execute(
            "INSERT INTO progreso (usuario, puntos) VALUES (?, ?);",
            (student_alias, 10)
        )
        
        # 4. Add profile entry
        cur.execute(
            "INSERT INTO student_profiles (student_id, profile_json) VALUES (?, ?);",
            (student_alias, "{}")
        )
        
        # 5. Add conversation
        cur.execute(
            "INSERT INTO conversaciones (usuario, titulo) VALUES (?, ?);",
            (student_alias, "Mi test charla")
        )
        conv_id = cur.lastrowid
        
        # 6. Add message
        cur.execute(
            "INSERT INTO messages (conv_id, usuario, remitente, contenido) VALUES (?, ?, ?, ?);",
            (conv_id, student_alias, "user", "Hola")
        )
        msg_id = cur.lastrowid
        
        # 7. Add metrics event referencing conversation/message
        cur.execute(
            "INSERT INTO metrics_events (created_at, usuario, conv_id, mensaje_id, event_type) VALUES (?, ?, ?, ?, ?);",
            ("2026-06-16T19:30:00", student_alias, conv_id, msg_id, "test_event")
        )

    # Make DELETE request to delete the student
    res = client.delete(f"/api/admin/students/{student_id}", headers=headers)
    assert res.status_code == 200
    body = res.get_json()
    assert body["ok"] is True
    assert "eliminados correctamente" in body["data"]["message"]

    # Verify everything was deleted
    with db_session() as conn:
        cur = conn.cursor()
        
        # Check usuario
        cur.execute("SELECT id FROM usuarios WHERE id = ?;", (student_id,))
        assert cur.fetchone() is None
        
        # Check interacciones
        cur.execute("SELECT id FROM interacciones WHERE usuario_id = ?;", (student_id,))
        assert cur.fetchone() is None
        
        # Check progreso
        cur.execute("SELECT id FROM progreso WHERE usuario = ?;", (student_alias,))
        assert cur.fetchone() is None
        
        # Check student_profiles
        cur.execute("SELECT student_id FROM student_profiles WHERE student_id = ?;", (student_alias,))
        assert cur.fetchone() is None
        
        # Check conversaciones
        cur.execute("SELECT id FROM conversaciones WHERE usuario = ?;", (student_alias,))
        assert cur.fetchone() is None
        
        # Check messages
        cur.execute("SELECT id FROM messages WHERE conv_id = ?;", (conv_id,))
        assert cur.fetchone() is None
        
        # Check metrics_events
        cur.execute("SELECT id FROM metrics_events WHERE conv_id = ?;", (conv_id,))
        assert cur.fetchone() is None


def test_student_deletion_non_existent(client, monkeypatch):
    monkeypatch.setenv("ADMIN_TOKEN", "test-admin-token")
    headers = {"X-Admin-Token": "test-admin-token"}

    # Attempt to delete non-existent user ID
    res = client.delete("/api/admin/students/99999", headers=headers)
    assert res.status_code == 404
    body = res.get_json()
    assert body["ok"] is False
    assert "no encontrado" in body["error"].lower()


def test_student_deletion_blocked_for_non_students(client, monkeypatch):
    monkeypatch.setenv("ADMIN_TOKEN", "test-admin-token")
    headers = {"X-Admin-Token": "test-admin-token"}

    # Generate unique alias
    rand_suffix = str(random.randint(100000, 999999))
    admin_alias = f"admin_test_user_{rand_suffix}"

    # Seed an admin user in usuarios table (role = 'admin')
    with db_session(write=True) as conn:
        cur = conn.cursor()
        
        # Clean up any potential leftover
        cur.execute("DELETE FROM usuarios WHERE alias = ?;", (admin_alias,))
        
        cur.execute(
            "INSERT INTO usuarios (alias, role, status) VALUES (?, ?, ?);",
            (admin_alias, "admin", "active")
        )
        admin_id = cur.lastrowid

    # Attempt to delete the admin user via the student deletion route
    res = client.delete(f"/api/admin/students/{admin_id}", headers=headers)
    assert res.status_code == 403
    body = res.get_json()
    assert body["ok"] is False
    assert "no se permite eliminar" in body["error"].lower()

    # Verify admin was not deleted
    with db_session() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id FROM usuarios WHERE id = ?;", (admin_id,))
        assert cur.fetchone() is not None
