import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

from handlers.card import send_card
from handlers.spreads import send_spread


class TempImagesCleanupTest(unittest.IsolatedAsyncioTestCase):
    async def test_reversed_card_temp_image_is_deleted_after_send(self) -> None:
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
            temp_dir_path = Path(temp_dir)
            source_image_path = temp_dir_path / "card.png"
            temp_image_path = temp_dir_path / "reversed.png"

            source_image_path.write_bytes(b"source")
            temp_image_path.write_bytes(b"temporary")

            message = AsyncMock()
            card = {
                "name": "Test Card",
                "image": "card.png",
                "description": "Description",
                "meaning": "Meaning",
            }

            with (
                patch("handlers.card.BASE_DIR", temp_dir_path),
                patch("handlers.card.create_reversed_image", return_value=temp_image_path),
            ):
                await send_card(message, card, is_reversed=True)

            self.assertFalse(temp_image_path.exists())
            self.assertTrue(source_image_path.exists())

    async def test_spread_collage_temp_image_is_deleted_after_send(self) -> None:
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
            temp_dir_path = Path(temp_dir)
            collage_path = temp_dir_path / "spread.jpg"
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
                patch("handlers.spreads.spend_daily_limit") as spend_daily_limit,
            ):
                await send_spread(message, "spread")

            self.assertFalse(collage_path.exists())
            spend_daily_limit.assert_called_once_with(None)


if __name__ == "__main__":
    unittest.main()
