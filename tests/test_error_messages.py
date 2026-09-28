import json
import unittest

import httpx
import openai

from services.error_messages import describe_error


def _fake_request():
    return httpx.Request("POST", "https://api.openai.com/v1/responses")


def _fake_response(status_code=500):
    return httpx.Response(status_code, request=_fake_request())


class DescribeErrorTests(unittest.TestCase):
    def test_rate_limit_error_is_friendly(self):
        exc = openai.RateLimitError("rate limited", response=_fake_response(429), body=None)

        message = describe_error(exc)

        self.assertIn("sobrecarregado", message)
        self.assertNotIn("Traceback", message)

    def test_authentication_error_is_friendly(self):
        exc = openai.AuthenticationError("bad key", response=_fake_response(401), body=None)

        message = describe_error(exc)

        self.assertIn("administrador", message)

    def test_timeout_error_is_friendly(self):
        exc = openai.APITimeoutError(request=_fake_request())

        message = describe_error(exc)

        self.assertIn("demorou mais", message)

    def test_connection_error_is_friendly(self):
        exc = openai.APIConnectionError(request=_fake_request())

        message = describe_error(exc)

        self.assertIn("conectar", message)

    def test_internal_server_error_is_friendly(self):
        exc = openai.InternalServerError("boom", response=_fake_response(500), body=None)

        message = describe_error(exc)

        self.assertIn("indisponível", message)

    def test_generic_api_status_error_mentions_status_code(self):
        exc = openai.PermissionDeniedError("nope", response=_fake_response(403), body=None)

        message = describe_error(exc)

        self.assertIn("403", message)

    def test_json_decode_error_is_friendly(self):
        try:
            json.loads("not json")
        except json.JSONDecodeError as exc:
            message = describe_error(exc)

        self.assertIn("formato inesperado", message)

    def test_value_error_message_is_preserved(self):
        exc = ValueError("Formato de arquivo não suportado. Use PDF ou TXT.")

        message = describe_error(exc)

        self.assertEqual(message, "Formato de arquivo não suportado. Use PDF ou TXT.")

    def test_unknown_error_falls_back_to_generic_safe_message(self):
        """Regressão: a mensagem genérica não pode vazar o texto cru da
        exceção (poderia conter caminho de arquivo, nome de tabela/coluna
        etc. para um usuário sem privilégio nenhum). O detalhe técnico vai
        pro log do servidor, não pra tela."""
        exc = RuntimeError("algo muito específico e sensível quebrou")

        message = describe_error(exc)

        self.assertIn("erro inesperado", message)
        self.assertNotIn("algo muito específico e sensível quebrou", message)


if __name__ == "__main__":
    unittest.main()
