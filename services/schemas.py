"""
Validação de schema para a saída do LLM de análise documental.

Por que isso existe: o LLM devolve JSON "livre" e, na prática, nem sempre respeita
os tipos pedidos no prompt. Um exemplo real encontrado nos testes do LexiFlow AI
(planilha testes_ai.xlsx, linha "politica_teste_lexiflow.pdf"): o campo
`personal_data_mentions`, que deveria ser um booleano, voltou como a string "Sim".
Como query_service.py fazia `if mentions is True:` (comparação estrita de
identidade), esse valor era silenciosamente tratado como "não identificado" —
um bug real de produção, não hipotético.

Este módulo valida e normaliza a saída do LLM ANTES que ela chegue ao resto do
sistema, para que esse tipo de discrepância vire um warning explícito em vez de
um bug silencioso.
"""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field, field_validator

DOCUMENT_TYPES = {
    "contrato_prestacao_servicos",
    "nda",
    "politica_interna",
    "aditivo_contratual",
    "fora_escopo",
}

_TRUE_STRINGS = {"sim", "true", "verdadeiro", "yes", "y", "s"}
_FALSE_STRINGS = {"não", "nao", "false", "falso", "no", "n"}


def _coerce_optional_bool(value):
    """Aceita bool/None nativos, mas também tolera strings como 'Sim'/'Não'
    que o LLM devolve às vezes em vez de true/false."""
    if value is None or isinstance(value, bool):
        return value

    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in _TRUE_STRINGS:
            return True
        if normalized in _FALSE_STRINGS:
            return False
        if normalized in ("", "null", "none"):
            return None

    return None


def _coerce_str_list(value):
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value if item is not None and str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


class LLMAnalysisResult(BaseModel):
    """Representa a saída (já validada) de `analyze_document_with_llm`."""

    document_name: Optional[str] = None
    document_type: str = "fora_escopo"
    summary: Optional[str] = None
    parties: list[str] = Field(default_factory=list)
    object: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    term_duration: Optional[str] = None
    renewal_clause: Optional[str] = None
    termination_clause: Optional[str] = None
    penalty_clause: Optional[str] = None
    confidentiality_clause: Optional[str] = None
    personal_data_mentions: Optional[bool] = None
    personal_data_details: Optional[str] = None
    key_obligations: list[str] = Field(default_factory=list)
    risk_alerts: list[str] = Field(default_factory=list)
    source_snippets: list[str] = Field(default_factory=list)

    @field_validator("document_type", mode="before")
    @classmethod
    def _validate_document_type(cls, value):
        if not isinstance(value, str) or value.strip().lower() not in DOCUMENT_TYPES:
            return "fora_escopo"
        return value.strip().lower()

    @field_validator("personal_data_mentions", mode="before")
    @classmethod
    def _validate_personal_data_mentions(cls, value):
        return _coerce_optional_bool(value)

    @field_validator("parties", "key_obligations", "risk_alerts", "source_snippets", mode="before")
    @classmethod
    def _validate_str_lists(cls, value):
        return _coerce_str_list(value)


def validate_llm_output(raw: dict) -> tuple[dict, list[str]]:
    """Valida/normaliza o dict cru devolvido pelo LLM.

    Retorna (dados_normalizados, warnings). `warnings` lista discrepâncias de
    tipo que foram corrigidas automaticamente — útil para logging/alerta,
    porque uma discrepância recorrente é sinal de que o prompt precisa de
    ajuste, mesmo que o sistema já tenha se protegido dela.
    """
    if not isinstance(raw, dict):
        return LLMAnalysisResult().model_dump(), ["Saída do LLM não era um objeto JSON; usando valores padrão."]

    warnings: list[str] = []

    raw_document_type = raw.get("document_type")
    if isinstance(raw_document_type, str) and raw_document_type.strip().lower() not in DOCUMENT_TYPES:
        warnings.append(
            f"document_type '{raw_document_type}' não é um tipo suportado; tratado como fora_escopo."
        )

    raw_pdm = raw.get("personal_data_mentions")
    coerced_pdm = _coerce_optional_bool(raw_pdm)
    if raw_pdm is not None and not isinstance(raw_pdm, bool) and coerced_pdm is not None:
        warnings.append(
            f"personal_data_mentions veio como {raw_pdm!r} (tipo {type(raw_pdm).__name__}) "
            f"em vez de booleano; convertido para {coerced_pdm}."
        )
    elif raw_pdm is not None and not isinstance(raw_pdm, bool) and coerced_pdm is None:
        warnings.append(
            f"personal_data_mentions veio como {raw_pdm!r}, não reconhecido como true/false; tratado como null."
        )

    validated = LLMAnalysisResult(**raw)
    return validated.model_dump(), warnings
