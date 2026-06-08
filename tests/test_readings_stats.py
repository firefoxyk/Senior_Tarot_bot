import json
import sqlite3
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import database
from database import (
    add_user,
    create_reading,
    get_active_users_count_for_date,
    get_active_users_count_since,
    get_cards_readings_count,
    get_readings_count_by_type,
    get_spread_readings_count,
    get_total_users_count,
    init_db,
)
from services.timezone import MOSCOW_TZ


class ReadingsStatsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.original_db_name = database.DB_NAME
        database.DB_NAME = str(Path(self.temp_dir.name) / "test.db")
        init_db()

    def tearDown(self) -> None:
        database.DB_NAME = self.original_db_name
        self.temp_dir.cleanup()

    def get_readings_rows(self) -> list[tuple[str, str]]:
        with sqlite3.connect(database.DB_NAME) as connection:
            rows = connection.execute(
                """
                SELECT type, cards_json
                FROM readings
                ORDER BY id
                """
            ).fetchall()

        return rows

    def test_create_reading_stores_cards_json(self) -> None:
        add_user(123, "tester", "Tester")
        card = {"name": "Test Card", "is_reversed": True}

        create_reading(123, "card", [card])

        rows = self.get_readings_rows()
        self.assertEqual(rows[0][0], "card")
        self.assertEqual(json.loads(rows[0][1]), [card])

    def test_stats_count_users_active_cards_and_spreads(self) -> None:
        add_user(123, "first", "First")
        add_user(456, "second", "Second")

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
            create_reading(456, "spread", [{"name": "A"}, {"name": "B"}, {"name": "C"}])
            create_reading(456, "career", [{"name": "A"}])

        self.assertEqual(get_total_users_count(), 2)
        self.assertEqual(get_active_users_count_for_date("2026-06-05"), 2)
        self.assertEqual(get_active_users_count_since("2026-05-30T00:00:00"), 2)
        self.assertEqual(get_cards_readings_count(), 1)
        self.assertEqual(get_readings_count_by_type("card"), 1)
        self.assertEqual(get_readings_count_by_type("spread"), 1)
        self.assertEqual(get_readings_count_by_type("career"), 1)
        self.assertEqual(get_readings_count_by_type("project"), 0)
        self.assertEqual(get_spread_readings_count(), 2)

    def test_stats_can_exclude_admin_readings(self) -> None:
        add_user(123, "admin", "Admin")
        add_user(456, "user", "User")

        with patch("database.datetime") as datetime_mock:
            datetime_mock.now.return_value = datetime(
                2026,
                6,
                5,
                12,
                0,
                tzinfo=MOSCOW_TZ,
            )
            create_reading(123, "card", [{"name": "Admin Card"}])
            create_reading(123, "spread", [{"name": "Admin Spread"}])
            create_reading(456, "card", [{"name": "User Card"}])
            create_reading(456, "career", [{"name": "User Career"}])

        excluded_user_ids = {123}

        self.assertEqual(
            get_active_users_count_for_date("2026-06-05", excluded_user_ids),
            1,
        )
        self.assertEqual(
            get_active_users_count_since("2026-05-30T00:00:00", excluded_user_ids),
            1,
        )
        self.assertEqual(get_readings_count_by_type("card", excluded_user_ids), 1)
        self.assertEqual(get_readings_count_by_type("spread", excluded_user_ids), 0)
        self.assertEqual(get_readings_count_by_type("career", excluded_user_ids), 1)
        self.assertEqual(get_spread_readings_count(excluded_user_ids), 1)


if __name__ == "__main__":
    unittest.main()
