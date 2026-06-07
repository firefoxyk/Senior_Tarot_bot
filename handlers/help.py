from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from database import is_morning_reminders_subscribed
from keyboards import main_menu_keyboard, reply_menu_keyboard
from services.users import save_callback_user, save_message_user
from texts import HELP_TEXT


router = Router()


async def send_help_with_keyboards(
    message: Message,
    user_id: int | None = None,
) -> None:
    notifications_subscribed = True

    if user_id is None and message.from_user:
        user_id = message.from_user.id

    if user_id is not None:
        notifications_subscribed = is_morning_reminders_subscribed(user_id)

    await message.answer(
        HELP_TEXT,
        reply_markup=reply_menu_keyboard(notifications_subscribed),
    )

    await message.answer(
        "Выбери действие:",
        reply_markup=main_menu_keyboard(notifications_subscribed),
    )


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    save_message_user(message)
    await send_help_with_keyboards(message)


@router.callback_query(F.data == "help")
async def callback_help(callback: CallbackQuery) -> None:
    save_callback_user(callback)
    await callback.answer()

    if callback.message:
        await send_help_with_keyboards(callback.message, callback.from_user.id)


@router.message(F.text == "ℹ️ Помощь")
async def reply_help(message: Message) -> None:
    save_message_user(message)
    await send_help_with_keyboards(message)
