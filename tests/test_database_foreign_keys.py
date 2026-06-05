import sqlite3
import tempfile
import unittest
from pathlib import Path

import database
from database import add_user, get_connection, init_db


class DatabaseForeignKeysTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.original_db_name = database.DB_NAME
        database.DB_NAME = str(Path(self.temp_dir.name) / "test.db")
        init_db()

    def tearDown(self) -> None:
        database.DB_NAME = self.original_db_name
        self.temp_dir.cleanup()

    def test_donations_user_id_references_users_user_id(self) -> None:
        with get_connection() as connection:
            foreign_keys = connection.execute("PRAGMA foreign_key_list(donations)").fetchall()

        self.assertTrue(
            any(
                foreign_key[2] == "users"
                and foreign_key[3] == "user_id"
                and foreign_key[4] == "user_id"
                for foreign_key in foreign_keys
            )
        )

    def test_donation_cannot_reference_missing_user(self) -> None:
        with self.assertRaises(sqlite3.IntegrityError):
            with get_connection() as connection:
                connection.execute(
                    """
                    INSERT INTO donations (
                        user_id,
                        amount_minor,
                        currency,
                        payment_id,
                        created_at
                    )
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        999,
                        9900,
                        "RUB",
                        "missing-user-payment",
                        "2026-06-05T12:00:00",
                    ),
                )

    def test_donation_can_reference_existing_user(self) -> None:
        add_user(123, "tester", "Tester")

        with get_connection() as connection:
            connection.execute(
                """
                INSERT INTO donations (
                    user_id,
                    amount_minor,
                    currency,
                    payment_id,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    123,
                    9900,
                    "RUB",
                    "existing-user-payment",
                    "2026-06-05T12:00:00",
                ),
            )
            row = connection.execute("SELECT COUNT(*) FROM donations").fetchone()

        self.assertEqual(int(row[0]), 1)


if __name__ == "__main__":
    unittest.main()
