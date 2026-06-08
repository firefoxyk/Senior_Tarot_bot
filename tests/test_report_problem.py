import os
import unittest
from datetime import datetime
from unittest.mock import AsyncMock, patch

from aiogram.types import InlineKeyboardMarkup

from handlers.report import (
    REPORT_PROMPT,
    REPORT_SUCCESS_TEXT,
    callback_report_problem,
    ReportProblem,
    cancel_report_by_command,
    cancel_report_by_callback,
    format_report_message,
    interrupt_report_by_command,
    interrupt_report_by_menu_button,
    receive_report_description,
    reply_report_problem,
    start_report_problem,
)


class FakeUser:
    def __init__(
        self,
        user_id: int = 456,
        username: str | None = "tester",
        first_name: str | None = "Test",
    ) -> None:
        self.id = user_id
        self.username = username
        self.first_name = first_name


class FakeBot:
    def __init__(self) -> None:
        self.send_message = AsyncMock()


class FakeChat:
    def __init__(self, chat_type: str) -> None:
        self.type = chat_type


class FakeMessage:
    def __init__(
        self,
        text: str,
        user: FakeUser | None = None,
        chat_type: str = "private",
    ) -> None:
        self.text = text
        self.from_user = user or FakeUser()
        self.chat = FakeChat(chat_type)
        self.bot = FakeBot()
        self.answer = AsyncMock()


class FakeCallback:
    def __init__(self, user: FakeUser | None = None, chat_type: str = "private") -> None:
        self.from_user = user or FakeUser()
        self.message = FakeMessage("", self.from_user, chat_type)
        self.answer = AsyncMock()


class FakeState:
    def __init__(self) -> None:
        self.state: object | None = None
        self.is_cleared = False

    async def set_state(self, state: object) -> None:
        self.state = state

    async def clear(self) -> None:
        self.is_cleared = True
        self.state = None


class ReportProblemTest(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.original_admin_ids = os.environ.get("ADMIN_IDS")
        os.environ["ADMIN_IDS"] = "123"

    def tearDown(self) -> None:
        if self.original_admin_ids is None:
            os.environ.pop("ADMIN_IDS", None)
        else:
            os.environ["ADMIN_IDS"] = self.original_admin_ids

    async def test_report_problem_button_enters_waiting_state(self) -> None:
        message = FakeMessage("Сообщить о проблеме")
        state = FakeState()

        with patch("handlers.report.save_message_user"):
            await reply_report_problem(message, state)

        self.assertEqual(state.state, ReportProblem.waiting_for_description)
        message.answer.assert_awaited_once()
        self.assertEqual(message.answer.await_args.args[0], REPORT_PROMPT)

    async def test_report_problem_inline_button_enters_waiting_state(self) -> None:
        callback = FakeCallback()
        state = FakeState()

        with patch("handlers.report.save_callback_user"):
            await callback_report_problem(callback, state)

        self.assertEqual(state.state, ReportProblem.waiting_for_description)
        callback.answer.assert_awaited_once()
        callback.message.answer.assert_awaited_once()
        self.assertEqual(callback.message.answer.await_args.args[0], REPORT_PROMPT)

    async def test_group_report_prompt_uses_inline_cancel_button(self) -> None:
        message = FakeMessage("Сообщить о проблеме", chat_type="group")
        state = FakeState()

        await start_report_problem(message, state)

        markup = message.answer.await_args.kwargs["reply_markup"]
        self.assertIsInstance(markup, InlineKeyboardMarkup)
        self.assertEqual(markup.inline_keyboard[0][0].callback_data, "cancel_report")

    async def test_next_message_is_sent_to_admin_and_user_gets_confirmation(self) -> None:
        message = FakeMessage("Кнопка карты дня не отвечает")
        state = FakeState()

        with (
            patch("handlers.report.datetime") as datetime_mock,
            patch("handlers.report.save_message_user"),
            patch("handlers.report.send_main_menu", new_callable=AsyncMock),
        ):
            datetime_mock.now.return_value.strftime.return_value = "2026-06-07 12:30:00 MSK"
            await receive_report_description(message, state)

        message.bot.send_message.assert_awaited_once()
        admin_id, admin_text = message.bot.send_message.await_args.args
        self.assertEqual(admin_id, 123)
        self.assertIn("Кнопка карты дня не отвечает", admin_text)
        self.assertIn("user_id:</b> 456", admin_text)
        self.assertIn("username:</b> @tester", admin_text)
        self.assertIn("first_name:</b> Test", admin_text)
        self.assertIn("2026-06-07 12:30:00 MSK", admin_text)
        self.assertTrue(state.is_cleared)
        self.assertEqual(message.answer.await_args_list[0].args[0], REPORT_SUCCESS_TEXT)

    def test_report_message_escapes_user_html(self) -> None:
        text = "<b>сломалось</b> & не работает"

        admin_text = format_report_message(
            user=FakeUser(username="bad<tag>", first_name="A&B"),
            text=text,
            received_at=datetime(2026, 6, 7, 12, 30),
        )

        self.assertIn("&lt;b&gt;сломалось&lt;/b&gt; &amp; не работает", admin_text)
        self.assertIn("@bad&lt;tag&gt;", admin_text)
        self.assertIn("A&amp;B", admin_text)
        self.assertNotIn(text, admin_text)

    async def test_cancel_command_clears_waiting_state(self) -> None:
        message = FakeMessage("/cancel")
        state = FakeState()
        state.state = ReportProblem.waiting_for_description

        with patch("handlers.report.send_main_menu", new_callable=AsyncMock):
            await cancel_report_by_command(message, state)

        self.assertTrue(state.is_cleared)
        self.assertEqual(message.answer.await_args_list[0].args[0], "Отменила отправку сообщения.")
        message.bot.send_message.assert_not_awaited()

    async def test_cancel_callback_clears_waiting_state(self) -> None:
        callback = FakeCallback(chat_type="group")
        state = FakeState()
        state.state = ReportProblem.waiting_for_description

        with patch("handlers.report.send_main_menu", new_callable=AsyncMock):
            await cancel_report_by_callback(callback, state)

        self.assertTrue(state.is_cleared)
        callback.answer.assert_awaited_once_with("Отменено")
        callback.message.answer.assert_awaited_once_with("Отменила отправку сообщения.")
        callback.message.bot.send_message.assert_not_awaited()

    async def test_start_command_interrupts_report_without_sending_to_admin(self) -> None:
        message = FakeMessage("/start")
        state = FakeState()
        state.state = ReportProblem.waiting_for_description

        with patch("handlers.report.send_main_menu", new_callable=AsyncMock):
            await interrupt_report_by_command(message, state)

        self.assertTrue(state.is_cleared)
        message.bot.send_message.assert_not_awaited()
        self.assertIn("Отменила отправку сообщения", message.answer.await_args_list[0].args[0])

    async def test_menu_button_interrupts_report_without_sending_to_admin(self) -> None:
        message = FakeMessage("🔮 Карта дня")
        state = FakeState()
        state.state = ReportProblem.waiting_for_description

        with patch("handlers.report.send_main_menu", new_callable=AsyncMock):
            await interrupt_report_by_menu_button(message, state)

        self.assertTrue(state.is_cleared)
        message.bot.send_message.assert_not_awaited()
        self.assertIn("Отменила отправку сообщения", message.answer.await_args_list[0].args[0])


if __name__ == "__main__":
    unittest.main()
