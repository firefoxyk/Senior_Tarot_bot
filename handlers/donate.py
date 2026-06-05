import os
from datetime import datetime

from aiogram import F, Router
from aiogram.types import CallbackQuery, LabeledPrice, Message, PreCheckoutQuery

from keyboards import donate_keyboard
from services.donations import DonationService
from services.users import grant_unlimited_access, save_callback_user, save_message_user


router = Router()

SUPPORT_PAYLOAD = "support_99"
SUPPORT_PRICE = 9900
SUPPORT_CURRENCY = "RUB"
SUPPORT_TITLE = "Поддержка проекта Senior Tarot"
SUPPORT_DESCRIPTION = "Поддержка сервера и развития проекта Senior Tarot"

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

UNLIMITED_ACCESS_TEXT = """
⚡ Спасибо за поддержку!

На 7 дней для тебя сняты все лимиты.
Доступ без лимитов активен до: {unlimited_until}
""".strip()


def get_payment_provider_token() -> str | None:
    token = os.getenv("PAYMENT_PROVIDER_TOKEN")

    if not token:
        return None

    return token.strip() or None


def get_server_goal_currency() -> str:
    return os.getenv("SERVER_MONTHLY_GOAL_CURRENCY", SUPPORT_CURRENCY).strip() or SUPPORT_CURRENCY


def format_amount_minor(amount_minor: int) -> str:
    major = amount_minor // 100
    minor = amount_minor % 100

    if minor:
        return f"{major}.{minor:02d}"

    return str(major)


def format_unlimited_until(value: str) -> str:
    try:
        unlimited_until = datetime.fromisoformat(value)
    except ValueError:
        return value

    return unlimited_until.strftime("%Y-%m-%d до %H:%M")


def build_donate_text() -> str:
    currency = get_server_goal_currency()
    progress = DonationService.get_monthly_server_progress(currency)

    return f"""
🃏 Карта «Оплата сервера»

Прямое положение:
Сервер продолжает работать ещё один месяц.

Перевёрнутое положение:
Автор начинает переносить бота на бесплатный VPS из сомнительного Telegram-канала.

Каждая поддержка на 99 ₽ помогает удерживать Senior Tarot на светлой стороне продакшена.

🖥 Сервер месяца
Собрано: {format_amount_minor(progress.collected_minor)} ₽ из {format_amount_minor(progress.goal_minor)} ₽
{progress.progress_bar} {progress.percent}%
""".strip()


def get_payment_id(message: Message) -> str | None:
    payment = message.successful_payment

    if not payment:
        return None

    payment_id = payment.provider_payment_charge_id or payment.telegram_payment_charge_id

    if payment_id:
        return payment_id

    if not message.chat or message.message_id is None:
        return None

    return (
        f"telegram_fallback:"
        f"{message.chat.id}:"
        f"{message.message_id}:"
        f"{payment.invoice_payload}:"
        f"{payment.total_amount}:"
        f"{payment.currency}"
    )


async def send_donate_info(message: Message) -> None:
    await message.answer(
        build_donate_text(),
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

    unlimited_until = None

    if message.from_user:
        payment_id = get_payment_id(message)

        if payment_id:
            donation_result = DonationService.create_donation(
                user_id=message.from_user.id,
                amount_minor=payment.total_amount,
                currency=payment.currency,
                payment_id=payment_id,
            )

            if not donation_result.created:
                return

        unlimited_until = grant_unlimited_access(message.from_user.id, days=7)

    if unlimited_until:
        await message.answer(
            f"{SUCCESSFUL_PAYMENT_TEXT}\n\n"
            f"{UNLIMITED_ACCESS_TEXT.format(unlimited_until=format_unlimited_until(unlimited_until))}"
        )
        return

    await message.answer(SUCCESSFUL_PAYMENT_TEXT)
