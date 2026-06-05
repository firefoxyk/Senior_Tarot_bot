import unittest
from unittest.mock import patch

from handlers.card import should_show_card_share_upsell, should_show_donation_upsell
from handlers.spreads import (
    should_show_spread_donation_upsell,
    should_show_spread_share_upsell,
)
from keyboards import donation_upsell_keyboard, share_bot_keyboard


class DonationUpsellTest(unittest.TestCase):
    def test_should_show_donation_upsell_true_below_probability(self) -> None:
        with patch("handlers.card.random.random", return_value=0.19):
            self.assertTrue(should_show_donation_upsell())

    def test_should_show_donation_upsell_false_at_probability_boundary(self) -> None:
        with patch("handlers.card.random.random", return_value=0.2):
            self.assertFalse(should_show_donation_upsell())

    def test_should_show_card_share_upsell_true_below_probability(self) -> None:
        with patch("handlers.card.random.random", return_value=0.19):
            self.assertTrue(should_show_card_share_upsell())

    def test_should_show_card_share_upsell_false_at_probability_boundary(self) -> None:
        with patch("handlers.card.random.random", return_value=0.2):
            self.assertFalse(should_show_card_share_upsell())

    def test_donation_upsell_keyboard_uses_donate_callback(self) -> None:
        keyboard = donation_upsell_keyboard()
        button = keyboard.inline_keyboard[0][0]

        self.assertEqual(button.callback_data, "donate")

    def test_share_bot_keyboard_uses_configured_bot_username(self) -> None:
        with patch.dict("os.environ", {"BOT_USERNAME": "@senior_tarot_bot"}):
            keyboard = share_bot_keyboard()

        button = keyboard.inline_keyboard[0][0]

        self.assertEqual(button.text, "📤 Поделиться ботом")
        self.assertEqual(button.url, "https://t.me/senior_tarot_bot")

    def test_should_show_spread_donation_upsell_true_below_probability(self) -> None:
        with patch("handlers.spreads.random.random", return_value=0.19):
            self.assertTrue(should_show_spread_donation_upsell())

    def test_should_show_spread_share_upsell_false_at_probability_boundary(self) -> None:
        with patch("handlers.spreads.random.random", return_value=0.2):
            self.assertFalse(should_show_spread_share_upsell())


if __name__ == "__main__":
    unittest.main()
