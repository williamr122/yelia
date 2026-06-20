"""Learning route API routes."""

from __future__ import annotations

import os
import structlog
from flask import request

from backend.services.learning_route_service import (
    UNITS,
    final_unlocked,
    grade_final_quiz,
    get_route,
    grade_quiz,
    mark_practice,
    public_final_quiz,
    public_quiz,
)
from backend.services.course_content_service import unit_content

from .chat_routes import chat_bp, limiter, _err, _ok, obtener_usuario_actual

logger = structlog.get_logger()


@chat_bp.route("/api/learning-route", methods=["GET"])
@limiter.limit(os.getenv("RATE_LIMIT_LEARNING_ROUTE", "60 per hour"))
def api_learning_route():
    usuario = obtener_usuario_actual()
    try:
        return _ok({"usuario": usuario, "units": UNITS, "route": get_route(usuario)})
    except Exception as exc:
        logger.error("Error cargando ruta de aprendizaje", usuario=usuario, error=str(exc))
        return _err("No se pudo cargar la ruta de aprendizaje.", 500)


@chat_bp.route("/api/learning-route/unit/<int:unit_id>/practice", methods=["POST"])
@limiter.limit(os.getenv("RATE_LIMIT_LEARNING_PRACTICE", "30 per hour"))
def api_learning_practice(unit_id: int):
    usuario = obtener_usuario_actual()
    try:
        return _ok({"usuario": usuario, "route": mark_practice(usuario, unit_id)})
    except Exception as exc:
        logger.error("Error marcando practica", usuario=usuario, unit_id=unit_id, error=str(exc))
        return _err("No se pudo marcar la practica.", 500)


@chat_bp.route("/api/learning-route/unit/<int:unit_id>/content", methods=["GET"])
@limiter.limit(os.getenv("RATE_LIMIT_LEARNING_CONTENT", "60 per hour"))
def api_learning_unit_content(unit_id: int):
    usuario = obtener_usuario_actual()
    try:
        route = get_route(usuario)
        state = route.get("units", {}).get(str(unit_id), {})
        if state.get("status") == "locked":
            return _err("Esta unidad aun esta bloqueada.", 403)
        return _ok(unit_content(unit_id))
    except Exception as exc:
        logger.error("Error cargando contenido de unidad", usuario=usuario, unit_id=unit_id, error=str(exc))
        return _err("No se pudo cargar el contenido de la unidad.", 500)


@chat_bp.route("/api/learning-route/unit/<int:unit_id>/quiz", methods=["GET"])
@limiter.limit(os.getenv("RATE_LIMIT_LEARNING_QUIZ", "60 per hour"))
def api_learning_quiz(unit_id: int):
    usuario = obtener_usuario_actual()
    try:
        route = get_route(usuario)
        state = route.get("units", {}).get(str(unit_id), {})
        if state.get("status") == "locked":
            return _err("Esta unidad aun esta bloqueada.", 403)
        return _ok(public_quiz(unit_id))
    except Exception as exc:
        logger.error("Error cargando quiz", usuario=usuario, unit_id=unit_id, error=str(exc))
        return _err("No se pudo cargar el quiz de unidad.", 500)


@chat_bp.route("/api/learning-route/unit/<int:unit_id>/quiz", methods=["POST"])
@limiter.limit(os.getenv("RATE_LIMIT_LEARNING_QUIZ_SUBMIT", "30 per hour"))
def api_learning_quiz_submit(unit_id: int):
    usuario = obtener_usuario_actual()
    data = request.get_json(silent=True) or {}
    answers = data.get("answers") or {}
    if not isinstance(answers, dict) or not answers:
        return _err("Responde el quiz antes de finalizar.", 400)
    try:
        return _ok({"usuario": usuario, **grade_quiz(usuario, unit_id, answers)})
    except Exception as exc:
        logger.error("Error calificando quiz", usuario=usuario, unit_id=unit_id, error=str(exc))
        return _err("No se pudo calificar el quiz de unidad.", 500)


@chat_bp.route("/api/learning-route/final-quiz", methods=["GET"])
@limiter.limit(os.getenv("RATE_LIMIT_LEARNING_FINAL_QUIZ", "30 per hour"))
def api_learning_final_quiz():
    usuario = obtener_usuario_actual()
    try:
        route = get_route(usuario)
        if not final_unlocked(route):
            return _err("Completa las 4 unidades antes de la evaluacion final.", 403)
        return _ok(public_final_quiz())
    except Exception as exc:
        logger.error("Error cargando evaluacion final", usuario=usuario, error=str(exc))
        return _err("No se pudo cargar la evaluacion final.", 500)


@chat_bp.route("/api/learning-route/final-quiz", methods=["POST"])
@limiter.limit(os.getenv("RATE_LIMIT_LEARNING_FINAL_SUBMIT", "20 per hour"))
def api_learning_final_quiz_submit():
    usuario = obtener_usuario_actual()
    data = request.get_json(silent=True) or {}
    answers = data.get("answers") or {}
    if not isinstance(answers, dict) or not answers:
        return _err("Responde la evaluacion final antes de finalizar.", 400)
    try:
        return _ok({"usuario": usuario, **grade_final_quiz(usuario, answers)})
    except ValueError as exc:
        return _err(str(exc), 403)
    except Exception as exc:
        logger.error("Error calificando evaluacion final", usuario=usuario, error=str(exc))
        return _err("No se pudo calificar la evaluacion final.", 500)
