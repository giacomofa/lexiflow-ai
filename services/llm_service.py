import json
import os
import re

def clean_generated_text(text: str) -> str:
    if not isinstance(text, str):
        return text

    cleaned = text.strip()
    cleaned = re.sub(r"[\u0900-\u097F]+", "", cleaned)  # remove devanagari
    cleaned = cleaned.replace("pnult_", "")
    cleaned = cleaned.replace("null_", "")
    cleaned = cleaned.replace("\u200b", "")
    cleaned = cleaned.replace("\ufeff", "")
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    return cleaned


def sanitize_analysis_payload(data):
    if isinstance(data, dict):
        return {key: sanitize_analysis_payload(value) for key, value in data.items()}
    if isinstance(data, list):
        return [sanitize_analysis_payload(item) for item in data]
    if isinstance(data, str):
        return clean_generated_text(data)
    return data

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def _safe_json_loads(content: str) -> dict:
    content = content.strip()

    if content.startswith("```json"):
        content = content.removeprefix("```json").strip()
    if content.startswith("```"):
        content = content.removeprefix("```").strip()
    if content.endswith("```"):
        content = content.removesuffix("```").strip()

    return json.loads(content)


def analyze_document_with_llm(document_name: str, document_text: str) -> dict:
    system_prompt = """
Você é um analisador de documentos corporativos da empresa fictícia NovaLex Serviços Corporativos.

Sua função é analisar documentos como contratos, acordos de confidencialidade, políticas internas e aditivos contratuais.

Regras obrigatórias:
1. Responda apenas com base no conteúdo fornecido.
2. Não invente informações que não estejam claramente presentes no texto.
3. Quando uma informação não puder ser identificada, retorne null.
4. Sua resposta deve estar em JSON válido.
5. Extraia somente o que puder ser sustentado pelo documento.
6. Inclua trechos curtos do documento como evidência em "source_snippets".
7. Classifique o documento em uma das seguintes categorias:
   - contrato_prestacao_servicos
   - nda
   - politica_interna
   - aditivo_contratual
   - fora_escopo
8. Use "fora_escopo" quando o documento não se enquadrar claramente nas categorias suportadas pelo MVP.
9. Se o documento for classificado como "fora_escopo", mantenha o resumo explicando brevemente isso e retorne null nos campos não aplicáveis.
10. O campo "summary" deve ser claro, objetivo e ter no máximo 5 linhas.
11. Não inclua comentários fora do JSON.
12. "start_date" e "end_date" só devem ser preenchidos quando houver datas de calendário explícitas no documento.
13. Expressões como "na data de sua assinatura" não devem preencher "start_date"; nesses casos, use null.
14. "termination_clause" só deve ser preenchido quando houver regra explícita de rescisão/encerramento do instrumento.
15. Não use conteúdo de multa ou penalidade para preencher "termination_clause".
16. "penalty_clause" só deve ser preenchido quando houver multa, penalidade contratual ou consequência pecuniária claramente identificável.
17. Medidas administrativas internas, sanções disciplinares genéricas ou consequências não pecuniárias não devem preencher "penalty_clause".
18. Use apenas português com alfabeto latino e pontuação normal.
"""

    user_prompt = f"""
Analise o documento abaixo e devolva a resposta no formato JSON especificado.

Schema esperado:
{{
  "document_name": "string",
  "document_type": "string",
  "summary": "string",
  "parties": ["string"],
  "object": "string",
  "start_date": "string ou null",
  "end_date": "string ou null",
  "term_duration": "string ou null",
  "renewal_clause": "string ou null",
  "termination_clause": "string ou null",
  "penalty_clause": "string ou null",
  "confidentiality_clause": "string ou null",
  "personal_data_mentions": true, false ou null,
  "personal_data_details": "string ou null",
  "key_obligations": ["string"],
  "risk_alerts": [],
  "source_snippets": ["string"]
}}

Instruções adicionais:
- Use null quando a informação não estiver claramente identificada.
- "risk_alerts" pode ser retornado como lista vazia.
- "source_snippets" deve conter de 2 a 5 trechos curtos do texto.
- Não use conhecimento externo.
- Se o documento estiver fora do escopo, classifique como "fora_escopo".
- Retorne apenas JSON válido.

Nome do arquivo:
{document_name}

Texto do documento:
{document_text}
"""

    response = client.responses.create(
        model="gpt-5.4-mini",
        input=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )

    content = response.output_text.strip()
    parsed = _safe_json_loads(content)
    return sanitize_analysis_payload(parsed)


def answer_question_with_context(
    document_name: str,
    user_question: str,
    retrieved_context: str,
    question_type: str = "open",
) -> str:
    system_prompt = """
Você é um assistente de análise documental da NovaLex Serviços Corporativos.

Sua tarefa é responder perguntas sobre documentos corporativos usando exclusivamente o contexto fornecido.

Regras obrigatórias:
1. Responda apenas com base no contexto recebido.
2. Se a resposta não estiver presente ou não estiver clara, diga explicitamente que a informação não foi identificada no documento.
3. Não invente cláusulas, datas, valores ou interpretações não sustentadas.
4. Não use placeholders, caracteres estranhos, siglas inventadas ou fragmentos sem sentido.
5. Use apenas português com alfabeto latino e pontuação normal.
6. Responda em linguagem natural, objetiva e profissional.
7. Sempre que possível, mencione resumidamente a evidência textual usada.
8. A resposta deve ter no máximo 4 linhas.
"""

    if question_type == "binary":
        style_instruction = """
Formato desejado:
- Responda começando com "Sim." ou "Não."
- Depois explique brevemente com base no contexto.
- Se negativo, diga que a informação não foi identificada nos trechos recuperados.
"""
    else:
        style_instruction = """
Formato desejado:
- Não comece com "Sim." ou "Não."
- Responda diretamente ao que foi perguntado.
- Se a informação não estiver clara, diga que ela não foi identificada no documento.
"""

    user_prompt = f"""
Responda à pergunta com base exclusivamente no contexto abaixo.

{style_instruction}

Nome do documento:
{document_name}

Contexto recuperado:
{retrieved_context}

Pergunta do usuário:
{user_question}
"""

    response = client.responses.create(
        model="gpt-5.4-mini",
        input=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )

    return response.output_text.strip()


def clean_llm_answer(text: str) -> str:
    if not text:
        return "Não foi possível gerar uma resposta."

    return clean_generated_text(text)