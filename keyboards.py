from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)


def reply_menu_keyboard() -> ReplyKeyboardMarkup:
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
                KeyboardButton(text="ℹ️ Помощь"),
            ],
            [
                KeyboardButton(text="☕ Поддержать проект"),
            ],
        ],
        resize_keyboard=True,
        input_field_placeholder="Выбери действие..."
    )


def main_menu_keyboard() -> InlineKeyboardMarkup:
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
                InlineKeyboardButton(text="ℹ️ Помощь", callback_data="help"),
            ],
            [
                InlineKeyboardButton(text="☕ Поддержать проект", callback_data="donate"),
            ],
        ]
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
