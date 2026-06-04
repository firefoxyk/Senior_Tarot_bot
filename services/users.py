from aiogram.types import CallbackQuery, Message

from database import add_user


def save_message_user(message: Message) -> None:
    user = message.from_user

    if not user:
        return

    add_user(
        user_id=user.id,
        username=user.username,
        first_name=user.first_name,
    )


def save_callback_user(callback: CallbackQuery) -> None:
    user = callback.from_user

    add_user(
        user_id=user.id,
        username=user.username,
        first_name=user.first_name,
    )