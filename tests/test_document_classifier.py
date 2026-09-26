import unittest

from services.document_classifier import classify_by_keywords, reconcile_classification


class ClassifyByKeywordsTests(unittest.TestCase):
    def test_contrato_prestacao_servicos_is_detected(self):
        text = "CONTRATO DE PRESTAÇÃO DE SERVIÇOS\nCONTRATANTE e CONTRATADA firmam o presente."

        doc_type, scores = classify_by_keywords(text)

        self.assertEqual(doc_type, "contrato_prestacao_servicos")
        self.assertGreater(scores["contrato_prestacao_servicos"], 0)

    def test_nda_is_detected(self):
        text = "ACORDO DE CONFIDENCIALIDADE (NDA)\nParte Reveladora e Parte Receptora."

        doc_type, _ = classify_by_keywords(text)

        self.assertEqual(doc_type, "nda")

    def test_politica_interna_is_detected(self):
        text = "POLÍTICA INTERNA DE SEGURANÇA DA INFORMAÇÃO\nEmpresa emissora: NovaLex."

        doc_type, _ = classify_by_keywords(text)

        self.assertEqual(doc_type, "politica_interna")

    def test_aditivo_contratual_is_detected(self):
        text = "ADITIVO CONTRATUAL Nº 01\nAs partes resolvem alterar a vigência do contrato original."

        doc_type, _ = classify_by_keywords(text)

        self.assertEqual(doc_type, "aditivo_contratual")

    def test_unrelated_text_is_fora_escopo(self):
        text = "ATA DE REUNIÃO COMERCIAL\nPauta: revisão do pipeline comercial."

        doc_type, scores = classify_by_keywords(text)

        self.assertEqual(doc_type, "fora_escopo")
        self.assertEqual(scores, {})

    def test_empty_text_is_fora_escopo(self):
        doc_type, scores = classify_by_keywords("")

        self.assertEqual(doc_type, "fora_escopo")
        self.assertEqual(scores, {})


class ReconcileClassificationTests(unittest.TestCase):
    def test_matching_classification_needs_no_review(self):
        text = "CONTRATO DE PRESTAÇÃO DE SERVIÇOS\nCONTRATANTE e CONTRATADA firmam o presente."

        result = reconcile_classification("contrato_prestacao_servicos", text)

        self.assertFalse(result["needs_review"])
        self.assertEqual(result["final_type"], "contrato_prestacao_servicos")
        self.assertIsNone(result["note"])

    def test_diverging_classification_flags_for_review(self):
        text = "ACORDO DE CONFIDENCIALIDADE (NDA)\nParte Reveladora e Parte Receptora."

        result = reconcile_classification("contrato_prestacao_servicos", text)

        self.assertTrue(result["needs_review"])
        self.assertEqual(result["final_type"], "contrato_prestacao_servicos")
        self.assertIsNotNone(result["note"])

    def test_llm_type_is_always_kept_as_final(self):
        """A heurística serve para SINALIZAR divergência, não para sobrescrever o LLM."""
        text = "texto qualquer sem palavras-chave claras"

        result = reconcile_classification("nda", text)

        self.assertEqual(result["final_type"], "nda")


if __name__ == "__main__":
    unittest.main()
