# database/db_manager.py
import sqlite3
from pathlib import Path
from typing import Optional, List, Tuple, Any


class DatabaseManager:
    """Синглтон для работы с SQLite базой данных"""

    _instance: Optional['DatabaseManager'] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True

        # Путь к БД в папке с приложением
        self.db_path = Path(__file__).parent / "hflow.db"
        self._connection: Optional[sqlite3.Connection] = None
        self._create_tables()

    def _get_connection(self) -> sqlite3.Connection:
        """Возвращает соединение с БД (создаёт при необходимости)"""
        if self._connection is None:
            self._connection = sqlite3.connect(str(self.db_path))
            self._connection.row_factory = sqlite3.Row
        return self._connection

    def _create_tables(self):
        """Создаёт все таблицы, если их нет"""
        conn = self._get_connection()
        cursor = conn.cursor()

        # topics (темы и папки)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS topics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                parent_id INTEGER,
                type TEXT DEFAULT 'topic',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (parent_id) REFERENCES topics(id) ON DELETE CASCADE
            )
        ''')

        # notes (заметки)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                topic_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                content TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (topic_id) REFERENCES topics(id) ON DELETE CASCADE
            )
        ''')

        # flashcards (карточки)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS flashcards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                topic_id INTEGER NOT NULL,
                type TEXT NOT NULL,
                question TEXT,
                answer TEXT,
                content TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (topic_id) REFERENCES topics(id) ON DELETE CASCADE
            )
        ''')

        # tasks (задачи)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                topic_id INTEGER,
                title TEXT NOT NULL,
                description TEXT,
                deadline DATETIME,
                status TEXT DEFAULT 'active',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                completed_at DATETIME,
                FOREIGN KEY (topic_id) REFERENCES topics(id) ON DELETE SET NULL
            )
        ''')

        # sessions (сессии)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                topic_id INTEGER NOT NULL,
                start_time DATETIME,
                end_time DATETIME,
                duration_minutes INTEGER,
                status TEXT DEFAULT 'active',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (topic_id) REFERENCES topics(id) ON DELETE CASCADE
            )
        ''')

        # session_state_logs (логи состояния во время сессий)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS session_state_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                metric TEXT NOT NULL,
                value INTEGER NOT NULL,
                minute INTEGER NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
            )
        ''')

        # quick_notes (быстрые записи)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS quick_notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                topic_id INTEGER NOT NULL,
                content TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE,
                FOREIGN KEY (topic_id) REFERENCES topics(id) ON DELETE CASCADE
            )
        ''')

        # session_events (события внутри сессии)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS session_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                event_type TEXT NOT NULL,
                event_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                description TEXT,
                FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
            )
        ''')

        # session_music (музыка во время сессии)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS session_music (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                sound_type TEXT,
                started_at DATETIME,
                ended_at DATETIME,
                FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
            )
        ''')

        # review_sessions (сессии повторения карточек)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS review_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                topic_id INTEGER NOT NULL,
                mode TEXT DEFAULT 'sequential',
                total_cards INTEGER,
                completed_cards INTEGER DEFAULT 0,
                started_at DATETIME,
                ended_at DATETIME,
                FOREIGN KEY (topic_id) REFERENCES topics(id) ON DELETE CASCADE
            )
        ''')

        # review_answers (ответы на карточки при повторении)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS review_answers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                review_session_id INTEGER NOT NULL,
                flashcard_id INTEGER NOT NULL,
                correct BOOLEAN,
                answered_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (review_session_id) REFERENCES review_sessions(id) ON DELETE CASCADE,
                FOREIGN KEY (flashcard_id) REFERENCES flashcards(id) ON DELETE CASCADE
            )
        ''')

        # app_settings (настройки приложения)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS app_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                setting_key TEXT UNIQUE NOT NULL,
                setting_value TEXT
            )
        ''')

        # search_history (история поиска)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS search_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Добавляем начальные настройки, если их нет
        cursor.execute("SELECT COUNT(*) FROM app_settings")
        if cursor.fetchone()[0] == 0:
            default_settings = [
                ('user_name', 'Пользователь'),
                ('theme', 'light'),
                ('activity_check_interval_minutes', '15'),
                ('auto_pause_minutes', '10'),
                ('auto_save_interval_seconds', '60'),
                ('notifications_enabled', 'true'),
                ('default_sound', 'off'),
            ]
            cursor.executemany(
                "INSERT INTO app_settings (setting_key, setting_value) VALUES (?, ?)",
                default_settings
            )
        # flashcard_progress (прогресс повторения карточек)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS flashcard_progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                flashcard_id INTEGER NOT NULL UNIQUE,
                review_count INTEGER DEFAULT 0,
                correct_count INTEGER DEFAULT 0,
                last_reviewed DATETIME,
                status TEXT DEFAULT 'new',
                FOREIGN KEY (flashcard_id) REFERENCES flashcards(id) ON DELETE CASCADE
                )
            ''')

        conn.commit()

    # ========== Базовые методы execute ==========

    def execute(self, query: str, params: tuple = ()) -> sqlite3.Cursor:
        """Выполняет запрос и возвращает курсор"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        return cursor

    def fetchone(self, query: str, params: tuple = ()) -> Optional[dict]:
        """Возвращает одну строку"""
        cursor = self.execute(query, params)
        row = cursor.fetchone()
        return dict(row) if row else None

    def fetchall(self, query: str, params: tuple = ()) -> List[dict]:
        """Возвращает все строки"""
        cursor = self.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]

    def insert(self, table: str, data: dict) -> int:
        """Вставляет запись и возвращает ID"""
        columns = ', '.join(data.keys())
        placeholders = ', '.join('?' * len(data))
        query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
        cursor = self.execute(query, tuple(data.values()))
        return cursor.lastrowid

    def update(self, table: str, data: dict, where: str, where_params: tuple = ()) -> int:
        """Обновляет записи и возвращает количество изменённых"""
        set_clause = ', '.join(f"{k} = ?" for k in data.keys())
        query = f"UPDATE {table} SET {set_clause} WHERE {where}"
        cursor = self.execute(query, tuple(data.values()) + where_params)
        return cursor.rowcount

    def delete(self, table: str, where: str, params: tuple = ()) -> int:
        """Удаляет записи и возвращает количество удалённых"""
        query = f"DELETE FROM {table} WHERE {where}"
        cursor = self.execute(query, params)
        return cursor.rowcount

    def close(self):
        """Закрывает соединение с БД"""
        if self._connection:
            self._connection.close()
            self._connection = None


# Глобальный экземпляр для удобного импорта
db = DatabaseManager()
