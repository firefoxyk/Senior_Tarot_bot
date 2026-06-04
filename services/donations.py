import os
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from database import get_connection


@dataclass(frozen=True)
class Donation:
    id: int
    user_id: int
    amount_minor: int
    currency: str
    payment_id: str
    created_at: str


@dataclass(frozen=True)
class CurrencyDonationStats:
    currency: str
    total_amount_minor: int
    donations_count: int


@dataclass(frozen=True)
class DonatorStats:
    user_id: int
    currency: str
    total_amount_minor: int
    donations_count: int


@dataclass(frozen=True)
class ServerProgress:
    collected_minor: int
    goal_minor: int
    currency: str
    percent: int
    progress_bar: str


def _row_to_donation(row: tuple[Any, ...]) -> Donation:
    return Donation(
        id=row[0],
        user_id=row[1],
        amount_minor=row[2],
        currency=row[3],
        payment_id=row[4],
        created_at=row[5],
    )


class DonationService:
    @staticmethod
    def create_donation(
        user_id: int,
        amount_minor: int,
        currency: str,
        payment_id: str,
    ) -> Donation:
        created_at = datetime.now(UTC).replace(tzinfo=None).isoformat()

        with get_connection() as connection:
            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT id, user_id, amount_minor, currency, payment_id, created_at
                FROM donations
                WHERE payment_id = ?
                """,
                (payment_id,),
            )
            existing = cursor.fetchone()

            if existing:
                return _row_to_donation(existing)

            cursor.execute(
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
                    user_id,
                    amount_minor,
                    currency,
                    payment_id,
                    created_at,
                ),
            )

            donation_id = cursor.lastrowid
            connection.commit()

        return Donation(
            id=donation_id,
            user_id=user_id,
            amount_minor=amount_minor,
            currency=currency,
            payment_id=payment_id,
            created_at=created_at,
        )

    @staticmethod
    def get_total_amount() -> int:
        with get_connection() as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT COALESCE(SUM(amount_minor), 0) FROM donations")
            row = cursor.fetchone()

        return int(row[0])

    @staticmethod
    def get_donations_count() -> int:
        with get_connection() as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT COUNT(*) FROM donations")
            row = cursor.fetchone()

        return int(row[0])

    @staticmethod
    def get_donators() -> list[int]:
        with get_connection() as connection:
            cursor = connection.cursor()
            cursor.execute(
                """
                SELECT DISTINCT user_id
                FROM donations
                ORDER BY user_id
                """
            )
            rows = cursor.fetchall()

        return [row[0] for row in rows]

    @staticmethod
    def get_donations_by_user(user_id: int) -> list[Donation]:
        with get_connection() as connection:
            cursor = connection.cursor()
            cursor.execute(
                """
                SELECT id, user_id, amount_minor, currency, payment_id, created_at
                FROM donations
                WHERE user_id = ?
                ORDER BY created_at DESC
                """,
                (user_id,),
            )
            rows = cursor.fetchall()

        return [_row_to_donation(row) for row in rows]

    @staticmethod
    def get_currency_stats() -> list[CurrencyDonationStats]:
        with get_connection() as connection:
            cursor = connection.cursor()
            cursor.execute(
                """
                SELECT currency, SUM(amount_minor) AS total_amount_minor, COUNT(*) AS donations_count
                FROM donations
                GROUP BY currency
                ORDER BY total_amount_minor DESC
                """
            )
            rows = cursor.fetchall()

        return [
            CurrencyDonationStats(
                currency=row[0],
                total_amount_minor=int(row[1]),
                donations_count=int(row[2]),
            )
            for row in rows
        ]

    @staticmethod
    def get_donator_stats() -> list[DonatorStats]:
        with get_connection() as connection:
            cursor = connection.cursor()
            cursor.execute(
                """
                SELECT user_id, currency, SUM(amount_minor) AS total_amount_minor, COUNT(*) AS donations_count
                FROM donations
                GROUP BY user_id, currency
                ORDER BY total_amount_minor DESC
                """
            )
            rows = cursor.fetchall()

        return [
            DonatorStats(
                user_id=row[0],
                currency=row[1],
                total_amount_minor=int(row[2]),
                donations_count=int(row[3]),
            )
            for row in rows
        ]

    @staticmethod
    def get_monthly_server_progress(currency: str) -> ServerProgress:
        goal_minor = int(os.getenv("SERVER_MONTHLY_GOAL_MINOR", "90000"))
        month_start = datetime.now(UTC).replace(
            day=1,
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
            tzinfo=None,
        ).isoformat()

        with get_connection() as connection:
            cursor = connection.cursor()
            cursor.execute(
                """
                SELECT COALESCE(SUM(amount_minor), 0)
                FROM donations
                WHERE currency = ?
                  AND created_at >= ?
                """,
                (currency, month_start),
            )
            row = cursor.fetchone()

        collected_minor = int(row[0])
        percent = min(100, int(collected_minor * 100 / goal_minor)) if goal_minor > 0 else 0
        filled_count = min(10, percent // 10)
        progress_bar = "█" * filled_count + "░" * (10 - filled_count)

        return ServerProgress(
            collected_minor=collected_minor,
            goal_minor=goal_minor,
            currency=currency,
            percent=percent,
            progress_bar=progress_bar,
        )
