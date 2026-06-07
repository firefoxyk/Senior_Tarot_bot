import sqlite3
import tempfile
import unittest
import os
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
        self.original_admin_ids = os.environ.get("ADMIN_IDS")
        database.DB_NAME = str(Path(self.temp_dir.name) / "test.db")
        os.environ.pop("ADMIN_IDS", None)
        init_db()
        add_user(123, "tester", "Tester")

    def tearDown(self) -> None:
        database.DB_NAME = self.original_db_name
        if self.original_admin_ids is None:
            os.environ.pop("ADMIN_IDS", None)
        else:
            os.environ["ADMIN_IDS"] = self.original_admin_ids
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

    async def test_check_daily_limit_blocks_after_limit_is_spent(self) -> None:
        user = FakeUser(123)
        message = FakeMessage(user)

        with patch("services.limits.get_today_moscow", return_value="2026-06-05"):
            spend_daily_limit(user)
            allowed = await check_daily_limit(message, user)

        self.assertFalse(allowed)
        self.assertEqual(len(message.answers), 1)

    async def test_unlimited_user_bypasses_daily_limit_without_spending_it(self) -> None:
        user = FakeUser(123)
        message = FakeMessage(user)
        self.set_unlimited_until("2026-06-12T12:00:00")

        with (
            patch("services.limits.get_today_moscow", return_value="2026-06-05"),
            patch("services.users._get_now_utc", return_value=database.datetime(2026, 6, 5, 12, 0, 0)),
        ):
            allowed = await check_daily_limit(message, user)
            spend_daily_limit(user)

        self.assertTrue(allowed)
        self.assertEqual(message.answers, [])
        self.assertIsNone(self.get_last_daily_action_date())

    async def test_admin_user_bypasses_daily_limit_after_limit_is_spent(self) -> None:
        os.environ["ADMIN_IDS"] = "123"
        user = FakeUser(123)
        message = FakeMessage(user)

        with patch("services.limits.get_today_moscow", return_value="2026-06-05"):
            spend_daily_limit(user)
            allowed = await check_daily_limit(message, user)

        self.assertTrue(allowed)
        self.assertEqual(message.answers, [])
        self.assertIsNone(self.get_last_daily_action_date())


if __name__ == "__main__":
    unittest.main()
