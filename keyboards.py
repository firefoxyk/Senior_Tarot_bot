import os

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)


def get_bot_share_url() -> str:
    bot_username = os.getenv("BOT_USERNAME", "BugOracleBot").strip() or "BugOracleBot"
    bot_username = bot_username.removeprefix("@")
    return f"https://t.me/{bot_username}"


def reply_menu_keyboard(notifications_subscribed: bool = True) -> ReplyKeyboardMarkup:
    notification_button_text = (
        "Отписаться от уведомлений"
        if notifications_subscribed
        else "Подписаться на уведомления"
    )

    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="🔮 Карта дня"),
                KeyboardButton(text="🃏 Общий расклад"),
            ],
            [
                KeyboardButton(text="💼 Карьера"),
                KeyboardButton(text="🚀 Проект"),
            ],
            [
                KeyboardButton(text="☕ Поддержать проект"),
            ],
            [
                KeyboardButton(text="ℹ️ Помощь"),
                KeyboardButton(text="Сообщить о проблеме"),
            ],
            [
                KeyboardButton(text=notification_button_text),
            ],
        ],
        resize_keyboard=True,
        input_field_placeholder="Выбери действие..."
    )


def main_menu_keyboard(notifications_subscribed: bool = True) -> InlineKeyboardMarkup:
    notification_button = InlineKeyboardButton(
        text=(
            "Отписаться от уведомлений"
            if notifications_subscribed
            else "Подписаться на уведомления"
        ),
        callback_data=(
            "unsubscribe_notifications"
            if notifications_subscribed
            else "subscribe_notifications"
        ),
    )

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🔮 Карта дня", callback_data="card"),
            ],
            [
                InlineKeyboardButton(text="🃏 Общий расклад", callback_data="spread"),
            ],
            [
                InlineKeyboardButton(text="💼 Карьера", callback_data="career"),
                InlineKeyboardButton(text="🚀 Проект", callback_data="project"),
            ],
            [
                InlineKeyboardButton(text="☕ Поддержать проект", callback_data="donate"),
            ],
            [
                InlineKeyboardButton(text="ℹ️ Помощь", callback_data="help"),
                InlineKeyboardButton(text="Сообщить о проблеме", callback_data="report_problem"),
            ],
            [
                notification_button,
            ],
        ]
    )


def cancel_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="Отмена"),
            ],
        ],
        resize_keyboard=True,
        input_field_placeholder="Опишите проблему или отмените ввод..."
    )


def donate_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔮 Сохранить карту в прямом положении",
                    callback_data="donate_pay",
                ),
            ],
        ]
    )


def donation_upsell_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="☕ Поддержать проект",
                    callback_data="donate",
                ),
            ],
        ]
    )


def share_bot_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📤 Поделиться ботом",
                    url=get_bot_share_url(),
                ),
            ],
        ]
    )
