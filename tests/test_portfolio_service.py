import unittest
from datetime import date

from services.portfolio_service import (
    STATUS_ATIVO,
    STATUS_SEM_VIGENCIA_APLICAVEL,
    STATUS_VENCENDO_EM_90_DIAS,
    STATUS_VENCIDO,
    build_portfolio_summary,
    compute_document_status,
    normalize_date,
)


class NormalizeDateTests(unittest.TestCase):
    def test_none_returns_none(self):
        self.assertIsNone(normalize_date(None))

    def test_empty_string_returns_none(self):
        self.assertIsNone(normalize_date(""))
        self.assertIsNone(normalize_date("   "))

    def test_iso_datetime_string_is_parsed(self):
        """Regressão: valores como '2026-01-01 00:00:00' vinham como string
        livre e quebravam o cálculo de vencimento antes desta normalização."""
        self.assertEqual(normalize_date("2026-01-01 00:00:00"), date(2026, 1, 1))

    def test_iso_date_string_is_parsed(self):
        self.assertEqual(normalize_date("2026-01-01"), date(2026, 1, 1))

    def test_brazilian_date_format_is_parsed(self):
        self.assertEqual(normalize_date("31/10/2026"), date(2026, 10, 31))

    def test_free_text_returns_none(self):
        self.assertIsNone(normalize_date("na data de sua assinatura"))

    def test_date_object_is_passed_through(self):
        d = date(2026, 5, 1)
        self.assertEqual(normalize_date(d), d)


class ComputeDocumentStatusTests(unittest.TestCase):
    def setUp(self):
        self.today = date(2026, 6, 1)

    def test_nda_without_end_date_is_not_vencido(self):
        """NDAs sem data de fim explícita não podem cair em 'vencido' por padrão."""
        result = compute_document_status("nda", None, self.today)

        self.assertEqual(result["status"], STATUS_SEM_VIGENCIA_APLICAVEL)
        self.assertEqual(result["reason"], "tipo_sem_vigencia_obrigatoria")

    def test_politica_interna_without_end_date_is_not_vencido(self):
        result = compute_document_status("politica_interna", None, self.today)

        self.assertEqual(result["status"], STATUS_SEM_VIGENCIA_APLICAVEL)

    def test_contrato_without_end_date_is_sem_vigencia_with_different_reason(self):
        result = compute_document_status("contrato_prestacao_servicos", None, self.today)

        self.assertEqual(result["status"], STATUS_SEM_VIGENCIA_APLICAVEL)
        self.assertEqual(result["reason"], "data_de_fim_nao_identificada")

    def test_past_end_date_is_vencido(self):
        result = compute_document_status("contrato_prestacao_servicos", "2026-01-01", self.today)

        self.assertEqual(result["status"], STATUS_VENCIDO)

    def test_end_date_within_90_days_is_vencendo(self):
        result = compute_document_status("contrato_prestacao_servicos", "2026-07-01", self.today)

        self.assertEqual(result["status"], STATUS_VENCENDO_EM_90_DIAS)

    def test_end_date_far_in_future_is_ativo(self):
        result = compute_document_status("contrato_prestacao_servicos", "2027-06-01", self.today)

        self.assertEqual(result["status"], STATUS_ATIVO)

    def test_end_date_exactly_today_is_vencendo_not_vencido(self):
        result = compute_document_status("contrato_prestacao_servicos", "2026-06-01", self.today)

        self.assertEqual(result["status"], STATUS_VENCENDO_EM_90_DIAS)


class BuildPortfolioSummaryTests(unittest.TestCase):
    def setUp(self):
        self.today = date(2026, 6, 1)

    def test_counts_and_by_type_are_aggregated(self):
        documents = [
            {"id": 1, "file_name": "a.txt", "document_type": "contrato_prestacao_servicos", "end_date": "2027-01-01"},
            {"id": 2, "file_name": "b.txt", "document_type": "contrato_prestacao_servicos", "end_date": "2026-01-01"},
            {"id": 3, "file_name": "c.txt", "document_type": "nda", "end_date": None},
            {"id": 4, "file_name": "d.txt", "document_type": "aditivo_contratual", "end_date": "2026-06-15"},
        ]

        summary = build_portfolio_summary(documents, self.today)

        self.assertEqual(summary["total"], 4)
        self.assertEqual(summary["counts"][STATUS_ATIVO], 1)
        self.assertEqual(summary["counts"][STATUS_VENCIDO], 1)
        self.assertEqual(summary["counts"][STATUS_SEM_VIGENCIA_APLICAVEL], 1)
        self.assertEqual(summary["counts"][STATUS_VENCENDO_EM_90_DIAS], 1)
        self.assertEqual(summary["by_type"]["contrato_prestacao_servicos"], 2)
        self.assertEqual(summary["by_type"]["nda"], 1)

    def test_upcoming_list_is_sorted_by_end_date_ascending(self):
        documents = [
            {"id": 1, "file_name": "later.txt", "document_type": "contrato_prestacao_servicos", "end_date": "2026-08-20"},
            {"id": 2, "file_name": "sooner.txt", "document_type": "contrato_prestacao_servicos", "end_date": "2026-06-10"},
        ]

        summary = build_portfolio_summary(documents, self.today)

        self.assertEqual([item["file_name"] for item in summary["upcoming"]], ["sooner.txt", "later.txt"])

    def test_empty_document_list(self):
        summary = build_portfolio_summary([], self.today)

        self.assertEqual(summary["total"], 0)
        self.assertEqual(summary["upcoming"], [])


if __name__ == "__main__":
    unittest.main()
