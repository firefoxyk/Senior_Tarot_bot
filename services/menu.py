from aiogram.types import Message

from database import is_morning_reminders_subscribed
from keyboards import main_menu_keyboard, reply_menu_keyboard


GROUP_MENU_HINT = "В группе используйте кнопки под сообщением или команды через /."


def is_private_chat(message: Message) -> bool:
    chat = getattr(message, "chat", None)
    if chat is None:
        return True

    return getattr(chat, "type", None) == "private"


def get_notifications_subscription_for_message(
    message: Message,
    user_id: int | None = None,
) -> bool:
    if user_id is None and message.from_user:
        user_id = message.from_user.id

    if user_id is None:
        return True

    return is_morning_reminders_subscribed(user_id)


async def send_reply_menu_or_plain_text(
    message: Message,
    text: str,
    notifications_subscribed: bool,
) -> None:
    if is_private_chat(message):
        await message.answer(
            text,
            reply_markup=reply_menu_keyboard(notifications_subscribed),
        )
        return

    await message.answer(text)


async def send_inline_menu(
    message: Message,
    notifications_subscribed: bool,
    text: str = "Выбери действие:",
) -> None:
    if not is_private_chat(message):
        text = f"{text}\n\n{GROUP_MENU_HINT}"

    await message.answer(
        text,
        reply_markup=main_menu_keyboard(notifications_subscribed),
    )


async def send_menu_pair(
    message: Message,
    text: str,
    user_id: int | None = None,
) -> None:
    notifications_subscribed = get_notifications_subscription_for_message(message, user_id)

    await send_reply_menu_or_plain_text(
        message=message,
        text=text,
        notifications_subscribed=notifications_subscribed,
    )

    await send_inline_menu(
        message=message,
        notifications_subscribed=notifications_subscribed,
    )
