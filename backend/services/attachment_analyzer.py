"""
Proyecto: YELIA4AP
Archivo: backend/services/attachment_analyzer.py
Descripción: Módulo del backend para la lógica asociada a esta carpeta/funcionalidad.

Revisión: 2026-02-10
"""
from __future__ import annotations

"""
Archivo: backend/services/attachment_analyzer.py
Proyecto: YELIA4AP
Última revisión: 2026-02-10

Módulo de backend en Python.

Convenciones:
- Funciones pequeñas, nombres descriptivos y manejo de errores explícito.
- Evitar prints en producción: usar logging si aplica.
"""


#
# Archivo: backend/services/attachment_analyzer.py
# Rol: Módulo del backend (Flask) de YELIA4AP.


"""Attachment Analyzer
Archivo del backend del sistema YELIA4AP.

Responsabilidad:
- Implementa la lógica asociada a este módulo.

backend/services/attachment_analyzer.py

Backend Flask — YELIA

Propósito:
    Extraer texto/estructura básica desde archivos adjuntos (PDF, DOCX, TXT, imágenes).
    Esto permite que el chat "entienda" el contenido del archivo y lo use como contexto.

Notas de implementación:
    - Este módulo NO llama al LLM. Solo extrae contenido.
    - OCR en imágenes es opcional: si pytesseract/Tesseract no está disponible,
      se retorna un mensaje informativo.
    - Se usan imports "lazy" (dentro de funciones) para evitar romper el servidor
      si una dependencia no está instalada.
"""
# =====================================
# Imports
# =====================================


from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Dict, Any
import os
import shutil



# =====================================
# Configuración / Constantes
# =====================================
@dataclass
# =====================================
# Funciones / Clases
# =====================================

class ExtractResult:
    """Resultado de extracción."""
    ok: bool
    text: str
    meta: Dict[str, Any]
    error: Optional[str] = None


_TEXT_LIMIT_CHARS = 60_000  # límite de seguridad (prompt/contexto)


def _clip(text: str, limit: int = _TEXT_LIMIT_CHARS) -> str:
    """Recorta el texto para evitar prompts gigantes."""
    if not text:
        return ""
    text = str(text)
    if len(text) <= limit:
        return text
    return text[: limit - 200] + "\n\n...[TRUNCADO]...\n"


def _read_txt(path: Path) -> ExtractResult:
    try:
        raw = path.read_text(encoding="utf-8", errors="ignore")
        return ExtractResult(ok=True, text=_clip(raw), meta={"type": "txt"})
    except Exception as e:
        return ExtractResult(ok=False, text="", meta={"type": "txt"}, error=str(e))


def _read_docx(path: Path) -> ExtractResult:
    try:
        from docx import Document  # type: ignore

        doc = Document(str(path))
        parts = []
        for p in doc.paragraphs:
            t = (p.text or "").strip()
            if t:
                parts.append(t)
        raw = "\n".join(parts)
        return ExtractResult(ok=True, text=_clip(raw), meta={"type": "docx", "paragraphs": len(parts)})
    except ModuleNotFoundError:
        return ExtractResult(
            ok=False,
            text="",
            meta={"type": "docx"},
            error="Dependencia faltante: python-docx. Instala: pip install python-docx",
        )
    except Exception as e:
        return ExtractResult(ok=False, text="", meta={"type": "docx"}, error=str(e))


def _read_pdf(path: Path) -> ExtractResult:
    # 1) Intento con pypdf (simple)
    try:
        from pypdf import PdfReader  # type: ignore

        reader = PdfReader(str(path))
        pages_text = []
        for i, page in enumerate(reader.pages):
            try:
                t = page.extract_text() or ""
            except Exception:
                t = ""
            if t.strip():
                pages_text.append(f"[Página {i+1}]\n{t.strip()}\n")

        raw = "\n".join(pages_text).strip()
        if raw:
            return ExtractResult(
                ok=True,
                text=_clip(raw),
                meta={"type": "pdf", "pages": len(reader.pages), "method": "pypdf"},
            )
    except ModuleNotFoundError:
        # seguimos a pdfplumber
        pass
    except Exception:
        # seguimos a pdfplumber
        pass

    # 2) Fallback con pdfplumber (a veces extrae mejor)
    try:
        import pdfplumber  # type: ignore

        pages_text = []
        with pdfplumber.open(str(path)) as pdf:
            for i, page in enumerate(pdf.pages):
                t = (page.extract_text() or "").strip()
                if t:
                    pages_text.append(f"[Página {i+1}]\n{t}\n")

        raw = "\n".join(pages_text).strip()
        if raw:
            return ExtractResult(
                ok=True,
                text=_clip(raw),
                meta={"type": "pdf", "pages": len(pages_text), "method": "pdfplumber"},
            )

        return ExtractResult(
            ok=False,
            text="",
            meta={"type": "pdf", "method": "pdfplumber"},
            error="No se pudo extraer texto del PDF (posible PDF escaneado).",
        )
    except ModuleNotFoundError:
        return ExtractResult(
            ok=False,
            text="",
            meta={"type": "pdf"},
            error="Dependencia faltante: pypdf o pdfplumber. Instala: pip install pypdf pdfplumber",
        )
    except Exception as e:
        return ExtractResult(ok=False, text="", meta={"type": "pdf"}, error=str(e))


def _configure_tesseract(pytesseract_module) -> Dict[str, Any]:
    """Configura la ruta de Tesseract si es necesario.

    Orden de prioridad:
    1) Variable de entorno TESSERACT_CMD
    2) tesseract disponible en PATH
    3) Rutas típicas de Windows
    """
    meta: Dict[str, Any] = {"tesseract": {"configured": False}}

    # 1) env var
    env_cmd = os.getenv("TESSERACT_CMD", "").strip()
    if env_cmd:
        if Path(env_cmd).exists():
            pytesseract_module.pytesseract.tesseract_cmd = env_cmd
            meta["tesseract"] = {"configured": True, "source": "env", "path": env_cmd}
            return meta
        meta["tesseract"] = {"configured": False, "source": "env", "path": env_cmd, "error": "Ruta no existe"}

    # 2) PATH
    which_cmd = shutil.which("tesseract")
    if which_cmd:
        pytesseract_module.pytesseract.tesseract_cmd = which_cmd
        meta["tesseract"] = {"configured": True, "source": "path", "path": which_cmd}
        return meta

    # 3) Windows typical paths
    candidates = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        r"C:\Tesseract-OCR\tesseract.exe",
    ]
    for c in candidates:
        if Path(c).exists():
            pytesseract_module.pytesseract.tesseract_cmd = c
            meta["tesseract"] = {"configured": True, "source": "windows_default", "path": c}
            return meta

    meta["tesseract"] = {"configured": False, "source": "not_found"}
    return meta


def _ocr_image(path: Path) -> ExtractResult:
    # OCR requiere dos cosas:
    #  - pytesseract (pip)
    #  - tesseract instalado en el sistema
    try:
        from PIL import Image  # type: ignore
    except ModuleNotFoundError:
        return ExtractResult(
            ok=False,
            text="",
            meta={"type": "image"},
            error="Dependencia faltante: Pillow. Instala: pip install pillow",
        )

    try:
        import pytesseract  # type: ignore
    except ModuleNotFoundError:
        return ExtractResult(
            ok=False,
            text="",
            meta={"type": "image"},
            error="OCR no disponible (falta pytesseract). Instala: pip install pytesseract y Tesseract OCR.",
        )

    # Configurar tesseract automáticamente (Windows-friendly)
    meta_cfg = _configure_tesseract(pytesseract)

    # Validar que realmente existe/funciona
    try:
        # Si no está instalado, esto suele lanzar error
        _ = pytesseract.get_tesseract_version()
    except Exception:
        return ExtractResult(
            ok=False,
            text="",
            meta={"type": "image", "method": "ocr", **meta_cfg},
            error=(
                "OCR no disponible: Tesseract no está instalado o no se encontró en el sistema.\n"
                "Solución:\n"
                "1) Instala Tesseract OCR en Windows\n"
                "2) Verifica: tesseract --version\n"
                "3) Si no está en PATH, define la variable TESSERACT_CMD con la ruta al tesseract.exe\n"
                "   Ejemplo: TESSERACT_CMD=C:\\Program Files\\Tesseract-OCR\\tesseract.exe"
            ),
        )

    try:
        img = Image.open(str(path))
        img = img.convert("L")  # mejora OCR en diagramas
        raw = pytesseract.image_to_string(img)
        raw = (raw or "").strip()

        if not raw:
            return ExtractResult(
                ok=False,
                text="",
                meta={"type": "image", "method": "ocr", **meta_cfg},
                error="No se detectó texto en la imagen (o está muy borrosa).",
            )

        return ExtractResult(ok=True, text=_clip(raw), meta={"type": "image", "method": "ocr", **meta_cfg})
    except Exception as e:
        return ExtractResult(ok=False, text="", meta={"type": "image", "method": "ocr", **meta_cfg}, error=str(e))


def extract_text_from_file(path: Path) -> ExtractResult:
    """Extrae texto de un archivo según su extensión.

    Args:
        path: Ruta local del archivo.

    Returns:
        ExtractResult con texto (si fue posible) y metadata.
    """
    ext = path.suffix.lower().lstrip(".")

    if ext == "txt":
        return _read_txt(path)
    if ext == "docx":
        return _read_docx(path)
    if ext == "pdf":
        return _read_pdf(path)
    if ext in {"png", "jpg", "jpeg"}:
        return _ocr_image(path)

    return ExtractResult(ok=False, text="", meta={"type": ext}, error="Tipo de archivo no soportado para análisis.")
