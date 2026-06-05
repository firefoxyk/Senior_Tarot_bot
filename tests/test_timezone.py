import unittest
from datetime import datetime
from unittest.mock import patch

from services.timezone import MOSCOW_TZ, get_today_moscow


class TimezoneTest(unittest.TestCase):
    def test_today_uses_moscow_timezone(self) -> None:
        with patch("services.timezone.datetime") as datetime_mock:
            datetime_mock.now.return_value = datetime(2026, 6, 6, 0, 30, tzinfo=MOSCOW_TZ)

            today = get_today_moscow()

        datetime_mock.now.assert_called_once_with(MOSCOW_TZ)
        self.assertEqual(today, "2026-06-06")


if __name__ == "__main__":
    unittest.main()
