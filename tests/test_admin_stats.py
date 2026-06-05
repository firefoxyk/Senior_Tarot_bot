import os
import sqlite3
import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import AsyncMock, patch

import database
from database import add_user, create_reading, init_db
from handlers.admin import cmd_stats


class FakeUser:
    id = 123


class FakeRegularUser:
    id = 456


class FakeMessage:
    def __init__(self, user: object | None = None) -> None:
        self.from_user = user or FakeUser()
        self.answer = AsyncMock()


class AdminStatsTest(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.original_db_name = database.DB_NAME
        self.original_admin_ids = os.environ.get("ADMIN_IDS")
        self.original_goal_currency = os.environ.get("SERVER_MONTHLY_GOAL_CURRENCY")

        database.DB_NAME = str(Path(self.temp_dir.name) / "test.db")
        os.environ["ADMIN_IDS"] = "123"
        os.environ["SERVER_MONTHLY_GOAL_CURRENCY"] = "RUB"
        init_db()

    def tearDown(self) -> None:
        database.DB_NAME = self.original_db_name

        if self.original_admin_ids is None:
            os.environ.pop("ADMIN_IDS", None)
        else:
            os.environ["ADMIN_IDS"] = self.original_admin_ids

        if self.original_goal_currency is None:
            os.environ.pop("SERVER_MONTHLY_GOAL_CURRENCY", None)
        else:
            os.environ["SERVER_MONTHLY_GOAL_CURRENCY"] = self.original_goal_currency

        self.temp_dir.cleanup()

    def insert_donation(self) -> None:
        with sqlite3.connect(database.DB_NAME) as connection:
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
                    "payment-1",
                    datetime.now(UTC).replace(tzinfo=None).isoformat(),
                ),
            )
            connection.commit()

    async def test_stats_command_shows_core_metrics(self) -> None:
        add_user(123, "admin", "Admin")
        add_user(456, "user", "User")
        create_reading(123, "card", [{"name": "Card"}])
        create_reading(456, "spread", [{"name": "Spread"}])
        self.insert_donation()

        with patch("handlers.admin.get_today_moscow", return_value=datetime.now().date().isoformat()):
            message = FakeMessage()
            await cmd_stats(message)

        text = message.answer.await_args.args[0]
        self.assertIn("Пользователей всего:</b> 2", text)
        self.assertIn("Активных за сегодня:</b> 2", text)
        self.assertIn("Выдано карт:</b> 1", text)
        self.assertIn("Сделано раскладов:</b> 1", text)
        self.assertIn("Донатов за месяц:</b> 99.00 RUB (1)", text)

    async def test_stats_command_denies_regular_user(self) -> None:
        message = FakeMessage(FakeRegularUser())

        await cmd_stats(message)

        text = message.answer.await_args.args[0]
        message.answer.assert_awaited_once()
        self.assertNotIn("<b>", text)


if __name__ == "__main__":
    unittest.main()
