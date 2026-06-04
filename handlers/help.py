from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from keyboards import main_menu_keyboard, reply_menu_keyboard
from services.users import save_callback_user, save_message_user
from texts import HELP_TEXT


router = Router()


async def send_help_with_keyboards(message: Message) -> None:
    await message.answer(
        HELP_TEXT,
        reply_markup=reply_menu_keyboard(),
    )

    await message.answer(
        "Выбери действие:",
        reply_markup=main_menu_keyboard(),
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
        await send_help_with_keyboards(callback.message)


@router.message(F.text == "ℹ️ Помощь")
async def reply_help(message: Message) -> None:
    save_message_user(message)
    await send_help_with_keyboards(message)