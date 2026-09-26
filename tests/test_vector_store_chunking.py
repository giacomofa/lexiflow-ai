import unittest

from rag.vector_store import chunk_document, group_by_section, split_large_paragraph


class SplitLargeParagraphTests(unittest.TestCase):
    def test_short_paragraph_is_not_split(self):
        text = "Texto curto."

        self.assertEqual(split_large_paragraph(text, max_chars=700), [text])

    def test_long_paragraph_is_split_on_sentence_boundaries(self):
        sentence = "Esta é uma frase de teste com tamanho razoável para o exemplo. "
        text = sentence * 20

        chunks = split_large_paragraph(text, max_chars=200)

        self.assertGreater(len(chunks), 1)
        for chunk in chunks:
            self.assertLessEqual(len(chunk), 220)


class GroupBySectionTests(unittest.TestCase):
    def test_section_headers_start_new_blocks(self):
        """Regressão do bug de chunking: antes, o texto inteiro virava um único
        chunk gigante misturando cláusulas de seções diferentes (ex.: VIGÊNCIA
        e MULTA no mesmo chunk), prejudicando a qualidade da busca vetorial."""
        text = (
            "VIGENCIA:\n"
            "O contrato tera vigencia de 12 meses.\n"
            "MULTA:\n"
            "Em caso de rescisao, incidira multa de 20%.\n"
            "CONFIDENCIALIDADE:\n"
            "As partes devem manter sigilo."
        )

        blocks = group_by_section(text)

        self.assertEqual(len(blocks), 3)
        self.assertTrue(blocks[0].startswith("VIGENCIA:"))
        self.assertTrue(blocks[1].startswith("MULTA:"))
        self.assertTrue(blocks[2].startswith("CONFIDENCIALIDADE:"))
        self.assertNotIn("MULTA", blocks[0])

    def test_text_without_headers_stays_as_single_block(self):
        text = "Linha um sem cabeçalho.\nLinha dois continuando o mesmo parágrafo."

        blocks = group_by_section(text)

        self.assertEqual(len(blocks), 1)

    def test_empty_text_produces_no_blocks(self):
        self.assertEqual(group_by_section(""), [])


class ChunkDocumentTests(unittest.TestCase):
    def test_chunks_do_not_mix_different_sections(self):
        text = (
            "VIGENCIA:\n"
            "O contrato tera vigencia de 12 meses.\n"
            "MULTA:\n"
            "Em caso de rescisao, incidira multa de 20%."
        )

        chunks = chunk_document(text, max_chars=700)

        self.assertEqual(len(chunks), 2)
        self.assertIn("VIGENCIA", chunks[0])
        self.assertIn("MULTA", chunks[1])
        self.assertNotIn("MULTA", chunks[0])


if __name__ == "__main__":
    unittest.main()
