from datetime import date

from aiogram.types import Message, User

from database import (
    update_last_daily_action_date,
    user_has_daily_action_today,
)
from keyboards import reply_menu_keyboard
from services.timezone import get_today_warsaw


async def check_daily_limit(message: Message, user: User | None = None) -> bool:
    user = user or message.from_user

    if not user:
        return False

    today = get_today_warsaw()

    if user_has_daily_action_today(user.id, today):
        await message.answer(
            (
                "⏳ На сегодня лимит гаданий уже использован.\n\n"
                "Можно сделать только <b>1 расклад или 1 карту дня в сутки</b>.\n"
                "Возвращайся завтра 🔮"
            ),
            reply_markup=reply_menu_keyboard(),
        )
        return False

    update_last_daily_action_date(
        user_id=user.id,
        date_value=today,
    )

    return True
