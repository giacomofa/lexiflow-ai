import unittest

from services.query_service import (
    answer_from_structured_analysis,
    enforce_answer_limits,
    infer_question_type,
    infer_structured_intent,
    strip_embedded_evidence,
)


class InferQuestionTypeTests(unittest.TestCase):
    def test_question_starting_with_binary_marker_is_binary(self):
        self.assertEqual(infer_question_type("Existe cláusula de multa?"), "binary")
        self.assertEqual(infer_question_type("O documento menciona dados pessoais?"), "binary")

    def test_open_question_is_open(self):
        self.assertEqual(infer_question_type("Qual é o objeto do contrato?"), "open")


class InferStructuredIntentTests(unittest.TestCase):
    def test_multa_keyword_maps_to_penalty_clause(self):
        self.assertEqual(infer_structured_intent("Existe multa por rescisão?"), "penalty_clause")

    def test_vigencia_keyword_maps_to_term_duration(self):
        self.assertEqual(infer_structured_intent("Qual a vigência do contrato?"), "term_duration")

    def test_unrecognized_question_has_no_structured_intent(self):
        self.assertIsNone(infer_structured_intent("Qual é a cor do logo da empresa?"))


class AnswerFromStructuredAnalysisTests(unittest.TestCase):
    def test_personal_data_mentions_true_answers_affirmatively(self):
        result = answer_from_structured_analysis(
            question="O documento menciona dados pessoais?",
            question_type="binary",
            full_analysis={"personal_data_mentions": True, "personal_data_details": "dados cadastrais"},
        )

        self.assertIsNotNone(result)
        self.assertTrue(result["answer"].startswith("Sim."))

    def test_personal_data_mentions_false_answers_negatively(self):
        result = answer_from_structured_analysis(
            question="O documento menciona dados pessoais?",
            question_type="binary",
            full_analysis={"personal_data_mentions": False},
        )

        self.assertTrue(result["answer"].startswith("Não."))

    def test_no_full_analysis_returns_none(self):
        result = answer_from_structured_analysis(
            question="Existe multa?", question_type="binary", full_analysis={}
        )

        self.assertIsNone(result)

    def test_unstructured_question_returns_none(self):
        result = answer_from_structured_analysis(
            question="Qual a cor do logo?", question_type="open", full_analysis={"penalty_clause": "20%"}
        )

        self.assertIsNone(result)


class StripEmbeddedEvidenceTests(unittest.TestCase):
    def test_removes_leading_resposta_label(self):
        answer = "Resposta: O prazo é de 12 meses."

        self.assertEqual(strip_embedded_evidence(answer), "O prazo é de 12 meses.")

    def test_removes_trailing_evidencias_encontradas_block(self):
        answer = "O prazo é de 12 meses.\n\nEvidências encontradas: trecho 1, trecho 2"

        self.assertEqual(strip_embedded_evidence(answer), "O prazo é de 12 meses.")

    def test_leaves_normal_answer_untouched(self):
        answer = "O prazo é de 12 meses."

        self.assertEqual(strip_embedded_evidence(answer), answer)


class EnforceAnswerLimitsTests(unittest.TestCase):
    def test_short_answer_is_untouched(self):
        answer = "Resposta curta."

        self.assertEqual(enforce_answer_limits(answer, max_chars=600), answer)

    def test_long_answer_is_truncated_with_ellipsis(self):
        answer = "palavra " * 200

        result = enforce_answer_limits(answer, max_chars=100)

        self.assertLessEqual(len(result), 104)
        self.assertTrue(result.endswith("..."))


if __name__ == "__main__":
    unittest.main()
