"""
Autenticação e controle de perfis (básico / admin).

Senhas nunca são armazenadas em texto plano: apenas o hash bcrypt é
persistido na coluna `password_hash` da tabela `users`.
"""
from __future__ import annotations

import os
import secrets
import sqlite3
from datetime import datetime, timedelta, timezone

import bcrypt

ROLE_BASIC = "basic"
ROLE_ADMIN = "admin"
VALID_ROLES = (ROLE_BASIC, ROLE_ADMIN)

DEFAULT_ADMIN_USERNAME = "admin"
DEFAULT_ADMIN_PASSWORD_ENV_VAR = "LEXIFLOW_DEFAULT_ADMIN_PASSWORD"
DEFAULT_ADMIN_PASSWORD_FALLBACK = "admin123"

# Sessão persistente (não deslogar a cada refresh): o token fica na URL
# (st.query_params), não num cookie httpOnly — um trade-off deliberado para
# uma ferramenta interna, não uma exposição pública sensível a fraude
# financeira. Por isso o TTL é curto e o token nunca revela nada por si só
# (256 bits aleatórios via secrets.token_urlsafe).
SESSION_TTL_HOURS = 12


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


def init_sessions_table(conn: sqlite3.Connection) -> None:
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            token TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP NOT NULL
        )
    """)
    conn.commit()


def _now() -> datetime:
    return datetime.now(timezone.utc)


def create_session(conn: sqlite3.Connection, user_id: int, ttl_hours: int = SESSION_TTL_HOURS) -> str:
    token = secrets.token_urlsafe(32)
    expires_at = _now() + timedelta(hours=ttl_hours)

    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO sessions (token, user_id, expires_at) VALUES (?, ?, ?)",
        (token, user_id, expires_at.isoformat()),
    )
    conn.commit()
    return token


def validate_session(conn: sqlite3.Connection, token: str) -> dict | None:
    """Retorna o usuário dono da sessão se o token existir e ainda não tiver
    expirado; None caso contrário (inclusive limpando a sessão expirada, de
    passagem, em vez de exigir um job de limpeza separado)."""
    if not token:
        return None

    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, expires_at FROM sessions WHERE token = ?", (token,))
    row = cursor.fetchone()

    if not row:
        return None

    expires_at = datetime.fromisoformat(row["expires_at"])
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    if expires_at < _now():
        cursor.execute("DELETE FROM sessions WHERE token = ?", (token,))
        conn.commit()
        return None

    user = get_user_by_id(conn, row["user_id"])
    if not user:
        return None

    return {"id": user["id"], "username": user["username"], "role": user["role"]}


def delete_session(conn: sqlite3.Connection, token: str) -> None:
    cursor = conn.cursor()
    cursor.execute("DELETE FROM sessions WHERE token = ?", (token,))
    conn.commit()
