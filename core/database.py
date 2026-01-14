"""
Управление базой данных
"""
import sqlite3
from pathlib import Path
from typing import Optional, List, Dict, Any
import logging
from .config import Config

logger = logging.getLogger(__name__)


class Database:
    """Гибкий менеджер базы данных"""

    def __init__(self, db_path: str = None):
        self.db_path = db_path or Config.DB_PATH
        self._ensure_db_directory()
        self.connection = None

    def _ensure_db_directory(self):
        """Создает директорию для БД если её нет"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

    def connect(self) -> sqlite3.Connection:
        """Устанавливает соединение с БД"""
        try:
            self.connection = sqlite3.connect(self.db_path)
            self.connection.row_factory = sqlite3.Row
            logger.info(f"Connected to database: {self.db_path}")
            return self.connection
        except sqlite3.Error as e:
            logger.error(f"Database connection error: {e}")
            raise

    def execute_query(self, query: str, params: tuple = None) -> sqlite3.Cursor:
        """Выполняет SQL запрос"""
        try:
            cursor = self.connection.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return cursor
        except sqlite3.Error as e:
            logger.error(f"Query execution error: {e}")
            raise

    def create_table(self, table_name: str, columns: Dict[str, str]):
        """
        Создает таблицу с указанными колонками
        columns: {'column_name': 'INTEGER PRIMARY KEY', 'name': 'TEXT', ...}
        """
        columns_def = ", ".join([f"{name} {type}" for name, type in columns.items()])
        query = f"CREATE TABLE IF NOT EXISTS {table_name} ({columns_def})"
        self.execute_query(query)
        self.connection.commit()

    def insert(self, table_name: str, data: Dict[str, Any]) -> int:
        """Вставляет запись в таблицу"""
        columns = ", ".join(data.keys())
        placeholders = ", ".join(["?"] * len(data))
        query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"

        cursor = self.execute_query(query, tuple(data.values()))
        self.connection.commit()
        return cursor.lastrowid

    def select(self, table_name: str,
               columns: List[str] = None,
               where: str = None,
               params: tuple = None) -> List[Dict]:
        """Выбирает записи из таблицы"""
        cols = "*" if not columns else ", ".join(columns)
        query = f"SELECT {cols} FROM {table_name}"

        if where:
            query += f" WHERE {where}"

        cursor = self.execute_query(query, params)
        return [dict(row) for row in cursor.fetchall()]

    def update(self, table_name: str, data: Dict[str, Any],
               where: str, where_params: tuple) -> bool:
        """Обновляет записи в таблице"""
        set_clause = ", ".join([f"{key} = ?" for key in data.keys()])
        query = f"UPDATE {table_name} SET {set_clause} WHERE {where}"
        params = tuple(data.values()) + where_params

        cursor = self.execute_query(query, params)
        self.connection.commit()
        return cursor.rowcount > 0

    def delete(self, table_name: str, where: str, params: tuple) -> bool:
        """Удаляет записи из таблицы"""
        query = f"DELETE FROM {table_name} WHERE {where}"
        cursor = self.execute_query(query, params)
        self.connection.commit()
        return cursor.rowcount > 0

    def close(self):
        """Закрывает соединение с БД"""
        if self.connection:
            self.connection.close()
            logger.info("Database connection closed")


# Глобальный экземпляр базы данных
db_manager = Database()