import unittest
from unittest.mock import AsyncMock, patch

from handlers.card import send_single_card


class FakeUser:
    id = 123


class CardUpsellTest(unittest.IsolatedAsyncioTestCase):
    async def test_share_upsell_is_not_checked_when_donation_upsell_is_shown(self) -> None:
        message = AsyncMock()
        message.from_user = FakeUser()
        card = {
            "name": "Test Card",
            "image": "card.png",
            "description": "Description",
            "meaning": "Meaning",
        }

        with (
            patch("handlers.card.save_message_user"),
            patch("handlers.card.check_daily_limit", new=AsyncMock(return_value=True)),
            patch("handlers.card.draw_cards", return_value=[card]),
            patch("handlers.card.random.choice", return_value=False),
            patch("handlers.card.send_card", new=AsyncMock()),
            patch("handlers.card.create_reading"),
            patch("handlers.card.update_daily_card_action_dates"),
            patch("handlers.card.should_show_donation_upsell", return_value=True),
            patch("handlers.card.should_show_card_share_upsell") as share_upsell,
        ):
            await send_single_card(message)

        message.answer.assert_awaited_once()
        share_upsell.assert_not_called()


if __name__ == "__main__":
    unittest.main()
