import sqlite3
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import database
from database import add_user, init_db
from services.users import (
    grant_unlimited_access,
    is_unlimited_user,
)


class UnlimitedAccessTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.original_db_name = database.DB_NAME
        database.DB_NAME = str(Path(self.temp_dir.name) / "test.db")
        init_db()
        add_user(123, "tester", "Tester")

    def tearDown(self) -> None:
        database.DB_NAME = self.original_db_name
        self.temp_dir.cleanup()

    def set_unlimited_until(self, value: str | None) -> None:
        with sqlite3.connect(database.DB_NAME) as connection:
            connection.execute(
                """
                UPDATE users
                SET unlimited_until = ?
                WHERE user_id = ?
                """,
                (value, 123),
            )
            connection.commit()

    def test_donation_grants_unlimited_until_about_7_days_ahead(self) -> None:
        now = datetime(2026, 6, 4, 12, 0, 0)

        with patch("services.users._get_now_utc", return_value=now):
            unlimited_until = grant_unlimited_access(123, days=7)

        self.assertEqual(datetime.fromisoformat(unlimited_until), now + timedelta(days=7))

    def test_repeated_donation_extends_from_active_unlimited_until(self) -> None:
        now = datetime(2026, 6, 4, 12, 0, 0)
        active_until = now + timedelta(days=3)
        self.set_unlimited_until(active_until.isoformat())

        with patch("services.users._get_now_utc", return_value=now):
            unlimited_until = grant_unlimited_access(123, days=7)

        self.assertEqual(datetime.fromisoformat(unlimited_until), active_until + timedelta(days=7))

    def test_expired_unlimited_until_extends_from_now(self) -> None:
        now = datetime(2026, 6, 4, 12, 0, 0)
        self.set_unlimited_until((now - timedelta(days=1)).isoformat())

        with patch("services.users._get_now_utc", return_value=now):
            unlimited_until = grant_unlimited_access(123, days=7)

        self.assertEqual(datetime.fromisoformat(unlimited_until), now + timedelta(days=7))

    def test_is_unlimited_user_true_for_future_date(self) -> None:
        now = datetime(2026, 6, 4, 12, 0, 0)
        self.set_unlimited_until((now + timedelta(days=1)).isoformat())

        with patch("services.users._get_now_utc", return_value=now):
            self.assertTrue(is_unlimited_user(123))

    def test_is_unlimited_user_false_for_empty_value(self) -> None:
        now = datetime(2026, 6, 4, 12, 0, 0)
        self.set_unlimited_until(None)

        with patch("services.users._get_now_utc", return_value=now):
            self.assertFalse(is_unlimited_user(123))

    def test_is_unlimited_user_false_for_past_date(self) -> None:
        now = datetime(2026, 6, 4, 12, 0, 0)
        self.set_unlimited_until((now - timedelta(seconds=1)).isoformat())

        with patch("services.users._get_now_utc", return_value=now):
            self.assertFalse(is_unlimited_user(123))


if __name__ == "__main__":
    unittest.main()
