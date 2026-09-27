"""
Validação de grounding: confere se as evidências citadas pelo LLM realmente
existem no texto original do documento.
"""
from __future__ import annotations

import re
from difflib import SequenceMatcher

_FUZZY_MATCH_THRESHOLD = 0.8
_WINDOW_SLACK = 20

# aspas retas e curvas que o LLM às vezes usa para "citar" um trecho como um
# todo (ex.: '"cláusula de multa..."'); sem remover isso, um snippet
# genuinamente correto pode falhar o match só por causa das aspas ao redor.
_SURROUNDING_QUOTE_CHARS = "\"'“”‘’«»"


def _normalize(text: str) -> str:
    normalized = re.sub(r"\s+", " ", text or "").strip().lower()
    return normalized.strip(_SURROUNDING_QUOTE_CHARS)


def _best_fuzzy_ratio(snippet: str, source_text: str) -> float:
    if not snippet or not source_text:
        return 0.0

    window = len(snippet) + _WINDOW_SLACK
    if window >= len(source_text):
        return SequenceMatcher(None, snippet, source_text).ratio()

    best = 0.0
    step = max(1, window // 2)
    for start in range(0, len(source_text) - window + 1, step):
        candidate = source_text[start:start + window]
        ratio = SequenceMatcher(None, snippet, candidate).ratio()
        if ratio > best:
            best = ratio
        if best >= 0.999:
            break

    return best


def check_snippet_grounding(snippet: str, source_text: str) -> dict:
    normalized_snippet = _normalize(snippet)
    normalized_source = _normalize(source_text)

    if not normalized_snippet:
        return {"snippet": snippet, "grounded": False, "match_type": "none", "score": 0.0}

    if normalized_snippet in normalized_source:
        return {"snippet": snippet, "grounded": True, "match_type": "exact", "score": 1.0}

    score = _best_fuzzy_ratio(normalized_snippet, normalized_source)
    if score >= _FUZZY_MATCH_THRESHOLD:
        return {"snippet": snippet, "grounded": True, "match_type": "fuzzy", "score": round(score, 3)}

    return {"snippet": snippet, "grounded": False, "match_type": "none", "score": round(score, 3)}


def annotate_grounding(snippets: list[str], source_text: str) -> list[dict]:
    return [check_snippet_grounding(snippet, source_text) for snippet in (snippets or [])]


def compute_field_confidence(fields: dict[str, str | None], source_text: str) -> dict[str, dict]:
    """Para cada campo de texto extraído pelo LLM (ex.: penalty_clause,
    termination_clause), verifica se o valor citado aparece de fato no
    documento original, reaproveitando a mesma lógica de grounding usada
    para os source_snippets. Campos vazios/nulos são omitidos (não há o
    que verificar)."""
    confidence = {}

    for field_name, value in fields.items():
        if not value or not isinstance(value, str):
            continue
        confidence[field_name] = check_snippet_grounding(value, source_text)

    return confidence


def grounding_summary(snippets: list[str], source_text: str) -> dict:
    results = annotate_grounding(snippets, source_text)
    total = len(results)
    ungrounded = [r for r in results if not r["grounded"]]

    return {
        "total": total,
        "grounded_count": total - len(ungrounded),
        "ungrounded_count": len(ungrounded),
        "ungrounded_snippets": [r["snippet"] for r in ungrounded],
        "details": results,
    }
