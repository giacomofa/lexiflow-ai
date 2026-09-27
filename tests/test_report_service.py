import unittest

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


if __name__ == "__main__":
    unittest.main()
