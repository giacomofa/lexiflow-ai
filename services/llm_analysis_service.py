from services.document_classifier import reconcile_classification
from services.grounding import compute_field_confidence, grounding_summary
from services.llm_service import analyze_document_with_llm

TEXT_FIELDS_FOR_CONFIDENCE = (
    "object",
    "term_duration",
    "renewal_clause",
    "termination_clause",
    "penalty_clause",
    "confidentiality_clause",
    "personal_data_details",
)


def _append_unique(alerts, alert):
    if alert not in alerts:
        alerts.append(alert)


def low_confidence_fields(field_confidence: dict) -> list[str]:
    """Campos cujo valor citado pelo LLM não foi encontrado (ou só foi
    encontrado de forma aproximada, abaixo do limiar de match exato/alto) no
    texto original — ver services/grounding.py, check_snippet_grounding."""
    return sorted(field for field, info in field_confidence.items() if not info.get("grounded"))


def build_deterministic_alerts(llm_result, reconciliation, grounding, field_confidence):
    alerts = list(llm_result.get("risk_alerts", []))
    document_type = reconciliation["final_type"]

    if document_type == "fora_escopo":
        _append_unique(alerts, "Documento fora do escopo do MVP atual.")
    if llm_result.get("personal_data_mentions") is True:
        _append_unique(alerts, "Documento menciona tratamento de dados pessoais.")
    if llm_result.get("penalty_clause"):
        _append_unique(alerts, "Documento contém cláusula de multa contratual.")
    if llm_result.get("confidentiality_clause"):
        _append_unique(alerts, "Documento contém cláusula de confidencialidade.")
    if document_type == "contrato_prestacao_servicos" and not llm_result.get("termination_clause"):
        _append_unique(alerts, "Não foi identificada cláusula clara de rescisão.")
    if document_type in ("contrato_prestacao_servicos", "aditivo_contratual") and not llm_result.get("term_duration"):
        _append_unique(alerts, "Não foi identificada vigência/prazo claro no documento.")
    if reconciliation["needs_review"]:
        _append_unique(alerts, "Classificação divergente entre o LLM e a checagem por palavras-chave — recomenda-se revisão manual.")
    if grounding["ungrounded_count"] > 0:
        _append_unique(alerts, f"{grounding['ungrounded_count']} trecho(s) de evidência citados pelo LLM não foram localizados no texto original do documento — recomenda-se revisão manual.")

    fields_with_low_confidence = low_confidence_fields(field_confidence)
    if fields_with_low_confidence:
        label = "campo" if len(fields_with_low_confidence) == 1 else "campos"
        _append_unique(
            alerts,
            f"{len(fields_with_low_confidence)} {label} com confiança baixa "
            f"({', '.join(fields_with_low_confidence)}) — recomenda-se revisão manual.",
        )

    return alerts


def analyze_document(text: str, file_name: str) -> dict:
    llm_result = analyze_document_with_llm(document_name=file_name, document_text=text)

    reconciliation = reconcile_classification(llm_result.get("document_type", "fora_escopo"), text)
    grounding = grounding_summary(llm_result.get("source_snippets", []), text)

    field_values = {field: llm_result.get(field) for field in TEXT_FIELDS_FOR_CONFIDENCE}
    field_confidence = compute_field_confidence(field_values, text)
    llm_result["field_confidence"] = field_confidence

    alerts = build_deterministic_alerts(llm_result, reconciliation, grounding, field_confidence)

    schema_warnings = llm_result.pop("_schema_warnings", None)
    if schema_warnings:
        for warning in schema_warnings:
            _append_unique(alerts, f"Aviso de validação de dados: {warning}")

    llm_result["risk_alerts"] = alerts
    llm_result["document_type"] = reconciliation["final_type"]

    needs_review = (
        reconciliation["needs_review"]
        or grounding["ungrounded_count"] > 0
        or bool(low_confidence_fields(field_confidence))
    )

    return {
        "document_type": reconciliation["final_type"],
        "summary": llm_result.get("summary") or "Resumo não identificado.",
        "alerts": alerts,
        "full_analysis": llm_result,
        "needs_review": needs_review,
    }
