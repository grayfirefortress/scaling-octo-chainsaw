import sqlite3
from datetime import datetime
from typing import Optional


class Database:
    """Класс для работы с базой данных SQLite."""

    def __init__(self, db_path: str = "bot.db") -> None:
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_db()

    def _init_db(self) -> None:
        """Создаёт таблицы, если их нет."""
        with self.conn:
            self.conn.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    first_seen TEXT
                )
                """
            )
            self.conn.execute(
                """
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    username TEXT,
                    text TEXT,
                    created_at TEXT
                )
                """
            )

    def register_user(
        self,
        user_id: int,
        username: Optional[str],
        first_name: Optional[str],
        last_name: Optional[str],
    ) -> None:
        """Регистрирует пользователя, если его ещё нет."""
        with self.conn:
            self.conn.execute(
                """
                INSERT OR IGNORE INTO users (user_id, username, first_name, last_name, first_seen)
                VALUES (?, ?, ?, ?, ?)
                """,
                (user_id, username, first_name, last_name, datetime.now().isoformat()),
            )

    def save_message(
        self,
        user_id: int,
        username: Optional[str],
        text: str,
    ) -> None:
        """Сохраняет сообщение пользователя."""
        with self.conn:
            self.conn.execute(
                """
                INSERT INTO messages (user_id, username, text, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (user_id, username, text, datetime.now().isoformat()),
            )

    def get_unique_users_count(self) -> int:
        """Возвращает количество уникальных пользователей."""
        row = self.conn.execute("SELECT COUNT(*) AS cnt FROM users").fetchone()
        return row["cnt"]

    def get_all_users(self) -> list:
        """Возвращает список всех пользователей."""
        return self.conn.execute(
            "SELECT user_id, username, first_name, last_name, first_seen FROM users"
        ).fetchall()

    def get_all_messages(self) -> list:
        """Возвращает список всех сообщений."""
        return self.conn.execute(
            "SELECT user_id, username, text, created_at FROM messages ORDER BY id"
        ).fetchall()