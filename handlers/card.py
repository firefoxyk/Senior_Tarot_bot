import random

from datetime import date

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, FSInputFile, Message, User

from database import update_last_daily_card_date, update_daily_card_action_dates
from services.cards import (
    BASE_DIR,
    Card,
    draw_cards,
    get_card_display_name,
    get_daily_prediction,
)
from services.images import create_reversed_image
from services.limits import check_daily_limit
from services.timezone import get_today_warsaw
from services.users import save_callback_user, save_message_user


router = Router()


async def send_card(
    message: Message,
    card: Card,
    title: str | None = None,
    is_reversed: bool = False,
) -> None:
    image_path = BASE_DIR / card["image"]

    card_name = get_card_display_name(card, is_reversed)
    prediction = get_daily_prediction(card, is_reversed)

    caption = f"""
🔮 <b>{title or "Карта"}</b>

🃏 <b>{card_name}</b>

📖 <b>Описание</b>
{card['description']}

🔮 <b>Предсказание</b>
{prediction}
"""

    if image_path.exists():
        if is_reversed:
            reversed_image_path = create_reversed_image(image_path)
            photo = FSInputFile(reversed_image_path)
        else:
            photo = FSInputFile(image_path)

        await message.answer_photo(
            photo=photo,
            caption=caption,
        )
    else:
        await message.answer(
            f"{caption}\n\n⚠️ Изображение не найдено: <code>{card['image']}</code>"
        )


async def send_single_card(message: Message, user: User | None = None) -> None:
    save_message_user(message)

    user = user or message.from_user

    if not await check_daily_limit(message, user):
        return

    if user:
        today = get_today_warsaw()
        update_daily_card_action_dates(
            user_id=user.id,
            today=today,
        )

    card = draw_cards(1)[0]
    is_reversed = random.choice([True, False])

    await send_card(
        message=message,
        card=card,
        title="Карта дня",
        is_reversed=is_reversed,
    )


@router.message(Command("card"))
async def cmd_card(message: Message) -> None:
    await send_single_card(message)


@router.callback_query(F.data == "card")
async def callback_card(callback: CallbackQuery) -> None:
    save_callback_user(callback)
    await callback.answer()

    if callback.message:
        await send_single_card(callback.message, callback.from_user)


@router.message(F.text == "🔮 Карта дня")
async def reply_card(message: Message) -> None:
    await send_single_card(message)
