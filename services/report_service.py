"""
Geração de relatório executivo em PDF a partir da análise de um documento.
"""
from __future__ import annotations

import io

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    ListFlowable,
    ListItem,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

NAVY = colors.HexColor("#1F3A5F")
LIGHT_GRAY = colors.HexColor("#F4F6FA")
BORDER_GRAY = colors.HexColor("#E3E8EF")
TEXT_COLOR = colors.HexColor("#1A2233")
MUTED_TEXT = colors.HexColor("#5B6472")

DOCUMENT_TYPE_LABELS = {
    "contrato_prestacao_servicos": "Contrato de prestação de serviços",
    "nda": "NDA (acordo de confidencialidade)",
    "politica_interna": "Política interna",
    "aditivo_contratual": "Aditivo contratual",
    "fora_escopo": "Fora do escopo do MVP",
}

FIELD_LABELS = (
    ("parties", "Partes envolvidas", "list"),
    ("object", "Objeto", "text"),
    ("start_date", "Data de início", "text"),
    ("end_date", "Data de fim", "text"),
    ("term_duration", "Prazo / vigência", "text"),
    ("renewal_clause", "Renovação", "text"),
    ("termination_clause", "Rescisão", "text"),
    ("penalty_clause", "Multa", "text"),
    ("confidentiality_clause", "Confidencialidade", "text"),
    ("personal_data_details", "Detalhes sobre dados pessoais", "text"),
    ("key_obligations", "Obrigações principais", "list"),
)


def _styles():
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "LexiflowTitle", parent=base["Title"], textColor=NAVY, fontSize=18, spaceAfter=2,
        ),
        "subtitle": ParagraphStyle(
            "LexiflowSubtitle", parent=base["Normal"], textColor=MUTED_TEXT, fontSize=10, spaceAfter=14,
        ),
        "h2": ParagraphStyle(
            "LexiflowH2", parent=base["Heading2"], textColor=NAVY, fontSize=13, spaceBefore=14, spaceAfter=6,
        ),
        "body": ParagraphStyle(
            "LexiflowBody", parent=base["Normal"], textColor=TEXT_COLOR, fontSize=10, leading=14,
        ),
        "meta": ParagraphStyle(
            "LexiflowMeta", parent=base["Normal"], textColor=MUTED_TEXT, fontSize=9, leading=13,
        ),
        "alert": ParagraphStyle(
            "LexiflowAlert", parent=base["Normal"], textColor=TEXT_COLOR, fontSize=10, leading=14,
        ),
        "footer": ParagraphStyle(
            "LexiflowFooter", parent=base["Normal"], textColor=MUTED_TEXT, fontSize=8, leading=11,
        ),
    }


def _format_field_value(value, kind: str) -> str | None:
    if kind == "list":
        if not value:
            return None
        return "; ".join(str(item) for item in value)

    if not value:
        return None
    return str(value)


def generate_pdf_report(document: dict) -> bytes:
    """Gera o PDF do relatório executivo e retorna os bytes do arquivo.

    `document` deve conter: file_name, document_type, summary, alerts,
    full_analysis (dict) e, opcionalmente, created_at e id.
    """
    styles = _styles()
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        title=f"Relatório LexiFlow AI - {document.get('file_name', '')}",
    )

    story = []

    story.append(Paragraph("LexiFlow AI", styles["title"]))
    story.append(Paragraph("Relatório executivo de análise documental", styles["subtitle"]))

    full_analysis = document.get("full_analysis") or {}
    document_type = document.get("document_type", "fora_escopo")
    type_label = DOCUMENT_TYPE_LABELS.get(document_type, document_type)

    meta_rows = [
        ["Arquivo:", document.get("file_name", "-")],
        ["Tipo documental:", type_label],
    ]
    if document.get("created_at"):
        meta_rows.append(["Processado em:", str(document["created_at"])])
    if document.get("id") is not None:
        meta_rows.append(["ID:", str(document["id"])])
    if full_analysis.get("prompt_version"):
        model_suffix = f" ({full_analysis['model']})" if full_analysis.get("model") else ""
        meta_rows.append(["Versão do prompt:", f"{full_analysis['prompt_version']}{model_suffix}"])

    meta_table = Table(meta_rows, colWidths=[3.5 * cm, None])
    meta_table.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TEXTCOLOR", (0, 0), (0, -1), MUTED_TEXT),
        ("TEXTCOLOR", (1, 0), (1, -1), TEXT_COLOR),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 12))

    story.append(Paragraph("Resumo executivo", styles["h2"]))
    story.append(Paragraph(document.get("summary") or "Resumo não identificado.", styles["body"]))

    alerts = document.get("alerts") or []
    story.append(Paragraph("Alertas identificados", styles["h2"]))
    if alerts:
        story.append(ListFlowable(
            [ListItem(Paragraph(alert, styles["alert"]), bulletColor=NAVY) for alert in alerts],
            bulletType="bullet",
            start="circle",
            leftIndent=12,
        ))
    else:
        story.append(Paragraph("Nenhum alerta identificado.", styles["body"]))

    structured_rows = []
    for field_key, label, kind in FIELD_LABELS:
        value = _format_field_value(full_analysis.get(field_key), kind)
        if value:
            structured_rows.append([label, value])

    if structured_rows:
        story.append(Paragraph("Análise estruturada", styles["h2"]))
        table = Table(
            [[Paragraph(f"<b>{label}</b>", styles["body"]), Paragraph(value, styles["body"])] for label, value in structured_rows],
            colWidths=[4 * cm, None],
        )
        table.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.5, BORDER_GRAY),
            ("BACKGROUND", (0, 0), (0, -1), LIGHT_GRAY),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(table)

    story.append(Spacer(1, 20))
    story.append(Paragraph(
        "Gerado automaticamente pelo LexiFlow AI. Este relatório é um apoio à análise inicial "
        "e não substitui a revisão de um especialista humano.",
        styles["footer"],
    ))

    doc.build(story)
    return buffer.getvalue()
