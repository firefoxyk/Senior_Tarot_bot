from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from services.menu import (
    get_notifications_subscription_for_message,
    send_inline_menu,
    send_menu_pair,
)
from services.users import save_message_user
from texts import WELCOME_TEXT


router = Router()


async def send_menu(message: Message) -> None:
    notifications_subscribed = get_notifications_subscription_for_message(message)
    await send_inline_menu(message, notifications_subscribed)


@router.message(Command("menu"))
async def cmd_menu(message: Message) -> None:
    save_message_user(message)
    await send_menu_pair(message, "Меню под рукой.")


@router.message(Command("start"))
async def cmd_start(message: Message) -> None:
    save_message_user(message)
    await send_menu_pair(message, WELCOME_TEXT)
