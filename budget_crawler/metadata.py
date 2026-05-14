import hashlib
import os
import re
import sqlite3
from datetime import datetime
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB_PATH = PROJECT_ROOT / "db" / "budget_metadata.db"


def ensure_db(db_path=DEFAULT_DB_PATH):
    """Create the crawler metadata database and apply lightweight migrations."""
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS budget_docs (
                id TEXT PRIMARY KEY,
                state TEXT NOT NULL,
                fiscal_year TEXT NOT NULL,
                document_type TEXT,
                estimate_type TEXT,
                ministry TEXT,
                source_url TEXT,
                local_path TEXT,
                file_hash TEXT,
                file_extension TEXT,
                last_crawled TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                parsing_status TEXT DEFAULT 'pending'
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS fiscal_indicators (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                doc_id TEXT,
                indicator_name TEXT,
                major_head TEXT,
                value REAL,
                unit TEXT,
                FOREIGN KEY (doc_id) REFERENCES budget_docs (id)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS doc_extraction_probe (
                doc_id TEXT PRIMARY KEY,
                probed_at TEXT,
                file_size_bytes INTEGER,
                page_count INTEGER,
                pdftotext_chars_p1 INTEGER,
                pdftotext_sample TEXT,
                pdfplumber_tables_p1 INTEGER,
                has_devanagari INTEGER DEFAULT 0,
                parser_route TEXT,
                austerity_score INTEGER DEFAULT 0,
                extravagance_score INTEGER DEFAULT 0,
                error TEXT,
                FOREIGN KEY (doc_id) REFERENCES budget_docs(id)
            )
            """
        )
        _ensure_columns(
            conn,
            "budget_docs",
            {
                "estimate_type": "TEXT",
                "ministry": "TEXT",
                "file_hash": "TEXT",
                "file_extension": "TEXT",
                "parsing_status": "TEXT DEFAULT 'pending'",
            },
        )
        conn.commit()
    finally:
        conn.close()


def index_budget_doc(
    *,
    doc_id,
    state,
    fiscal_year,
    document_type,
    source_url,
    local_path,
    file_extension=None,
    estimate_type=None,
    ministry=None,
    parsing_status="pending",
    db_path=DEFAULT_DB_PATH,
):
    """Upsert one crawled document into the metadata index."""
    ensure_db(db_path)
    local_path = str(Path(local_path).resolve()) if local_path else None
    file_extension = file_extension or _extension_from_path(local_path)
    file_hash = sha256_file(local_path) if local_path and os.path.exists(local_path) else None

    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            """
            INSERT OR REPLACE INTO budget_docs (
                id, state, fiscal_year, document_type, estimate_type, ministry,
                source_url, local_path, file_hash, file_extension, last_crawled,
                parsing_status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                doc_id,
                state,
                fiscal_year,
                document_type,
                estimate_type,
                ministry,
                source_url,
                local_path,
                file_hash,
                file_extension,
                datetime.now().isoformat(timespec="seconds"),
                parsing_status,
            ),
        )
        conn.commit()
    finally:
        conn.close()


def make_doc_id(*parts, max_len=140):
    raw = "_".join(str(part) for part in parts if part is not None)
    doc_id = re.sub(r"[^A-Za-z0-9]+", "_", raw).strip("_").lower()
    return doc_id[:max_len]


def safe_path_name(value, max_len=180):
    value = re.sub(r"\s+", " ", value).strip()
    value = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", value)
    value = re.sub(r"_+", "_", value).strip(" ._")
    return (value or "untitled")[:max_len]


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _ensure_columns(conn, table, columns):
    existing = {row[1] for row in conn.execute(f"PRAGMA table_info({table})")}
    for name, definition in columns.items():
        if name not in existing:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {name} {definition}")


def _extension_from_path(path):
    if not path:
        return None
    suffix = Path(path).suffix.lower().lstrip(".")
    return suffix or None


def upsert_probe_result(
    *,
    doc_id,
    file_size_bytes,
    page_count,
    pdftotext_chars_p1,
    pdftotext_sample,
    pdfplumber_tables_p1,
    has_devanagari,
    parser_route,
    austerity_score=0,
    extravagance_score=0,
    error,
    db_path=DEFAULT_DB_PATH,
):
    ensure_db(db_path)
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            """
            INSERT OR REPLACE INTO doc_extraction_probe (
                doc_id, probed_at, file_size_bytes, page_count,
                pdftotext_chars_p1, pdftotext_sample, pdfplumber_tables_p1,
                has_devanagari, parser_route, austerity_score, extravagance_score, error
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                doc_id,
                datetime.now().isoformat(timespec="seconds"),
                file_size_bytes,
                page_count,
                pdftotext_chars_p1,
                pdftotext_sample,
                pdfplumber_tables_p1,
                1 if has_devanagari else 0,
                parser_route,
                austerity_score,
                extravagance_score,
                error,
            ),
        )
        conn.commit()
    finally:
        conn.close()
