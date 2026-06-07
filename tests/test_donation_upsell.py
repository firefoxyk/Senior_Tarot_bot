import unittest
from unittest.mock import patch

from handlers.card import should_show_card_share_upsell, should_show_donation_upsell
from handlers.spreads import (
    should_show_spread_donation_upsell,
    should_show_spread_share_upsell,
)
from keyboards import (
    donation_upsell_keyboard,
    get_bot_share_url,
    main_menu_keyboard,
    reply_menu_keyboard,
    share_bot_keyboard,
)


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

    def test_main_menu_places_donate_above_help_report_and_notifications_below(self) -> None:
        keyboard = main_menu_keyboard()

        self.assertEqual(
            [
                (button.text, button.callback_data)
                for button in keyboard.inline_keyboard[3]
            ],
            [("☕ Поддержать проект", "donate")],
        )
        self.assertEqual(
            [
                (button.text, button.callback_data)
                for button in keyboard.inline_keyboard[4]
            ],
            [("ℹ️ Помощь", "help"), ("Сообщить о проблеме", "report_problem")],
        )
        self.assertEqual(
            [
                (button.text, button.callback_data)
                for button in keyboard.inline_keyboard[5]
            ],
            [("Отписаться от уведомлений", "unsubscribe_notifications")],
        )

    def test_reply_menu_places_donate_above_help_report_and_notifications_below(self) -> None:
        keyboard = reply_menu_keyboard(notifications_subscribed=True)

        self.assertEqual(
            [button.text for button in keyboard.keyboard[2]],
            ["☕ Поддержать проект"],
        )
        self.assertEqual(
            [button.text for button in keyboard.keyboard[3]],
            ["ℹ️ Помощь", "Сообщить о проблеме"],
        )
        self.assertEqual(
            [button.text for button in keyboard.keyboard[4]],
            ["Отписаться от уведомлений"],
        )

    def test_reply_menu_shows_subscribe_button_for_unsubscribed_user(self) -> None:
        keyboard = reply_menu_keyboard(notifications_subscribed=False)
        button_texts = [
            button.text
            for row in keyboard.keyboard
            for button in row
        ]

        self.assertIn("Подписаться на уведомления", button_texts)

    def test_share_bot_keyboard_uses_configured_bot_username(self) -> None:
        with patch.dict("os.environ", {"BOT_USERNAME": "@BugOracleBot"}):
            keyboard = share_bot_keyboard()

        button = keyboard.inline_keyboard[0][0]

        self.assertEqual(button.text, "📤 Поделиться ботом")
        self.assertEqual(button.url, "https://t.me/BugOracleBot")

    def test_share_bot_url_defaults_to_bug_oracle_bot(self) -> None:
        with patch.dict("os.environ", {}, clear=True):
            self.assertEqual(get_bot_share_url(), "https://t.me/BugOracleBot")

    def test_should_show_spread_donation_upsell_true_below_probability(self) -> None:
        with patch("handlers.spreads.random.random", return_value=0.19):
            self.assertTrue(should_show_spread_donation_upsell())

    def test_should_show_spread_share_upsell_false_at_probability_boundary(self) -> None:
        with patch("handlers.spreads.random.random", return_value=0.2):
            self.assertFalse(should_show_spread_share_upsell())


if __name__ == "__main__":
    unittest.main()
