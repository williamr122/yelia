from __future__ import annotations

"""Heuristica ligera para activar busqueda web solo cuando aporta valor."""

import re
import unicodedata
from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class WebSearchDecision:
    enabled: bool
    reason: str
    score: int


def _norm(text: str) -> str:
    text = (text or "").strip().lower()
    return "".join(c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn")


_DIRECT_WEB_TERMS = (
    "busca en internet",
    "buscar en internet",
    "busca en la web",
    "buscar en la web",
    "consulta internet",
    "conectado a internet",
    "busqueda web",
    "busquedas web",
    "googlea",
    "investiga en internet",
)

_FRESH_TERMS = (
    "actual",
    "actualizado",
    "actualizada",
    "reciente",
    "recientes",
    "ultimo",
    "ultima",
    "ultimos",
    "ultimas",
    "hoy",
    "ayer",
    "esta semana",
    "este mes",
    "este ano",
    "noticia",
    "noticias",
    "novedades",
    "version nueva",
    "ultima version",
    "precio",
    "precios",
)

_SOURCE_TERMS = (
    "fuente",
    "fuentes",
    "cita",
    "citas",
    "link",
    "links",
    "enlace",
    "enlaces",
    "url",
    "pagina oficial",
    "documentacion oficial",
    "docs",
    "paper",
    "articulo",
)

_RECOMMENDATION_TERMS = (
    "recomienda",
    "recomendacion",
    "recomendaciones",
    "tutorial",
    "curso",
    "recurso",
    "recursos",
    "guia",
    "guia oficial",
)


def decide_web_search(text: str) -> WebSearchDecision:
    """Decide si la pregunta debe ir con herramienta web/grounding."""
    q = _norm(text)
    if not q:
        return WebSearchDecision(False, "empty", 0)

    score = 0
    reasons: list[str] = []

    if any(term in q for term in _DIRECT_WEB_TERMS):
        score += 4
        reasons.append("direct_web_request")

    if any(term in q for term in _FRESH_TERMS):
        score += 2
        reasons.append("freshness")

    if any(term in q for term in _SOURCE_TERMS):
        score += 2
        reasons.append("sources")

    if any(term in q for term in _RECOMMENDATION_TERMS):
        score += 1
        reasons.append("recommendations")

    current_year = date.today().year
    years = [int(y) for y in re.findall(r"\b(20\d{2})\b", q)]
    if any(y >= current_year - 1 for y in years):
        score += 2
        reasons.append("recent_year")

    if "mejor" in q and any(term in q for term in ("libreria", "framework", "modelo", "api", "herramienta")):
        score += 1
        reasons.append("current_recommendation")

    enabled = score >= 2
    return WebSearchDecision(enabled, ",".join(reasons) if reasons else "not_needed", score)


def should_use_web_search(text: str) -> bool:
    return decide_web_search(text).enabled
