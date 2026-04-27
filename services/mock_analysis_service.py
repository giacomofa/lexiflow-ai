def classify_document(text: str) -> str:
    text_lower = text.lower()

    if "acordo de confidencialidade" in text_lower or "nda" in text_lower:
        return "nda"
    if "política interna" in text_lower or "politica interna" in text_lower:
        return "politica_interna"
    if "aditivo" in text_lower:
        return "aditivo_contratual"
    if "contrato" in text_lower:
        return "contrato_prestacao_servicos"

    return "nao_identificado"


def generate_summary(text: str, document_type: str) -> str:
    summaries = {
        "contrato_prestacao_servicos": "Documento classificado como contrato de prestação de serviços. Contém regras sobre objeto, vigência e obrigações entre as partes.",
        "nda": "Documento classificado como acordo de confidencialidade. O foco principal está na proteção e no sigilo das informações compartilhadas.",
        "politica_interna": "Documento classificado como política interna. Apresenta diretrizes e regras corporativas para orientação dos colaboradores.",
        "aditivo_contratual": "Documento classificado como aditivo contratual. O conteúdo sugere alteração de condições previamente estabelecidas em contrato original.",
        "nao_identificado": "Não foi possível identificar claramente o tipo do documento com a análise inicial."
    }

    return summaries.get(document_type, "Resumo não disponível.")


def generate_alerts(text: str) -> list[str]:
    text_lower = text.lower()
    alerts = []

    if "dados pessoais" in text_lower:
        alerts.append("Documento menciona dados pessoais.")

    if "confidencialidade" in text_lower or "sigilo" in text_lower:
        alerts.append("Documento contém cláusula ou obrigação de confidencialidade.")

    if "multa" in text_lower:
        alerts.append("Documento contém menção a multa.")

    if "rescis" in text_lower:
        alerts.append("Documento contém menção a rescisão.")
    else:
        alerts.append("Não foi identificada cláusula clara de rescisão.")

    return alerts


def analyze_document(text: str) -> dict:
    document_type = classify_document(text)
    summary = generate_summary(text, document_type)
    alerts = generate_alerts(text)

    return {
        "document_type": document_type,
        "summary": summary,
        "alerts": alerts
    }