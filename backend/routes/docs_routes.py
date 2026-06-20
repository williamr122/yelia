"""
Proyecto: YELIA4AP
Archivo: backend/routes/docs_routes.py
Descripción: Módulo del backend para la lógica asociada a esta carpeta/funcionalidad.

Revisión: 2026-02-10
"""
from __future__ import annotations

"""Docs Routes
Archivo del backend del sistema YELIA4AP.

Responsabilidad:
- Implementa la lógica asociada a este módulo.
"""

#
# Archivo: backend/routes/docs_routes.py
# Rol: Módulo del backend (Flask) de YELIA4AP.



import os
from datetime import datetime

from flask import Blueprint, jsonify, request, current_app, g

from ..core.security import require_staff_or_token


docs_bp = Blueprint("docs_bp", __name__)


def _docs_enabled() -> bool:
    """Habilita /docs y /openapi.json solo para personal (admin/docente) o token.

    - En producción, por defecto se exige sesión de staff o ADMIN_TOKEN.
    - Puedes deshabilitar por completo con DISABLE_DOCS=1.
    """
    if (os.getenv("DISABLE_DOCS") or "0").strip() == "1":
        return False
    return require_staff_or_token()


# ============================================================
# 1) OpenAPI (JSON)
# ============================================================
@docs_bp.route("/openapi.json", methods=["GET"])
def openapi_json():
    """Devuelve un OpenAPI 3.0 mínimo para inspección rápida.

    IMPORTANTE:
        - Este spec es intencionalmente "ligero" para no acoplar el backend
          a generadores ni dependencias.
        - Si se agregan nuevas rutas en el futuro, se puede extender fácilmente.
    """

    if not _docs_enabled():
        return jsonify({"success": False, "message": "Docs deshabilitados / no autorizado."}), 401

    base_url = request.host_url.rstrip("/")

    # Mínimo necesario para Swagger UI + jurado (extendible sin acoplar)
    # pueda probar rápido sin adivinar el formato.
    spec = {
        "openapi": "3.0.3",
        "info": {
            "title": "YELIA Backend API",
            "version": os.getenv("API_VERSION", "1.0.0"),
            "description": "API del prototipo YELIA (tesis).",
        },
        "servers": [{"url": base_url}],
        "paths": {
            "/api/chat": {
                "post": {
                    "summary": "Chat principal",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "message": {"type": "string"},
                                        "conversation_id": {"type": "integer"},
                                        "profile": {"type": "object"},
                                    },
                                    "required": ["message"],
                                },
                                "examples": {
                                    "mensaje_simple": {
                                        "summary": "Mensaje normal",
                                        "value": {"message": "Hola YELIA, ¿qué es CRISP-DM?"},
                                    },
                                    "continuar_conversacion": {
                                        "summary": "Continuar conversación existente",
                                        "value": {
                                            "message": "Explícame la fase de Modelado.",
                                            "conversation_id": 12,
                                        },
                                    },
                                    "con_perfil": {
                                        "summary": "Con perfil (contexto académico)",
                                        "value": {
                                            "message": "Hazme un quiz rápido de Programación Avanzada.",
                                            "profile": {
                                                "carrera": "Sistemas de Información",
                                                "nivel": "FII",
                                            },
                                        },
                                    },
                                },
                            }
                        },
                    },
                    "responses": {
                        "200": {
                            "description": "Respuesta del asistente",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "ok": {"type": "boolean"},
                                            "data": {"type": "object"},
                                            "conversation_id": {"type": "integer"},
                                            "reply": {"type": "string"},
                                            "tema": {"type": ["string", "null"]},
                                        },
                                    },
                                    "examples": {
                                        "respuesta_ok": {
                                            "summary": "Respuesta típica",
                                            "value": {
                                                "ok": True,
                                                "conversation_id": 12,
                                                "reply": "CRISP-DM es una metodología...",
                                                "tema": "CRISP-DM",
                                                "data": {
                                                    "conversation_id": 12,
                                                    "reply": "CRISP-DM es una metodología...",
                                                    "tema": "CRISP-DM",
                                                },
                                            },
                                        }
                                    },
                                }
                            },
                        },
                        "4XX": {"description": "Error de validación / negocio"},
                        "5XX": {"description": "Error inesperado"},
                    },
                }
            },
            "/api/history": {"get": {"summary": "Historial reciente", "responses": {"200": {"description": "OK"}}}},
            "/api/conversation/{conv_id}": {
                "get": {
                    "summary": "Detalle conversación",
                    "parameters": [
                        {"name": "conv_id", "in": "path", "required": True, "schema": {"type": "integer"}},
                    ],
                    "responses": {"200": {"description": "OK"}},
                },
                "delete": {
                    "summary": "Eliminar conversación",
                    "parameters": [
                        {"name": "conv_id", "in": "path", "required": True, "schema": {"type": "integer"}},
                    ],
                    "responses": {"200": {"description": "OK"}},
                },
            },
            "/api/conversation/{conv_id}/rename": {
                "post": {
                    "summary": "Renombrar conversación",
                    "parameters": [
                        {"name": "conv_id", "in": "path", "required": True, "schema": {"type": "integer"}},
                    ],
                    "responses": {"200": {"description": "OK"}},
                }
            },
            "/api/temas": {"get": {"summary": "Listado de temas", "responses": {"200": {"description": "OK"}}}},
            "/api/progreso": {"get": {"summary": "Progreso del usuario", "responses": {"200": {"description": "OK"}}}},
            "/api/update-profile": {"post": {"summary": "Actualizar perfil", "responses": {"200": {"description": "OK"}}}},
            "/api/auth/login": {"post": {"summary": "Login", "responses": {"200": {"description": "OK"}}}},
            "/api/auth/logout": {"post": {"summary": "Logout", "responses": {"200": {"description": "OK"}}}},
            "/api/auth/whoami": {"get": {"summary": "Sesión actual", "responses": {"200": {"description": "OK"}}}},
            "/api/attachments/upload": {
                "post": {
                    "summary": "Subir adjunto",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "multipart/form-data": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "file": {"type": "string", "format": "binary"},
                                        "conversation_id": {"type": "integer"},
                                    },
                                    "required": ["file"],
                                },
                                "examples": {
                                    "subir_pdf": {
                                        "summary": "Ejemplo (campos)",
                                        "value": {"conversation_id": 12},
                                    }
                                },
                            }
                        },
                    },
                    "responses": {
                        "200": {
                            "description": "OK",
                            "content": {
                                "application/json": {
                                    "examples": {
                                        "respuesta_ok": {
                                            "summary": "Respuesta típica",
                                            "value": {
                                                "ok": True,
                                                "data": {
                                                    "attachment": {
                                                        "id": 1,
                                                        "original_name": "apuntes.pdf",
                                                        "stored_name": "20260113_011500_apuntes.pdf",
                                                        "mime": "application/pdf",
                                                        "size_bytes": 123456,
                                                        "url": "/static/uploads/20260113_011500_apuntes.pdf",
                                                    }
                                                },
                                            },
                                        }
                                    }
                                }
                            },
                        }
                    },
                }
            },
            "/api/attachments/analyze": {
                "post": {
                    "summary": "Analizar adjunto (extraer texto)",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "id": {"type": "integer"},
                                        "attachment_id": {"type": "integer"},
                                    },
                                    "required": ["id"],
                                },
                                "examples": {
                                    "ejemplo": {
                                        "summary": "Analizar por id",
                                        "value": {"id": 1},
                                    }
                                },
                            }
                        },
                    },
                    "responses": {"200": {"description": "OK"}},
                }
            },
            "/api/metrics": {"get": {"summary": "Métricas básicas", "responses": {"200": {"description": "OK"}}}},
            "/api/recommendations": {"post": {"summary": "Recomendacion de recursos", "responses": {"200": {"description": "OK"}}}},
            "/api/personalized-feedback": {"post": {"summary": "Retroalimentacion personalizada", "responses": {"200": {"description": "OK"}}}},
            "/api/adaptive-plan": {"post": {"summary": "Personalizacion adaptativa", "responses": {"200": {"description": "OK"}}}},
            "/api/feedback": {"post": {"summary": "Feedback", "responses": {"200": {"description": "OK"}}}},
            "/health": {"get": {"summary": "Salud del sistema", "responses": {"200": {"description": "OK"}}}},
            "/api/debug/request-id": {
                "get": {
                    "summary": "Debug: validar request_id",
                    "responses": {"200": {"description": "OK"}},
                }
            },
        },
    }

    return jsonify(spec)


# ============================================================
# 2) Swagger UI (sin dependencias)
# ============================================================

@docs_bp.route("/docs", methods=["GET"])
def swagger_ui():
    """Swagger UI visual para demo."""
    if not _docs_enabled():
        return jsonify({"success": False, "message": "Docs deshabilitados / no autorizado."}), 401

    html = """<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>YELIA API Docs</title>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css"/>
  <style>
    body { margin: 0; background: #ffffff; }
    #swagger-ui { min-height: 100vh; }
  </style>
</head>
<body>
  <div id="swagger-ui"></div>

  <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-standalone-preset.js"></script>

  <script>
    window.onload = function() {
      if (typeof SwaggerUIBundle === "undefined") {
        document.body.innerHTML = `
          <main style="max-width:900px;margin:60px auto;font-family:Arial,sans-serif">
            <h1>YELIA API Docs</h1>
            <p>No se pudo cargar Swagger UI desde CDN, pero la API está disponible.</p>
            <p>Abre <a href="/openapi.json">/openapi.json</a> para ver la especificación completa.</p>
          </main>
        `;
        return;
      }

      SwaggerUIBundle({
        url: "/openapi.json",
        dom_id: "#swagger-ui",
        deepLinking: true,
        displayRequestDuration: true,
        persistAuthorization: true,
        presets: [
          SwaggerUIBundle.presets.apis,
          SwaggerUIStandalonePreset
        ],
        layout: "StandaloneLayout"
      });
    };
  </script>
</body>
</html>"""
    return html

# ============================================================
# 3) Debug endpoint: request-id
# ============================================================
@docs_bp.route("/api/debug/request-id", methods=["GET"])
def debug_request_id():
    """Endpoint de prueba para el jurado.

    Nota:
        - Responde con el request_id actual.
        - Útil para demostrar trazabilidad (headers + logs).
    """

    if not require_staff_or_token():
        return jsonify({"success": False, "message": "No autorizado."}), 401

    # Permite desactivar en producción si se desea
    env = os.getenv("ENV", "development").lower().strip()
    debug_enabled = os.getenv("DEBUG_ENDPOINTS", "1").lower().strip() in ("1", "true", "yes", "y", "on")
    if env not in ("development", "dev", "local") and not debug_enabled:
        return jsonify({"ok": False, "error": "Debug deshabilitado."}), 404

    rid = getattr(g, "request_id", None)
    return jsonify({
        "ok": True,
        "request_id": rid,
        "method": request.method,
        "path": request.path,
        "server_time": datetime.utcnow().isoformat() + "Z",
        "database": current_app.config.get("DATABASE_PATH"),
    })
