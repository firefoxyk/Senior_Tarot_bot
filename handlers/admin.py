import os
from datetime import datetime, timedelta

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from database import (
    get_active_users_count_for_date,
    get_active_users_count_since,
    get_morning_reminders_subscribed_count,
    get_morning_reminders_unsubscribed_count,
    get_readings_count_by_type,
    get_total_users_count,
)
from services.admins import get_admin_ids
from services.donations import DonationService
from services.timezone import get_today_moscow


router = Router()


def is_admin(message: Message) -> bool:
    return bool(message.from_user and message.from_user.id in get_admin_ids())


def format_amount_minor(amount_minor: int, currency: str) -> str:
    major = amount_minor // 100
    minor = amount_minor % 100
    return f"{major}.{minor:02d} {currency}"


def format_date(value: str) -> str:
    try:
        return datetime.fromisoformat(value).strftime("%Y-%m-%d")
    except ValueError:
        return value[:10]


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
    week_start = (datetime.fromisoformat(today) - timedelta(days=6)).date().isoformat()
    currency = os.getenv("SERVER_MONTHLY_GOAL_CURRENCY", "RUB").strip() or "RUB"
    donations_progress = DonationService.get_monthly_server_progress(currency)
    latest_donations = DonationService.get_latest_public_donations(limit=5)

    latest_donation_lines = [
        (
            f"{index}. {format_amount_minor(donation.amount_minor, donation.currency)} "
            f"({format_date(donation.created_at)})"
        )
        for index, donation in enumerate(latest_donations, start=1)
    ]

    if not latest_donation_lines:
        latest_donation_lines = ["Пока нет донатов."]

    text = "\n".join(
        [
            "📊 <b>Статистика</b>",
            "",
            f"👥 <b>Пользователей всего:</b> {get_total_users_count()}",
            f"📈 <b>Активных за сегодня:</b> {get_active_users_count_for_date(today)}",
            f"📈 <b>Активных за неделю:</b> {get_active_users_count_since(f'{week_start}T00:00:00')}",
            f"🔔 <b>Подписаны на утренние напоминания:</b> {get_morning_reminders_subscribed_count()}",
            f"🔕 <b>Отписаны от утренних напоминаний:</b> {get_morning_reminders_unsubscribed_count()}",
            "",
            f"🔮 <b>Карт дня выдано:</b> {get_readings_count_by_type('card')}",
            f"🃏 <b>Общих раскладов:</b> {get_readings_count_by_type('spread')}",
            f"💼 <b>Карьерных раскладов:</b> {get_readings_count_by_type('career')}",
            f"🚀 <b>Проектных раскладов:</b> {get_readings_count_by_type('project')}",
            "",
            f"☕ <b>Донатов за месяц:</b> {donations_progress.donations_count}",
            (
                f"💰 <b>Сумма донатов:</b> "
                f"{format_amount_minor(donations_progress.collected_minor, donations_progress.currency)}"
            ),
            "",
            "<b>ТОП-5 последних донатеров:</b>",
            *latest_donation_lines,
        ]
    )

    await message.answer(text)
