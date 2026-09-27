import tempfile
import unittest
from pathlib import Path

from services import storage_service
from services.auth_service import ROLE_ADMIN, ROLE_BASIC, create_user


class StorageServiceUserFilteringTests(unittest.TestCase):
    def setUp(self):
        self._tmp_dir = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self._original_db_path = storage_service.DB_PATH
        storage_service.DB_PATH = Path(self._tmp_dir.name) / "test_lexiflow.db"

        storage_service.init_db()

        with storage_service.get_connection() as conn:
            self.basic_user_id = create_user(conn, "usuario_basico", "senha123", role=ROLE_BASIC)
            self.other_basic_user_id = create_user(conn, "outro_usuario", "senha123", role=ROLE_BASIC)
            self.admin_user_id = create_user(conn, "admin_teste", "senha123", role=ROLE_ADMIN)

        self.doc_id_basic = storage_service.save_document_analysis(
            file_name="doc_do_usuario_basico.txt",
            document_text="texto 1",
            result={"document_type": "nda", "summary": "resumo 1", "alerts": [], "full_analysis": {}},
            user_id=self.basic_user_id,
        )
        self.doc_id_other = storage_service.save_document_analysis(
            file_name="doc_do_outro_usuario.txt",
            document_text="texto 2",
            result={"document_type": "nda", "summary": "resumo 2", "alerts": [], "full_analysis": {}},
            user_id=self.other_basic_user_id,
        )

    def tearDown(self):
        storage_service.DB_PATH = self._original_db_path
        self._tmp_dir.cleanup()

    def test_basic_user_only_sees_own_documents(self):
        documents = storage_service.list_documents(self.basic_user_id, ROLE_BASIC)

        file_names = [doc["file_name"] for doc in documents]
        self.assertEqual(file_names, ["doc_do_usuario_basico.txt"])

    def test_admin_sees_documents_from_all_users(self):
        documents = storage_service.list_documents(self.admin_user_id, ROLE_ADMIN)

        file_names = {doc["file_name"] for doc in documents}
        self.assertEqual(file_names, {"doc_do_usuario_basico.txt", "doc_do_outro_usuario.txt"})

    def test_basic_user_cannot_fetch_another_users_document_by_id(self):
        """Regressão de gating: um usuário básico não deve conseguir abrir,
        por id, um documento processado por outro usuário básico."""
        result = storage_service.get_document_by_id(self.doc_id_other, self.basic_user_id, ROLE_BASIC)

        self.assertIsNone(result)

    def test_basic_user_can_fetch_own_document_by_id(self):
        result = storage_service.get_document_by_id(self.doc_id_basic, self.basic_user_id, ROLE_BASIC)

        self.assertIsNotNone(result)
        self.assertEqual(result["file_name"], "doc_do_usuario_basico.txt")

    def test_admin_can_fetch_any_users_document_by_id(self):
        result = storage_service.get_document_by_id(self.doc_id_basic, self.admin_user_id, ROLE_ADMIN)

        self.assertIsNotNone(result)
        self.assertEqual(result["file_name"], "doc_do_usuario_basico.txt")

    def test_overview_respects_same_filtering_as_list_documents(self):
        overview_basic = storage_service.list_documents_for_overview(self.basic_user_id, ROLE_BASIC)
        overview_admin = storage_service.list_documents_for_overview(self.admin_user_id, ROLE_ADMIN)

        self.assertEqual(len(overview_basic), 1)
        self.assertEqual(len(overview_admin), 2)

    def test_needs_review_defaults_to_false_when_absent_from_result(self):
        document = storage_service.get_document_by_id(self.doc_id_basic, self.basic_user_id, ROLE_BASIC)

        self.assertFalse(document["needs_review"])

    def test_needs_review_true_round_trips_through_list_and_get(self):
        """Fecha o loop: um documento sinalizado para revisão (ex.: campo com
        confiança baixa) precisa continuar marcado depois de salvo, não só na
        renderização imediata após o processamento."""
        doc_id = storage_service.save_document_analysis(
            file_name="doc_precisa_revisao.txt",
            document_text="texto 3",
            result={
                "document_type": "nda",
                "summary": "resumo 3",
                "alerts": ["1 campo com confiança baixa (penalty_clause) — recomenda-se revisão manual."],
                "full_analysis": {},
                "needs_review": True,
            },
            user_id=self.basic_user_id,
        )

        fetched = storage_service.get_document_by_id(doc_id, self.basic_user_id, ROLE_BASIC)
        listed = storage_service.list_documents(self.basic_user_id, ROLE_BASIC)
        listed_flags = {doc["id"]: doc["needs_review"] for doc in listed}

        self.assertTrue(fetched["needs_review"])
        self.assertTrue(listed_flags[doc_id])
        self.assertFalse(listed_flags[self.doc_id_basic])


if __name__ == "__main__":
    unittest.main()
