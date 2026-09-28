"""
Rótulos canônicos de tipo documental — fonte única de verdade, compartilhada
entre a UI (badges em app/theme.py) e o relatório em PDF
(services/report_service.py). Antes existiam dois dicts mantidos
independentemente, que já haviam divergido (ex.: "NDA" na tela vs "NDA
(acordo de confidencialidade)" no PDF, para o mesmo documento).
"""
from __future__ import annotations

DOCUMENT_TYPE_LABELS = {
    "contrato_prestacao_servicos": "Contrato de prestação de serviços",
    "nda": "NDA (acordo de confidencialidade)",
    "politica_interna": "Política interna",
    "aditivo_contratual": "Aditivo contratual",
    "fora_escopo": "Fora do escopo do MVP",
}
