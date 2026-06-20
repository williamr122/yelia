"""
Proyecto: YELIA4AP
Archivo: create_admin.py
Descripción: Script utilitario compatible con PostgreSQL 15 y SQLite legacy para crear el primer administrador.

Revisión: 2026-06-04
"""
from __future__ import annotations

"""
create_admin.py

Creación del primer administrador (bootstrap) — YELIA4AP

Corrección aplicada:
- Ya no usa sqlite3.connect directamente.
- Usa backend.db.session.db_session, la misma capa de persistencia del proyecto.
- Funciona con PostgreSQL 15 en Docker y conserva compatibilidad SQLite legacy.
"""

import os
import sys
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash

from backend.db.session import db_session

load_dotenv()

DEFAULT_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
DEFAULT_EMAIL = os.getenv("ADMIN_EMAIL", "admin@yelia.local")
DEFAULT_ROLE = "admin"
DEFAULT_STATUS = "active"


def _accounts_table_exists(cur) -> bool:
    """Verifica si existe la tabla accounts usando la capa compatible del proyecto."""
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?;", ("accounts",))
    return cur.fetchone() is not None


def _admin_exists_conn(conn) -> bool:
    cur = conn.cursor()
    if not _accounts_table_exists(cur):
        return False
    cur.execute("SELECT 1 FROM accounts WHERE role = ? LIMIT 1;", ("admin",))
    return cur.fetchone() is not None


def create_or_update_admin(password: str) -> bool:
    """Crea o actualiza el usuario admin. Retorna True si hizo cambios."""
    if not password or len(password) < 8:
        raise ValueError("La contraseña es obligatoria y debe tener mínimo 8 caracteres.")

    pw_hash = generate_password_hash(password, method="pbkdf2:sha256", salt_length=16)

    with db_session(write=True) as conn:
        cur = conn.cursor()

        if not _accounts_table_exists(cur):
            raise RuntimeError("No existe la tabla accounts. Arranca primero la app para inicializar la base de datos.")

        cur.execute("SELECT id FROM accounts WHERE username = ? LIMIT 1;", (DEFAULT_USERNAME,))
        row = cur.fetchone()

        if row is None:
            cur.execute(
                """
                INSERT INTO accounts (username, email, password_hash, role, status)
                VALUES (?, ?, ?, ?, ?);
                """,
                (DEFAULT_USERNAME, DEFAULT_EMAIL, pw_hash, DEFAULT_ROLE, DEFAULT_STATUS),
            )
            print(f"✅ Usuario '{DEFAULT_USERNAME}' creado.")
            return True

        cur.execute(
            """
            UPDATE accounts
            SET email = ?, password_hash = ?, role = ?, status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE username = ?;
            """,
            (DEFAULT_EMAIL, pw_hash, DEFAULT_ROLE, DEFAULT_STATUS, DEFAULT_USERNAME),
        )
        print(f"✅ Usuario '{DEFAULT_USERNAME}' ya existía → actualizado.")
        return True


def create_initial_admin(app=None) -> bool:
    """Hook llamado desde app.py al iniciar.

    No usa input(). Solo crea admin si ADMIN_PASSWORD o INITIAL_ADMIN_PASSWORD existe.
    Compatible con PostgreSQL 15 mediante backend.db.session.
    """
    password = os.getenv("ADMIN_PASSWORD") or os.getenv("INITIAL_ADMIN_PASSWORD")
    if not password:
        return False

    with db_session(write=False) as conn:
        if _admin_exists_conn(conn):
            return False

    create_or_update_admin(password=password)
    return True


def main() -> None:
    """Ejecución manual local/dev."""
    password = os.getenv("ADMIN_PASSWORD") or os.getenv("INITIAL_ADMIN_PASSWORD")
    if not password:
        password = input("→ Ingresa la contraseña para el usuario admin: ").strip()

    if not password:
        print("❌ La contraseña es obligatoria.")
        sys.exit(1)
    if len(password) < 8:
        print("❌ La contraseña debe tener al mínimo 8 caracteres.")
        sys.exit(1)

    create_or_update_admin(password=password)


if __name__ == "__main__":
    main()
