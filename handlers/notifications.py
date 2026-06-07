from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from database import set_morning_reminders_subscription
from keyboards import main_menu_keyboard, reply_menu_keyboard
from services.users import save_callback_user, save_message_user


router = Router()


async def send_notifications_subscription_menu(
    message: Message,
    notifications_subscribed: bool,
) -> None:
    if notifications_subscribed:
        text = "Готово, утренние напоминания включены."
    else:
        text = "Готово, утренние напоминания отключены."

    await message.answer(
        text,
        reply_markup=reply_menu_keyboard(notifications_subscribed),
    )

    await message.answer(
        "Выбери действие:",
        reply_markup=main_menu_keyboard(notifications_subscribed),
    )


@router.callback_query(F.data == "unsubscribe_notifications")
async def callback_unsubscribe_notifications(callback: CallbackQuery) -> None:
    save_callback_user(callback)
    set_morning_reminders_subscription(callback.from_user.id, False)
    await callback.answer("Уведомления отключены")

    if callback.message:
        await send_notifications_subscription_menu(callback.message, False)


@router.callback_query(F.data == "subscribe_notifications")
async def callback_subscribe_notifications(callback: CallbackQuery) -> None:
    save_callback_user(callback)
    set_morning_reminders_subscription(callback.from_user.id, True)
    await callback.answer("Уведомления включены")

    if callback.message:
        await send_notifications_subscription_menu(callback.message, True)


@router.message(F.text == "Отписаться от уведомлений")
async def reply_unsubscribe_notifications(message: Message) -> None:
    save_message_user(message)

    if not message.from_user:
        return

    set_morning_reminders_subscription(message.from_user.id, False)
    await send_notifications_subscription_menu(message, False)


@router.message(F.text == "Подписаться на уведомления")
async def reply_subscribe_notifications(message: Message) -> None:
    save_message_user(message)

    if not message.from_user:
        return

    set_morning_reminders_subscription(message.from_user.id, True)
    await send_notifications_subscription_menu(message, True)
