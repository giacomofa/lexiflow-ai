import tempfile
import unittest
from pathlib import Path

from rag import vector_store


class IndexDocumentReindexingTests(unittest.TestCase):
    def setUp(self):
        self._tmp_dir = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self._original_chroma_path = vector_store.CHROMA_PATH
        vector_store.CHROMA_PATH = Path(self._tmp_dir.name) / "test_chroma_db"

    def tearDown(self):
        vector_store.CHROMA_PATH = self._original_chroma_path
        self._tmp_dir.cleanup()

    def _chunk_ids_for(self, document_id):
        collection = vector_store.get_collection()
        result = collection.get(where={"document_id": document_id})
        return set(result["ids"])

    def test_reindexing_with_fewer_chunks_removes_stale_ones(self):
        """Regressão: reindexar um documento cujo novo chunking produz MENOS
        pedaços que uma indexação anterior não pode deixar os chunk_ids
        extras da vez anterior órfãos na coleção."""
        long_text = "\n".join(
            f"SECAO {i}:\n" + ("Texto de exemplo para preencher o chunk. " * 30)
            for i in range(10)
        )
        chunk_count_first = vector_store.index_document(document_id=1, file_name="doc.txt", document_text=long_text)
        self.assertGreater(chunk_count_first, 1)

        first_ids = self._chunk_ids_for(1)
        self.assertEqual(len(first_ids), chunk_count_first)

        short_text = "SECAO UNICA:\nTexto curto."
        chunk_count_second = vector_store.index_document(document_id=1, file_name="doc.txt", document_text=short_text)

        second_ids = self._chunk_ids_for(1)

        self.assertEqual(len(second_ids), chunk_count_second)
        self.assertLess(chunk_count_second, chunk_count_first)
        # nenhum chunk_id da indexação anterior deveria sobreviver
        self.assertEqual(second_ids, {f"doc_1_chunk_{i}" for i in range(chunk_count_second)})

    def test_reindexing_to_empty_text_removes_all_chunks(self):
        vector_store.index_document(document_id=2, file_name="doc.txt", document_text="Algum texto aqui para indexar.")
        self.assertGreater(len(self._chunk_ids_for(2)), 0)

        vector_store.index_document(document_id=2, file_name="doc.txt", document_text="")

        self.assertEqual(self._chunk_ids_for(2), set())

    def test_reindexing_does_not_affect_other_documents(self):
        vector_store.index_document(document_id=10, file_name="a.txt", document_text="Texto do documento dez.")
        vector_store.index_document(document_id=20, file_name="b.txt", document_text="Texto do documento vinte.")

        vector_store.index_document(document_id=10, file_name="a.txt", document_text="Texto atualizado do documento dez.")

        self.assertGreater(len(self._chunk_ids_for(10)), 0)
        self.assertGreater(len(self._chunk_ids_for(20)), 0)


if __name__ == "__main__":
    unittest.main()
