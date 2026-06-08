import json
import sqlite3
from datetime import UTC, datetime
from typing import Any

from services.timezone import MOSCOW_TZ


DB_NAME = "senior_tarot.db"


def get_connection() -> sqlite3.Connection:
    """
    Создаёт подключение к SQLite.
    """
    connection = sqlite3.connect(DB_NAME)
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


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
                last_daily_action_date TEXT,
                unlimited_until TEXT,
                blocked_at TEXT,
                morning_reminders_subscribed INTEGER NOT NULL DEFAULT 1
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS donations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                amount_minor INTEGER NOT NULL,
                currency TEXT NOT NULL,
                payment_id TEXT NOT NULL UNIQUE,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS readings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                type TEXT NOT NULL CHECK(type IN ('card', 'spread', 'career', 'project')),
                cards_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
            """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_readings_user_created_at
            ON readings(user_id, created_at)
            """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_readings_type
            ON readings(type)
            """
        )

        cursor.execute("PRAGMA foreign_key_list(readings)")
        reading_foreign_keys = cursor.fetchall()

        if not any(foreign_key[2] == "users" for foreign_key in reading_foreign_keys):
            cursor.execute(
                """
                INSERT OR IGNORE INTO users (
                    user_id,
                    created_at
                )
                SELECT DISTINCT
                    user_id,
                    ?
                FROM readings
                """,
                (datetime.now(UTC).replace(tzinfo=None).isoformat(),),
            )
            cursor.execute("ALTER TABLE readings RENAME TO readings_without_fk")
            cursor.execute(
                """
                CREATE TABLE readings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    type TEXT NOT NULL CHECK(type IN ('card', 'spread', 'career', 'project')),
                    cards_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
                """
            )
            cursor.execute(
                """
                INSERT OR IGNORE INTO readings (
                    id,
                    user_id,
                    type,
                    cards_json,
                    created_at
                )
                SELECT
                    id,
                    user_id,
                    type,
                    cards_json,
                    created_at
                FROM readings_without_fk
                """
            )
            cursor.execute("DROP TABLE readings_without_fk")

        cursor.execute("PRAGMA table_info(donations)")
        donation_columns = [column[1] for column in cursor.fetchall()]

        if "amount" in donation_columns and "amount_minor" not in donation_columns:
            cursor.execute(
                """
                INSERT OR IGNORE INTO users (
                    user_id,
                    created_at
                )
                SELECT DISTINCT
                    user_id,
                    ?
                FROM donations
                """,
                (datetime.now(UTC).replace(tzinfo=None).isoformat(),),
            )
            cursor.execute("ALTER TABLE donations RENAME TO donations_old")
            cursor.execute(
                """
                CREATE TABLE donations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    amount_minor INTEGER NOT NULL,
                    currency TEXT NOT NULL,
                    payment_id TEXT NOT NULL UNIQUE,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
                """
            )
            cursor.execute(
                """
                INSERT OR IGNORE INTO donations (
                    id,
                    user_id,
                    amount_minor,
                    currency,
                    payment_id,
                    created_at
                )
                SELECT
                    id,
                    user_id,
                    CAST(ROUND(CAST(amount AS REAL) * 100) AS INTEGER),
                    'RUB',
                    payment_id,
                    created_at
                FROM donations_old
                """
            )
            cursor.execute("DROP TABLE donations_old")

        cursor.execute("PRAGMA foreign_key_list(donations)")
        donation_foreign_keys = cursor.fetchall()

        if not any(foreign_key[2] == "users" for foreign_key in donation_foreign_keys):
            cursor.execute(
                """
                INSERT OR IGNORE INTO users (
                    user_id,
                    created_at
                )
                SELECT DISTINCT
                    user_id,
                    ?
                FROM donations
                """,
                (datetime.now(UTC).replace(tzinfo=None).isoformat(),),
            )
            cursor.execute("ALTER TABLE donations RENAME TO donations_without_fk")
            cursor.execute(
                """
                CREATE TABLE donations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    amount_minor INTEGER NOT NULL,
                    currency TEXT NOT NULL,
                    payment_id TEXT NOT NULL UNIQUE,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
                """
            )
            cursor.execute(
                """
                INSERT OR IGNORE INTO donations (
                    id,
                    user_id,
                    amount_minor,
                    currency,
                    payment_id,
                    created_at
                )
                SELECT
                    id,
                    user_id,
                    amount_minor,
                    currency,
                    payment_id,
                    created_at
                FROM donations_without_fk
                """
            )
            cursor.execute("DROP TABLE donations_without_fk")

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_donations_user_id
            ON donations(user_id)
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

        if "unlimited_until" not in columns:
            cursor.execute(
                """
                ALTER TABLE users
                ADD COLUMN unlimited_until TEXT
                """
            )

        if "blocked_at" not in columns:
            cursor.execute(
                """
                ALTER TABLE users
                ADD COLUMN blocked_at TEXT
                """
            )

        if "morning_reminders_subscribed" not in columns:
            cursor.execute(
                """
                ALTER TABLE users
                ADD COLUMN morning_reminders_subscribed INTEGER NOT NULL DEFAULT 1
                """
            )

        cursor.execute(
            """
            UPDATE users
            SET morning_reminders_subscribed = 1
            WHERE morning_reminders_subscribed IS NULL
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
                datetime.now(UTC).replace(tzinfo=None).isoformat(),
            ),
        )

        cursor.execute(
            """
            UPDATE users
            SET username = ?,
                first_name = ?,
                blocked_at = NULL
            WHERE user_id = ?
            """,
            (
                username,
                first_name,
                user_id,
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
            WHERE blocked_at IS NULL
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
            WHERE (last_daily_card_date IS NULL OR last_daily_card_date != ?)
              AND (last_daily_action_date IS NULL OR last_daily_action_date != ?)
              AND blocked_at IS NULL
              AND morning_reminders_subscribed = 1
            """,
            (today, today),
        )

        rows = cursor.fetchall()

    return [row[0] for row in rows]


def set_morning_reminders_subscription(user_id: int, is_subscribed: bool) -> None:
    with get_connection() as connection:
        cursor = connection.cursor()

        cursor.execute(
            """
            UPDATE users
            SET morning_reminders_subscribed = ?
            WHERE user_id = ?
            """,
            (
                1 if is_subscribed else 0,
                user_id,
            ),
        )

        connection.commit()


def is_morning_reminders_subscribed(user_id: int) -> bool:
    with get_connection() as connection:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT morning_reminders_subscribed
            FROM users
            WHERE user_id = ?
            """,
            (user_id,),
        )

        row = cursor.fetchone()

    if not row:
        return True

    return bool(row[0])


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


def mark_user_blocked(user_id: int) -> None:
    with get_connection() as connection:
        cursor = connection.cursor()

        cursor.execute(
            """
            UPDATE users
            SET blocked_at = ?
            WHERE user_id = ?
            """,
            (
                datetime.now(UTC).replace(tzinfo=None).isoformat(),
                user_id,
            ),
        )

        connection.commit()


def create_reading(user_id: int, reading_type: str, cards: list[dict[str, Any]]) -> None:
    created_at = datetime.now(MOSCOW_TZ).replace(tzinfo=None).isoformat()
    cards_json = json.dumps(cards, ensure_ascii=False)

    with get_connection() as connection:
        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO readings (
                user_id,
                type,
                cards_json,
                created_at
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                user_id,
                reading_type,
                cards_json,
                created_at,
            ),
        )

        connection.commit()


def get_total_users_count() -> int:
    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        row = cursor.fetchone()

    return int(row[0])


def get_morning_reminders_subscribed_count() -> int:
    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT COUNT(*)
            FROM users
            WHERE morning_reminders_subscribed = 1
              AND blocked_at IS NULL
            """
        )
        row = cursor.fetchone()

    return int(row[0])


def get_morning_reminders_unsubscribed_count() -> int:
    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT COUNT(*)
            FROM users
            WHERE morning_reminders_subscribed = 0
              AND blocked_at IS NULL
            """
        )
        row = cursor.fetchone()

    return int(row[0])


def build_excluded_users_clause(
    excluded_user_ids: set[int] | None,
    column_name: str = "user_id",
) -> tuple[str, list[int]]:
    if not excluded_user_ids:
        return "", []

    excluded_user_ids_list = sorted(excluded_user_ids)
    placeholders = ", ".join("?" for _ in excluded_user_ids_list)
    return f" AND {column_name} NOT IN ({placeholders})", excluded_user_ids_list


def get_active_users_count_for_date(
    today: str,
    excluded_user_ids: set[int] | None = None,
) -> int:
    return get_active_users_count_between(
        start=f"{today}T00:00:00",
        end=f"{today}T23:59:59.999999",
        excluded_user_ids=excluded_user_ids,
    )


def get_active_users_count_between(
    start: str,
    end: str,
    excluded_user_ids: set[int] | None = None,
) -> int:
    excluded_clause, excluded_params = build_excluded_users_clause(excluded_user_ids)

    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute(
            f"""
            SELECT COUNT(DISTINCT user_id)
            FROM readings
            WHERE created_at >= ?
              AND created_at < ?
              {excluded_clause}
            """,
            [
                start,
                end,
                *excluded_params,
            ],
        )
        row = cursor.fetchone()

    return int(row[0])


def get_active_users_count_since(
    start: str,
    excluded_user_ids: set[int] | None = None,
) -> int:
    excluded_clause, excluded_params = build_excluded_users_clause(excluded_user_ids)

    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute(
            f"""
            SELECT COUNT(DISTINCT user_id)
            FROM readings
            WHERE created_at >= ?
              {excluded_clause}
            """,
            [
                start,
                *excluded_params,
            ],
        )
        row = cursor.fetchone()

    return int(row[0])


def get_cards_readings_count(excluded_user_ids: set[int] | None = None) -> int:
    return get_readings_count_by_type("card", excluded_user_ids)


def get_readings_count_by_type(
    reading_type: str,
    excluded_user_ids: set[int] | None = None,
) -> int:
    excluded_clause, excluded_params = build_excluded_users_clause(excluded_user_ids)

    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute(
            f"""
            SELECT COUNT(*)
            FROM readings
            WHERE type = ?
              {excluded_clause}
            """,
            [
                reading_type,
                *excluded_params,
            ],
        )
        row = cursor.fetchone()

    return int(row[0])


def get_spread_readings_count(excluded_user_ids: set[int] | None = None) -> int:
    excluded_clause, excluded_params = build_excluded_users_clause(excluded_user_ids)

    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute(
            f"""
            SELECT COUNT(*)
            FROM readings
            WHERE type IN ('spread', 'career', 'project')
              {excluded_clause}
            """,
            excluded_params,
        )
        row = cursor.fetchone()

    return int(row[0])


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
