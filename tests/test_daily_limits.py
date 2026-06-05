import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import database
from database import add_user, init_db
from services.limits import check_daily_limit, spend_daily_limit


class FakeUser:
    def __init__(self, user_id: int) -> None:
        self.id = user_id


class FakeMessage:
    def __init__(self, user: FakeUser | None) -> None:
        self.from_user = user
        self.answers: list[tuple[str, object | None]] = []

    async def answer(self, text: str, reply_markup: object | None = None) -> None:
        self.answers.append((text, reply_markup))


class DailyLimitsTest(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.original_db_name = database.DB_NAME
        database.DB_NAME = str(Path(self.temp_dir.name) / "test.db")
        init_db()
        add_user(123, "tester", "Tester")

    def tearDown(self) -> None:
        database.DB_NAME = self.original_db_name
        self.temp_dir.cleanup()

    def get_last_daily_action_date(self) -> str | None:
        with sqlite3.connect(database.DB_NAME) as connection:
            row = connection.execute(
                """
                SELECT last_daily_action_date
                FROM users
                WHERE user_id = ?
                """,
                (123,),
            ).fetchone()

        return row[0]

    async def test_check_daily_limit_does_not_spend_limit(self) -> None:
        user = FakeUser(123)
        message = FakeMessage(user)

        with patch("services.limits.get_today_moscow", return_value="2026-06-05"):
            allowed = await check_daily_limit(message, user)

        self.assertTrue(allowed)
        self.assertEqual(message.answers, [])
        self.assertIsNone(self.get_last_daily_action_date())

    def test_spend_daily_limit_updates_last_daily_action_date(self) -> None:
        user = FakeUser(123)

        with patch("services.limits.get_today_moscow", return_value="2026-06-05"):
            spend_daily_limit(user)

        self.assertEqual(self.get_last_daily_action_date(), "2026-06-05")


if __name__ == "__main__":
    unittest.main()
