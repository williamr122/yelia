"""
Proyecto: YELIA4AP
Archivo: backend/routes/export_routes.py
Descripción: Módulo del backend para la lógica asociada a esta carpeta/funcionalidad.

Revisión: 2026-02-10
"""
from __future__ import annotations

"""
Archivo: backend/routes/export_routes.py
Proyecto: YELIA4AP
Última revisión: 2026-02-10

Módulo de backend en Python.

Convenciones:
- Funciones pequeñas, nombres descriptivos y manejo de errores explícito.
- Evitar prints en producción: usar logging si aplica.
"""


#
# Archivo: backend/routes/export_routes.py
# Rol: Módulo del backend (Flask) de YELIA4AP.

"""Export Routes
Archivo del backend del sistema YELIA4AP.

Responsabilidad:
- Implementa la lógica asociada a este módulo.

backend/routes/export_routes.py

Exportación CSV — YELIA

Endpoints pensados para auditoría/backup rápido en prototipo:
- /api/export/students.csv
- /api/export/attachments.csv
- /api/export/metrics.csv
- /api/export/student/<alias>/activity.csv

Acceso:
- Sesión role admin/teacher, o ADMIN_TOKEN (dev/local/test).
"""
# =====================================
# Imports
# =====================================


import csv
import io
from typing import Any, Dict, List, Optional, Tuple

import structlog
from flask import Blueprint, Response, request, session

# PDF (reportlab)
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

from backend.db.session import db_session
from backend.core.security import require_admin_token


# =====================================
# Configuración / Constantes
# =====================================
logger = structlog.get_logger()

export_bp = Blueprint("export", __name__)
# =====================================
# Funciones / Clases
# =====================================


def _session_role() -> str:
    return (session.get("admin_role") or session.get("teacher_role") or session.get("role") or "").strip().lower()

def _require_admin_or_teacher() -> Optional[Tuple[Any, int]]:
    role = _session_role()
    if role in ("admin", "teacher", "docente"):
        return None
    if require_admin_token():
        return None
    return ({"ok": False, "error": "No autorizado."}, 401)

def _csv_response(filename: str, rows: List[Dict[str, Any]]) -> Response:
    output = io.StringIO()
    if not rows:
        # Aun así devolvemos CSV válido con header vacío
        output.write("")
        data = output.getvalue()
        return Response(
            data,
            mimetype="text/csv; charset=utf-8",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    # Orden estable: primero keys del primer row
    fieldnames = list(rows[0].keys())
    writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    for r in rows:
        writer.writerow({k: ("" if r.get(k) is None else r.get(k)) for k in fieldnames})

    data = output.getvalue()
    return Response(
        data,
        mimetype="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )

def _pdf_response(filename: str, build_fn) -> Response:
    """Genera un PDF con reportlab usando un builder que escribe sobre canvas."""
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    try:
        build_fn(c)
        c.showPage()
        c.save()
    except Exception:
        # Si falla, intentar cerrar de todas formas
        try:
            c.showPage(); c.save()
        except Exception:
            pass
        raise
    pdf_bytes = buf.getvalue()
    return Response(
        pdf_bytes,
        mimetype="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )

@export_bp.get("/api/export/students.csv")
def export_students_csv():
    denied = _require_admin_or_teacher()
    if denied is not None:
        payload, status = denied
        return payload, status

    q = (request.args.get("q") or "").strip().lower()

    sql = """
    SELECT
        u.id, u.alias, COALESCE(u.email,'') AS email,
        COALESCE(u.role,'student') AS role,
        COALESCE(u.status,'active') AS status,
        u.created_at, u.last_seen,
        COALESCE(p.puntos,0) AS puntos,
        COALESCE(p.temas_aprendidos,0) AS temas_aprendidos,
        COALESCE(p.ciclo_academico,'') AS ciclo_academico,
        COALESCE(p.estado_materia,'') AS estado_materia,
        COALESCE(p.updated_at,'') AS progreso_updated_at
    FROM usuarios u
    LEFT JOIN progreso p ON p.usuario = u.alias
    WHERE 1=1
    """
    params: List[Any] = []
    if q:
        sql += " AND (LOWER(u.alias) LIKE ? OR LOWER(COALESCE(u.email,'')) LIKE ?)"
        like = f"%{q}%"
        params.extend([like, like])

    sql += " ORDER BY u.created_at DESC LIMIT 2000;"

    with db_session() as conn:
        cur = conn.cursor()
        cur.execute(sql, tuple(params))
        rows = [dict(r) for r in cur.fetchall()]

    return _csv_response("yelia_students.csv", rows)

@export_bp.get("/api/export/attachments.csv")
def export_attachments_csv():
    denied = _require_admin_or_teacher()
    if denied is not None:
        payload, status = denied
        return payload, status

    with db_session() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, created_at, usuario, original_name, mime, size_bytes, url, conversation_id
            FROM attachments
            ORDER BY id DESC
            LIMIT 2000;
            """
        )
        rows = [dict(r) for r in cur.fetchall()]
    return _csv_response("yelia_attachments.csv", rows)



@export_bp.get("/api/export/chats.csv")
def export_chats_csv():
    """Exporta conversaciones (chats) con filtros opcionales: q, student, days."""
    denied = _require_admin_or_teacher()
    if denied is not None:
        payload, status = denied
        return payload, status

    q = (request.args.get("q") or "").strip().lower()
    student = (request.args.get("student") or "").strip()
    try:
        days = int(request.args.get("days") or 0)
    except Exception:
        days = 0
    days = max(0, min(days, 365))

    where = []
    params: List[Any] = []
    if q:
        where.append("(LOWER(COALESCE(c.usuario,'')) LIKE ? OR LOWER(COALESCE(c.titulo,'')) LIKE ?)")
        like = f"%{q}%"
        params.extend([like, like])
    if student:
        where.append("LOWER(COALESCE(c.usuario,'')) = LOWER(?)")
        params.append(student)
    if days and days > 0:
        where.append("datetime(c.created_at) >= datetime('now', ?)")
        params.append(f"-{days} days")

    where_sql = (" WHERE " + " AND ".join(where)) if where else ""
    sql = f"""
      SELECT c.id, c.usuario, c.titulo AS title, c.created_at,
             COALESCE((SELECT MAX(m.created_at) FROM messages m WHERE m.conv_id=c.id), c.created_at) AS updated_at
      FROM conversaciones c
      {where_sql}
      ORDER BY c.id DESC
      LIMIT 3000;
    """

    with db_session() as conn:
        cur = conn.cursor()
        cur.execute(sql, tuple(params))
        rows = [dict(r) for r in cur.fetchall()]

    return _csv_response("yelia_chats.csv", rows)


@export_bp.get("/api/export/audit.pdf")
def export_audit_pdf():
    """Reporte PDF rápido (auditoría) de chats/adjuntos.

    Params:
        tab: 'chats'|'att'  (qué tabla priorizar)
        q, student, days: mismos filtros
    """
    denied = _require_admin_or_teacher()
    if denied is not None:
        payload, status = denied
        return payload, status

    tab = (request.args.get("tab") or "chats").strip().lower()
    q = (request.args.get("q") or "").strip().lower()
    student = (request.args.get("student") or "").strip()
    try:
        days = int(request.args.get("days") or 0)
    except Exception:
        days = 0
    days = max(0, min(days, 365))

    # Reutiliza consultas simples (top 60)
    def _fetch_chats():
        where = []
        params: List[Any] = []
        if q:
            where.append("(LOWER(COALESCE(c.usuario,'')) LIKE ? OR LOWER(COALESCE(c.titulo,'')) LIKE ?)")
            like = f"%{q}%"; params.extend([like, like])
        if student:
            where.append("LOWER(COALESCE(c.usuario,'')) = LOWER(?)"); params.append(student)
        if days and days > 0:
            where.append("datetime(c.created_at) >= datetime('now', ?)"); params.append(f"-{days} days")
        where_sql = (" WHERE " + " AND ".join(where)) if where else ""
        sql = f"""
          SELECT c.id, c.usuario, c.titulo AS title, c.created_at,
                 COALESCE((SELECT MAX(m.created_at) FROM messages m WHERE m.conv_id=c.id), c.created_at) AS updated_at
          FROM conversaciones c
          {where_sql}
          ORDER BY c.id DESC
          LIMIT 60;
        """
        with db_session() as conn:
            cur = conn.cursor(); cur.execute(sql, tuple(params));
            return [dict(r) for r in cur.fetchall()]

    def _fetch_atts():
        where = []
        params: List[Any] = []
        if q:
            where.append("(LOWER(COALESCE(usuario,'')) LIKE ? OR LOWER(COALESCE(original_name,'')) LIKE ? OR LOWER(COALESCE(mime,'')) LIKE ?)")
            like = f"%{q}%"; params.extend([like, like, like])
        if student:
            where.append("LOWER(COALESCE(usuario,'')) = LOWER(?)"); params.append(student)
        if days and days > 0:
            where.append("datetime(created_at) >= datetime('now', ?)"); params.append(f"-{days} days")
        where_sql = (" WHERE " + " AND ".join(where)) if where else ""
        sql = f"""
          SELECT id, created_at, usuario, original_name, mime, size_bytes, url
          FROM attachments
          {where_sql}
          ORDER BY id DESC
          LIMIT 60;
        """
        with db_session() as conn:
            cur = conn.cursor(); cur.execute(sql, tuple(params));
            return [dict(r) for r in cur.fetchall()]

    chats = _fetch_chats()
    atts = _fetch_atts()

    def build(c):
        w, h = letter
        x = 0.7*inch
        y = h - 0.75*inch
        c.setFont("Helvetica-Bold", 14)
        c.drawString(x, y, "YELIA — Reporte de Auditoría")
        y -= 0.25*inch
        c.setFont("Helvetica", 9)
        subtitle = f"Filtro: q='{q or '-'}' • estudiante='{student or '-'}' • rango={days or 'todo'}"
        c.drawString(x, y, subtitle)
        y -= 0.35*inch

        def section(title, rows, cols):
            nonlocal y
            c.setFont("Helvetica-Bold", 11)
            c.drawString(x, y, title)
            y -= 0.18*inch
            c.setFont("Helvetica", 8)
            # headers
            c.drawString(x, y, " | ".join(cols))
            y -= 0.14*inch
            c.setLineWidth(0.5)
            c.line(x, y, w - x, y)
            y -= 0.12*inch
            for r in rows:
                if y < 0.9*inch:
                    c.showPage()
                    y = h - 0.75*inch
                    c.setFont("Helvetica", 8)
                vals = []
                for col in cols:
                    v = r.get(col) if col in r else r.get(col.lower())
                    s = "" if v is None else str(v)
                    s = s.replace("\n", " ").strip()
                    if len(s) > 60:
                        s = s[:57] + "..."
                    vals.append(s)
                c.drawString(x, y, " | ".join(vals))
                y -= 0.14*inch
            y -= 0.25*inch

        if tab in ("att", "attachments"):
            section("Adjuntos (top 60)", atts, ["id","usuario","original_name","mime","created_at"])
            section("Chats (top 60)", chats, ["id","usuario","title","created_at","updated_at"])
        else:
            section("Chats (top 60)", chats, ["id","usuario","title","created_at","updated_at"])
            section("Adjuntos (top 60)", atts, ["id","usuario","original_name","mime","created_at"])

        c.setFont("Helvetica-Oblique", 8)
        c.drawString(x, 0.65*inch, "Generado por YELIA (prototipo) — solo lectura.")

    return _pdf_response("yelia_audit.pdf", build)

@export_bp.get("/api/export/metrics.csv")
def export_metrics_csv():
    denied = _require_admin_or_teacher()
    if denied is not None:
        payload, status = denied
        return payload, status

    with db_session() as conn:
        cur = conn.cursor()
        # Export de metrics_events (hasta 5000 filas).
        # La BD puede no tener columnas nuevas (nivel_detectado/quality_score),
        # así que armamos el SELECT según el esquema real.
        cur.execute("PRAGMA table_info(metrics_events);")
        mcols = {r[1] for r in cur.fetchall()}
        select_cols = ["id", "created_at", "usuario", "tema", "confusion_detectada"]
        if "nivel_detectado" in mcols:
            select_cols.insert(4, "nivel_detectado")
        if "quality_score" in mcols:
            select_cols.append("quality_score")

        cur.execute(
            f"""SELECT {", ".join(select_cols)}
                 FROM metrics_events
                 ORDER BY id DESC
                 LIMIT 5000;"""
        )
        rows = [dict(r) for r in cur.fetchall()]
    return _csv_response("yelia_metrics.csv", rows)

@export_bp.get("/api/export/student/<alias>/activity.csv")
def export_student_activity_csv(alias: str):
    denied = _require_admin_or_teacher()
    if denied is not None:
        payload, status = denied
        return payload, status

    alias = (alias or "").strip()
    if not alias:
        return {"ok": False, "error": "Alias requerido."}, 400

    rows: List[Dict[str, Any]] = []
    with db_session() as conn:
        cur = conn.cursor()
        # Interacciones
        cur.execute(
            """
            SELECT created_at, usuario, tema, dificultad, confusion
            FROM interacciones
            WHERE usuario = ?
            ORDER BY created_at DESC
            LIMIT 500;
            """,
            (alias,),
        )
        for r in cur.fetchall():
            d = dict(r)
            d["tipo"] = "interaccion"
            rows.append(d)

        # Conversaciones (meta)
        cur.execute(
            """
            SELECT c.id AS conv_id,
                   COALESCE(c.titulo,'') AS title,
                   c.created_at,
                   COALESCE((SELECT MAX(created_at) FROM messages m WHERE m.conv_id = c.id), c.created_at) AS updated_at,
                   COALESCE(c.focus_topic,'') AS focus_topic
            FROM conversaciones c
            WHERE c.usuario = ?
            ORDER BY updated_at DESC
            LIMIT 200;
            """,
            (alias,),
        )
        for r in cur.fetchall():
            d = dict(r)
            d["tipo"] = "conversacion"
            rows.append(d)

        # Adjuntos
        cur.execute(
            """
            SELECT id, created_at, usuario, original_name, mime, size_bytes, url, conversation_id
            FROM attachments
            WHERE usuario = ?
            ORDER BY created_at DESC
            LIMIT 500;
            """,
            (alias,),
        )
        for r in cur.fetchall():
            d = dict(r)
            d["tipo"] = "adjunto"
            rows.append(d)

    # Ordena por created_at si existe
    def _k(x: Dict[str, Any]):
        return x.get("created_at") or ""
    rows.sort(key=_k, reverse=True)

    return _csv_response(f"yelia_activity_{alias}.csv", rows)


@export_bp.post("/api/export/quiz-report.pdf")
def export_quiz_report_pdf():
    # 1. Comprobar configuración global de descarga
    with db_session() as conn:
        cur = conn.cursor()
        cur.execute("SELECT value FROM global_settings WHERE key = 'allow_pdf_download';")
        row = cur.fetchone()
        allow_download = row["value"] if row else "1"
        
    is_staff = (session.get("teacher_role") or "").strip().lower() in ("admin", "docente", "teacher")
    if allow_download == "0" and not is_staff:
        return {"success": False, "message": "La descarga de reportes PDF ha sido desactivada por el docente."}, 403

    # 2. Leer payload JSON
    data = request.get_json(silent=True) or {}
    if not data:
        return {"success": False, "message": "Payload JSON vacío o inválido."}, 400

    # 3. Generar PDF usando ReportLab Platypus
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=letter,
        rightMargin=54,
        leftMargin=54,
        topMargin=54,
        bottomMargin=54
    )
    
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=colors.HexColor('#1e3a8a'),
        spaceAfter=6
    )
    
    meta_label_style = ParagraphStyle(
        'MetaLabel',
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=11,
        textColor=colors.HexColor('#4b5563')
    )
    
    meta_val_style = ParagraphStyle(
        'MetaValue',
        fontName='Helvetica',
        fontSize=9,
        leading=11,
        textColor=colors.HexColor('#1f2937')
    )
    
    score_pass_style = ParagraphStyle(
        'ScorePass',
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=14,
        textColor=colors.HexColor('#047857'),
        alignment=1
    )
    
    score_fail_style = ParagraphStyle(
        'ScoreFail',
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=14,
        textColor=colors.HexColor('#b91c1c'),
        alignment=1
    )
    
    q_num_style = ParagraphStyle(
        'QNum',
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=13,
        textColor=colors.HexColor('#1e3a8a'),
        spaceAfter=3
    )
    
    q_text_style = ParagraphStyle(
        'QText',
        fontName='Helvetica',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#1f2937'),
        spaceAfter=6
    )
    
    ans_correct_style = ParagraphStyle(
        'AnsCorrect',
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#047857')
    )
    
    ans_incorrect_style = ParagraphStyle(
        'AnsIncorrect',
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#b91c1c')
    )
    
    ans_info_style = ParagraphStyle(
        'AnsInfo',
        fontName='Helvetica',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#4b5563')
    )

    story = []
    
    # Header Table
    left_header = f"<b>YELIA4AP</b><br/><font size=10 color='#4b5563'>Reporte de Evaluación de Estudiante</font>"
    
    score_num = data.get("percent", 0)
    passed = score_num >= 70
    status_text = "APROBADO" if passed else "REPROBADO"
    score_html = f"<font size=20><b>{score_num}%</b></font><br/><font size=9><b>{status_text}</b></font>"
    
    header_data = [
        [Paragraph(left_header, title_style), Paragraph(score_html, score_pass_style if passed else score_fail_style)]
    ]
    header_table = Table(header_data, colWidths=[360, 144])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ALIGN', (1,0), (1,0), 'CENTER'),
        ('BACKGROUND', (1,0), (1,0), colors.HexColor('#ecfdf5') if passed else colors.HexColor('#fef2f2')),
        ('BOX', (1,0), (1,0), 1, colors.HexColor('#10b981') if passed else colors.HexColor('#f87171')),
        ('BOTTOMPADDING', (1,0), (1,0), 8),
        ('TOPPADDING', (1,0), (1,0), 8),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 12))
    
    # Metadata Table
    meta_data = [
        [Paragraph("Estudiante (Alias):", meta_label_style), Paragraph(data.get("alias", "Invitado"), meta_val_style),
         Paragraph("Tipo de Prueba:", meta_label_style), Paragraph(data.get("type_label", "Evaluación"), meta_val_style)],
        [Paragraph("Unidad / Tema:", meta_label_style), Paragraph(data.get("unit_title", "General"), meta_val_style),
         Paragraph("Resultado:", meta_label_style), Paragraph(f"{data.get('score', 0)} / {data.get('total', 0)} respuestas correctas", meta_val_style)]
    ]
    meta_table = Table(meta_data, colWidths=[100, 152, 100, 152])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f9fafb')),
        ('PADDING', (0,0), (-1,-1), 6),
        ('LINEBELOW', (0,0), (-1,-1), 0.5, colors.HexColor('#e5e7eb')),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 15))
    
    # Questions heading
    story.append(Paragraph("<b>Detalle del Examen:</b>", styles['Heading3']))
    story.append(Spacer(1, 8))
    
    # Questions rendering
    for idx, q in enumerate(data.get("questions", [])):
        q_story = []
        q_story.append(Paragraph(f"Pregunta {idx + 1}: {q.get('topic', '')}", q_num_style))
        q_story.append(Paragraph(q.get("question", ""), q_text_style))
        
        options = q.get("options", [])
        selected_idx = q.get("selected")
        correct_idx = q.get("correct")
        
        for opt_idx, opt_text in enumerate(options):
            prefix = f"{chr(65 + opt_idx)}) "
            is_selected = (selected_idx == opt_idx)
            is_correct_option = (correct_idx == opt_idx)
            
            if is_selected:
                if is_correct_option:
                    p_text = f"<b>{prefix}{opt_text}</b> — <i>(Tu respuesta, CORRECTA)</i>"
                    style = ans_correct_style
                else:
                    p_text = f"<b>{prefix}{opt_text}</b> — <i>(Tu respuesta, INCORRECTA)</i>"
                    style = ans_incorrect_style
            elif is_correct_option:
                p_text = f"{prefix}{opt_text} — <i>(Respuesta correcta)</i>"
                style = ans_correct_style
            else:
                p_text = f"{prefix}{opt_text}"
                style = ans_info_style
                
            q_story.append(Paragraph(p_text, style))
            q_story.append(Spacer(1, 3))
            
        q_story.append(Spacer(1, 8))
        story.append(KeepTogether(q_story))
        
    def add_footer(canvas, doc):
        canvas.saveState()
        canvas.setFont('Helvetica-Oblique', 8)
        canvas.setFillColor(colors.HexColor('#9ca3af'))
        canvas.drawString(54, 30, "Reporte generado por YELIA4AP — Asistente de Apoyo en POO.")
        canvas.drawRightString(doc.pagesize[0] - 54, 30, f"Página {doc.page}")
        canvas.restoreState()
        
    doc.build(story, onFirstPage=add_footer, onLaterPages=add_footer)
    
    pdf_bytes = buf.getvalue()
    filename = f"Reporte_{data.get('type_label', 'Evaluacion').replace(' ', '_')}_{data.get('alias', 'Invitado')}.pdf"
    
    return Response(
        pdf_bytes,
        mimetype="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
