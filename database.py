import sqlite3
from datetime import datetime


DB_NAME = "senior_tarot.db"


def get_connection() -> sqlite3.Connection:
    """
    Создаёт подключение к SQLite.
    """
    return sqlite3.connect(DB_NAME)


def init_db() -> None:
    """
    Создаёт таблицу пользователей при запуске бота.
    """
    with get_connection() as connection:
        cursor = connection.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER UNIQUE,
                username TEXT,
                first_name TEXT,
                created_at TEXT,
                last_daily_card_date TEXT,
                last_daily_action_date TEXT
            )
            """
        )

        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]

        if "last_daily_card_date" not in columns:
            cursor.execute(
                """
                ALTER TABLE users
                ADD COLUMN last_daily_card_date TEXT
                """
            )

        if "last_daily_action_date" not in columns:
            cursor.execute(
                """
                ALTER TABLE users
                ADD COLUMN last_daily_action_date TEXT
                """
            )

        connection.commit()


def add_user(user_id: int, username: str | None, first_name: str | None) -> None:
    """
    Добавляет пользователя в БД.
    При повторном действии пользователь не дублируется.
    """
    with get_connection() as connection:
        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT OR IGNORE INTO users (
                user_id,
                username,
                first_name,
                created_at
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                user_id,
                username,
                first_name,
                datetime.utcnow().isoformat(),
            ),
        )

        connection.commit()


def get_all_users() -> list[int]:
    """
    Возвращает список user_id всех пользователей.
    """
    with get_connection() as connection:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT user_id
            FROM users
            """
        )

        rows = cursor.fetchall()

    return [row[0] for row in rows]


def update_last_daily_card_date(user_id: int, date_value: str) -> None:
    """
    Сохраняет дату последнего вытягивания карты дня.
    """
    with get_connection() as connection:
        cursor = connection.cursor()

        cursor.execute(
            """
            UPDATE users
            SET last_daily_card_date = ?
            WHERE user_id = ?
            """,
            (date_value, user_id),
        )

        connection.commit()


def update_daily_card_action_dates(user_id: int, today: str) -> None:
    """
    Атомарно обновляет обе даты в одной транзакции для карты дня:
    - last_daily_action_date (блокирует повторное действие сегодня)
    - last_daily_card_date (для уведомлений завтра)
    
    Гарантирует согласованность: обе даты обновляются вместе или не обновляются вообще.
    Исправляет race condition между двумя отдельными UPDATE запросами.
    
    Args:
        user_id: ID пользователя
        today: Дата в формате ISO (YYYY-MM-DD)
    """
    with get_connection() as connection:
        cursor = connection.cursor()

        cursor.execute(
            """
            UPDATE users
            SET last_daily_action_date = ?,
                last_daily_card_date = ?
            WHERE user_id = ?
            """,
            (today, today, user_id),
        )

        connection.commit()


def get_users_without_daily_card_today(today: str) -> list[int]:
    """
    Возвращает пользователей, которые сегодня ещё не вытягивали карту дня.
    """
    with get_connection() as connection:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT user_id
            FROM users
            WHERE last_daily_card_date IS NULL
               OR last_daily_card_date != ?
            """,
            (today,),
        )

        rows = cursor.fetchall()

    return [row[0] for row in rows]


def update_last_daily_action_date(user_id: int, date_value: str) -> None:
    """
    Сохраняет дату последнего расклада или карты дня.
    """
    with get_connection() as connection:
        cursor = connection.cursor()

        cursor.execute(
            """
            UPDATE users
            SET last_daily_action_date = ?
            WHERE user_id = ?
            """,
            (date_value, user_id),
        )

        connection.commit()


def user_has_daily_action_today(user_id: int, today: str) -> bool:
    """
    Проверяет, делал ли пользователь карту дня или расклад сегодня.
    """
    with get_connection() as connection:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT last_daily_action_date
            FROM users
            WHERE user_id = ?
            """,
            (user_id,),
        )

        row = cursor.fetchone()

    if not row:
        return False

    return row[0] == today