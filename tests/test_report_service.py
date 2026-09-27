import io
import unittest

from pypdf import PdfReader

from services.report_service import generate_pdf_report


class GeneratePdfReportTests(unittest.TestCase):
    def test_full_document_produces_a_valid_pdf(self):
        document = {
            "id": 1,
            "file_name": "contrato_teste.txt",
            "document_type": "contrato_prestacao_servicos",
            "summary": "Contrato de prestação de serviços de TI.",
            "alerts": ["Documento contém cláusula de multa contratual."],
            "created_at": "2026-09-26 10:00:00",
            "full_analysis": {
                "parties": ["Empresa A", "Empresa B"],
                "object": "Prestação de serviços de TI.",
                "start_date": "01/01/2026",
                "end_date": "31/12/2026",
                "term_duration": "12 meses",
                "penalty_clause": "Multa de 20%.",
                "key_obligations": ["Prestar suporte técnico."],
            },
        }

        pdf_bytes = generate_pdf_report(document)

        self.assertTrue(pdf_bytes.startswith(b"%PDF"))
        self.assertGreater(len(pdf_bytes), 500)

    def test_minimal_document_without_full_analysis_does_not_crash(self):
        document = {
            "file_name": "ata_reuniao.txt",
            "document_type": "fora_escopo",
            "summary": None,
            "alerts": [],
            "full_analysis": {},
        }

        pdf_bytes = generate_pdf_report(document)

        self.assertTrue(pdf_bytes.startswith(b"%PDF"))

    def test_unknown_document_type_falls_back_to_raw_value(self):
        document = {
            "file_name": "arquivo.txt",
            "document_type": "tipo_nao_mapeado",
            "summary": "resumo",
            "alerts": [],
            "full_analysis": {},
        }

        pdf_bytes = generate_pdf_report(document)

        self.assertTrue(pdf_bytes.startswith(b"%PDF"))

    def test_prompt_version_appears_in_pdf_when_present(self):
        """Rastreabilidade: o relatório precisa deixar visível com qual
        versão de prompt/modelo a análise foi gerada, para não virar um
        registro mudo se o prompt mudar no futuro."""
        document = {
            "file_name": "contrato.txt",
            "document_type": "contrato_prestacao_servicos",
            "summary": "resumo",
            "alerts": [],
            "full_analysis": {"prompt_version": "v1", "model": "gpt-5.4-mini"},
        }

        pdf_bytes = generate_pdf_report(document)
        text = "".join(page.extract_text() or "" for page in PdfReader(io.BytesIO(pdf_bytes)).pages)

        self.assertIn("v1", text)
        self.assertIn("gpt-5.4-mini", text)

    def test_missing_prompt_version_is_omitted_without_crashing(self):
        document = {
            "file_name": "contrato.txt",
            "document_type": "contrato_prestacao_servicos",
            "summary": "resumo",
            "alerts": [],
            "full_analysis": {},
        }

        pdf_bytes = generate_pdf_report(document)

        self.assertTrue(pdf_bytes.startswith(b"%PDF"))


if __name__ == "__main__":
    unittest.main()
