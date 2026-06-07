import logging
from datetime import date

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError

from database import get_users_without_daily_card_today, mark_user_blocked
from keyboards import main_menu_keyboard
from services.timezone import get_today_moscow


logger = logging.getLogger(__name__)


async def send_daily_card_reminders(bot: Bot) -> None:
    today = get_today_moscow()
    users = get_users_without_daily_card_today(today)
    
    logger.info(f"[Daily Card Reminder] Starting reminders for {len(users)} users (date: {today})")
    
    success_count = 0
    blocked_count = 0
    error_count = 0

    for user_id in users:
        try:
            await bot.send_message(
                chat_id=user_id,
                text=(
                    "🔮 Пора вытянуть карту дня!\n\n"
                    "Узнай, что сегодня приготовил тебе Senior Tarot."
                ),
                reply_markup=main_menu_keyboard(notifications_subscribed=True),
            )
            success_count += 1
            logger.info(f"[Daily Card Reminder] ✅ Sent reminder to user {user_id}")
            
        except TelegramForbiddenError:
            blocked_count += 1
            mark_user_blocked(user_id)
            logger.warning(f"[Daily Card Reminder] ⚠️ User {user_id} blocked bot or deleted account")
            
        except TelegramBadRequest as e:
            error_count += 1
            logger.warning(f"[Daily Card Reminder] ⚠️ Bad request for user {user_id}: {e}")
            
        except Exception as e:
            error_count += 1
            logger.exception(f"[Daily Card Reminder] ❌ Failed to send reminder to user {user_id}: {e}")
    
    logger.info(
        f"[Daily Card Reminder] Summary: {success_count} sent, "
        f"{blocked_count} blocked/deleted, {error_count} errors"
    )
