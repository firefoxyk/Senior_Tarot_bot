from aiogram.types import Message, User

from database import (
    update_last_daily_action_date,
    user_has_daily_action_today,
)
from services.admins import is_admin_user
from services.menu import (
    get_notifications_subscription_for_message,
    is_private_chat,
    send_inline_menu,
    send_reply_menu_or_plain_text,
)
from services.timezone import get_today_moscow
from services.users import is_unlimited_user


async def check_daily_limit(message: Message, user: User | None = None) -> bool:
    user = user or message.from_user

    if not user:
        return False

    if is_admin_user(user.id) or is_unlimited_user(user.id):
        return True

    today = get_today_moscow()

    if user_has_daily_action_today(user.id, today):
        limit_text = (
            "⏳ На сегодня лимит гаданий уже использован.\n\n"
            "Можно сделать только <b>1 расклад или 1 карту дня в сутки</b>.\n"
            "Возвращайся завтра 🔮"
        )
        notifications_subscribed = get_notifications_subscription_for_message(
            message=message,
            user_id=user.id,
        )

        await send_reply_menu_or_plain_text(
            message=message,
            text=limit_text,
            notifications_subscribed=notifications_subscribed,
        )

        if not is_private_chat(message):
            await send_inline_menu(
                message=message,
                notifications_subscribed=notifications_subscribed,
            )

        return False

    return True


def spend_daily_limit(user: User | None) -> None:
    if not user:
        return

    if is_admin_user(user.id) or is_unlimited_user(user.id):
        return

    update_last_daily_action_date(
        user_id=user.id,
        date_value=get_today_moscow(),
    )
