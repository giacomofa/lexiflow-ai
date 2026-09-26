"""
Autenticação e controle de perfis (básico / admin).

Senhas nunca são armazenadas em texto plano: apenas o hash bcrypt é
persistido na coluna `password_hash` da tabela `users`.
"""
from __future__ import annotations

import os
import sqlite3

import bcrypt

ROLE_BASIC = "basic"
ROLE_ADMIN = "admin"
VALID_ROLES = (ROLE_BASIC, ROLE_ADMIN)

DEFAULT_ADMIN_USERNAME = "admin"
DEFAULT_ADMIN_PASSWORD_ENV_VAR = "LEXIFLOW_DEFAULT_ADMIN_PASSWORD"
DEFAULT_ADMIN_PASSWORD_FALLBACK = "admin123"


def hash_password(plain_password: str) -> str:
    return bcrypt.hashpw(plain_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, password_hash: str) -> bool:
    if not plain_password or not password_hash:
        return False
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        return False


def init_users_table(conn: sqlite3.Connection) -> None:
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'basic',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()


def create_user(conn: sqlite3.Connection, username: str, password: str, role: str = ROLE_BASIC) -> int:
    if role not in VALID_ROLES:
        raise ValueError(f"role inválido: {role!r}. Use um de {VALID_ROLES}.")

    password_hash = hash_password(password)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
        (username, password_hash, role),
    )
    conn.commit()
    return cursor.lastrowid


def get_user_by_username(conn: sqlite3.Connection, username: str) -> dict | None:
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, password_hash, role FROM users WHERE username = ?", (username,))
    row = cursor.fetchone()

    if not row:
        return None

    return {"id": row["id"], "username": row["username"], "password_hash": row["password_hash"], "role": row["role"]}


def get_user_by_id(conn: sqlite3.Connection, user_id: int) -> dict | None:
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, password_hash, role FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()

    if not row:
        return None

    return {"id": row["id"], "username": row["username"], "password_hash": row["password_hash"], "role": row["role"]}


def authenticate(conn: sqlite3.Connection, username: str, password: str) -> dict | None:
    user = get_user_by_username(conn, username)
    if not user or not verify_password(password, user["password_hash"]):
        return None

    return {"id": user["id"], "username": user["username"], "role": user["role"]}


def any_user_exists(conn: sqlite3.Connection) -> bool:
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    return cursor.fetchone()[0] > 0


def ensure_default_admin(conn: sqlite3.Connection) -> int | None:
    """Garante que exista pelo menos um usuário admin, criando um padrão na
    primeira execução. Retorna o id do admin criado, ou None se já havia
    usuários cadastrados."""
    if any_user_exists(conn):
        return None

    default_password = os.getenv(DEFAULT_ADMIN_PASSWORD_ENV_VAR, DEFAULT_ADMIN_PASSWORD_FALLBACK)
    return create_user(conn, DEFAULT_ADMIN_USERNAME, default_password, role=ROLE_ADMIN)
