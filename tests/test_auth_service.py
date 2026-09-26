import sqlite3
import unittest

from services.auth_service import (
    ROLE_ADMIN,
    ROLE_BASIC,
    DEFAULT_ADMIN_USERNAME,
    authenticate,
    create_user,
    ensure_default_admin,
    hash_password,
    init_users_table,
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


if __name__ == "__main__":
    unittest.main()
