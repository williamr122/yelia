"""Small input validation helpers for account and student access."""

from __future__ import annotations

import re
from typing import Optional, Tuple


USERNAME_RE = re.compile(r"^[A-Za-z0-9._-]{4,32}$")
STUDENT_CODE_RE = re.compile(r"^[A-Za-z0-9._-]{4,32}$")


def normalize_identifier(value: str, *, max_len: int = 32) -> str:
    raw = (value or "").strip()
    return "".join(ch for ch in raw if ch.isalnum() or ch in ("-", "_", "."))[:max_len]


def validate_username(value: str) -> Tuple[Optional[str], Optional[str]]:
    username = normalize_identifier(value)
    if not USERNAME_RE.fullmatch(username):
        return None, "El usuario debe tener 4 a 32 caracteres y usar solo letras, numeros, punto, guion o guion bajo."
    return username, None


def validate_student_code(value: str) -> Tuple[Optional[str], Optional[str]]:
    code = normalize_identifier(value)
    if not STUDENT_CODE_RE.fullmatch(code):
        return None, "El codigo o alias debe tener 4 a 32 caracteres y usar solo letras, numeros, punto, guion o guion bajo."
    return code, None


def validate_password(value: str, *, min_len: int = 8, label: str = "La contrasena") -> Optional[str]:
    password = value or ""
    if len(password) < min_len:
        return f"{label} debe tener minimo {min_len} caracteres."
    if len(password) > 128:
        return f"{label} es demasiado larga."
    if password.strip() != password:
        return f"{label} no debe iniciar ni terminar con espacios."
    return None
