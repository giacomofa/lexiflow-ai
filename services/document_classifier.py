"""
Classificação documental determinística (camada extra, independente do LLM).
"""
from __future__ import annotations

import re
from collections import Counter

DOCUMENT_TYPES = (
    "contrato_prestacao_servicos",
    "nda",
    "politica_interna",
    "aditivo_contratual",
)

_KEYWORDS = {
    "contrato_prestacao_servicos": [
        ("contrato de prestação de serviços", 1),
        ("contrato de prestacao de servicos", 1),
        ("contratante", 1),
        ("contratada", 1),
        ("prestação de serviços", 1),
        ("prestacao de servicos", 1),
    ],
    "nda": [
        ("acordo de confidencialidade", 2),
        (r"\bnda\b", 2),
        ("parte reveladora", 1),
        ("parte receptora", 1),
        ("informações confidenciais", 1),
        ("informacoes confidenciais", 1),
    ],
    "politica_interna": [
        ("política interna", 2),
        ("politica interna", 2),
        ("diretrizes", 1),
        ("empresa emissora", 1),
        ("colaboradores autorizados", 1),
        ("princípios de segurança", 1),
        ("principios de seguranca", 1),
    ],
    "aditivo_contratual": [
        ("aditivo contratual", 2),
        (r"aditivo\s+n[ºo°]", 2),
        ("termo aditivo", 2),
        ("altera a vigência", 1),
        ("altera a vigencia", 1),
        ("alterar a vigência", 1),
        ("alterar a vigencia", 1),
        ("contrato original", 1),
    ],
}

_MIN_SCORE_TO_SUGGEST = 1


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip().lower()


def classify_by_keywords(text: str) -> tuple[str, dict[str, int]]:
    normalized = _normalize(text)
    scores: Counter[str] = Counter()

    for doc_type, keywords in _KEYWORDS.items():
        for pattern, weight in keywords:
            if re.search(pattern, normalized):
                scores[doc_type] += weight

    if not scores or max(scores.values()) < _MIN_SCORE_TO_SUGGEST:
        return "fora_escopo", dict(scores)

    best_type, _ = scores.most_common(1)[0]
    return best_type, dict(scores)


def reconcile_classification(llm_document_type: str, text: str) -> dict:
    keyword_type, scores = classify_by_keywords(text)

    if llm_document_type == keyword_type:
        return {
            "final_type": llm_document_type,
            "needs_review": False,
            "note": None,
            "keyword_scores": scores,
        }

    note = (
        f"Classificação divergente: o LLM sugeriu '{llm_document_type}', "
        f"mas a heurística de palavras-chave sugeriu '{keyword_type}' "
        f"(scores: {scores}). Recomenda-se revisão manual."
    )

    return {
        "final_type": llm_document_type,
        "needs_review": True,
        "note": note,
        "keyword_scores": scores,
    }
