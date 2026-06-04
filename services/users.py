from datetime import UTC, datetime, timedelta

from aiogram.types import CallbackQuery, Message

from database import add_user, get_connection


def save_message_user(message: Message) -> None:
    user = message.from_user

    if not user:
        return

    add_user(
        user_id=user.id,
        username=user.username,
        first_name=user.first_name,
    )


def save_callback_user(callback: CallbackQuery) -> None:
    user = callback.from_user

    add_user(
        user_id=user.id,
        username=user.username,
        first_name=user.first_name,
    )


def _get_now_utc() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def _parse_utc_datetime(value: str | None) -> datetime | None:
    if not value:
        return None

    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def get_unlimited_until(user_id: int) -> str | None:
    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT unlimited_until
            FROM users
            WHERE user_id = ?
            """,
            (user_id,),
        )
        row = cursor.fetchone()

    if not row:
        return None

    return row[0]


def is_unlimited_user(user_id: int) -> bool:
    unlimited_until = _parse_utc_datetime(get_unlimited_until(user_id))

    if not unlimited_until:
        return False

    return unlimited_until > _get_now_utc()


def grant_unlimited_access(user_id: int, days: int = 7) -> str:
    now = _get_now_utc()
    current_until = _parse_utc_datetime(get_unlimited_until(user_id))
    base_datetime = current_until if current_until and current_until > now else now
    new_unlimited_until = (base_datetime + timedelta(days=days)).isoformat()

    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute(
            """
            UPDATE users
            SET unlimited_until = ?
            WHERE user_id = ?
            """,
            (new_unlimited_until, user_id),
        )
        connection.commit()

    return new_unlimited_until
