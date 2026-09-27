import unittest

from services.grounding import check_snippet_grounding, compute_field_confidence, grounding_summary


class CheckSnippetGroundingTests(unittest.TestCase):
    def setUp(self):
        self.source_text = (
            "O contrato poderá ser rescindido mediante aviso prévio de 30 dias. "
            "Em caso de rescisão antecipada sem justa causa, incidirá multa de 20%."
        )

    def test_exact_substring_is_grounded(self):
        result = check_snippet_grounding("aviso prévio de 30 dias", self.source_text)

        self.assertTrue(result["grounded"])
        self.assertEqual(result["match_type"], "exact")
        self.assertEqual(result["score"], 1.0)

    def test_slightly_altered_snippet_is_fuzzy_grounded(self):
        result = check_snippet_grounding(
            "O contrato pode ser rescindido mediante aviso prévio de 30 dias.",
            self.source_text,
        )

        self.assertTrue(result["grounded"])
        self.assertEqual(result["match_type"], "fuzzy")

    def test_fabricated_snippet_is_not_grounded(self):
        result = check_snippet_grounding(
            "o contrato prevê pagamento de bônus anual de 50%", self.source_text
        )

        self.assertFalse(result["grounded"])
        self.assertEqual(result["match_type"], "none")

    def test_snippet_wrapped_in_quotes_is_still_grounded(self):
        """Regressão: o LLM às vezes devolve o snippet inteiro entre aspas
        (ex.: '"aviso prévio de 30 dias"'), o que não deveria por si só
        invalidar um trecho que de fato existe no documento."""
        result = check_snippet_grounding('"aviso prévio de 30 dias"', self.source_text)

        self.assertTrue(result["grounded"])
        self.assertEqual(result["match_type"], "exact")

    def test_empty_snippet_is_not_grounded(self):
        result = check_snippet_grounding("", self.source_text)

        self.assertFalse(result["grounded"])


class GroundingSummaryTests(unittest.TestCase):
    def test_summary_counts_grounded_and_ungrounded_snippets(self):
        source_text = "As partes comprometem-se a manter sigilo sobre as informações trocadas."
        snippets = [
            "manter sigilo sobre as informações trocadas",
            "penalidade de 90% do valor do contrato",
        ]

        summary = grounding_summary(snippets, source_text)

        self.assertEqual(summary["total"], 2)
        self.assertEqual(summary["grounded_count"], 1)
        self.assertEqual(summary["ungrounded_count"], 1)
        self.assertIn("penalidade de 90% do valor do contrato", summary["ungrounded_snippets"])

    def test_summary_with_no_snippets(self):
        summary = grounding_summary([], "qualquer texto")

        self.assertEqual(summary["total"], 0)
        self.assertEqual(summary["grounded_count"], 0)
        self.assertEqual(summary["ungrounded_count"], 0)


class ComputeFieldConfidenceTests(unittest.TestCase):
    def setUp(self):
        self.source_text = (
            "MULTA: Em caso de rescisao antecipada sem justa causa, incidira multa de 20%. "
            "CONFIDENCIALIDADE: As partes devem manter sigilo sobre as informacoes trocadas."
        )

    def test_field_grounded_in_source_gets_high_score(self):
        fields = {"penalty_clause": "incidira multa de 20%"}

        confidence = compute_field_confidence(fields, self.source_text)

        self.assertTrue(confidence["penalty_clause"]["grounded"])

    def test_fabricated_field_value_gets_low_confidence(self):
        """Regressão: o LLM pode preencher um campo com um valor plausível mas
        que não está de fato no texto original; isso deve ficar visível."""
        fields = {"penalty_clause": "multa de 500% sobre o valor total do contrato"}

        confidence = compute_field_confidence(fields, self.source_text)

        self.assertFalse(confidence["penalty_clause"]["grounded"])

    def test_none_and_empty_fields_are_omitted(self):
        fields = {"penalty_clause": None, "termination_clause": "", "confidentiality_clause": "manter sigilo"}

        confidence = compute_field_confidence(fields, self.source_text)

        self.assertNotIn("penalty_clause", confidence)
        self.assertNotIn("termination_clause", confidence)
        self.assertIn("confidentiality_clause", confidence)

    def test_non_string_field_is_omitted(self):
        fields = {"parties": ["Empresa A", "Empresa B"]}

        confidence = compute_field_confidence(fields, self.source_text)

        self.assertNotIn("parties", confidence)


if __name__ == "__main__":
    unittest.main()
