from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from database import is_morning_reminders_subscribed
from keyboards import main_menu_keyboard, reply_menu_keyboard
from services.users import save_message_user
from texts import WELCOME_TEXT


router = Router()


async def send_menu(message: Message) -> None:
    notifications_subscribed = True

    if message.from_user:
        notifications_subscribed = is_morning_reminders_subscribed(message.from_user.id)

    await message.answer(
        "Выбери действие:",
        reply_markup=main_menu_keyboard(notifications_subscribed),
    )


@router.message(Command("menu"))
async def cmd_menu(message: Message) -> None:
    save_message_user(message)
    notifications_subscribed = True

    if message.from_user:
        notifications_subscribed = is_morning_reminders_subscribed(message.from_user.id)

    await message.answer(
        "Меню под рукой.",
        reply_markup=reply_menu_keyboard(notifications_subscribed),
    )

    await send_menu(message)


@router.message(Command("start"))
async def cmd_start(message: Message) -> None:
    save_message_user(message)
    notifications_subscribed = True

    if message.from_user:
        notifications_subscribed = is_morning_reminders_subscribed(message.from_user.id)

    await message.answer(
        WELCOME_TEXT,
        reply_markup=reply_menu_keyboard(notifications_subscribed),
    )

    await message.answer(
        "Выбери действие:",
        reply_markup=main_menu_keyboard(notifications_subscribed),
    )
