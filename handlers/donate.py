from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from keyboards import donate_keyboard
from services.users import save_callback_user, save_message_user


router = Router()


DONATE_TEXT = """
🃏 Карта «Оплата сервера»

Прямое положение:
Сервер продолжает работать ещё один месяц.

Перевёрнутое положение:
Автор начинает изучать тарифы бесплатного хостинга.

Если хочется сохранить карту в прямом положении — можно поддержать проект на 99 ₽.
""".strip()

DONATE_STUB_TEXT = """
💳 Поддержка проекта

Стоимость: 99 ₽

Telegram Payments будет подключён позже.
""".strip()


async def send_donate_info(message: Message) -> None:
    await message.answer(
        DONATE_TEXT,
        reply_markup=donate_keyboard(),
    )


@router.message(F.text == "☕ Поддержать проект")
async def reply_donate(message: Message) -> None:
    save_message_user(message)
    await send_donate_info(message)


@router.callback_query(F.data == "donate")
async def callback_donate(callback: CallbackQuery) -> None:
    save_callback_user(callback)
    await callback.answer()

    if callback.message:
        await send_donate_info(callback.message)


@router.callback_query(F.data == "donate_pay")
async def callback_donate_pay(callback: CallbackQuery) -> None:
    save_callback_user(callback)
    await callback.answer()

    if callback.message:
        await callback.message.answer(DONATE_STUB_TEXT)
