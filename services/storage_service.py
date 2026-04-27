import json
import sqlite3
from pathlib import Path


DB_PATH = Path(__file__).resolve().parent.parent / "data" / "lexiflow.db"


def get_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DB_PATH)


def _ensure_column_exists(conn, table_name: str, column_name: str, column_type: str):
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    existing_columns = [row[1] for row in cursor.fetchall()]

    if column_name not in existing_columns:
        cursor.execute(
            f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"
        )
        conn.commit()


def init_db():
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_name TEXT NOT NULL,
                document_type TEXT,
                summary TEXT,
                alerts_json TEXT,
                document_text TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()

        _ensure_column_exists(conn, "documents", "full_analysis_json", "TEXT")


def save_document_analysis(file_name: str, document_text: str, result: dict) -> int:
    alerts_json = json.dumps(result.get("alerts", []), ensure_ascii=False)
    full_analysis_json = json.dumps(
        result.get("full_analysis", {}),
        ensure_ascii=False
    )

    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO documents (
                file_name,
                document_type,
                summary,
                alerts_json,
                document_text,
                full_analysis_json
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            file_name,
            result.get("document_type"),
            result.get("summary"),
            alerts_json,
            document_text,
            full_analysis_json
        ))

        conn.commit()
        return cursor.lastrowid


def list_documents():
    with get_connection() as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, file_name, document_type, summary, alerts_json, created_at
            FROM documents
            ORDER BY id DESC
        """)

        rows = cursor.fetchall()

    documents = []
    for row in rows:
        documents.append({
            "id": row["id"],
            "file_name": row["file_name"],
            "document_type": row["document_type"],
            "summary": row["summary"],
            "alerts": json.loads(row["alerts_json"]) if row["alerts_json"] else [],
            "created_at": row["created_at"]
        })

    return documents


def get_document_by_id(document_id: int):
    with get_connection() as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                id,
                file_name,
                document_type,
                summary,
                alerts_json,
                document_text,
                full_analysis_json,
                created_at
            FROM documents
            WHERE id = ?
        """, (document_id,))

        row = cursor.fetchone()

    if not row:
        return None

    return {
        "id": row["id"],
        "file_name": row["file_name"],
        "document_type": row["document_type"],
        "summary": row["summary"],
        "alerts": json.loads(row["alerts_json"]) if row["alerts_json"] else [],
        "document_text": row["document_text"],
        "full_analysis": json.loads(row["full_analysis_json"]) if row["full_analysis_json"] else {},
        "created_at": row["created_at"]
    }


def list_documents_for_indexing():
    with get_connection() as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, file_name, document_text
            FROM documents
            ORDER BY id ASC
        """)

        rows = cursor.fetchall()

    return [
        {
            "id": row["id"],
            "file_name": row["file_name"],
            "document_text": row["document_text"],
        }
        for row in rows
    ]