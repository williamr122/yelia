"""
Proyecto: YELIA4AP
Archivo: create_account.py
Descripción: Script utilitario compatible con PostgreSQL 15 y SQLite legacy para crear cuentas.

Revisión: 2026-06-04
"""
from __future__ import annotations

"""
create_account.py

Corrección aplicada:
- Ya no usa sqlite3.connect directamente.
- Usa backend.db.session.db_session, la misma capa de persistencia del proyecto.
- Funciona con PostgreSQL 15 en Docker y conserva compatibilidad SQLite legacy.
"""

import sys
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash

from backend.db.session import db_session

load_dotenv()


def prompt(msg: str, default: str = "") -> str:
    v = input(f"{msg}{' [' + default + ']' if default else ''}: ").strip()
    return v or default


def _accounts_table_exists(cur) -> bool:
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?;", ("accounts",))
    return cur.fetchone() is not None


def main() -> None:
    username = prompt("Username", "admin2")
    email = prompt("Email", f"{username}@local")
    password = prompt("Password (no se guarda en código)", "")

    if not password:
        print("❌ Password requerido.")
        sys.exit(1)
    if len(password) < 8:
        print("❌ La contraseña debe tener al menos 8 caracteres.")
        sys.exit(1)

    role = prompt("Role (admin/teacher/student)", "admin").lower().strip()
    status = prompt("Status (active/blocked)", "active").lower().strip()

    if role not in ("admin", "teacher", "student"):
        print("❌ Role inválido. Usa admin, teacher o student.")
        sys.exit(1)
    if status not in ("active", "blocked"):
        print("❌ Status inválido. Usa active o blocked.")
        sys.exit(1)

    password_hash = generate_password_hash(password, method="pbkdf2:sha256", salt_length=16)

    try:
        with db_session(write=True) as conn:
            cur = conn.cursor()

            if not _accounts_table_exists(cur):
                print("❌ No existe la tabla accounts. Arranca primero la app para que se cree.")
                sys.exit(1)

            cur.execute("SELECT id FROM accounts WHERE username = ?;", (username,))
            row = cur.fetchone()

            if row:
                cur.execute(
                    """
                    UPDATE accounts
                    SET email = ?, password_hash = ?, role = ?, status = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE username = ?;
                    """,
                    (email, password_hash, role, status, username),
                )
                print(f"✅ OK: '{username}' ya existía → se ACTUALIZÓ (hash + role + status)")
            else:
                cur.execute(
                    """
                    INSERT INTO accounts (username, email, password_hash, role, status)
                    VALUES (?, ?, ?, ?, ?);
                    """,
                    (username, email, password_hash, role, status),
                )
                print("✅ OK: cuenta creada")

            print("👤 Usuario:", username)
            print("🔑 Clave:", password)
            print("🧩 Rol:", role)

    except Exception as e:
        print(f"❌ Error en la base de datos: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
