from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def main_menu_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(
                text="🔮 Карта дня",
                callback_data="card"
            ),
        ],
        [
            InlineKeyboardButton(
                text="🃏 Общий расклад",
                callback_data="spread"
            ),
        ],
        [
            InlineKeyboardButton(
                text="💼 Карьера",
                callback_data="career"
            ),
            InlineKeyboardButton(
                text="🚀 Проект",
                callback_data="project"
            ),
        ],
        [
            InlineKeyboardButton(
                text="ℹ️ Помощь",
                callback_data="help"
            ),
        ],
    ]

    return InlineKeyboardMarkup(
        inline_keyboard=keyboard
    )