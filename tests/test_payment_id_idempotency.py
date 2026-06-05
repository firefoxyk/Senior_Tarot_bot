import sqlite3
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, patch

import database
from database import add_user, init_db
from handlers.donate import SUPPORT_PAYLOAD, successful_payment
from services.donations import DonationService


class FakeUser:
    id = 123
    username = "tester"
    first_name = "Tester"


class FakePayment:
    invoice_payload = SUPPORT_PAYLOAD
    total_amount = 9900
    currency = "RUB"
    provider_payment_charge_id = "provider-payment-1"
    telegram_payment_charge_id = "telegram-payment-1"


class FakePaymentWithoutId:
    invoice_payload = SUPPORT_PAYLOAD
    total_amount = 9900
    currency = "RUB"
    provider_payment_charge_id = None
    telegram_payment_charge_id = None


class FakeMessage:
    def __init__(self) -> None:
        self.from_user = FakeUser()
        self.successful_payment = FakePayment()
        self.answer = AsyncMock()
        self.chat = None
        self.message_id = None


class PaymentIdIdempotencyTest(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.original_db_name = database.DB_NAME
        database.DB_NAME = str(Path(self.temp_dir.name) / "test.db")
        init_db()
        add_user(123, "tester", "Tester")

    def tearDown(self) -> None:
        database.DB_NAME = self.original_db_name
        self.temp_dir.cleanup()

    def get_user_unlimited_until(self) -> str | None:
        with sqlite3.connect(database.DB_NAME) as connection:
            row = connection.execute(
                """
                SELECT unlimited_until
                FROM users
                WHERE user_id = ?
                """,
                (FakeUser.id,),
            ).fetchone()

        return row[0] if row else None

    def get_donations_count(self) -> int:
        with sqlite3.connect(database.DB_NAME) as connection:
            row = connection.execute("SELECT COUNT(*) FROM donations").fetchone()

        return int(row[0])

    def test_create_donation_returns_existing_record_for_duplicate_payment_id(self) -> None:
        first_result = DonationService.create_donation(
            user_id=123,
            amount_minor=9900,
            currency="RUB",
            payment_id="payment-1",
        )
        second_result = DonationService.create_donation(
            user_id=123,
            amount_minor=9900,
            currency="RUB",
            payment_id="payment-1",
        )

        self.assertTrue(first_result.created)
        self.assertFalse(second_result.created)
        self.assertEqual(first_result.donation.id, second_result.donation.id)
        self.assertEqual(self.get_donations_count(), 1)

    async def test_successful_payment_is_processed_once_per_payment_id(self) -> None:
        now = datetime(2026, 6, 5, 12, 0, 0)

        with (
            patch("services.users._get_now_utc", return_value=now),
            self.assertLogs("handlers.donate", level="INFO") as logs,
        ):
            first_message = FakeMessage()
            await successful_payment(first_message)

            second_message = FakeMessage()
            await successful_payment(second_message)

        self.assertEqual(self.get_donations_count(), 1)
        self.assertEqual(
            datetime.fromisoformat(self.get_user_unlimited_until()),
            now + timedelta(days=7),
        )
        first_message.answer.assert_awaited_once()
        second_message.answer.assert_not_awaited()
        self.assertTrue(
            any("Payment processed successfully" in message for message in logs.output)
        )
        self.assertTrue(any("Duplicate payment ignored" in message for message in logs.output))

    async def test_successful_payment_without_payment_id_does_not_grant_unlimited(self) -> None:
        message = FakeMessage()
        message.successful_payment = FakePaymentWithoutId()

        with self.assertLogs("handlers.donate", level="ERROR") as logs:
            await successful_payment(message)

        self.assertEqual(self.get_donations_count(), 0)
        self.assertIsNone(self.get_user_unlimited_until())
        message.answer.assert_not_awaited()
        self.assertTrue(
            any("Successful payment has no payment_id" in message for message in logs.output)
        )


if __name__ == "__main__":
    unittest.main()
