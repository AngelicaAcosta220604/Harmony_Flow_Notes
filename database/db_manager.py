# database/db_manager.py
import sqlite3
import sys
import logging
from pathlib import Path
from typing import Optional, List, Tuple, Any

from utils.resource_paths import get_db_path

# Настройка логирования
logger = logging.getLogger(__name__)


class DatabaseManager:
    """Менеджер базы данных с безопасной инициализацией"""

    # Классовая переменная для отслеживания инициализации
    _initialized: bool = False

    def __init__(self):
        # Проверяем классовую переменную, а не атрибут экземпляра
        if DatabaseManager._initialized:
            return

        try:
            # Получаем путь к БД
            self.db_path = get_db_path()
            logger.info(f"Путь к БД: {self.db_path}")

            # Создаем директорию, если она не существует
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Директория БД проверена: {self.db_path.parent}")

            self._connection: Optional[sqlite3.Connection] = None

            # Создаем таблицы
            self._create_tables()

            # Помечаем как инициализированный
            DatabaseManager._initialized = True
            logger.info("DatabaseManager успешно инициализирован")

        except PermissionError as e:
            logger.error(f"Нет прав для создания БД по пути {self.db_path}: {e}")
            raise RuntimeError(
                f"Невозможно создать базу данных по пути {self.db_path}. "
                f"Проверьте права доступа или запустите приложение от имени администратора."
            ) from e
        except OSError as e:
            logger.error(f"Ошибка файловой системы при создании БД: {e}")
            raise RuntimeError(
                f"Ошибка при создании базы данных: {e}. "
                f"Проверьте наличие свободного места на диске."
            ) from e
        except Exception as e:
            logger.error(f"Неожиданная ошибка при инициализации БД: {e}", exc_info=True)
            raise RuntimeError(f"Критическая ошибка при инициализации базы данных: {e}") from e

    def _get_connection(self) -> sqlite3.Connection:
        """Возвращает соединение с БД (создаёт при необходимости)"""
        try:
            if self._connection is None:
                self._connection = sqlite3.connect(str(self.db_path))
                self._connection.row_factory = sqlite3.Row
                # Включаем поддержку внешних ключей
                self._connection.execute("PRAGMA foreign_keys = ON")
                logger.debug("Соединение с БД установлено")
            return self._connection
        except sqlite3.Error as e:
            logger.error(f"Ошибка подключения к БД: {e}")
            raise RuntimeError(f"Невозможно подключиться к базе данных: {e}") from e

    def _create_tables(self):
        """Создаёт все таблицы, если их нет"""
        try:
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
                    focus INTEGER DEFAULT 50,
                    energy INTEGER DEFAULT 50,
                    interest INTEGER DEFAULT 50,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (topic_id) REFERENCES topics(id) ON DELETE CASCADE
                )
            ''')

            cursor.execute("PRAGMA table_info(sessions)")
            columns = [row[1] for row in cursor.fetchall()]

            if 'focus' not in columns:
                cursor.execute("ALTER TABLE sessions ADD COLUMN focus INTEGER DEFAULT 50")
            if 'energy' not in columns:
                cursor.execute("ALTER TABLE sessions ADD COLUMN energy INTEGER DEFAULT 50")
            if 'interest' not in columns:
                cursor.execute("ALTER TABLE sessions ADD COLUMN interest INTEGER DEFAULT 50")
            if 'elapsed_seconds' not in columns:
                cursor.execute("ALTER TABLE sessions ADD COLUMN elapsed_seconds INTEGER DEFAULT 0")

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
                    ('user_name', ''),
                    ('theme', 'light'),
                    ('activity_check_interval_minutes', '15'),
                    ('auto_pause_minutes', '10'),
                    ('auto_save_interval_seconds', '60'),
                    ('notifications_enabled', 'true'),
                    ('default_sound', 'off'),
                    ('onboarding_completed', 'false'),
                ]
                cursor.executemany(
                    "INSERT INTO app_settings (setting_key, setting_value) VALUES (?, ?)",
                    default_settings
                )
            else:
                # Для уже существующих БД добавляем флаг, если его нет
                cursor.execute(
                    "SELECT COUNT(*) FROM app_settings WHERE setting_key = 'onboarding_completed'"
                )
                if cursor.fetchone()[0] == 0:
                    cursor.execute(
                        "INSERT INTO app_settings (setting_key, setting_value) VALUES (?, ?)",
                        ('onboarding_completed', 'true')
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

            # session_intervals (интервалы активной работы)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS session_intervals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER NOT NULL,
                    start_time DATETIME,
                    end_time DATETIME,
                    duration_seconds INTEGER DEFAULT 0,
                    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
                )
            ''')

            conn.commit()
            logger.debug("Все таблицы созданы/проверены")

        except sqlite3.Error as e:
            logger.error(f"Ошибка SQLite при создании таблиц: {e}", exc_info=True)
            raise RuntimeError(f"Ошибка базы данных при создании таблиц: {e}") from e
        except Exception as e:
            logger.error(f"Неожиданная ошибка при создании таблиц: {e}", exc_info=True)
            raise RuntimeError(f"Критическая ошибка при создании таблиц: {e}") from e

    # ========== Базовые методы execute ==========

    def execute(self, query: str, params: tuple = ()) -> sqlite3.Cursor:
        """Выполняет запрос и возвращает курсор"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor
        except sqlite3.Error as e:
            logger.error(f"Ошибка выполнения запроса: {query}, params: {params}, error: {e}")
            raise RuntimeError(f"Ошибка выполнения запроса к БД: {e}") from e

    def fetchone(self, query: str, params: tuple = ()) -> Optional[dict]:
        """Возвращает одну строку"""
        try:
            cursor = self.execute(query, params)
            row = cursor.fetchone()
            return dict(row) if row else None
        except Exception as e:
            logger.error(f"Ошибка fetchone: {query}, error: {e}")
            return None

    def fetchall(self, query: str, params: tuple = ()) -> List[dict]:
        """Возвращает все строки"""
        try:
            cursor = self.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Ошибка fetchall: {query}, error: {e}")
            return []

    def insert(self, table: str, data: dict) -> int:
        """Вставляет запись и возвращает ID"""
        try:
            columns = ', '.join(data.keys())
            placeholders = ', '.join('?' * len(data))
            query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
            cursor = self.execute(query, tuple(data.values()))
            return cursor.lastrowid
        except Exception as e:
            logger.error(f"Ошибка insert в таблицу {table}: {e}")
            raise

    def update(self, table: str, data: dict, where: str, where_params: tuple = ()) -> int:
        """Обновляет записи и возвращает количество изменённых"""
        try:
            set_clause = ', '.join(f"{k} = ?" for k in data.keys())
            query = f"UPDATE {table} SET {set_clause} WHERE {where}"
            cursor = self.execute(query, tuple(data.values()) + where_params)
            return cursor.rowcount
        except Exception as e:
            logger.error(f"Ошибка update в таблице {table}: {e}")
            raise

    def delete(self, table: str, where: str, params: tuple = ()) -> int:
        """Удаляет записи и возвращает количество удалённых"""
        try:
            query = f"DELETE FROM {table} WHERE {where}"
            cursor = self.execute(query, params)
            return cursor.rowcount
        except Exception as e:
            logger.error(f"Ошибка delete из таблицы {table}: {e}")
            raise

    def close(self):
        """Закрывает соединение с БД"""
        try:
            if self._connection:
                self._connection.close()
                self._connection = None
                logger.debug("Соединение с БД закрыто")
        except Exception as e:
            logger.error(f"Ошибка закрытия соединения: {e}")


# Глобальный экземпляр для удобного импорта
# ВАЖНО: Этот экземпляр создается при первом импорте модуля
try:
    db = DatabaseManager()
except Exception as e:
    logger.critical(f"Критическая ошибка при создании глобального экземпляра БД: {e}", exc_info=True)
    # Создаем "пустой" объект, чтобы импорты не падали
    db = None
    raise RuntimeError("Невозможно инициализировать базу данных. Приложение не может быть запущено.") from e