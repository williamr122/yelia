from __future__ import annotations

import os
from urllib.parse import urlsplit, urlunsplit

from flask import redirect, request, render_template_string


def frontend_base_url() -> str:
    """Return the public Next.js frontend URL used by Flask UI redirects."""
    raw = (
        os.getenv("NEXT_FRONTEND_URL")
        or os.getenv("PUBLIC_FRONTEND_URL")
        or os.getenv("FRONTEND_URL")
        or ""
    ).strip()

    if "," in raw:
        raw = raw.split(",", 1)[0].strip()

    if not raw:
        if "VERCEL" in os.environ:
            return ""
        return "http://localhost:3000"

    return raw.rstrip("/")


def frontend_url(path: str | None = None) -> str:
    """Build a Next.js URL preserving query strings for UI routes."""
    target_path = path or request.path or "/"
    if not target_path.startswith("/"):
        target_path = "/" + target_path

    base = frontend_base_url()
    if not base:
        return target_path
    parts = urlsplit(base)
    query = request.query_string.decode("utf-8", errors="ignore")
    return urlunsplit((parts.scheme, parts.netloc, target_path, query, ""))


def render_backend_landing_page():
    html = """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>YELIA4AP - API Backend</title>
        <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&display=swap" rel="stylesheet">
        <style>
            :root {
                --bg: #0b0f19;
                --card-bg: rgba(255, 255, 255, 0.03);
                --card-border: rgba(255, 255, 255, 0.08);
                --text: #f3f4f6;
                --text-muted: #9ca3af;
                --primary: #6366f1;
                --primary-glow: rgba(99, 102, 241, 0.15);
                --success: #10b981;
            }
            body {
                margin: 0;
                padding: 0;
                font-family: 'Outfit', sans-serif;
                background-color: var(--bg);
                color: var(--text);
                display: flex;
                align-items: center;
                justify-content: center;
                min-height: 100vh;
                overflow-x: hidden;
            }
            .background-glow {
                position: absolute;
                width: 400px;
                height: 400px;
                background: radial-gradient(circle, var(--primary-glow) 0%, transparent 70%);
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                z-index: 1;
                pointer-events: none;
            }
            .container {
                position: relative;
                z-index: 2;
                max-width: 600px;
                width: 90%;
                padding: 2.5rem;
                background: var(--card-bg);
                border: 1px solid var(--card-border);
                border-radius: 24px;
                backdrop-filter: blur(16px);
                box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
                text-align: center;
                animation: fadeIn 0.8s ease-out;
            }
            @keyframes fadeIn {
                from { opacity: 0; transform: translateY(20px); }
                to { opacity: 1; transform: translateY(0); }
            }
            .status-badge {
                display: inline-flex;
                align-items: center;
                gap: 8px;
                padding: 6px 16px;
                background: rgba(16, 185, 129, 0.1);
                border: 1px solid rgba(16, 185, 129, 0.2);
                color: var(--success);
                font-weight: 600;
                font-size: 0.875rem;
                border-radius: 100px;
                margin-bottom: 1.5rem;
            }
            .status-dot {
                width: 8px;
                height: 8px;
                background-color: var(--success);
                border-radius: 50%;
                box-shadow: 0 0 8px var(--success);
                animation: pulse 2s infinite;
            }
            @keyframes pulse {
                0% { transform: scale(0.95); opacity: 0.5; }
                50% { transform: scale(1.1); opacity: 1; }
                100% { transform: scale(0.95); opacity: 0.5; }
            }
            h1 {
                margin: 0 0 1rem 0;
                font-size: 2.25rem;
                font-weight: 800;
                background: linear-gradient(135deg, #fff 0%, #a5b4fc 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
            }
            p {
                font-size: 1.05rem;
                line-height: 1.6;
                color: var(--text-muted);
                margin-bottom: 2rem;
            }
            .card-instructions {
                text-align: left;
                background: rgba(0, 0, 0, 0.2);
                border-radius: 16px;
                padding: 1.5rem;
                margin-bottom: 2rem;
                border: 1px solid rgba(255, 255, 255, 0.03);
            }
            .card-instructions h2 {
                font-size: 1.15rem;
                margin-top: 0;
                color: #fff;
                font-weight: 600;
            }
            .card-instructions ol {
                margin: 0;
                padding-left: 1.25rem;
                color: var(--text-muted);
                font-size: 0.95rem;
                line-height: 1.5;
            }
            .card-instructions li {
                margin-bottom: 0.75rem;
            }
            .code-block {
                background: #111827;
                padding: 4px 8px;
                border-radius: 6px;
                font-family: monospace;
                color: #e5e7eb;
                border: 1px solid rgba(255, 255, 255, 0.05);
            }
            .footer {
                font-size: 0.825rem;
                color: rgba(255, 255, 255, 0.2);
                margin-top: 2rem;
                border-top: 1px solid rgba(255, 255, 255, 0.05);
                padding-top: 1.25rem;
            }
        </style>
    </head>
    <body>
        <div class="background-glow"></div>
        <div class="container">
            <div class="status-badge">
                <span class="status-dot"></span>
                <span>API Servidor Activo</span>
            </div>
            <h1>YELIA4AP Backend</h1>
            <p>
                El motor del asistente virtual de programación está funcionando correctamente en Vercel, pero has accedido directamente al enlace de la API.
            </p>
            <div class="card-instructions">
                <h2>¿Cómo ingresar a la aplicación?</h2>
                <ol>
                    <li>Abre el enlace de tu despliegue del <strong>frontend de Next.js</strong> (no este enlace de Flask).</li>
                    <li>
                        Si deseas que este enlace te redirija automáticamente al frontend, configura la variable de entorno <span class="code-block">FRONTEND_URL</span> en los ajustes del proyecto de Vercel de este backend apuntando a tu dominio de Next.js:
                        <br><br>
                        Ejemplo: <span class="code-block">FRONTEND_URL=https://tu-proyecto-frontend.vercel.app</span>
                    </li>
                </ol>
            </div>
            <div class="footer">
                Proyecto Académico de Titulación — YELIA4AP
            </div>
        </div>
    </body>
    </html>
    """
    return render_template_string(html)


def frontend_redirect(path: str | None = None, code: int = 302):
    """Redirect legacy Flask UI routes to the Next.js frontend."""
    base = frontend_base_url()
    if not base:
        return render_backend_landing_page()
    return redirect(frontend_url(path), code=code)
