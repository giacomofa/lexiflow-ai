import sqlite3
import unittest

from services.auth_service import (
    ROLE_ADMIN,
    ROLE_BASIC,
    DEFAULT_ADMIN_USERNAME,
    authenticate,
    create_session,
    create_user,
    delete_session,
    ensure_default_admin,
    hash_password,
    init_sessions_table,
    init_users_table,
    validate_session,
    verify_password,
)


class PasswordHashingTests(unittest.TestCase):
    def test_hash_is_never_the_plain_password(self):
        password_hash = hash_password("minha-senha-secreta")

        self.assertNotEqual(password_hash, "minha-senha-secreta")

    def test_correct_password_verifies(self):
        password_hash = hash_password("minha-senha-secreta")

        self.assertTrue(verify_password("minha-senha-secreta", password_hash))

    def test_wrong_password_does_not_verify(self):
        password_hash = hash_password("minha-senha-secreta")

        self.assertFalse(verify_password("senha-errada", password_hash))

    def test_empty_inputs_do_not_verify(self):
        self.assertFalse(verify_password("", "algum-hash"))
        self.assertFalse(verify_password("senha", ""))


class InMemoryDBTestCase(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(":memory:")
        init_users_table(self.conn)
        init_sessions_table(self.conn)

    def tearDown(self):
        self.conn.close()


class CreateUserAndAuthenticateTests(InMemoryDBTestCase):
    def test_create_user_and_authenticate_with_correct_password(self):
        create_user(self.conn, "giacomo", "senha123", role=ROLE_BASIC)

        user = authenticate(self.conn, "giacomo", "senha123")

        self.assertIsNotNone(user)
        self.assertEqual(user["username"], "giacomo")
        self.assertEqual(user["role"], ROLE_BASIC)

    def test_authenticate_with_wrong_password_returns_none(self):
        create_user(self.conn, "giacomo", "senha123", role=ROLE_BASIC)

        self.assertIsNone(authenticate(self.conn, "giacomo", "senha-errada"))

    def test_authenticate_unknown_user_returns_none(self):
        self.assertIsNone(authenticate(self.conn, "ninguem", "qualquer"))

    def test_invalid_role_is_rejected(self):
        with self.assertRaises(ValueError):
            create_user(self.conn, "giacomo", "senha123", role="superadmin")


class EnsureDefaultAdminTests(InMemoryDBTestCase):
    def test_creates_default_admin_when_no_users_exist(self):
        created_id = ensure_default_admin(self.conn)

        self.assertIsNotNone(created_id)
        user = authenticate(self.conn, DEFAULT_ADMIN_USERNAME, "admin123")
        self.assertIsNotNone(user)
        self.assertEqual(user["role"], ROLE_ADMIN)

    def test_does_nothing_when_a_user_already_exists(self):
        create_user(self.conn, "giacomo", "senha123", role=ROLE_BASIC)

        result = ensure_default_admin(self.conn)

        self.assertIsNone(result)
        self.assertIsNone(authenticate(self.conn, DEFAULT_ADMIN_USERNAME, "admin123"))


class SessionPersistenceTests(InMemoryDBTestCase):
    """Sessão persistente (não deslogar a cada refresh): o token fica em
    st.query_params e é validado contra a tabela sessions."""

    def setUp(self):
        super().setUp()
        self.user_id = create_user(self.conn, "giacomo", "senha123", role=ROLE_BASIC)

    def test_create_session_returns_a_nonempty_token(self):
        token = create_session(self.conn, self.user_id)

        self.assertTrue(token)
        self.assertGreater(len(token), 20)

    def test_two_sessions_get_different_tokens(self):
        self.assertNotEqual(create_session(self.conn, self.user_id), create_session(self.conn, self.user_id))

    def test_validate_session_returns_the_owning_user(self):
        token = create_session(self.conn, self.user_id)

        user = validate_session(self.conn, token)

        self.assertIsNotNone(user)
        self.assertEqual(user["id"], self.user_id)
        self.assertEqual(user["username"], "giacomo")
        self.assertEqual(user["role"], ROLE_BASIC)
        self.assertNotIn("password_hash", user)

    def test_validate_session_unknown_token_returns_none(self):
        self.assertIsNone(validate_session(self.conn, "token-que-nao-existe"))

    def test_validate_session_empty_token_returns_none(self):
        self.assertIsNone(validate_session(self.conn, ""))
        self.assertIsNone(validate_session(self.conn, None))

    def test_expired_session_is_rejected_and_cleaned_up(self):
        """Regressão: uma sessão expirada não pode continuar logando o
        usuário automaticamente para sempre."""
        token = create_session(self.conn, self.user_id, ttl_hours=-1)

        self.assertIsNone(validate_session(self.conn, token))

        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM sessions WHERE token = ?", (token,))
        self.assertEqual(cursor.fetchone()[0], 0)

    def test_delete_session_invalidates_it(self):
        token = create_session(self.conn, self.user_id)

        delete_session(self.conn, token)

        self.assertIsNone(validate_session(self.conn, token))

    def test_deleting_unknown_session_does_not_raise(self):
        delete_session(self.conn, "token-que-nao-existe")


if __name__ == "__main__":
    unittest.main()
