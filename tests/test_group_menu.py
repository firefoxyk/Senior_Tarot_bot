import unittest
from unittest.mock import AsyncMock, patch

from aiogram.types import InlineKeyboardMarkup, ReplyKeyboardMarkup

from services.menu import GROUP_MENU_HINT, send_menu_pair


class FakeChat:
    def __init__(self, chat_type: str) -> None:
        self.type = chat_type


class FakeUser:
    id = 123


class FakeMessage:
    def __init__(self, chat_type: str) -> None:
        self.chat = FakeChat(chat_type)
        self.from_user = FakeUser()
        self.answer = AsyncMock()


class GroupMenuTest(unittest.IsolatedAsyncioTestCase):
    async def test_private_chat_gets_reply_and_inline_menus(self) -> None:
        message = FakeMessage("private")

        with patch("services.menu.is_morning_reminders_subscribed", return_value=True):
            await send_menu_pair(message, "Меню под рукой.")

        first_markup = message.answer.await_args_list[0].kwargs["reply_markup"]
        second_markup = message.answer.await_args_list[1].kwargs["reply_markup"]

        self.assertIsInstance(first_markup, ReplyKeyboardMarkup)
        self.assertIsInstance(second_markup, InlineKeyboardMarkup)

    async def test_group_chat_gets_plain_text_and_inline_menu_only(self) -> None:
        message = FakeMessage("group")

        with patch("services.menu.is_morning_reminders_subscribed", return_value=True):
            await send_menu_pair(message, "Меню под рукой.")

        first_call = message.answer.await_args_list[0]
        second_call = message.answer.await_args_list[1]

        self.assertNotIn("reply_markup", first_call.kwargs)
        self.assertIsInstance(second_call.kwargs["reply_markup"], InlineKeyboardMarkup)
        self.assertIn(GROUP_MENU_HINT, second_call.args[0])


if __name__ == "__main__":
    unittest.main()
