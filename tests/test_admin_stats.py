import os
import sqlite3
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, patch

import database
from database import add_user, create_reading, init_db, set_morning_reminders_subscription
from handlers.admin import cmd_stats
from services.timezone import MOSCOW_TZ


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

    def insert_donation(
        self,
        amount_minor: int,
        payment_id: str,
        created_at: str,
    ) -> None:
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
                    amount_minor,
                    "RUB",
                    payment_id,
                    created_at,
                ),
            )
            connection.commit()

    async def test_stats_command_shows_real_metrics_without_personal_donation_data(self) -> None:
        add_user(123, "admin", "Admin")
        add_user(456, "user", "User")
        set_morning_reminders_subscription(456, False)
        with patch("database.datetime") as datetime_mock:
            datetime_mock.now.return_value = datetime(
                2026,
                6,
                5,
                12,
                0,
                tzinfo=MOSCOW_TZ,
            )
            create_reading(123, "card", [{"name": "Card"}])
            create_reading(123, "spread", [{"name": "Admin Spread"}])
            create_reading(123, "career", [{"name": "Admin Career"}])
            create_reading(123, "project", [{"name": "Admin Project"}])
            create_reading(456, "card", [{"name": "User Card"}])
            create_reading(456, "spread", [{"name": "Spread"}])
            create_reading(456, "career", [{"name": "Career"}])
            create_reading(456, "project", [{"name": "Project"}])
        self.insert_donation(9900, "payment-private-1", "2026-06-05T12:00:00")
        self.insert_donation(19900, "payment-private-2", "2026-06-04T12:00:00")

        with patch("handlers.admin.get_today_moscow", return_value="2026-06-05"):
            message = FakeMessage()
            await cmd_stats(message)

        text = message.answer.await_args.args[0]
        self.assertIn("Пользователей всего:</b> 2", text)
        self.assertIn("Активных за сегодня:</b> 1", text)
        self.assertIn("Активных за неделю:</b> 1", text)
        self.assertIn("Подписаны на утренние напоминания:</b> 1", text)
        self.assertIn("Отписаны от утренних напоминаний:</b> 1", text)
        self.assertIn("Карт дня выдано:</b> 1", text)
        self.assertIn("Общих раскладов:</b> 1", text)
        self.assertIn("Карьерных раскладов:</b> 1", text)
        self.assertIn("Проектных раскладов:</b> 1", text)
        self.assertIn("Донатов за месяц:</b> 2", text)
        self.assertIn("Сумма донатов:</b> 298.00 RUB", text)
        self.assertIn("ТОП-5 последних донатеров:", text)
        self.assertIn("199.00 RUB (2026-06-04)", text)
        self.assertIn("99.00 RUB (2026-06-05)", text)
        self.assertNotIn("payment-private", text)

    async def test_stats_command_denies_regular_user(self) -> None:
        message = FakeMessage(FakeRegularUser())

        await cmd_stats(message)

        text = message.answer.await_args.args[0]
        message.answer.assert_awaited_once()
        self.assertNotIn("<b>", text)


if __name__ == "__main__":
    unittest.main()
