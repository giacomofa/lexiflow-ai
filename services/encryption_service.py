"""
Criptografia em repouso para colunas sensíveis do banco (texto integral do
documento e a análise estruturada, que pode conter dados pessoais extraídos
verbatim em personal_data_details).

O sistema já identifica quando um documento menciona dados pessoais, mas
identificar não é o mesmo que proteger: sem isso, quem tivesse acesso direto
ao arquivo data/lexiflow.db conseguiria ler tudo em texto plano.
"""
from __future__ import annotations

import os
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken

_KEY_ENV_VAR = "LEXIFLOW_ENCRYPTION_KEY"
_KEY_FILE_PATH = Path(__file__).resolve().parent.parent / "data" / ".encryption_key"

_fernet: Fernet | None = None


def _load_or_create_key() -> bytes:
    env_key = os.getenv(_KEY_ENV_VAR)
    if env_key:
        return env_key.encode("utf-8")

    if _KEY_FILE_PATH.exists():
        return _KEY_FILE_PATH.read_bytes()

    # Bootstrap local: gera uma chave na primeira execução, como já é feito
    # para o admin padrão em auth_service.ensure_default_admin. Em produção
    # (ex.: Streamlit Community Cloud), defina LEXIFLOW_ENCRYPTION_KEY nos
    # secrets em vez de depender deste arquivo — um filesystem efêmero
    # perderia a chave (e, com ela, o acesso a tudo que foi criptografado)
    # a cada novo deploy.
    _KEY_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
    key = Fernet.generate_key()
    _KEY_FILE_PATH.write_bytes(key)
    return key


def _get_fernet() -> Fernet:
    global _fernet
    if _fernet is None:
        _fernet = Fernet(_load_or_create_key())
    return _fernet


def encrypt_text(plain_text: str | None) -> str | None:
    """Cifra um texto para armazenamento. None permanece None (não força
    campos opcionais a virarem string)."""
    if plain_text is None:
        return None

    token = _get_fernet().encrypt(plain_text.encode("utf-8"))
    return token.decode("utf-8")


def decrypt_text(stored_value: str | None) -> str | None:
    """Decifra um valor salvo por encrypt_text.

    Registros gravados antes desta camada existir não são tokens Fernet
    válidos — nesse caso, o valor é devolvido como veio (texto plano), para
    que o histórico já existente continue legível em vez de quebrar."""
    if stored_value is None:
        return None

    try:
        return _get_fernet().decrypt(stored_value.encode("utf-8")).decode("utf-8")
    except (InvalidToken, ValueError):
        return stored_value
