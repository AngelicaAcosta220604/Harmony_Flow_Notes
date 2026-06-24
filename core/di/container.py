# core/di/container.py
import sys
import os
import logging

# ✅ Настройка логирования ДО всех импортов
logger = logging.getLogger(__name__)

# Добавляем корневую папку проекта в PYTHONPATH
# ✅ ИСПРАВЛЕНО: безопасное определение пути
try:
    if getattr(sys, 'frozen', False):
        # В EXE используем папку с исполняемым файлом
        project_root = os.path.dirname(sys.executable)
    else:
        # В скрипте используем корень проекта
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    logger.debug(f"Project root: {project_root}")
except Exception as e:
    logger.error(f"Ошибка определения project_root: {e}", exc_info=True)

# Теперь импорты должны работать
try:
    from database.db_manager import db
    from database.repositories.topic_repo import TopicRepository
    from database.repositories.note_repo import NoteRepository
    from database.repositories.task_repo import TaskRepository
    from database.repositories.flashcard_repo import FlashcardRepository
    from database.repositories.session_repo import SessionRepository
    from database.repositories.session_state_log_repo import SessionStateLogRepository
    from database.repositories.quick_note_repo import QuickNoteRepository
    from database.repositories.review_repo import ReviewRepository
    from database.repositories.settings_repo import SettingsRepository

    from services.time_service import TimeService
    from services.notification_service import NotificationService
    from services.hotkey_service import HotkeyService
    from services.sound_service import SoundService

    from modules.topics.controller import TopicController
    from modules.topics.analytics_controller import TopicAnalyticsController
    from modules.notes.controller import NoteController
    from modules.tasks.controller import TaskController
    from modules.tasks.calendar_controller import CalendarController
    from modules.flashcards.controller import FlashcardController
    from modules.flashcards.review_controller import ReviewController
    from modules.sessions.controller import SessionController
    from modules.sessions.state_log_controller import SessionStateLogController
    from modules.analytics.controller import AnalyticsController
    from modules.search.controller import SearchController
    from modules.music.controller import MusicController
    from modules.settings.controller import SettingsController
    from modules.dashboard.controller import DashboardController

    logger.debug("Все импорты успешно загружены")
except Exception as e:
    logger.critical(f"Критическая ошибка при импорте модулей: {e}", exc_info=True)
    raise


class Container:
    """Контейнер для dependency injection."""

    def __init__(self):
        self._initialized = False
        self._navigation = None  # Слот для хранения синглтона навигации

    def init(self):
        """Инициализирует все зависимости"""
        if self._initialized:
            return

        try:
            logger.info("Инициализация контейнера зависимостей...")

            # ==================== НАВИГАЦИЯ ====================
            # Используем отложенный импорт для предотвращения циклических зависимостей
            from core.navigation import Navigation
            self._navigation = Navigation()
            logger.debug("Navigation инициализирован")

            # ==================== РЕПОЗИТОРИИ ====================
            try:
                self.topic_repo = TopicRepository()
                self.note_repo = NoteRepository()
                self.task_repo = TaskRepository()
                self.flashcard_repo = FlashcardRepository()
                self.session_repo = SessionRepository()
                self.state_log_repo = SessionStateLogRepository()
                self.quick_note_repo = QuickNoteRepository()
                self.review_repo = ReviewRepository()
                self.settings_repo = SettingsRepository()
                logger.debug("Все репозитории инициализированы")
            except Exception as e:
                logger.critical(f"Ошибка инициализации репозиториев: {e}", exc_info=True)
                raise

            # ==================== СЕРВИСЫ ====================
            try:
                self.time_service = TimeService()
                self.notification_service = NotificationService()
                self.hotkey_service = HotkeyService()
                self.sound_service = SoundService()
                logger.debug("Все сервисы инициализированы")
            except Exception as e:
                logger.critical(f"Ошибка инициализации сервисов: {e}", exc_info=True)
                raise

            # ==================== КОНТРОЛЛЕРЫ ====================
            try:
                self.topic_controller = TopicController(
                    self.topic_repo,
                    self.note_repo,
                    self.task_repo,
                    self.flashcard_repo,
                    self.session_repo
                )
                self.topic_analytics_controller = TopicAnalyticsController(
                    self.session_repo, self.task_repo, self.note_repo, self.flashcard_repo
                )
                self.note_controller = NoteController(self.note_repo)
                self.task_controller = TaskController(
                    self.task_repo, self.topic_repo, self.notification_service
                )
                self.calendar_controller = CalendarController(self.task_controller)
                self.flashcard_controller = FlashcardController(self.flashcard_repo)
                self.review_controller = ReviewController(self.review_repo, self.flashcard_repo)
                self.session_controller = SessionController(
                    self.session_repo, self.state_log_repo, self.quick_note_repo, self.topic_repo
                )
                self.state_log_controller = SessionStateLogController(self.state_log_repo)
                self.analytics_controller = AnalyticsController(
                    self.session_repo, self.task_repo, self.note_repo, self.flashcard_repo
                )
                self.search_controller = SearchController(
                    self.topic_repo, self.note_repo, self.task_repo, self.flashcard_repo
                )
                self.music_controller = MusicController(self.sound_service)
                self.settings_controller = SettingsController(self.settings_repo)
                self.dashboard_controller = DashboardController(
                    self.topic_repo, self.task_repo, self.session_repo,
                    self.note_repo, self.flashcard_repo, self.settings_repo
                )
                logger.debug("Все контроллеры инициализированы")
            except Exception as e:
                logger.critical(f"Ошибка инициализации контроллеров: {e}", exc_info=True)
                raise

            self._initialized = True
            logger.info("Контейнер зависимостей успешно инициализирован")

        except Exception as e:
            logger.critical(f"Критическая ошибка инициализации контейнера: {e}", exc_info=True)
            raise RuntimeError(f"Невозможно инициализировать контейнер зависимостей: {e}") from e


# Глобальный экземпляр контейнера
container = Container()