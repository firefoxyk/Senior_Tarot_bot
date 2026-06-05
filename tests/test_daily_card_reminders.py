import tempfile
import unittest
from pathlib import Path

import database
from database import (
    add_user,
    get_users_without_daily_card_today,
    init_db,
    mark_user_blocked,
    update_daily_card_action_dates,
    update_last_daily_action_date,
)


class DailyCardRemindersTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.original_db_name = database.DB_NAME
        database.DB_NAME = str(Path(self.temp_dir.name) / "test.db")
        init_db()

    def tearDown(self) -> None:
        database.DB_NAME = self.original_db_name
        self.temp_dir.cleanup()

    def test_user_with_spread_today_is_not_invited_for_daily_card(self) -> None:
        add_user(123, "spread_user", "Spread")
        update_last_daily_action_date(123, "2026-06-05")

        users = get_users_without_daily_card_today("2026-06-05")

        self.assertNotIn(123, users)

    def test_user_with_daily_card_today_is_not_invited(self) -> None:
        add_user(123, "card_user", "Card")
        update_daily_card_action_dates(123, "2026-06-05")

        users = get_users_without_daily_card_today("2026-06-05")

        self.assertNotIn(123, users)

    def test_user_without_daily_action_today_is_invited(self) -> None:
        add_user(123, "idle_user", "Idle")

        users = get_users_without_daily_card_today("2026-06-05")

        self.assertIn(123, users)

    def test_user_with_yesterday_action_is_invited(self) -> None:
        add_user(123, "yesterday_user", "Yesterday")
        update_last_daily_action_date(123, "2026-06-04")

        users = get_users_without_daily_card_today("2026-06-05")

        self.assertIn(123, users)

    def test_blocked_user_is_not_invited(self) -> None:
        add_user(123, "blocked_user", "Blocked")
        mark_user_blocked(123)

        users = get_users_without_daily_card_today("2026-06-05")

        self.assertNotIn(123, users)

    def test_add_user_unblocks_returning_user(self) -> None:
        add_user(123, "blocked_user", "Blocked")
        mark_user_blocked(123)

        add_user(123, "returning_user", "Returning")
        users = get_users_without_daily_card_today("2026-06-05")

        self.assertIn(123, users)


if __name__ == "__main__":
    unittest.main()
