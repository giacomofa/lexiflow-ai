"""
Componentes visuais compartilhados (CSS, badges, cards de métrica) para dar
uma aparência mais executiva/corporativa ao Streamlit, além do tema base em
.streamlit/config.toml.
"""
from __future__ import annotations

import html

import streamlit as st

from services.document_types import DOCUMENT_TYPE_LABELS

# nomes de arquivo e outros valores digitados/enviados pelo usuário precisam
# ser escapados antes de entrar em qualquer HTML renderizado com
# unsafe_allow_html=True (badges e tabelas usam HTML "confiável" gerado por
# este módulo, mas o texto do usuário nunca deve ir direto).
escape = html.escape

# paleta semântica: cada "palette_key" tem cor de fundo, texto e borda.
PALETTE = {
    "navy": {"bg": "#E8EEF6", "text": "#1F3A5F", "border": "#1F3A5F"},
    "success": {"bg": "#E6F4EA", "text": "#1E7B34", "border": "#1E7B34"},
    "warning": {"bg": "#FFF4E0", "text": "#B26A00", "border": "#B26A00"},
    "danger": {"bg": "#FDE8E8", "text": "#B3261E", "border": "#B3261E"},
    "neutral": {"bg": "#EEF1F5", "text": "#5B6472", "border": "#5B6472"},
    "purple": {"bg": "#F3E8FD", "text": "#7E3AF2", "border": "#7E3AF2"},
    "teal": {"bg": "#E6F7F5", "text": "#0E7C7B", "border": "#0E7C7B"},
    "orange": {"bg": "#FFF0E5", "text": "#C2570C", "border": "#C2570C"},
}

STATUS_BADGES = {
    "ativo": {"label": "Ativo", "palette": "success"},
    "vencendo_em_90_dias": {"label": "Vencendo em 90 dias", "palette": "warning"},
    "vencido": {"label": "Vencido", "palette": "danger"},
    "sem_vigencia_aplicavel": {"label": "Sem vigência aplicável", "palette": "neutral"},
}

DOCUMENT_TYPE_BADGES = {
    "contrato_prestacao_servicos": {"label": DOCUMENT_TYPE_LABELS["contrato_prestacao_servicos"], "palette": "navy"},
    "nda": {"label": DOCUMENT_TYPE_LABELS["nda"], "palette": "purple"},
    "politica_interna": {"label": DOCUMENT_TYPE_LABELS["politica_interna"], "palette": "teal"},
    "aditivo_contratual": {"label": DOCUMENT_TYPE_LABELS["aditivo_contratual"], "palette": "orange"},
    "fora_escopo": {"label": DOCUMENT_TYPE_LABELS["fora_escopo"], "palette": "neutral"},
}


def inject_base_styles():
    st.markdown(
        """
        <style>
        [data-testid="stAppDeployButton"] { display: none; }
        footer { visibility: hidden; }

        h1, h2, h3 { color: #1F3A5F; }

        .lf-card {
            background: #FFFFFF;
            border: 1px solid #E3E8EF;
            border-left: 4px solid var(--lf-accent, #1F3A5F);
            border-radius: 8px;
            padding: 16px 18px;
            box-shadow: 0 1px 2px rgba(16, 24, 40, 0.04);
        }
        .lf-card .lf-card-label {
            font-size: 0.85em;
            color: #5B6472;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.03em;
        }
        .lf-card .lf-card-value {
            font-size: 1.9em;
            font-weight: 700;
            color: #1A2233;
            line-height: 1.3;
        }
        .lf-card .lf-card-icon {
            font-size: 1.3em;
        }

        .lf-badge {
            display: inline-block;
            padding: 2px 10px;
            border-radius: 999px;
            font-size: 0.82em;
            font-weight: 600;
            border: 1px solid;
            white-space: nowrap;
        }

        .lf-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.95em;
        }
        .lf-table th {
            text-align: left;
            padding: 8px 12px;
            background: #F4F6FA;
            color: #5B6472;
            font-size: 0.82em;
            text-transform: uppercase;
            letter-spacing: 0.03em;
            border-bottom: 1px solid #E3E8EF;
        }
        .lf-table td {
            padding: 8px 12px;
            border-bottom: 1px solid #EEF1F5;
            color: #1A2233;
        }
        .lf-table tr:last-child td { border-bottom: none; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_badge_table(rows: list[dict], columns: list[tuple[str, str]]):
    """Renderiza uma tabela HTML simples com badges. `columns` é uma lista de
    (chave, cabeçalho); se o valor em `row[chave]` já for HTML (badge), ele é
    inserido como está."""
    header_html = "".join(f"<th>{header}</th>" for _, header in columns)
    body_html = ""

    for row in rows:
        cells = "".join(f"<td>{row.get(key, '')}</td>" for key, _ in columns)
        body_html += f"<tr>{cells}</tr>"

    st.markdown(
        f'<table class="lf-table"><thead><tr>{header_html}</tr></thead><tbody>{body_html}</tbody></table>',
        unsafe_allow_html=True,
    )


def render_badge(label: str, palette_key: str) -> str:
    colors = PALETTE.get(palette_key, PALETTE["neutral"])
    return (
        f'<span class="lf-badge" style="background:{colors["bg"]}; '
        f'color:{colors["text"]}; border-color:{colors["border"]};">{label}</span>'
    )


def render_status_badge(status: str) -> str:
    info = STATUS_BADGES.get(status, {"label": status, "palette": "neutral"})
    return render_badge(info["label"], info["palette"])


def render_document_type_badge(document_type: str) -> str:
    info = DOCUMENT_TYPE_BADGES.get(document_type, {"label": document_type or "Não identificado", "palette": "neutral"})
    return render_badge(info["label"], info["palette"])


def confidence_tier(score: float) -> tuple[str, str]:
    """Retorna (label, palette_key) para um score de grounding (0-1)."""
    if score >= 0.8:
        return "Confiança alta", "success"
    if score >= 0.5:
        return "Confiança média", "warning"
    return "Confiança baixa", "danger"


def render_confidence_badge(score: float) -> str:
    label, palette_key = confidence_tier(score)
    return render_badge(label, palette_key)


def render_metric_card(icon: str, label: str, value, palette_key: str = "navy") -> str:
    accent = PALETTE.get(palette_key, PALETTE["navy"])["border"]
    return (
        f'<div class="lf-card" style="--lf-accent: {accent};">'
        f'<div class="lf-card-icon">{icon}</div>'
        f'<div class="lf-card-label">{label}</div>'
        f'<div class="lf-card-value">{value}</div>'
        f'</div>'
    )
