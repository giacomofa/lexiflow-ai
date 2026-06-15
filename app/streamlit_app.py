import sys
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

from services.document_loader import load_document
from services.text_preprocessor import preprocess_text
from services.llm_analysis_service import analyze_document
from services.storage_service import (
    init_db,
    save_document_analysis,
    list_documents,
    get_document_by_id,
    list_documents_for_indexing,
)
from services.query_service import answer_question_from_document
from rag.vector_store import index_document

st.set_page_config(page_title="LexiFlow AI", page_icon="📄", layout="wide")

init_db()


def reindex_all_documents():
    documents = list_documents_for_indexing()

    total_docs = len(documents)
    success_count = 0
    total_chunks = 0
    errors = []

    for doc in documents:
        try:
            chunk_count = index_document(
                document_id=doc["id"],
                file_name=doc["file_name"],
                document_text=doc["document_text"],
            )
            success_count += 1
            total_chunks += chunk_count
        except Exception as e:
            errors.append(f"ID {doc['id']} | {doc['file_name']} | Erro: {e}")

    return {
        "total_docs": total_docs,
        "success_count": success_count,
        "total_chunks": total_chunks,
        "errors": errors,
    }


def render_list(title: str, items):
    st.write(f"**{title}:**")
    if items:
        for item in items:
            st.write(f"- {item}")
    else:
        st.write("Não identificado.")


def render_text(title: str, value):
    st.write(f"**{title}:** {value if value else 'Não identificado.'}")


def render_yes_no(title: str, value):
    if value is True:
        st.write(f"**{title}:** Sim")
    elif value is False:
        st.write(f"**{title}:** Não")
    else:
        st.write(f"**{title}:** Não identificado.")


def render_structured_analysis(full_analysis: dict):
    if not full_analysis:
        st.info("Este documento não possui análise estruturada salva. Reprocesse o arquivo para gerar os campos completos.")
        return

    st.subheader("Análise estruturada")

    tab1, tab2, tab3 = st.tabs(["Campos principais", "Cláusulas e risco", "Evidências"])

    with tab1:
        col1, col2 = st.columns(2)

        with col1:
            render_list("Partes envolvidas", full_analysis.get("parties"))
            render_text("Objeto", full_analysis.get("object"))
            render_text("Data de início", full_analysis.get("start_date"))
            render_text("Data de fim", full_analysis.get("end_date"))
            render_text("Prazo / vigência", full_analysis.get("term_duration"))

        with col2:
            render_text("Renovação", full_analysis.get("renewal_clause"))
            render_yes_no("Menciona dados pessoais", full_analysis.get("personal_data_mentions"))
            render_text("Detalhes sobre dados pessoais", full_analysis.get("personal_data_details"))
            render_list("Obrigações principais", full_analysis.get("key_obligations"))

    with tab2:
        render_text("Rescisão", full_analysis.get("termination_clause"))
        render_text("Multa", full_analysis.get("penalty_clause"))
        render_text("Confidencialidade", full_analysis.get("confidentiality_clause"))
        render_list("Alertas identificados", full_analysis.get("risk_alerts"))

    with tab3:
        render_list("Trechos de evidência", full_analysis.get("source_snippets"))

        with st.expander("Ver JSON bruto da análise"):
            st.json(full_analysis)


def render_reindex_section():
    st.sidebar.subheader("Administração")

    if st.sidebar.button("Reindexar documentos salvos", key="reindex_button"):
        with st.spinner("Reindexando documentos no Chroma..."):
            reindex_result = reindex_all_documents()

        if reindex_result["errors"]:
            st.warning(
                f"Reindexação concluída com ressalvas. "
                f"Documentos indexados com sucesso: {reindex_result['success_count']}/{reindex_result['total_docs']}. "
                f"Chunks criados/atualizados: {reindex_result['total_chunks']}."
            )

            st.write("**Erros encontrados:**")
            for error in reindex_result["errors"]:
                st.write(f"- {error}")
        else:
            st.success(
                f"Reindexação concluída com sucesso. "
                f"Documentos indexados: {reindex_result['success_count']}/{reindex_result['total_docs']}. "
                f"Chunks criados/atualizados: {reindex_result['total_chunks']}."
            )


def render_process_page():
    st.title("LexiFlow AI")
    st.subheader("Processar documento")
    st.write("Envie um contrato, política, NDA ou aditivo para análise.")

    uploaded_file = st.file_uploader(
        "Envie um documento PDF ou TXT",
        type=["pdf", "txt"],
        key="upload_process_page"
    )

    if uploaded_file is not None:
        st.success(f"Arquivo recebido: {uploaded_file.name}")

        try:
            raw_text = load_document(uploaded_file)
            processed_text = preprocess_text(raw_text)

            st.subheader("Texto extraído do documento")
            st.text_area(
                "Conteúdo",
                value=processed_text,
                height=250,
                key="text_area_process_page"
            )

            if st.button("Processar documento", key="process_button"):
                with st.spinner("Analisando documento com IA..."):
                    result = analyze_document(processed_text, uploaded_file.name)

                document_id = save_document_analysis(
                    file_name=uploaded_file.name,
                    document_text=processed_text,
                    result=result
                )

                chunk_count = 0
                indexing_error = None

                try:
                    chunk_count = index_document(
                        document_id=document_id,
                        file_name=uploaded_file.name,
                        document_text=processed_text,
                    )
                except Exception as e:
                    indexing_error = str(e)

                st.subheader("Resultado da análise")
                st.write(f"**Tipo do documento:** {result['document_type']}")
                st.write(f"**Resumo executivo:** {result['summary']}")

                if result["document_type"] == "fora_escopo":
                    st.warning(
                        "Este documento foi classificado como fora do escopo do MVP. "
                        "O LexiFlow foi desenhado para contratos, políticas internas, NDAs e aditivos contratuais."
                    )

                st.write("**Alertas:**")
                for alert in result["alerts"]:
                    st.write(f"- {alert}")

                render_structured_analysis(result.get("full_analysis", {}))

                if indexing_error:
                    st.warning(
                        "Documento processado e salvo com sucesso, mas a indexação vetorial falhou nesta tentativa. "
                        f"Erro: {indexing_error}"
                    )
                else:
                    st.success(
                        f"Documento processado, salvo e indexado com sucesso. Chunks criados: {chunk_count}"
                    )

        except Exception as e:
            st.error(f"Erro ao processar o documento: {e}")


def render_history_page():
    st.title("LexiFlow AI")
    st.subheader("Consultar histórico")
    st.write("Selecione um documento já processado para consultar os detalhes e fazer perguntas.")

    documents = list_documents()

    if not documents:
        st.info("Nenhum documento processado ainda.")
        return

    options = {
        f"ID {doc['id']} | {doc['file_name']} | {doc['document_type']}": doc["id"]
        for doc in documents
    }

    selected_label = st.selectbox(
        "Selecione um documento salvo:",
        list(options.keys()),
        index=None,
        placeholder="Escolha um documento do histórico...",
        key="history_selectbox"
    )

    if selected_label is None:
        st.info("Selecione um documento para visualizar os detalhes.")
        return

    selected_id = options[selected_label]
    selected_doc = get_document_by_id(selected_id)

    if not selected_doc:
        st.warning("Documento não encontrado.")
        return

    st.subheader("Detalhes do documento selecionado")
    st.write(f"**ID:** {selected_doc['id']}")
    st.write(f"**Arquivo:** {selected_doc['file_name']}")
    st.write(f"**Tipo:** {selected_doc['document_type']}")
    st.write(f"**Processado em:** {selected_doc['created_at']}")
    st.write(f"**Resumo:** {selected_doc['summary']}")
    
    if selected_doc["document_type"] == "fora_escopo":
        st.warning(
            "Este documento foi classificado como fora do escopo do MVP. "
            "As funcionalidades de extração e consulta podem ser menos aderentes do que nos tipos suportados."
        )

    st.write("**Alertas:**")
    if selected_doc["alerts"]:
        for alert in selected_doc["alerts"]:
            st.write(f"- {alert}")
    else:
        st.write("Nenhum alerta identificado.")

    render_structured_analysis(selected_doc.get("full_analysis", {}))

    st.text_area(
        "Texto completo do documento",
        value=selected_doc["document_text"],
        height=300,
        disabled=True,
        key=f"history_document_text_{selected_doc['id']}"
    )

    if selected_doc["document_type"] == "fora_escopo":
        st.subheader("Perguntas sobre o documento")
        st.info(
            "A funcionalidade de perguntas e respostas está disponível apenas para "
            "contratos, políticas internas, NDAs e aditivos contratuais."
        )
    else:
        st.subheader("Pergunte sobre este documento")
        user_question = st.text_input(
            "Digite sua pergunta:",
            placeholder="Ex.: Existe cláusula de multa?",
            key=f"history_question_input_{selected_doc['id']}"
        )

        if st.button("Responder pergunta", key="answer_button"):
            if user_question.strip():
                with st.spinner("Buscando evidências e gerando resposta..."):
                    qa_result = answer_question_from_document(
                        selected_doc["id"],
                        selected_doc["file_name"],
                        user_question,
                        selected_doc.get("full_analysis", {})
                    )

                st.write("**Resposta:**")
                st.write(qa_result["answer"])

                if qa_result["evidence"]:
                    st.write("**Evidências encontradas:**")
                    for evidence in qa_result["evidence"]:
                        st.write(f"- {evidence}")
                else:
                    st.write("**Evidências:** Nenhum trecho relevante foi encontrado.")
            else:
                st.warning("Digite uma pergunta antes de continuar.")


st.sidebar.title("LexiFlow AI")
page = st.sidebar.radio(
    "Navegação",
    ["Processar documento", "Consultar histórico"],
    key="main_navigation"
)

render_reindex_section()

if page == "Processar documento":
    render_process_page()
else:
    render_history_page()