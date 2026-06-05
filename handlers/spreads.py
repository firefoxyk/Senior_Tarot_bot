from contextlib import suppress

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, FSInputFile, Message, User

from services.cards import (
    BASE_DIR,
    SPREADS,
    draw_cards,
    get_card_text,
)
from services.images import create_spread_collage
from services.limits import check_daily_limit, spend_daily_limit
from services.users import save_callback_user, save_message_user


router = Router()


async def send_spread(
    message: Message,
    spread_key: str,
    user: User | None = None,
) -> None:
    save_message_user(message)
    user = user or message.from_user

    if not await check_daily_limit(message, user):
        return

    spread = SPREADS[spread_key]
    positions = spread["positions"]
    cards = draw_cards(len(positions))

    collage_path = create_spread_collage(cards, BASE_DIR)

    text_parts = [
        f"<b>{spread['title']}</b>",
        spread["intro"],
    ]

    for position, card in zip(positions, cards):
        field = position.get("field", "meaning")
        interpretation = get_card_text(card, field)

        text_parts.append(
            f"""
<b>{position['title']}</b>
🃏 {card['name']}
{interpretation}
""".strip()
        )

    caption = "\n\n".join(text_parts)

    try:
        await message.answer_photo(
            photo=FSInputFile(collage_path),
            caption=caption,
        )
    finally:
        with suppress(FileNotFoundError):
            collage_path.unlink()

    spend_daily_limit(user)


@router.message(Command("spread"))
async def cmd_spread(message: Message) -> None:
    await send_spread(message, "spread")


@router.message(Command("career"))
async def cmd_career(message: Message) -> None:
    await send_spread(message, "career")


@router.message(Command("project"))
async def cmd_project(message: Message) -> None:
    await send_spread(message, "project")


@router.callback_query(F.data == "spread")
async def callback_spread(callback: CallbackQuery) -> None:
    save_callback_user(callback)
    await callback.answer()

    if callback.message:
        await send_spread(callback.message, "spread", callback.from_user)


@router.callback_query(F.data == "career")
async def callback_career(callback: CallbackQuery) -> None:
    save_callback_user(callback)
    await callback.answer()

    if callback.message:
        await send_spread(callback.message, "career", callback.from_user)


@router.callback_query(F.data == "project")
async def callback_project(callback: CallbackQuery) -> None:
    save_callback_user(callback)
    await callback.answer()

    if callback.message:
        await send_spread(callback.message, "project", callback.from_user)


@router.message(F.text == "🃏 Общий расклад")
async def reply_spread(message: Message) -> None:
    await send_spread(message, "spread")


@router.message(F.text == "💼 Карьера")
async def reply_career(message: Message) -> None:
    await send_spread(message, "career")


@router.message(F.text == "🚀 Проект")
async def reply_project(message: Message) -> None:
    await send_spread(message, "project")
