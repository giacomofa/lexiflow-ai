import unittest

from services.llm_analysis_service import build_deterministic_alerts


def _reconciliation(final_type="contrato_prestacao_servicos", needs_review=False):
    return {"final_type": final_type, "needs_review": needs_review, "note": None, "keyword_scores": {}}


def _grounding(ungrounded_count=0):
    return {
        "total": 0,
        "grounded_count": 0,
        "ungrounded_count": ungrounded_count,
        "ungrounded_snippets": [],
        "details": [],
    }


class BuildDeterministicAlertsTests(unittest.TestCase):
    def test_risk_alerts_are_built_even_when_llm_returns_none(self):
        """Regressão: o LLM quase nunca preenchia risk_alerts sozinho; os
        alertas relevantes agora são construídos por regras determinísticas."""
        llm_result = {
            "risk_alerts": [],
            "personal_data_mentions": True,
            "penalty_clause": "Multa de 20%",
            "confidentiality_clause": None,
            "termination_clause": None,
            "term_duration": None,
        }

        alerts = build_deterministic_alerts(
            llm_result, _reconciliation(), _grounding()
        )

        self.assertIn("Documento menciona tratamento de dados pessoais.", alerts)
        self.assertIn("Documento contém cláusula de multa contratual.", alerts)
        self.assertIn("Não foi identificada cláusula clara de rescisão.", alerts)
        self.assertIn("Não foi identificada vigência/prazo claro no documento.", alerts)

    def test_fora_escopo_document_gets_scope_alert(self):
        llm_result = {"risk_alerts": [], "personal_data_mentions": None}

        alerts = build_deterministic_alerts(
            llm_result, _reconciliation(final_type="fora_escopo"), _grounding()
        )

        self.assertIn("Documento fora do escopo do MVP atual.", alerts)

    def test_diverging_classification_adds_review_alert(self):
        llm_result = {"risk_alerts": [], "personal_data_mentions": None}

        alerts = build_deterministic_alerts(
            llm_result, _reconciliation(needs_review=True), _grounding()
        )

        self.assertTrue(any("Classificação divergente" in alert for alert in alerts))

    def test_ungrounded_snippets_add_review_alert(self):
        llm_result = {"risk_alerts": [], "personal_data_mentions": None}

        alerts = build_deterministic_alerts(
            llm_result, _reconciliation(), _grounding(ungrounded_count=2)
        )

        self.assertTrue(any("2 trecho(s) de evidência" in alert for alert in alerts))

    def test_alerts_from_llm_are_preserved_and_not_duplicated(self):
        llm_result = {
            "risk_alerts": ["Documento contém cláusula de multa contratual."],
            "penalty_clause": "Multa de 20%",
            "personal_data_mentions": None,
        }

        alerts = build_deterministic_alerts(
            llm_result, _reconciliation(), _grounding()
        )

        self.assertEqual(
            alerts.count("Documento contém cláusula de multa contratual."), 1
        )

    def test_well_formed_contract_has_no_deterministic_alerts_beyond_llm(self):
        llm_result = {
            "risk_alerts": [],
            "personal_data_mentions": False,
            "penalty_clause": None,
            "confidentiality_clause": None,
            "termination_clause": "Rescisão mediante aviso prévio de 30 dias.",
            "term_duration": "12 meses",
        }

        alerts = build_deterministic_alerts(
            llm_result, _reconciliation(), _grounding()
        )

        self.assertEqual(alerts, [])


if __name__ == "__main__":
    unittest.main()
