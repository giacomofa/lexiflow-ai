import unittest

from services.document_types import DOCUMENT_TYPE_LABELS
from services.schemas import DOCUMENT_TYPES


class DocumentTypeLabelsTests(unittest.TestCase):
    def test_has_a_label_for_every_supported_document_type(self):
        """Regressão: os rótulos de tipo documental viviam duplicados em
        app/theme.py (badges) e services/report_service.py (PDF) e já
        haviam divergido entre si. Agora os dois importam de aqui — este
        teste garante que a fonte única continua cobrindo todos os tipos
        que services.schemas realmente aceita."""
        self.assertEqual(set(DOCUMENT_TYPE_LABELS.keys()), DOCUMENT_TYPES)

    def test_theme_badges_and_pdf_labels_stay_in_sync(self):
        from app.theme import DOCUMENT_TYPE_BADGES

        for document_type, label in DOCUMENT_TYPE_LABELS.items():
            self.assertEqual(DOCUMENT_TYPE_BADGES[document_type]["label"], label)


if __name__ == "__main__":
    unittest.main()
