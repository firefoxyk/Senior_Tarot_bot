import asyncio
import logging
import os

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import BotCommand
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv

from database import init_db
from handlers import router
from notifications import send_daily_card_reminders


def build_bot_commands() -> list[BotCommand]:
    return [
        BotCommand(command="start", description="Старт"),
        BotCommand(command="menu", description="Меню"),
        BotCommand(command="help", description="Помощь"),
        BotCommand(command="card", description="Карта дня"),
        BotCommand(command="spread", description="Общий расклад"),
        BotCommand(command="career", description="Карьерный расклад"),
        BotCommand(command="project", description="Проектный расклад"),
    ]


async def main() -> None:
    load_dotenv()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    bot_token = os.getenv("BOT_TOKEN")

    if not bot_token:
        raise RuntimeError(
            "BOT_TOKEN не найден. Добавьте токен в файл .env"
        )

    init_db()

    bot = Bot(
        token=bot_token,
        default=DefaultBotProperties(
            parse_mode=ParseMode.HTML
        )
    )

    dp = Dispatcher()
    dp.include_router(router)
    await bot.set_my_commands(build_bot_commands())

    scheduler = AsyncIOScheduler(
        timezone="Europe/Moscow"
    )

    scheduler.add_job(
        send_daily_card_reminders,
        trigger="cron",
        hour=10,
        minute=0,
        args=[bot],
        id="daily_card_reminder",
        replace_existing=True,
    )
    

    scheduler.start()

    print("Daily reminders scheduler started")
    print("Senior Tarot bot started")

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
