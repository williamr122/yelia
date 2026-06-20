from __future__ import annotations

import os
from urllib.parse import urlsplit, urlunsplit

from flask import redirect, request


def frontend_base_url() -> str:
    """Return the public Next.js frontend URL used by Flask UI redirects."""
    raw = (
        os.getenv("NEXT_FRONTEND_URL")
        or os.getenv("PUBLIC_FRONTEND_URL")
        or os.getenv("FRONTEND_URL")
        or "http://localhost:3000"
    ).strip()

    if "," in raw:
        raw = raw.split(",", 1)[0].strip()

    return raw.rstrip("/") or "http://localhost:3000"


def frontend_url(path: str | None = None) -> str:
    """Build a Next.js URL preserving query strings for UI routes."""
    target_path = path or request.path or "/"
    if not target_path.startswith("/"):
        target_path = "/" + target_path

    base = frontend_base_url()
    parts = urlsplit(base)
    query = request.query_string.decode("utf-8", errors="ignore")
    return urlunsplit((parts.scheme, parts.netloc, target_path, query, ""))


def frontend_redirect(path: str | None = None, code: int = 302):
    """Redirect legacy Flask UI routes to the Next.js frontend."""
    return redirect(frontend_url(path), code=code)
