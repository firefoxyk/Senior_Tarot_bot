from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from keyboards import main_menu_keyboard, reply_menu_keyboard
from services.users import save_message_user
from texts import WELCOME_TEXT


router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message) -> None:
    save_message_user(message)

    await message.answer(
        WELCOME_TEXT,
        reply_markup=reply_menu_keyboard(),
    )

    await message.answer(
        "Выбери действие:",
        reply_markup=main_menu_keyboard(),
    )