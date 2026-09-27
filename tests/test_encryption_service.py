import unittest

from services.encryption_service import decrypt_text, encrypt_text


class EncryptDecryptRoundTripTests(unittest.TestCase):
    def test_round_trip_returns_original_text(self):
        original = "CONTRATO DE PRESTAÇÃO DE SERVIÇOS\nCPF: 123.456.789-00"

        encrypted = encrypt_text(original)
        decrypted = decrypt_text(encrypted)

        self.assertEqual(decrypted, original)

    def test_encrypted_value_does_not_contain_plaintext(self):
        original = "informação sensível que não deveria vazar em texto plano"

        encrypted = encrypt_text(original)

        self.assertNotIn("informação sensível", encrypted)
        self.assertNotIn("texto plano", encrypted)

    def test_none_round_trips_as_none(self):
        self.assertIsNone(encrypt_text(None))
        self.assertIsNone(decrypt_text(None))

    def test_empty_string_round_trips(self):
        encrypted = encrypt_text("")
        self.assertEqual(decrypt_text(encrypted), "")

    def test_legacy_plaintext_value_falls_back_instead_of_crashing(self):
        """Regressão: registros salvos antes da criptografia existir não são
        tokens Fernet válidos. decrypt_text não pode quebrar o histórico
        antigo — deve devolver o valor como veio."""
        legacy_plaintext = "CONTRATO DE PRESTAÇÃO DE SERVIÇOS DE TI (salvo antes da criptografia)"

        self.assertEqual(decrypt_text(legacy_plaintext), legacy_plaintext)

    def test_two_encryptions_of_same_text_differ(self):
        """Fernet usa IV aleatório por chamada; duas cifragens do mesmo
        texto não devem produzir o mesmo token (evita vazar padrões)."""
        original = "mesmo texto"

        self.assertNotEqual(encrypt_text(original), encrypt_text(original))


if __name__ == "__main__":
    unittest.main()
