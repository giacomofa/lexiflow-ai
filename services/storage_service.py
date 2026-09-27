import json
import sqlite3
from pathlib import Path

from services.auth_service import ROLE_ADMIN, ensure_default_admin, init_users_table
from services.encryption_service import decrypt_text, encrypt_text


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


def _backfill_document_owners(conn):
    """Documentos criados antes da autenticação existir não têm user_id.
    Atribui esses registros legados ao primeiro admin cadastrado, para que
    continuem visíveis (ao admin) em vez de desaparecerem do histórico."""
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM documents WHERE user_id IS NULL")
    if cursor.fetchone()[0] == 0:
        return

    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE role = ? ORDER BY id ASC LIMIT 1", (ROLE_ADMIN,))
    admin_row = cursor.fetchone()
    if not admin_row:
        return

    cursor.execute("UPDATE documents SET user_id = ? WHERE user_id IS NULL", (admin_row["id"],))
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
        _ensure_column_exists(conn, "documents", "user_id", "INTEGER")
        _ensure_column_exists(conn, "documents", "needs_review", "INTEGER")

        init_users_table(conn)
        ensure_default_admin(conn)

        _backfill_document_owners(conn)


def save_document_analysis(file_name: str, document_text: str, result: dict, user_id: int) -> int:
    alerts_json = json.dumps(result.get("alerts", []), ensure_ascii=False)
    full_analysis_json = json.dumps(
        result.get("full_analysis", {}),
        ensure_ascii=False
    )

    # document_text e full_analysis_json são as colunas mais sensíveis: o
    # texto integral do documento e os campos extraídos (incluindo
    # personal_data_details, quando aplicável) ficam cifrados em repouso —
    # ver services/encryption_service.py.
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO documents (
                file_name,
                document_type,
                summary,
                alerts_json,
                document_text,
                full_analysis_json,
                user_id,
                needs_review
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            file_name,
            result.get("document_type"),
            result.get("summary"),
            alerts_json,
            encrypt_text(document_text),
            encrypt_text(full_analysis_json),
            user_id,
            1 if result.get("needs_review") else 0,
        ))

        conn.commit()
        return cursor.lastrowid


def list_documents(user_id: int, role: str):
    with get_connection() as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        if role == ROLE_ADMIN:
            cursor.execute("""
                SELECT id, file_name, document_type, summary, alerts_json, created_at, user_id, needs_review
                FROM documents
                ORDER BY id DESC
            """)
            rows = cursor.fetchall()
        else:
            cursor.execute("""
                SELECT id, file_name, document_type, summary, alerts_json, created_at, user_id, needs_review
                FROM documents
                WHERE user_id = ?
                ORDER BY id DESC
            """, (user_id,))
            rows = cursor.fetchall()

    documents = []
    for row in rows:
        documents.append({
            "id": row["id"],
            "file_name": row["file_name"],
            "document_type": row["document_type"],
            "summary": row["summary"],
            "alerts": json.loads(row["alerts_json"]) if row["alerts_json"] else [],
            "created_at": row["created_at"],
            "user_id": row["user_id"],
            "needs_review": bool(row["needs_review"]),
        })

    return documents


def get_document_by_id(document_id: int, user_id: int, role: str):
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
                created_at,
                user_id,
                needs_review
            FROM documents
            WHERE id = ?
        """, (document_id,))

        row = cursor.fetchone()

    if not row:
        return None

    if role != ROLE_ADMIN and row["user_id"] != user_id:
        return None

    document_text = decrypt_text(row["document_text"])
    full_analysis_json = decrypt_text(row["full_analysis_json"])

    return {
        "id": row["id"],
        "file_name": row["file_name"],
        "document_type": row["document_type"],
        "summary": row["summary"],
        "alerts": json.loads(row["alerts_json"]) if row["alerts_json"] else [],
        "document_text": document_text,
        "full_analysis": json.loads(full_analysis_json) if full_analysis_json else {},
        "created_at": row["created_at"],
        "user_id": row["user_id"],
        "needs_review": bool(row["needs_review"]),
    }


def delete_document(document_id: int, user_id: int, role: str) -> bool:
    """Exclui permanentemente um documento (texto, análise e alertas).

    Usuário básico só pode excluir os próprios documentos; admin pode
    excluir qualquer um. Não remove os chunks correspondentes no Chroma —
    isso é responsabilidade de quem chama (ver
    rag.vector_store.delete_document_chunks), para manter este módulo sem
    depender da camada de indexação vetorial.

    Retorna True se algum registro foi de fato excluído.
    """
    with get_connection() as conn:
        cursor = conn.cursor()

        if role == ROLE_ADMIN:
            cursor.execute("DELETE FROM documents WHERE id = ?", (document_id,))
        else:
            cursor.execute(
                "DELETE FROM documents WHERE id = ? AND user_id = ?", (document_id, user_id)
            )

        conn.commit()
        return cursor.rowcount > 0


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
            "document_text": decrypt_text(row["document_text"]),
        }
        for row in rows
    ]


def list_documents_for_overview(user_id: int, role: str):
    """Retorna os campos necessários para a Visão geral executiva: tipo
    documental e a análise estruturada completa (de onde vêm start_date/
    end_date), respeitando o mesmo filtro de perfil de list_documents."""
    with get_connection() as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        if role == ROLE_ADMIN:
            cursor.execute("""
                SELECT id, file_name, document_type, full_analysis_json, created_at
                FROM documents
                ORDER BY id DESC
            """)
            rows = cursor.fetchall()
        else:
            cursor.execute("""
                SELECT id, file_name, document_type, full_analysis_json, created_at
                FROM documents
                WHERE user_id = ?
                ORDER BY id DESC
            """, (user_id,))
            rows = cursor.fetchall()

    documents = []
    for row in rows:
        full_analysis_json = decrypt_text(row["full_analysis_json"])
        full_analysis = json.loads(full_analysis_json) if full_analysis_json else {}
        documents.append({
            "id": row["id"],
            "file_name": row["file_name"],
            "document_type": row["document_type"],
            "start_date": full_analysis.get("start_date"),
            "end_date": full_analysis.get("end_date"),
            "created_at": row["created_at"],
        })

    return documents
