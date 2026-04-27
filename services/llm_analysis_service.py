from services.llm_service import analyze_document_with_llm


def analyze_document(text: str, file_name: str) -> dict:
    llm_result = analyze_document_with_llm(
        document_name=file_name,
        document_text=text
    )

    alerts = list(llm_result.get("risk_alerts", []))

    if llm_result.get("document_type") == "fora_escopo":
        if "Documento fora do escopo do MVP atual." not in alerts:
            alerts.append("Documento fora do escopo do MVP atual.")

    if llm_result.get("personal_data_mentions") is True:
        if "Documento menciona tratamento de dados pessoais." not in alerts:
            alerts.append("Documento menciona tratamento de dados pessoais.")

    if llm_result.get("penalty_clause"):
        if "Documento contém cláusula de multa contratual." not in alerts:
            alerts.append("Documento contém cláusula de multa contratual.")

    if llm_result.get("confidentiality_clause"):
        if "Documento contém cláusula de confidencialidade." not in alerts:
            alerts.append("Documento contém cláusula de confidencialidade.")

    if (
        llm_result.get("document_type") == "contrato_prestacao_servicos"
        and not llm_result.get("termination_clause")
    ):
        if "Não foi identificada cláusula clara de rescisão." not in alerts:
            alerts.append("Não foi identificada cláusula clara de rescisão.")

    llm_result["risk_alerts"] = alerts
    
    return {
        "document_type": llm_result.get("document_type", "fora_escopo"),
        "summary": llm_result.get("summary", "Resumo não identificado."),
        "alerts": alerts,
        "full_analysis": llm_result,
    }