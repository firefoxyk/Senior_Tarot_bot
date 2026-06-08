from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from services.menu import send_menu_pair
from services.users import save_callback_user, save_message_user
from texts import HELP_TEXT


router = Router()


async def send_help_with_keyboards(
    message: Message,
    user_id: int | None = None,
) -> None:
    await send_menu_pair(message, HELP_TEXT, user_id)


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
