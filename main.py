import asyncio
import os

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from dotenv import load_dotenv

from database import init_db
from handlers import router


async def main() -> None:
    load_dotenv()

    bot_token = os.getenv("BOT_TOKEN")

    if not bot_token:
        raise RuntimeError("BOT_TOKEN не найден. Добавьте токен в файл .env")

    init_db()

    bot = Bot(
        token=bot_token,
        default=DefaultBotProperties(
            parse_mode=ParseMode.HTML
        )
    )

    dp = Dispatcher()
    dp.include_router(router)

    print("Senior Tarot bot started")

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())