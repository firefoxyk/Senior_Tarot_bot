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
                created_at TEXT
            )
            """
        )

        connection.commit()


def add_user(user_id: int, username: str | None, first_name: str | None) -> None:
    """
    Добавляет пользователя в БД.
    При повторном /start пользователь не дублируется.
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