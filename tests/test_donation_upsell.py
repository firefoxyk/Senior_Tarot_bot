import unittest
from unittest.mock import patch

from handlers.card import should_show_card_share_upsell, should_show_donation_upsell
from handlers.spreads import (
    should_show_spread_donation_upsell,
    should_show_spread_share_upsell,
)
from keyboards import donation_upsell_keyboard, main_menu_keyboard, reply_menu_keyboard, share_bot_keyboard


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

    def test_main_menu_shows_unsubscribe_button_for_subscribed_user(self) -> None:
        keyboard = main_menu_keyboard(notifications_subscribed=True)
        button = keyboard.inline_keyboard[5][0]

        self.assertEqual(button.text, "Отписаться от уведомлений")
        self.assertEqual(button.callback_data, "unsubscribe_notifications")

    def test_main_menu_shows_subscribe_button_for_unsubscribed_user(self) -> None:
        keyboard = main_menu_keyboard(notifications_subscribed=False)
        button = keyboard.inline_keyboard[5][0]

        self.assertEqual(button.text, "Подписаться на уведомления")
        self.assertEqual(button.callback_data, "subscribe_notifications")

    def test_main_menu_has_report_problem_button(self) -> None:
        keyboard = main_menu_keyboard()
        button = keyboard.inline_keyboard[4][0]

        self.assertEqual(button.text, "Сообщить о проблеме")
        self.assertEqual(button.callback_data, "report_problem")

    def test_reply_menu_has_report_problem_button(self) -> None:
        keyboard = reply_menu_keyboard()
        button_texts = [
            button.text
            for row in keyboard.keyboard
            for button in row
        ]

        self.assertIn("Сообщить о проблеме", button_texts)

    def test_reply_menu_shows_subscribe_button_for_unsubscribed_user(self) -> None:
        keyboard = reply_menu_keyboard(notifications_subscribed=False)
        button_texts = [
            button.text
            for row in keyboard.keyboard
            for button in row
        ]

        self.assertIn("Подписаться на уведомления", button_texts)

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
