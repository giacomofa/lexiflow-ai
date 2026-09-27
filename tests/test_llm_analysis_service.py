import unittest

from services.llm_analysis_service import build_deterministic_alerts, low_confidence_fields


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


def _field_confidence(**fields_and_scores):
    """Constrói um dict de field_confidence no formato de
    services.grounding.check_snippet_grounding, a partir de {campo: score}."""
    return {
        field: {"snippet": "x", "grounded": score >= 0.8, "match_type": "exact" if score >= 0.8 else "none", "score": score}
        for field, score in fields_and_scores.items()
    }


class LowConfidenceFieldsTests(unittest.TestCase):
    def test_returns_only_ungrounded_fields_sorted(self):
        field_confidence = _field_confidence(penalty_clause=0.3, object=0.95, termination_clause=0.5)

        self.assertEqual(low_confidence_fields(field_confidence), ["penalty_clause", "termination_clause"])

    def test_empty_when_all_fields_grounded(self):
        field_confidence = _field_confidence(penalty_clause=1.0, object=0.9)

        self.assertEqual(low_confidence_fields(field_confidence), [])

    def test_empty_dict_returns_empty_list(self):
        self.assertEqual(low_confidence_fields({}), [])


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
            llm_result, _reconciliation(), _grounding(), _field_confidence()
        )

        self.assertIn("Documento menciona tratamento de dados pessoais.", alerts)
        self.assertIn("Documento contém cláusula de multa contratual.", alerts)
        self.assertIn("Não foi identificada cláusula clara de rescisão.", alerts)
        self.assertIn("Não foi identificada vigência/prazo claro no documento.", alerts)

    def test_fora_escopo_document_gets_scope_alert(self):
        llm_result = {"risk_alerts": [], "personal_data_mentions": None}

        alerts = build_deterministic_alerts(
            llm_result, _reconciliation(final_type="fora_escopo"), _grounding(), _field_confidence()
        )

        self.assertIn("Documento fora do escopo do MVP atual.", alerts)

    def test_diverging_classification_adds_review_alert(self):
        llm_result = {"risk_alerts": [], "personal_data_mentions": None}

        alerts = build_deterministic_alerts(
            llm_result, _reconciliation(needs_review=True), _grounding(), _field_confidence()
        )

        self.assertTrue(any("Classificação divergente" in alert for alert in alerts))

    def test_ungrounded_snippets_add_review_alert(self):
        llm_result = {"risk_alerts": [], "personal_data_mentions": None}

        alerts = build_deterministic_alerts(
            llm_result, _reconciliation(), _grounding(ungrounded_count=2), _field_confidence()
        )

        self.assertTrue(any("2 trecho(s) de evidência" in alert for alert in alerts))

    def test_low_confidence_field_adds_review_alert(self):
        """Fecha o loop entre confiança por campo e os alertas/needs_review:
        antes, um campo com confiança baixa só aparecia como badge na tela,
        sem nunca virar um alerta nem sinalizar necessidade de revisão."""
        llm_result = {"risk_alerts": [], "personal_data_mentions": None}
        field_confidence = _field_confidence(penalty_clause=0.4)

        alerts = build_deterministic_alerts(
            llm_result, _reconciliation(), _grounding(), field_confidence
        )

        self.assertTrue(any("confiança baixa" in alert and "penalty_clause" in alert for alert in alerts))

    def test_alerts_from_llm_are_preserved_and_not_duplicated(self):
        llm_result = {
            "risk_alerts": ["Documento contém cláusula de multa contratual."],
            "penalty_clause": "Multa de 20%",
            "personal_data_mentions": None,
        }

        alerts = build_deterministic_alerts(
            llm_result, _reconciliation(), _grounding(), _field_confidence()
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
            llm_result, _reconciliation(), _grounding(), _field_confidence(termination_clause=1.0)
        )

        self.assertEqual(alerts, [])


if __name__ == "__main__":
    unittest.main()
