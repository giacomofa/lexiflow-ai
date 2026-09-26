import unittest

from services.grounding import check_snippet_grounding, grounding_summary


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


if __name__ == "__main__":
    unittest.main()
