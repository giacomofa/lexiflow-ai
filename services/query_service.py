from rag.vector_store import query_document
from services.llm_service import answer_question_with_context, clean_llm_answer


BINARY_STARTS = (
    "existe",
    "há",
    "ha",
    "tem",
    "possui",
    "contém",
    "contem",
    "inclui",
    "menciona",
    "prevê",
    "preve",
    "foi identificado",
    "tem cláusula",
    "tem clausula",
    "ha cláusula",
    "ha clausula",
    "o documento menciona",
    "o documento possui",
    "o documento prevê",
    "o documento preve",
    "o documento trata",
    "o documento fala",
    "o documento contém",
    "o documento contem",
    "o documento tem",
)

STRUCTURED_INTENTS = {
    "multa": "penalty_clause",
    "confidencialidade": "confidentiality_clause",
    "sigilo": "confidentiality_clause",
    "rescisão": "termination_clause",
    "rescisao": "termination_clause",
    "vigência": "term_duration",
    "vigencia": "term_duration",
    "partes": "parties",
    "dados pessoais": "personal_data_mentions",
}


def infer_question_type(question: str) -> str:
    normalized = question.strip().lower()
    if normalized.startswith(BINARY_STARTS):
        return "binary"
    return "open"


def infer_structured_intent(question: str) -> str | None:
    normalized = question.strip().lower()

    for keyword, intent in STRUCTURED_INTENTS.items():
        if keyword in normalized:
            return intent

    return None


def shorten_evidence(text: str, max_chars: int = 260) -> str:
    if not text:
        return ""

    cleaned = " ".join(text.split())

    if len(cleaned) <= max_chars:
        return cleaned

    shortened = cleaned[:max_chars].rsplit(" ", 1)[0].strip()
    return shortened + "..."


def filter_relevant_snippets(snippets: list[str], keyword: str | None = None) -> list[str]:
    if not snippets:
        return []

    if keyword:
        filtered = [snippet for snippet in snippets if keyword.lower() in snippet.lower()]
        if filtered:
            return [shorten_evidence(snippet) for snippet in filtered[:2]]

    return [shorten_evidence(snippet) for snippet in snippets[:2]]


def answer_from_structured_analysis(
    question: str,
    question_type: str,
    full_analysis: dict,
) -> dict | None:
    if not full_analysis:
        return None

    intent = infer_structured_intent(question)
    if not intent:
        return None

    source_snippets = full_analysis.get("source_snippets", [])

    if intent == "penalty_clause":
        value = full_analysis.get("penalty_clause")
        if value:
            if question_type == "binary":
                answer = f"Sim. Foi identificada cláusula de multa: {value}"
            else:
                answer = f"A cláusula de multa identificada é: {value}"
            evidence = filter_relevant_snippets(source_snippets, "multa")
        else:
            answer = "Não. Não foi identificada cláusula de multa no documento."
            evidence = filter_relevant_snippets(source_snippets, "multa")
        return {"answer": answer, "evidence": evidence}

    if intent == "confidentiality_clause":
        value = full_analysis.get("confidentiality_clause")
        if value:
            if question_type == "binary":
                answer = f"Sim. Foi identificada cláusula de confidencialidade: {value}"
            else:
                answer = f"A cláusula de confidencialidade identificada é: {value}"
            evidence = filter_relevant_snippets(source_snippets, "confid")
        else:
            answer = (
                "Não. Não foi identificada cláusula formal de confidencialidade no documento."
            )
            evidence = filter_relevant_snippets(source_snippets, "confid")
        return {"answer": answer, "evidence": evidence}

    if intent == "termination_clause":
        value = full_analysis.get("termination_clause")
        if value:
            if question_type == "binary":
                answer = f"Sim. Foi identificada cláusula de rescisão: {value}"
            else:
                answer = f"A cláusula de rescisão identificada é: {value}"
            evidence = filter_relevant_snippets(source_snippets, "rescis")
        else:
            answer = "Não. Não foi identificada cláusula clara de rescisão no documento."
            evidence = filter_relevant_snippets(source_snippets, "rescis")
        return {"answer": answer, "evidence": evidence}

    if intent == "term_duration":
        term_duration = full_analysis.get("term_duration")
        start_date = full_analysis.get("start_date")
        end_date = full_analysis.get("end_date")

        if term_duration or start_date or end_date:
            parts = []
            if term_duration:
                parts.append(f"{term_duration}")
            if start_date and end_date:
                parts.append(f"com início em {start_date} e término em {end_date}")
            answer = "A vigência identificada é " + ", ".join(parts) + "."
        else:
            answer = "A vigência não foi identificada no documento."

        evidence = filter_relevant_snippets(source_snippets, "vig")
        return {"answer": answer, "evidence": evidence}

    if intent == "parties":
        parties = full_analysis.get("parties")
        if parties:
            answer = "As partes identificadas são: " + "; ".join(parties) + "."
        else:
            answer = "As partes envolvidas não foram identificadas de forma clara no documento."

        evidence = filter_relevant_snippets(source_snippets)
        return {"answer": answer, "evidence": evidence}

    if intent == "personal_data_mentions":
        mentions = full_analysis.get("personal_data_mentions")
        details = full_analysis.get("personal_data_details")

        if mentions is True:
            if question_type == "binary":
                answer = "Sim. O documento menciona dados pessoais."
                if details:
                    answer += f" Detalhe identificado: {details}"
            else:
                answer = details if details else "O documento menciona dados pessoais."
        else:
            answer = "Não. Não foi identificada menção clara a dados pessoais no documento."

        evidence = filter_relevant_snippets(source_snippets, "dados")
        return {"answer": answer, "evidence": evidence}

    return None


def answer_question_from_document(
    document_id: int,
    document_name: str,
    question: str,
    full_analysis: dict | None = None,
) -> dict:
    question_type = infer_question_type(question)

    structured_result = answer_from_structured_analysis(
        question=question,
        question_type=question_type,
        full_analysis=full_analysis or {},
    )

    if structured_result:
        structured_result["answer"] = clean_llm_answer(structured_result["answer"])
        return structured_result

    relevant_chunks = query_document(document_id, question, n_results=3)

    if not relevant_chunks:
        return {
            "answer": "Não identifiquei uma resposta clara para essa pergunta no documento.",
            "evidence": []
        }

    full_context_blocks = [item["text"] for item in relevant_chunks]
    retrieved_context = "\n\n".join(full_context_blocks)

    llm_answer = answer_question_with_context(
        document_name=document_name,
        user_question=question,
        retrieved_context=retrieved_context,
        question_type=question_type,
    )

    llm_answer = clean_llm_answer(llm_answer)

    negative_markers = (
        "não foi identificada",
        "não foi identificado",
        "não identifiquei",
        "não foi encontrada",
        "não foi encontrado",
        "não está presente",
        "não consta no documento",
        "não foi possível identificar",
    )

    if any(marker in llm_answer.lower() for marker in negative_markers):
        evidence = []
    else:
        evidence = [shorten_evidence(item["text"]) for item in relevant_chunks[:2]]

    return {
        "answer": llm_answer,
        "evidence": evidence
    }