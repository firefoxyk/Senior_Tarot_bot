import os

from aiogram import F, Router
from aiogram.types import CallbackQuery, LabeledPrice, Message, PreCheckoutQuery

from keyboards import donate_keyboard
from services.users import save_callback_user, save_message_user


router = Router()

SUPPORT_PAYLOAD = "support_99"
SUPPORT_PRICE = 9900
SUPPORT_CURRENCY = "RUB"
SUPPORT_TITLE = "Поддержка проекта Senior Tarot"
SUPPORT_DESCRIPTION = "Поддержка сервера и развития проекта Senior Tarot"


DONATE_TEXT = """
🃏 Карта «Оплата сервера»

Прямое положение:
Сервер продолжает работать ещё один месяц.

Перевёрнутое положение:
Автор начинает переносить бота на бесплатный VPS из сомнительного Telegram-канала.

Каждая поддержка на 99 ₽ помогает удерживать Senior Tarot на светлой стороне продакшена.
""".strip()

PAYMENT_TOKEN_MISSING_TEXT = """
💳 Поддержка проекта сейчас недоступна.

Платёжный токен ещё не настроен.
""".strip()

SUCCESSFUL_PAYMENT_TEXT = """
🃏 Карта «Поддержка проекта»

Прямое положение:
Сервер оплачен.

Перевёрнутое положение:
Автор временно перестал смотреть цены на бесплатный хостинг.

Спасибо за поддержку Senior Tarot ☕
""".strip()


def get_payment_provider_token() -> str | None:
    token = os.getenv("PAYMENT_PROVIDER_TOKEN")

    if not token:
        return None

    return token.strip() or None


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

    provider_token = get_payment_provider_token()

    if callback.message:
        if not provider_token:
            await callback.message.answer(PAYMENT_TOKEN_MISSING_TEXT)
            return

        await callback.message.answer_invoice(
            title=SUPPORT_TITLE,
            description=SUPPORT_DESCRIPTION,
            payload=SUPPORT_PAYLOAD,
            provider_token=provider_token,
            currency=SUPPORT_CURRENCY,
            prices=[
                LabeledPrice(
                    label=SUPPORT_TITLE,
                    amount=SUPPORT_PRICE,
                ),
            ],
        )


@router.pre_checkout_query()
async def pre_checkout_query(pre_checkout: PreCheckoutQuery) -> None:
    provider_token = get_payment_provider_token()

    if pre_checkout.invoice_payload != SUPPORT_PAYLOAD:
        await pre_checkout.answer(
            ok=False,
            error_message="Некорректный платёж.",
        )
        return

    if not provider_token:
        await pre_checkout.answer(
            ok=False,
            error_message="Платежи временно недоступны.",
        )
        return

    await pre_checkout.answer(ok=True)


@router.message(F.successful_payment)
async def successful_payment(message: Message) -> None:
    payment = message.successful_payment

    if not payment or payment.invoice_payload != SUPPORT_PAYLOAD:
        return

    save_message_user(message)

    await message.answer(SUCCESSFUL_PAYMENT_TEXT)
