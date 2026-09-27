import sqlite3
import sys
from datetime import date
from pathlib import Path

import pandas as pd
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

from services.auth_service import ROLE_ADMIN, ROLE_BASIC, authenticate, create_user
from services.document_loader import load_document
from services.text_preprocessor import preprocess_text
from services.llm_analysis_service import analyze_document
from services.portfolio_service import (
    STATUS_ATIVO,
    STATUS_VENCENDO_EM_90_DIAS,
    STATUS_VENCIDO,
    build_portfolio_summary,
)
from services.storage_service import (
    get_connection,
    init_db,
    save_document_analysis,
    list_documents,
    list_documents_for_overview,
    get_document_by_id,
    list_documents_for_indexing,
)
from services.query_service import answer_question_from_document
from services.error_messages import describe_error
from services.report_service import generate_pdf_report
from rag.vector_store import index_document

sys.path.append(str(Path(__file__).resolve().parent))
from theme import (  # noqa: E402
    escape,
    inject_base_styles,
    render_badge_table,
    render_confidence_badge,
    render_document_type_badge,
    render_metric_card,
    render_status_badge,
)

st.set_page_config(page_title="LexiFlow AI", page_icon="📄", layout="wide")

inject_base_styles()

init_db()


def render_login_page():
    _, center_col, _ = st.columns([1, 1.2, 1])

    with center_col:
        st.markdown("<div style='height: 60px'></div>", unsafe_allow_html=True)
        st.markdown("### 📄 LexiFlow AI")
        st.caption("Triagem e consulta inteligente de documentos corporativos")

        with st.container(border=True):
            st.subheader("Login")

            with st.form("login_form"):
                username = st.text_input("Usuário")
                password = st.text_input("Senha", type="password")
                submitted = st.form_submit_button("Entrar", use_container_width=True)

            if submitted:
                with get_connection() as conn:
                    user = authenticate(conn, username, password)

                if user:
                    st.session_state["user"] = user
                    st.rerun()
                else:
                    st.error("Usuário ou senha inválidos.")


if "user" not in st.session_state:
    render_login_page()
    st.stop()

current_user = st.session_state["user"]


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


def render_text(title: str, value, field_key: str = None, field_confidence: dict = None):
    badge = ""
    if field_key and field_confidence and field_key in field_confidence:
        score = field_confidence[field_key]["score"]
        badge = f" {render_confidence_badge(score)}"

    st.markdown(f"**{title}:** {value if value else 'Não identificado.'}{badge}", unsafe_allow_html=True)


def render_yes_no(title: str, value):
    if value is True:
        st.write(f"**{title}:** Sim")
    elif value is False:
        st.write(f"**{title}:** Não")
    else:
        st.write(f"**{title}:** Não identificado.")


def render_alerts(alerts):
    if not alerts:
        st.write("Nenhum alerta identificado.")
        return

    for alert in alerts:
        st.markdown(f"⚠️ {alert}")


def render_structured_analysis(full_analysis: dict):
    if not full_analysis:
        st.info("Este documento não possui análise estruturada salva. Reprocesse o arquivo para gerar os campos completos.")
        return

    st.subheader("Análise estruturada")

    field_confidence = full_analysis.get("field_confidence", {})

    tab1, tab2, tab3 = st.tabs(["Campos principais", "Cláusulas e risco", "Evidências"])

    with tab1:
        col1, col2 = st.columns(2)

        with col1:
            render_list("Partes envolvidas", full_analysis.get("parties"))
            render_text("Objeto", full_analysis.get("object"), "object", field_confidence)
            render_text("Data de início", full_analysis.get("start_date"))
            render_text("Data de fim", full_analysis.get("end_date"))
            render_text("Prazo / vigência", full_analysis.get("term_duration"), "term_duration", field_confidence)

        with col2:
            render_text("Renovação", full_analysis.get("renewal_clause"), "renewal_clause", field_confidence)
            render_yes_no("Menciona dados pessoais", full_analysis.get("personal_data_mentions"))
            render_text(
                "Detalhes sobre dados pessoais",
                full_analysis.get("personal_data_details"),
                "personal_data_details",
                field_confidence,
            )
            render_list("Obrigações principais", full_analysis.get("key_obligations"))

    with tab2:
        render_text("Rescisão", full_analysis.get("termination_clause"), "termination_clause", field_confidence)
        render_text("Multa", full_analysis.get("penalty_clause"), "penalty_clause", field_confidence)
        render_text(
            "Confidencialidade", full_analysis.get("confidentiality_clause"), "confidentiality_clause", field_confidence
        )
        st.write("**Alertas identificados:**")
        render_alerts(full_analysis.get("risk_alerts"))

    with tab3:
        render_list("Trechos de evidência", full_analysis.get("source_snippets"))

        with st.expander("Ver JSON bruto da análise"):
            st.json(full_analysis)


def render_overview_page():
    st.title("LexiFlow AI")
    st.subheader("Visão geral")

    documents = list_documents_for_overview(current_user["id"], current_user["role"])
    summary = build_portfolio_summary(documents, date.today())

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(render_metric_card("📁", "Total de documentos", summary["total"], "navy"), unsafe_allow_html=True)
    with col2:
        st.markdown(render_metric_card("✅", "Ativos", summary["counts"][STATUS_ATIVO], "success"), unsafe_allow_html=True)
    with col3:
        st.markdown(
            render_metric_card("⏳", "Vencendo em 90 dias", summary["counts"][STATUS_VENCENDO_EM_90_DIAS], "warning"),
            unsafe_allow_html=True,
        )
    with col4:
        st.markdown(render_metric_card("⛔", "Vencidos", summary["counts"][STATUS_VENCIDO], "danger"), unsafe_allow_html=True)

    st.divider()

    st.subheader("Distribuição por tipo documental")
    if summary["by_type"]:
        chart_data = pd.DataFrame(
            {"quantidade": summary["by_type"].values()},
            index=list(summary["by_type"].keys()),
        )
        st.bar_chart(chart_data, color="#1F3A5F")
    else:
        st.info("Nenhum documento processado ainda.")

    st.divider()

    st.subheader("Vence em breve (próximos 90 dias)")
    if summary["upcoming"]:
        rows = [
            {
                "arquivo": escape(item["file_name"]),
                "tipo": render_document_type_badge(item["document_type"]),
                "status": render_status_badge(STATUS_VENCENDO_EM_90_DIAS),
                "data_fim": item["end_date"].strftime("%d/%m/%Y"),
            }
            for item in summary["upcoming"]
        ]
        render_badge_table(
            rows,
            [("arquivo", "Arquivo"), ("tipo", "Tipo documental"), ("status", "Status"), ("data_fim", "Data de fim")],
        )
    else:
        st.info("Nenhum documento vencendo nos próximos 90 dias.")


def render_admin_sidebar():
    if current_user["role"] != ROLE_ADMIN:
        return

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

    with st.sidebar.expander("Criar novo usuário"):
        with st.form("create_user_form", clear_on_submit=True):
            new_username = st.text_input("Usuário", key="new_username")
            new_password = st.text_input("Senha", type="password", key="new_password")
            new_role = st.selectbox("Perfil", [ROLE_BASIC, ROLE_ADMIN], key="new_role")
            create_submitted = st.form_submit_button("Criar usuário")

        if create_submitted:
            if not new_username.strip() or not new_password:
                st.error("Informe usuário e senha.")
            else:
                try:
                    with get_connection() as conn:
                        create_user(conn, new_username.strip(), new_password, role=new_role)
                    st.success(f"Usuário '{new_username.strip()}' criado com sucesso.")
                except sqlite3.IntegrityError:
                    st.error("Já existe um usuário com esse nome.")


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
                    result=result,
                    user_id=current_user["id"],
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
                st.markdown(
                    f"**Tipo do documento:** {render_document_type_badge(result['document_type'])}",
                    unsafe_allow_html=True,
                )
                st.write(f"**Resumo executivo:** {result['summary']}")

                if result["document_type"] == "fora_escopo":
                    st.warning(
                        "Este documento foi classificado como fora do escopo do MVP. "
                        "O LexiFlow foi desenhado para contratos, políticas internas, NDAs e aditivos contratuais."
                    )

                st.write("**Alertas:**")
                render_alerts(result["alerts"])

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

                pdf_bytes = generate_pdf_report({
                    "id": document_id,
                    "file_name": uploaded_file.name,
                    "document_type": result["document_type"],
                    "summary": result["summary"],
                    "alerts": result["alerts"],
                    "full_analysis": result.get("full_analysis", {}),
                })
                st.download_button(
                    "Baixar relatório em PDF",
                    data=pdf_bytes,
                    file_name=f"relatorio_lexiflow_{document_id}.pdf",
                    mime="application/pdf",
                    key="download_report_process_page",
                )

        except Exception as e:
            st.error(describe_error(e))


def render_history_page():
    st.title("LexiFlow AI")
    st.subheader("Consultar histórico")
    st.write("Selecione um documento já processado para consultar os detalhes e fazer perguntas.")

    documents = list_documents(current_user["id"], current_user["role"])

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
    selected_doc = get_document_by_id(selected_id, current_user["id"], current_user["role"])

    if not selected_doc:
        st.warning("Documento não encontrado.")
        return

    st.subheader("Detalhes do documento selecionado")
    st.write(f"**ID:** {selected_doc['id']}")
    st.write(f"**Arquivo:** {selected_doc['file_name']}")
    st.markdown(f"**Tipo:** {render_document_type_badge(selected_doc['document_type'])}", unsafe_allow_html=True)
    st.write(f"**Processado em:** {selected_doc['created_at']}")
    st.write(f"**Resumo:** {selected_doc['summary']}")

    if selected_doc["document_type"] == "fora_escopo":
        st.warning(
            "Este documento foi classificado como fora do escopo do MVP. "
            "As funcionalidades de extração e consulta podem ser menos aderentes do que nos tipos suportados."
        )

    st.write("**Alertas:**")
    render_alerts(selected_doc["alerts"])

    render_structured_analysis(selected_doc.get("full_analysis", {}))

    try:
        pdf_bytes = generate_pdf_report(selected_doc)
        st.download_button(
            "Baixar relatório em PDF",
            data=pdf_bytes,
            file_name=f"relatorio_lexiflow_{selected_doc['id']}.pdf",
            mime="application/pdf",
            key=f"download_report_history_{selected_doc['id']}",
        )
    except Exception as e:
        st.warning(f"Não foi possível gerar o PDF do relatório: {describe_error(e)}")

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
                try:
                    with st.spinner("Buscando evidências e gerando resposta..."):
                        qa_result = answer_question_from_document(
                            selected_doc["id"],
                            selected_doc["file_name"],
                            user_question,
                            selected_doc.get("full_analysis", {})
                        )
                except Exception as e:
                    st.error(describe_error(e))
                    qa_result = None

                if qa_result:
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
st.sidebar.write(f"Usuário: **{current_user['username']}** ({current_user['role']})")
if st.sidebar.button("Sair", key="logout_button"):
    del st.session_state["user"]
    st.rerun()

st.sidebar.divider()

page = st.sidebar.radio(
    "Navegação",
    ["Visão geral", "Processar documento", "Consultar histórico"],
    key="main_navigation"
)

render_admin_sidebar()

if page == "Visão geral":
    render_overview_page()
elif page == "Processar documento":
    render_process_page()
else:
    render_history_page()