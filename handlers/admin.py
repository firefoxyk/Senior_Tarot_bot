import os

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from database import (
    get_active_users_count_for_date,
    get_cards_readings_count,
    get_spread_readings_count,
    get_total_users_count,
)
from services.donations import DonationService
from services.timezone import get_today_moscow


router = Router()


def get_admin_ids() -> set[int]:
    raw_admin_ids = os.getenv("ADMIN_IDS", "")
    separators = str.maketrans({",": " ", ";": " ", "\n": " "})
    normalized_admin_ids = raw_admin_ids.translate(separators)

    admin_ids: set[int] = set()

    for value in normalized_admin_ids.split():
        try:
            admin_ids.add(int(value))
        except ValueError:
            continue

    return admin_ids


def is_admin(message: Message) -> bool:
    return bool(message.from_user and message.from_user.id in get_admin_ids())


def format_amount_minor(amount_minor: int, currency: str) -> str:
    major = amount_minor // 100
    minor = amount_minor % 100
    return f"{major}.{minor:02d} {currency}"


@router.message(Command("donations_stats"))
async def cmd_donations_stats(message: Message) -> None:
    if not is_admin(message):
        await message.answer("Доступ запрещён.")
        return

    donations_count = DonationService.get_donations_count()
    currency_stats = DonationService.get_currency_stats()
    donator_stats = DonationService.get_donator_stats()

    text_parts = [
        "💳 <b>Статистика донатов</b>",
        f"<b>Всего донатов:</b> {donations_count}",
    ]

    if currency_stats:
        currency_lines = [
            (
                f"{stats.currency}: "
                f"{format_amount_minor(stats.total_amount_minor, stats.currency)} "
                f"({stats.donations_count})"
            )
            for stats in currency_stats
        ]
        text_parts.append("<b>Собрано по валютам:</b>\n" + "\n".join(currency_lines))
    else:
        text_parts.append("<b>Собрано по валютам:</b>\nПока нет донатов.")

    if donator_stats:
        donator_lines = [
            (
                f"{stats.user_id}: "
                f"{format_amount_minor(stats.total_amount_minor, stats.currency)} "
                f"({stats.donations_count})"
            )
            for stats in donator_stats
        ]
        text_parts.append("<b>Донатеры:</b>\n" + "\n".join(donator_lines))
    else:
        text_parts.append("<b>Донатеры:</b>\nПока нет донатов.")

    await message.answer("\n\n".join(text_parts))


@router.message(Command("stats"))
async def cmd_stats(message: Message) -> None:
    if not is_admin(message):
        await message.answer("Доступ запрещён.")
        return

    today = get_today_moscow()
    currency = os.getenv("SERVER_MONTHLY_GOAL_CURRENCY", "RUB").strip() or "RUB"
    donations_progress = DonationService.get_monthly_server_progress(currency)

    text = "\n".join(
        [
            "📊 <b>Статистика</b>",
            f"<b>Пользователей всего:</b> {get_total_users_count()}",
            f"<b>Активных за сегодня:</b> {get_active_users_count_for_date(today)}",
            f"<b>Выдано карт:</b> {get_cards_readings_count()}",
            f"<b>Сделано раскладов:</b> {get_spread_readings_count()}",
            (
                f"<b>Донатов за месяц:</b> "
                f"{format_amount_minor(donations_progress.collected_minor, donations_progress.currency)} "
                f"({donations_progress.donations_count})"
            ),
        ]
    )

    await message.answer(text)
