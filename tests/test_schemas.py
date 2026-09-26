import unittest

from services.schemas import validate_llm_output


class ValidateLLMOutputTests(unittest.TestCase):
    def test_personal_data_mentions_sim_is_coerced_to_true(self):
        """Regressão do bug real: o LLM às vezes devolve 'Sim' em vez de true,
        e query_service.py fazia `if mentions is True` (comparação estrita)."""
        raw = {"personal_data_mentions": "Sim"}

        validated, warnings = validate_llm_output(raw)

        self.assertIs(validated["personal_data_mentions"], True)
        self.assertEqual(len(warnings), 1)
        self.assertIn("personal_data_mentions", warnings[0])

    def test_personal_data_mentions_nao_is_coerced_to_false(self):
        raw = {"personal_data_mentions": "Não"}

        validated, warnings = validate_llm_output(raw)

        self.assertIs(validated["personal_data_mentions"], False)
        self.assertEqual(len(warnings), 1)

    def test_personal_data_mentions_native_bool_produces_no_warning(self):
        raw = {"personal_data_mentions": True}

        validated, warnings = validate_llm_output(raw)

        self.assertIs(validated["personal_data_mentions"], True)
        self.assertEqual(warnings, [])

    def test_personal_data_mentions_unrecognized_string_becomes_none(self):
        raw = {"personal_data_mentions": "talvez"}

        validated, warnings = validate_llm_output(raw)

        self.assertIsNone(validated["personal_data_mentions"])
        self.assertEqual(len(warnings), 1)

    def test_invalid_document_type_falls_back_to_fora_escopo(self):
        raw = {"document_type": "categoria_inexistente"}

        validated, warnings = validate_llm_output(raw)

        self.assertEqual(validated["document_type"], "fora_escopo")
        self.assertEqual(len(warnings), 1)

    def test_valid_document_type_is_preserved(self):
        raw = {"document_type": "nda"}

        validated, warnings = validate_llm_output(raw)

        self.assertEqual(validated["document_type"], "nda")
        self.assertEqual(warnings, [])

    def test_string_list_fields_accept_single_string(self):
        raw = {"parties": "Empresa X"}

        validated, _ = validate_llm_output(raw)

        self.assertEqual(validated["parties"], ["Empresa X"])

    def test_string_list_fields_default_to_empty_list(self):
        raw = {}

        validated, _ = validate_llm_output(raw)

        self.assertEqual(validated["parties"], [])
        self.assertEqual(validated["risk_alerts"], [])
        self.assertEqual(validated["source_snippets"], [])

    def test_non_dict_input_returns_defaults_with_warning(self):
        validated, warnings = validate_llm_output("não é um dict")

        self.assertEqual(validated["document_type"], "fora_escopo")
        self.assertEqual(len(warnings), 1)


if __name__ == "__main__":
    unittest.main()
