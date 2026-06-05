import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

from handlers.spreads import send_spread


class SpreadUpsellTest(unittest.IsolatedAsyncioTestCase):
    async def test_share_upsell_is_not_checked_when_donation_upsell_is_shown(self) -> None:
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
            collage_path = Path(temp_dir) / "spread.jpg"
            collage_path.write_bytes(b"temporary")

            message = AsyncMock()
            message.from_user = None
            card = {
                "name": "Test Card",
                "meaning": "Meaning",
            }

            with (
                patch("handlers.spreads.save_message_user"),
                patch("handlers.spreads.check_daily_limit", new=AsyncMock(return_value=True)),
                patch("handlers.spreads.draw_cards", return_value=[card, card, card]),
                patch("handlers.spreads.create_spread_collage", return_value=collage_path),
                patch("handlers.spreads.spend_daily_limit"),
                patch("handlers.spreads.should_show_spread_donation_upsell", return_value=True),
                patch("handlers.spreads.should_show_spread_share_upsell") as share_upsell,
            ):
                await send_spread(message, "spread")

            message.answer.assert_awaited_once()
            share_upsell.assert_not_called()


if __name__ == "__main__":
    unittest.main()
