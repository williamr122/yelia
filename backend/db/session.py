"""
Proyecto: YELIA4AP
Archivo: backend/db/session.py
Descripción: Capa de persistencia compatible con PostgreSQL 15 y SQLite legacy.

Esta versión mantiene la API interna original del proyecto (`get_db_connection`,
`db_session`, `init_db`) para no romper rutas/repositorios ya existentes, pero
permite usar PostgreSQL 15 mediante DATABASE_URL/DB_URL.
"""

import os
import re
import sqlite3
import threading
from contextlib import contextmanager
from typing import Any, Optional, Dict, List

import structlog

logger = structlog.get_logger()

_DB_LOCK = threading.RLock()
_DB_PATH: Optional[str] = None
_DB_URL: Optional[str] = None
_DB_ENGINE: Optional[str] = None


def _infer_default_db_path() -> str:
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return os.path.join(base_dir, "yelia.db")


def _normalize_db_url(url: str) -> str:
    if url.startswith("postgres://"):
        return "postgresql://" + url[len("postgres://"):]
    return url


def _detect_engine() -> str:
    global _DB_ENGINE, _DB_URL
    url = (os.getenv("DATABASE_URL") or os.getenv("DB_URL") or "").strip()
    if url.startswith(("postgresql://", "postgres://")):
        _DB_URL = _normalize_db_url(url)
        _DB_ENGINE = "postgresql"
        return _DB_ENGINE
    _DB_ENGINE = "sqlite"
    return _DB_ENGINE


def is_postgres() -> bool:
    return _detect_engine() == "postgresql"


def _get_db_path() -> str:
    global _DB_PATH
    if not _DB_PATH:
        env_path = os.getenv("DATABASE_PATH") or os.getenv("DB_PATH")
        _DB_PATH = env_path.strip() if isinstance(env_path, str) and env_path.strip() else _infer_default_db_path()
    if not os.path.isabs(_DB_PATH):
        _DB_PATH = os.path.abspath(_DB_PATH)
    return _DB_PATH


def get_db_path() -> str:
    if is_postgres():
        return _DB_URL or "postgresql"
    return _get_db_path()


class PgRow:
    """Fila tipo sqlite.Row compatible con dict(row), row[0] y row['columna']."""
    def __init__(self, columns, values):
        self._columns = list(columns or [])
        self._values = tuple(values or [])
        self._map = {c: self._values[i] for i, c in enumerate(self._columns)}

    def __getitem__(self, key):
        if isinstance(key, int):
            return self._values[key]
        return self._map[key]

    def get(self, key, default=None):
        return self._map.get(key, default)

    def keys(self):
        return self._map.keys()

    def values(self):
        return self._map.values()

    def items(self):
        return self._map.items()

    def __iter__(self):
        # dict(row) requiere iterar claves, igual que un mapping.
        return iter(self._columns)

    def __len__(self):
        return len(self._values)

    def __contains__(self, key):
        return key in self._map

    def __repr__(self):
        return repr(self._map)


def _convert_sql_for_postgres(sql: str) -> str:
    s = sql.strip()
    # Transacciones/PRAGMA de SQLite que PostgreSQL no usa.
    if re.match(r"^PRAGMA\s+", s, re.I):
        return ""
    if re.match(r"^BEGIN\s+IMMEDIATE\s*;?$", s, re.I):
        return "BEGIN;"

    # Compatibilidad de esquema.
    s = re.sub(r"\bINTEGER\s+PRIMARY\s+KEY\s+AUTOINCREMENT\b", "SERIAL PRIMARY KEY", s, flags=re.I)
    s = re.sub(r"\bREAL\b", "DOUBLE PRECISION", s, flags=re.I)
    s = re.sub(r"\bCURRENT_TIMESTAMP\b", "CURRENT_TIMESTAMP", s, flags=re.I)

    # Placeholders sqlite (?) a psycopg2 (%s). No se usan signos ? en strings del proyecto.
    s = s.replace("?", "%s")

    # Funciones de fecha SQLite -> PostgreSQL. El parámetro suele llegar como '-7 days'.
    s = re.sub(r"datetime\('now',\s*%s\)", r"(CURRENT_TIMESTAMP + (%s)::interval)", s, flags=re.I)
    s = re.sub(r"datetime\(([^,]+),\s*%s\)", r"(\1::timestamp + (%s)::interval)", s, flags=re.I)
    s = re.sub(r"datetime\(([^)]+)\)", r"(\1::timestamp)", s, flags=re.I)
    s = re.sub(r"\bDATETIME\b", "TIMESTAMP", s, flags=re.I)

    # sqlite_master -> information_schema.tables/views.
    s = re.sub(
        r"SELECT\s+name\s+FROM\s+sqlite_master\s+WHERE\s+type\s*=\s*'table'\s+AND\s+name\s*=\s*%s\s*;?",
        "SELECT table_name AS name FROM information_schema.tables WHERE table_schema='public' AND table_name=%s;",
        s,
        flags=re.I,
    )
    s = re.sub(
        r"SELECT\s+1\s+FROM\s+sqlite_master\s+WHERE\s+type\s+IN\s*\('table','view'\)\s+AND\s+name\s*=\s*%s\s+LIMIT\s+1\s*;?",
        "SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name=%s LIMIT 1;",
        s,
        flags=re.I,
    )
    s = re.sub(
        r"SELECT\s+name,\s*type\s+FROM\s+sqlite_master\s+WHERE\s+type\s+IN\s*\('table','view'\)\s+ORDER\s+BY\s+type,\s*name\s*;?",
        "SELECT table_name AS name, table_type AS type FROM information_schema.tables WHERE table_schema='public' ORDER BY table_type, table_name;",
        s,
        flags=re.I,
    )
    s = re.sub(
        r"SELECT\s+name\s+FROM\s+sqlite_master\s+WHERE\s+type\s+IN\s*\('table','view'\)\s+AND\s+name\s*=\s*%s",
        "SELECT table_name AS name FROM information_schema.tables WHERE table_schema='public' AND table_name=%s",
        s,
        flags=re.I,
    )

    return s


class PgCursor:
    def __init__(self, cursor):
        self._cur = cursor
        self.lastrowid = None
        self.rowcount = -1
        self._prefetched = None

    def execute(self, sql: str, params: Any = None):
        s0 = (sql or "").strip()
        pragma_match = re.match(r"^PRAGMA\s+table_info\(([^)]+)\)\s*;?$", s0, re.I)
        if pragma_match:
            table = pragma_match.group(1).strip().strip('"').strip("'")
            self._cur.execute(
                """
                SELECT ordinal_position - 1 AS cid,
                       column_name AS name,
                       data_type AS type,
                       CASE WHEN is_nullable='NO' THEN 1 ELSE 0 END AS notnull,
                       column_default AS dflt_value,
                       CASE WHEN column_name='id' OR column_name LIKE '%%_id' THEN 1 ELSE 0 END AS pk
                FROM information_schema.columns
                WHERE table_schema='public' AND table_name=%s
                ORDER BY ordinal_position;
                """,
                (table,),
            )
            self.rowcount = self._cur.rowcount
            return self

        sql_pg = _convert_sql_for_postgres(sql)
        if not sql_pg:
            self._prefetched = []
            self.rowcount = 0
            return self

        params = () if params is None else params
        # Para mantener `lastrowid` de sqlite en INSERT simples.
        insert_match = re.match(r"^INSERT\s+INTO\s+([a-zA-Z_][a-zA-Z0-9_]*)\s+", sql_pg.strip(), re.I)
        id_tables = {"usuarios", "interacciones", "progreso", "conversaciones", "messages", "metrics_events", "attachments", "accounts", "audit_logs", "structured_quizzes"}
        is_insert = insert_match is not None and insert_match.group(1).lower() in id_tables
        has_returning = re.search(r"\bRETURNING\b", sql_pg, re.I) is not None
        if is_insert and not has_returning:
            sql_pg = sql_pg.rstrip().rstrip(";") + " RETURNING id;"
            self._cur.execute(sql_pg, params)
            row = self._cur.fetchone()
            self.lastrowid = row[0] if row else None
            self._prefetched = []
        else:
            self._cur.execute(sql_pg, params)
            self._prefetched = None
        self.rowcount = self._cur.rowcount
        return self

    def executemany(self, sql: str, seq_of_params):
        sql_pg = _convert_sql_for_postgres(sql)
        self._cur.executemany(sql_pg, seq_of_params)
        self.rowcount = self._cur.rowcount
        return self

    def fetchone(self):
        if self._prefetched is not None:
            if not self._prefetched:
                return None
            return self._prefetched.pop(0)
        row = self._cur.fetchone()
        if row is None:
            return None
        cols = [d[0] for d in (self._cur.description or [])]
        return PgRow(cols, row)

    def fetchall(self):
        if self._prefetched is not None:
            out = self._prefetched
            self._prefetched = []
            return out
        rows = self._cur.fetchall()
        cols = [d[0] for d in (self._cur.description or [])]
        return [PgRow(cols, r) for r in rows]

    def close(self):
        return self._cur.close()


class PgConnection:
    def __init__(self, conn):
        self._conn = conn

    def cursor(self):
        return PgCursor(self._conn.cursor())

    def execute(self, sql: str, params: Any = None):
        cur = self.cursor()
        return cur.execute(sql, params)

    def commit(self):
        return self._conn.commit()

    def rollback(self):
        return self._conn.rollback()

    def close(self):
        return self._conn.close()


def _configure_sqlite_connection(conn: sqlite3.Connection) -> None:
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA synchronous = NORMAL;")
    conn.execute("PRAGMA busy_timeout = 5000;")


def get_db_connection():
    if is_postgres():
        try:
            import psycopg2
        except ImportError as exc:
            raise RuntimeError("Falta instalar psycopg2-binary para usar PostgreSQL.") from exc
        conn = psycopg2.connect(_DB_URL)
        conn.autocommit = False
        return PgConnection(conn)

    path = _get_db_path()
    parent_dir = os.path.dirname(path)
    if parent_dir and not os.path.exists(parent_dir):
        os.makedirs(parent_dir, exist_ok=True)
    conn = sqlite3.connect(path, check_same_thread=False, timeout=30)
    conn.row_factory = sqlite3.Row
    _configure_sqlite_connection(conn)
    return conn


def get_connection():
    return get_db_connection()


@contextmanager
def db_session(write: bool = False):
    conn = get_db_connection()
    try:
        if write:
            conn.execute("BEGIN IMMEDIATE;" if not is_postgres() else "BEGIN;")
        yield conn
        if write:
            conn.commit()
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass
        raise
    finally:
        try:
            conn.close()
        except Exception:
            pass


def _ensure_column(cur, table: str, col: str, col_sql: str) -> None:
    if is_postgres():
        cur.execute("SELECT table_name AS name FROM information_schema.tables WHERE table_schema='public' AND table_name=%s;", (table,))
        if not cur.fetchone():
            return
        cur.execute("SELECT column_name AS name FROM information_schema.columns WHERE table_schema='public' AND table_name=%s;", (table,))
        cols = {r[0] for r in cur.fetchall()}
    else:
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
        if not cur.fetchone():
            return
        cur.execute(f"PRAGMA table_info({table});")
        cols = {r[1] for r in cur.fetchall()}
    if col not in cols:
        cur.execute(f"ALTER TABLE {table} ADD COLUMN {col} {col_sql};")
        logger.info("Columna agregada", table=table, column=col)


def init_db(app=None) -> None:
    global _DB_PATH, _DB_URL, _DB_ENGINE
    engine = _detect_engine()

    if engine == "sqlite":
        if app is not None and app.config.get("DATABASE_PATH"):
            _DB_PATH = app.config.get("DATABASE_PATH")
        elif not _DB_PATH:
            _DB_PATH = _infer_default_db_path()
        if _DB_PATH and not os.path.isabs(_DB_PATH):
            _DB_PATH = os.path.abspath(_DB_PATH)
        log_target = _DB_PATH
    else:
        log_target = _DB_URL

    with _DB_LOCK:
        with db_session(write=True) as conn:
            cur = conn.cursor()

            cur.execute("""
                CREATE TABLE IF NOT EXISTS usuarios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    alias TEXT NOT NULL UNIQUE,
                    email TEXT,
                    password_hash TEXT,
                    diagnostic_locked INTEGER DEFAULT 0,
                    role TEXT DEFAULT 'student',
                    status TEXT DEFAULT 'active',
                    last_seen TEXT,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS interacciones (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    usuario_id INTEGER NOT NULL,
                    pregunta TEXT NOT NULL,
                    respuesta TEXT NOT NULL,
                    tema TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(usuario_id) REFERENCES usuarios(id)
                );
            """)
            _ensure_column(cur, "usuarios", "password_hash", "TEXT")
            _ensure_column(cur, "usuarios", "diagnostic_locked", "INTEGER DEFAULT 0")
            cur.execute("""
                CREATE TABLE IF NOT EXISTS progreso (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    usuario TEXT NOT NULL UNIQUE,
                    puntos INTEGER DEFAULT 0,
                    temas_aprendidos TEXT,
                    ciclo_academico TEXT,
                    estado_materia TEXT,
                    nivel_materia TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS student_profiles (
                    student_id TEXT PRIMARY KEY,
                    profile_json TEXT NOT NULL,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS conversaciones (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    usuario TEXT NOT NULL,
                    titulo TEXT,
                    focus_topic TEXT,
                    focus_attachment_ids TEXT,
                    focus_updated_at TEXT,
                    memory_summary TEXT,
                    memory_msg_count INTEGER,
                    memory_updated_at TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    conv_id INTEGER NOT NULL,
                    usuario TEXT NOT NULL,
                    remitente TEXT NOT NULL,
                    contenido TEXT NOT NULL,
                    tema TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(conv_id) REFERENCES conversaciones(id) ON DELETE CASCADE
                );
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS structured_quizzes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    conv_id INTEGER,
                    usuario TEXT NOT NULL,
                    tema TEXT,
                    source_message_id INTEGER,
                    quiz_json TEXT NOT NULL,
                    status TEXT DEFAULT 'active',
                    last_score INTEGER,
                    total_questions INTEGER,
                    answered_at TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(conv_id) REFERENCES conversaciones(id) ON DELETE CASCADE,
                    FOREIGN KEY(source_message_id) REFERENCES messages(id) ON DELETE SET NULL
                );
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS metrics_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    conv_id INTEGER,
                    usuario TEXT,
                    mensaje_id INTEGER,
                    nivel_detectado TEXT,
                    quality_score REAL,
                    motivo TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(conv_id) REFERENCES conversaciones(id),
                    FOREIGN KEY(mensaje_id) REFERENCES messages(id)
                );
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS attachments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    conv_id INTEGER,
                    message_id INTEGER,
                    usuario TEXT NOT NULL,
                    original_name TEXT NOT NULL,
                    stored_name TEXT NOT NULL,
                    filename TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    mime TEXT,
                    size_bytes INTEGER,
                    sha256 TEXT,
                    url TEXT,
                    status TEXT DEFAULT 'active',
                    uploaded_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(conv_id) REFERENCES conversaciones(id) ON DELETE CASCADE,
                    FOREIGN KEY(message_id) REFERENCES messages(id) ON DELETE SET NULL
                );
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS accounts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL UNIQUE,
                    email TEXT,
                    password_hash TEXT NOT NULL,
                    role TEXT NOT NULL DEFAULT 'teacher',
                    status TEXT NOT NULL DEFAULT 'active',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    last_seen TEXT,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS audit_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    actor TEXT NOT NULL,
                    action TEXT NOT NULL,
                    target TEXT,
                    meta_json TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS teacher_requests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL,
                    email TEXT,
                    password_hash TEXT NOT NULL,
                    reason TEXT,
                    status TEXT NOT NULL DEFAULT 'pending',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    decided_by TEXT,
                    decided_at TEXT
                );
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS learning_routes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    usuario TEXT NOT NULL UNIQUE,
                    route_json TEXT,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS global_settings (
                    key TEXT PRIMARY KEY,
                    value TEXT
                );
            """)
            cur.execute("INSERT OR IGNORE INTO global_settings (key, value) VALUES ('allow_pdf_download', '1');")

            _ensure_column(cur, "usuarios", "last_seen", "TEXT")
            _ensure_column(cur, "usuarios", "updated_at", "TEXT DEFAULT CURRENT_TIMESTAMP")
            _ensure_column(cur, "messages", "tema", "TEXT")
            _ensure_column(cur, "messages", "proveedor", "TEXT")
            _ensure_column(cur, "messages", "response_ms", "INTEGER")
            _ensure_column(cur, "structured_quizzes", "last_score", "INTEGER")
            _ensure_column(cur, "structured_quizzes", "total_questions", "INTEGER")
            _ensure_column(cur, "structured_quizzes", "answered_at", "TEXT")
            _ensure_column(cur, "interacciones", "tema", "TEXT")
            _ensure_column(cur, "progreso", "nivel_materia", "TEXT")

            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_student_profiles_updated ON student_profiles(updated_at);",
                "CREATE INDEX IF NOT EXISTS idx_metrics_conv ON metrics_events(conv_id);",
                "CREATE INDEX IF NOT EXISTS idx_metrics_usuario_created ON metrics_events(usuario, created_at);",
                "CREATE INDEX IF NOT EXISTS idx_attachments_conv ON attachments(conv_id);",
                "CREATE INDEX IF NOT EXISTS idx_attachments_usuario ON attachments(usuario);",
                "CREATE INDEX IF NOT EXISTS idx_attachments_created ON attachments(created_at DESC);",
                "CREATE INDEX IF NOT EXISTS idx_attachments_uploaded ON attachments(uploaded_at DESC);",
                "CREATE INDEX IF NOT EXISTS idx_attachments_original_name ON attachments(original_name);",
                "CREATE INDEX IF NOT EXISTS idx_interacciones_usuario ON interacciones(usuario_id);",
                "CREATE INDEX IF NOT EXISTS idx_progreso_usuario ON progreso(usuario);",
                "CREATE INDEX IF NOT EXISTS idx_conversaciones_usuario ON conversaciones(usuario);",
                "CREATE INDEX IF NOT EXISTS idx_messages_conv ON messages(conv_id);",
                "CREATE INDEX IF NOT EXISTS idx_messages_conv_created ON messages(conv_id, created_at);",
                "CREATE INDEX IF NOT EXISTS idx_messages_usuario_created ON messages(usuario, created_at);",
                "CREATE INDEX IF NOT EXISTS idx_messages_tema ON messages(tema);",
                "CREATE INDEX IF NOT EXISTS idx_messages_remitente ON messages(remitente);",
                "CREATE INDEX IF NOT EXISTS idx_learning_routes_usuario ON learning_routes(usuario);",
                "CREATE INDEX IF NOT EXISTS idx_messages_tema_remitente ON messages(tema, remitente);",
                "CREATE INDEX IF NOT EXISTS idx_structured_quizzes_conv ON structured_quizzes(conv_id);",
                "CREATE INDEX IF NOT EXISTS idx_structured_quizzes_usuario ON structured_quizzes(usuario);",
                "CREATE INDEX IF NOT EXISTS idx_structured_quizzes_status ON structured_quizzes(status);",
            ]
            for idx in indexes:
                cur.execute(idx)

    logger.info("Base de datos inicializada correctamente", engine=engine, target=log_target)


# Helpers legacy usados por servicios/rutas.
def crear_conversacion(usuario: str, titulo: Optional[str] = None) -> int:
    usuario = usuario.strip() or "anonimo"
    with _DB_LOCK:
        with db_session(write=True) as conn:
            cur = conn.cursor()
            cur.execute("INSERT INTO conversaciones (usuario, titulo) VALUES (?, ?);", (usuario, titulo))
            if cur.lastrowid is None:
                raise RuntimeError("No se pudo obtener el ID de la conversación recién creada.")
            return int(cur.lastrowid)


def renombrar_conversacion(conv_id: int, nuevo_titulo: str) -> None:
    nuevo_titulo = (nuevo_titulo or "").strip()
    with _DB_LOCK:
        with db_session(write=True) as conn:
            conn.execute("UPDATE conversaciones SET titulo = ? WHERE id = ?;", (nuevo_titulo, conv_id))


def guardar_mensaje(conv_id: int, usuario: str, remitente: str, contenido: str, tema: Optional[str] = None) -> int:
    usuario = usuario.strip() or "anonimo"
    remitente = (remitente or "user").strip()
    contenido = (contenido or "").strip()
    with _DB_LOCK:
        with db_session(write=True) as conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO messages (conv_id, usuario, remitente, contenido, tema) VALUES (?, ?, ?, ?, ?);",
                (conv_id, usuario, remitente, contenido, tema),
            )
            if cur.lastrowid is None:
                raise RuntimeError("No se pudo obtener el ID del mensaje recién creado.")
            return int(cur.lastrowid)


def obtener_mensajes(conv_id: int, limit: int = 50):
    with db_session() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM messages WHERE conv_id = ? ORDER BY created_at ASC, id ASC LIMIT ?;",
            (conv_id, int(limit)),
        )
        return cur.fetchall()
def obtener_conversaciones_usuario(
    usuario: str,
    limite: int = 20,
    offset: int = 0,
) -> List[Dict[str, Any]]:
    usuario = usuario.strip() or "anonimo"
    with db_session(write=False) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, titulo, created_at
            FROM conversaciones
            WHERE usuario = ?
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?;
            """,
            (usuario, limite, offset),
        )
        rows = cur.fetchall()

    return [
        {"id": int(r["id"]), "titulo": r["titulo"], "created_at": r["created_at"]}
        for r in rows
    ]

def obtener_mensajes_conversacion(
    conv_id: int,
    limite: int = 100,
    offset: int = 0,
    ascendente: bool = True,
) -> List[Dict[str, Any]]:
    orden = "ASC" if ascendente else "DESC"
    with db_session(write=False) as conn:
        cur = conn.cursor()
        cur.execute(
            f"""
            SELECT id, remitente, contenido, tema, created_at
            FROM messages
            WHERE conv_id = ?
            ORDER BY created_at {orden}, id {orden}
            LIMIT ? OFFSET ?;
            """,
            (conv_id, limite, offset),
        )
        rows = cur.fetchall()

    return [
        {
            "id": int(r["id"]),
            "remitente": r["remitente"],
            "contenido": r["contenido"],
            "tema": r["tema"],
            "created_at": r["created_at"],
        }
        for r in rows
    ]

# ============================================================
# SECCIÓN 6: MEMORIA DE CONTINUIDAD (FOCO DE CONVERSACIÓN)
# ============================================================

def obtener_foco_conversacion(conv_id: int, usuario: str) -> Dict[str, Any]:
    usuario = (usuario or "").strip() or "anonimo"
    with db_session(write=False) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT focus_topic, focus_attachment_ids
            FROM conversaciones
            WHERE id = ? AND usuario = ?
            LIMIT 1;
            """,
            (int(conv_id), usuario),
        )
        row = cur.fetchone()
        if not row:
            return {"focus_topic": None, "focus_attachment_ids": []}

    raw_ids = (row["focus_attachment_ids"] or "").strip()
    ids: List[int] = []
    if raw_ids:
        for part in raw_ids.split(","):
            part = part.strip()
            if not part:
                continue
            try:
                ids.append(int(part))
            except Exception:
                continue

    return {"focus_topic": row["focus_topic"], "focus_attachment_ids": ids}

def actualizar_foco_conversacion(
    conv_id: int,
    usuario: str,
    *,
    focus_topic: Optional[str] = None,
    focus_attachment_ids: Optional[List[int]] = None,
) -> None:
    usuario = (usuario or "").strip() or "anonimo"
    topic = (focus_topic or "").strip() if focus_topic is not None else None
    ids_csv = None
    if focus_attachment_ids is not None:
        ids = [int(x) for x in focus_attachment_ids if str(x).strip().isdigit()]
        ids = ids[:3]
        ids_csv = ",".join(str(i) for i in ids)

    with _DB_LOCK:
        with db_session(write=True) as conn:
            cur = conn.cursor()
            sets = []
            params: List[Any] = []
            if topic is not None:
                sets.append("focus_topic = ?")
                params.append(topic)
            if ids_csv is not None:
                sets.append("focus_attachment_ids = ?")
                params.append(ids_csv)

            sets.append("focus_updated_at = CURRENT_TIMESTAMP")
            params.extend([int(conv_id), usuario])

            cur.execute(
                f"UPDATE conversaciones SET {', '.join(sets)} WHERE id = ? AND usuario = ?;",
                tuple(params),
            )

# ============================================================
# SECCIÓN 7: RESUMEN AUTOMÁTICO (MEMORY SUMMARY)
# ============================================================

def obtener_memoria_conversacion(conv_id: int, usuario: str) -> Dict[str, Any]:
    usuario = (usuario or "").strip() or "anonimo"
    with db_session(write=False) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT memory_summary, COALESCE(memory_msg_count, 0) AS memory_msg_count
            FROM conversaciones
            WHERE id = ? AND usuario = ?
            LIMIT 1;
            """,
            (int(conv_id), usuario),
        )
        row = cur.fetchone()
        if not row:
            return {"memory_summary": None, "memory_msg_count": 0}
        return {"memory_summary": row["memory_summary"], "memory_msg_count": int(row["memory_msg_count"] or 0)}

def actualizar_memoria_conversacion(
    conv_id: int,
    usuario: str,
    *,
    memory_summary: str,
    memory_msg_count: int,
) -> None:
    usuario = (usuario or "").strip() or "anonimo"
    resumen = (memory_summary or "").strip()
    with _DB_LOCK:
        with db_session(write=True) as conn:
            cur = conn.cursor()
            cur.execute(
                """
                UPDATE conversaciones
                SET memory_summary = ?,
                    memory_msg_count = ?,
                    memory_updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND usuario = ?;
                """,
                (resumen, int(memory_msg_count), int(conv_id), usuario),
            )

# ============================================================
# SECCIÓN 8: LEGACY (USUARIOS / INTERACCIONES)
# ============================================================

def get_or_create_usuario(alias: str = "anonimo") -> int:
    alias = alias.strip() or "anonimo"
    with _DB_LOCK:
        with db_session(write=True) as conn:
            cur = conn.cursor()
            cur.execute("SELECT id FROM usuarios WHERE alias = ?;", (alias,))
            row = cur.fetchone()
            if row:
                return int(row["id"])

            cur.execute("INSERT INTO usuarios (alias) VALUES (?);", (alias,))
            lastrowid = cur.lastrowid
            return int(lastrowid) if lastrowid is not None else 0

def registrar_interaccion(
    usuario_id: int,
    pregunta: str,
    respuesta: str,
    tema: Optional[str] = None,
) -> None:
    with _DB_LOCK:
        with db_session(write=True) as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO interacciones (usuario_id, pregunta, respuesta, tema)
                VALUES (?, ?, ?, ?);
                """,
                (usuario_id, pregunta, respuesta, tema),
            )

def _merge_temas_vistos(actual: Optional[str], nuevo_tema: Optional[str]) -> str:
    if not nuevo_tema:
        return actual or ""
    temas = set()
    if actual:
        temas.update(t.strip() for t in actual.split(",") if t.strip())
    temas.add(nuevo_tema)
    return ",".join(sorted(temas))

def actualizar_progreso_legacy(
    usuario_id: int,
    tema: Optional[str] = None,
    quiz_aprobado: bool = False,
) -> None:
    with _DB_LOCK:
        with db_session(write=True) as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT id, temas_aprendidos, puntos
                FROM progreso
                WHERE id = ?;
                """,
                (usuario_id,),
            )
            row = cur.fetchone()

            temas_vistos = None
            quizzes = 0
            if row:
                temas_vistos = row["temas_aprendidos"]
                quizzes = row["puntos"] or 0

            temas_vistos = _merge_temas_vistos(temas_vistos, tema)
            if quiz_aprobado:
                quizzes += 1

            if row:
                cur.execute(
                    """
                    UPDATE progreso
                    SET temas_aprendidos = ?, puntos = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?;
                    """,
                    (temas_vistos, quizzes, usuario_id),
                )
            else:
                cur.execute(
                    """
                    INSERT INTO progreso (usuario, puntos, temas_aprendidos)
                    VALUES (?, ?, ?);
                    """,
                    (f"usuario_{usuario_id}", quizzes, temas_vistos),
                )

def obtener_resumen_progreso(usuario_id: int) -> Dict[str, Any]:
    with db_session(write=False) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT temas_aprendidos, puntos, updated_at
            FROM progreso
            WHERE id = ?;
            """,
            (usuario_id,),
        )
        row = cur.fetchone()

    if not row:
        return {
            "temas_vistos": [],
            "quizzes_aprobados": 0,
            "nivel": "Sin registro",
            "ultima_actualizacion": None,
        }

    temas = []
    if row["temas_aprendidos"]:
        temas = [t for t in row["temas_aprendidos"].split(",") if t]

    return {
        "temas_vistos": temas,
        "quizzes_aprobados": int(row["puntos"] or 0),
        "nivel": "Inicial",
        "ultima_actualizacion": row["updated_at"],
    }

def obtener_ultimas_interacciones(
    usuario_id: int,
    limite: int = 10,
) -> List[Dict[str, Any]]:
    with db_session(write=False) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT pregunta, respuesta, tema, created_at
            FROM interacciones
            WHERE usuario_id = ?
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?;
            """,
            (usuario_id, limite),
        )
        rows = cur.fetchall()

    return [
        {
            "pregunta": r["pregunta"],
            "respuesta": r["respuesta"],
            "tema": r["tema"],
            "fecha": r["created_at"],
        }
        for r in rows
    ]
