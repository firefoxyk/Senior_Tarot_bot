import os
import sqlite3
import tempfile
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path

import database
from database import init_db
from services.donations import DonationService


class DonationsProgressTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.original_db_name = database.DB_NAME
        self.original_goal_minor = os.environ.get("SERVER_MONTHLY_GOAL_MINOR")

        database.DB_NAME = str(Path(self.temp_dir.name) / "test.db")
        os.environ["SERVER_MONTHLY_GOAL_MINOR"] = "90000"
        init_db()

    def tearDown(self) -> None:
        database.DB_NAME = self.original_db_name

        if self.original_goal_minor is None:
            os.environ.pop("SERVER_MONTHLY_GOAL_MINOR", None)
        else:
            os.environ["SERVER_MONTHLY_GOAL_MINOR"] = self.original_goal_minor

        self.temp_dir.cleanup()

    def insert_donation(
        self,
        amount_minor: int,
        currency: str = "RUB",
        created_at: str | None = None,
        payment_id: str | None = None,
    ) -> None:
        created_at = created_at or datetime.now(UTC).replace(tzinfo=None).isoformat()
        payment_id = payment_id or f"payment:{currency}:{amount_minor}:{created_at}"

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
                (1, amount_minor, currency, payment_id, created_at),
            )
            connection.commit()

    def test_no_donations(self) -> None:
        progress = DonationService.get_monthly_server_progress("RUB")

        self.assertEqual(progress.collected_minor, 0)
        self.assertEqual(progress.goal_minor, 90000)
        self.assertEqual(progress.percent, 0)
        self.assertEqual(progress.progress_bar, "░░░░░░░░░░")

    def test_19800_of_90000_is_22_percent(self) -> None:
        self.insert_donation(19800)

        progress = DonationService.get_monthly_server_progress("RUB")

        self.assertEqual(progress.collected_minor, 19800)
        self.assertEqual(progress.percent, 22)
        self.assertEqual(progress.progress_bar, "██░░░░░░░░")

    def test_more_than_goal_is_capped_at_100_percent(self) -> None:
        self.insert_donation(120000)

        progress = DonationService.get_monthly_server_progress("RUB")

        self.assertEqual(progress.collected_minor, 120000)
        self.assertEqual(progress.percent, 100)
        self.assertEqual(progress.progress_bar, "██████████")

    def test_different_currencies_are_not_mixed(self) -> None:
        self.insert_donation(19800, currency="RUB", payment_id="rub")
        self.insert_donation(50000, currency="USD", payment_id="usd")

        progress = DonationService.get_monthly_server_progress("RUB")

        self.assertEqual(progress.collected_minor, 19800)
        self.assertEqual(progress.percent, 22)

    def test_previous_month_is_not_counted(self) -> None:
        previous_month = datetime.now(UTC).replace(tzinfo=None, day=1) - timedelta(days=1)
        self.insert_donation(
            90000,
            created_at=previous_month.replace(day=1).isoformat(),
            payment_id="previous-month",
        )

        progress = DonationService.get_monthly_server_progress("RUB")

        self.assertEqual(progress.collected_minor, 0)


if __name__ == "__main__":
    unittest.main()
