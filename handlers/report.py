from datetime import datetime
from html import escape

from aiogram import F, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message, User

from database import is_morning_reminders_subscribed
from keyboards import cancel_keyboard, main_menu_keyboard, reply_menu_keyboard
from services.admins import get_admin_ids
from services.timezone import MOSCOW_TZ
from services.users import save_callback_user, save_message_user


router = Router()

REPORT_PROMPT = (
    "Опишите, пожалуйста, что пошло не так. Можно одним сообщением. "
    "Если можете — укажите, на каком действии возникла проблема."
)
REPORT_SUCCESS_TEXT = "Спасибо! Я передала сообщение разработчику 🛠"
REPORT_FAILURE_TEXT = "Не получилось отправить сообщение. Попробуйте позже."
REPORT_CANCELLED_TEXT = "Отменила отправку сообщения."
REPORT_INTERRUPTED_TEXT = "Отменила отправку сообщения. Выберите действие заново."
MENU_TEXTS = {
    "🔮 Карта дня",
    "🃏 Общий расклад",
    "💼 Карьера",
    "🚀 Проект",
    "ℹ️ Помощь",
    "Сообщить о проблеме",
    "Отписаться от уведомлений",
    "Подписаться на уведомления",
    "☕ Поддержать проект",
}


class ReportProblem(StatesGroup):
    waiting_for_description = State()


def format_report_message(user: User | None, text: str, received_at: datetime) -> str:
    user_id = user.id if user else "unknown"
    username = f"@{user.username}" if user and user.username else "не указан"
    first_name = user.first_name if user and user.first_name else "не указано"
    received_at_text = received_at.strftime("%Y-%m-%d %H:%M:%S %Z")

    return "\n".join(
        [
            "🛠 <b>Сообщение о проблеме</b>",
            "",
            f"<b>Дата:</b> {escape(received_at_text)}",
            f"<b>user_id:</b> {escape(str(user_id))}",
            f"<b>username:</b> {escape(username)}",
            f"<b>first_name:</b> {escape(first_name)}",
            "",
            "<b>Текст проблемы:</b>",
            escape(text),
        ]
    )


async def send_report_to_admins(message: Message, report_text: str) -> bool:
    admin_ids = get_admin_ids()

    if not admin_ids:
        return False

    admin_message = format_report_message(
        user=message.from_user,
        text=report_text,
        received_at=datetime.now(MOSCOW_TZ),
    )

    try:
        for admin_id in admin_ids:
            await message.bot.send_message(admin_id, admin_message)
    except Exception:
        return False

    return True


async def start_report_problem(message: Message, state: FSMContext) -> None:
    await state.set_state(ReportProblem.waiting_for_description)
    await message.answer(
        REPORT_PROMPT,
        reply_markup=cancel_keyboard(),
    )


async def send_main_menu(message: Message) -> None:
    notifications_subscribed = True

    if message.from_user:
        notifications_subscribed = is_morning_reminders_subscribed(message.from_user.id)

    await message.answer(
        "Выбери действие:",
        reply_markup=reply_menu_keyboard(notifications_subscribed),
    )

    await message.answer(
        "Меню под рукой.",
        reply_markup=main_menu_keyboard(notifications_subscribed),
    )


@router.message(Command("cancel"), StateFilter(ReportProblem.waiting_for_description))
async def cancel_report_by_command(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(REPORT_CANCELLED_TEXT)
    await send_main_menu(message)


@router.message(F.text == "Отмена", StateFilter(ReportProblem.waiting_for_description))
async def cancel_report_by_button(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(REPORT_CANCELLED_TEXT)
    await send_main_menu(message)


@router.message(F.text.startswith("/"), StateFilter(ReportProblem.waiting_for_description))
async def interrupt_report_by_command(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(REPORT_INTERRUPTED_TEXT)
    await send_main_menu(message)


@router.message(F.text.in_(MENU_TEXTS), StateFilter(ReportProblem.waiting_for_description))
async def interrupt_report_by_menu_button(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(REPORT_INTERRUPTED_TEXT)
    await send_main_menu(message)


@router.message(F.text == "Сообщить о проблеме")
async def reply_report_problem(message: Message, state: FSMContext) -> None:
    save_message_user(message)
    await start_report_problem(message, state)


@router.callback_query(F.data == "report_problem")
async def callback_report_problem(callback: CallbackQuery, state: FSMContext) -> None:
    save_callback_user(callback)
    await callback.answer()

    if callback.message:
        await start_report_problem(callback.message, state)


@router.message(StateFilter(ReportProblem.waiting_for_description), F.text)
async def receive_report_description(message: Message, state: FSMContext) -> None:
    save_message_user(message)
    is_sent = await send_report_to_admins(message, message.text or "")
    await state.clear()

    if is_sent:
        await message.answer(REPORT_SUCCESS_TEXT)
    else:
        await message.answer(REPORT_FAILURE_TEXT)

    await send_main_menu(message)
