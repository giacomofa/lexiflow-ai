"""
Normalização de datas e categorização de status para a Visão geral executiva.

Por que isso existe: start_date/end_date vêm da extração do LLM como texto
livre — às vezes "2026-01-01 00:00:00", às vezes "01/05/2026", às vezes null.
Antes de calcular vencimento é preciso normalizar isso para um tipo data real.

Além disso, NDAs e políticas internas legitimamente podem não ter uma data de
fim explícita no documento (a vigência é por prazo indeterminado ou vinculada
a evento, não a uma data-calendário). Esses casos não podem cair em "vencido"
por padrão só porque end_date está ausente.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta

STATUS_ATIVO = "ativo"
STATUS_VENCENDO_EM_90_DIAS = "vencendo_em_90_dias"
STATUS_VENCIDO = "vencido"
STATUS_SEM_VIGENCIA_APLICAVEL = "sem_vigencia_aplicavel"

VENCENDO_EM_DIAS = 90

_TIPOS_SEM_VIGENCIA_OBRIGATORIA = {"nda", "politica_interna"}

_DATE_FORMATS = (
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%d",
    "%d/%m/%Y",
    "%d-%m-%Y",
)


def normalize_date(raw_value) -> date | None:
    """Converte um valor de data em formato livre para `date`, ou None se não
    for possível interpretar (ex.: texto descritivo, string vazia, None)."""
    if raw_value is None:
        return None

    if isinstance(raw_value, datetime):
        return raw_value.date()

    if isinstance(raw_value, date):
        return raw_value

    if not isinstance(raw_value, str):
        return None

    cleaned = raw_value.strip()
    if not cleaned:
        return None

    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(cleaned, fmt).date()
        except ValueError:
            continue

    return None


def compute_document_status(document_type: str, end_date_raw, today: date) -> dict:
    """Retorna {status, end_date (date normalizada ou None), reason}."""
    end_date = normalize_date(end_date_raw)

    if end_date is None:
        reason = (
            "tipo_sem_vigencia_obrigatoria"
            if document_type in _TIPOS_SEM_VIGENCIA_OBRIGATORIA
            else "data_de_fim_nao_identificada"
        )
        return {"status": STATUS_SEM_VIGENCIA_APLICAVEL, "end_date": None, "reason": reason}

    if end_date < today:
        return {"status": STATUS_VENCIDO, "end_date": end_date, "reason": None}

    if end_date <= today + timedelta(days=VENCENDO_EM_DIAS):
        return {"status": STATUS_VENCENDO_EM_90_DIAS, "end_date": end_date, "reason": None}

    return {"status": STATUS_ATIVO, "end_date": end_date, "reason": None}


def build_portfolio_summary(documents: list[dict], today: date) -> dict:
    """`documents` é uma lista de dicts com pelo menos `document_type` e
    `end_date` (formato livre). Retorna métricas agregadas para a Visão
    geral: contagens por status, distribuição por tipo documental e a lista
    de documentos vencendo em breve, ordenada por data."""
    counts = {
        STATUS_ATIVO: 0,
        STATUS_VENCENDO_EM_90_DIAS: 0,
        STATUS_VENCIDO: 0,
        STATUS_SEM_VIGENCIA_APLICAVEL: 0,
    }
    by_type: dict[str, int] = {}
    upcoming = []

    for doc in documents:
        document_type = doc.get("document_type") or "fora_escopo"
        by_type[document_type] = by_type.get(document_type, 0) + 1

        status_info = compute_document_status(document_type, doc.get("end_date"), today)
        counts[status_info["status"]] += 1

        if status_info["status"] == STATUS_VENCENDO_EM_90_DIAS:
            upcoming.append({
                "id": doc.get("id"),
                "file_name": doc.get("file_name"),
                "document_type": document_type,
                "end_date": status_info["end_date"],
            })

    upcoming.sort(key=lambda item: item["end_date"])

    return {
        "total": len(documents),
        "counts": counts,
        "by_type": by_type,
        "upcoming": upcoming,
    }
