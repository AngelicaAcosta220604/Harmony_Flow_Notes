# core/di/container.py
import sys
import os

# Добавляем корневую папку проекта в PYTHONPATH
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

print(f"[DEBUG] Project root: {project_root}")
print(f"[DEBUG] sys.path: {sys.path}")

# Теперь импорты должны работать
from datebase.db_manager import db
from datebase.repositories.topic_repo import TopicRepository
from datebase.repositories.note_repo import NoteRepository
from datebase.repositories.task_repo import TaskRepository
from datebase.repositories.flashcard_repo import FlashcardRepository
from datebase.repositories.session_repo import SessionRepository
from datebase.repositories.session_state_log_repo import SessionStateLogRepository
from datebase.repositories.quick_note_repo import QuickNoteRepository
from datebase.repositories.review_repo import ReviewRepository
from datebase.repositories.settings_repo import SettingsRepository

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


class Container:
    """Контейнер для dependency injection."""

    def __init__(self):
        self._initialized = False
        self._navigation = None  # Слот для хранения синглтона навигации

    def init(self):
        """Инициализирует все зависимости"""
        if self._initialized:
            return

        # ==================== НАВИГАЦИЯ ====================
        # Используем отложенный импорт для предотвращения циклических зависимостей
        from core.navigation import Navigation
        self._navigation = Navigation()

        # ==================== РЕПОЗИТОРИИ ====================
        self.topic_repo = TopicRepository()
        self.note_repo = NoteRepository()
        self.task_repo = TaskRepository()
        self.flashcard_repo = FlashcardRepository()
        self.session_repo = SessionRepository()
        self.state_log_repo = SessionStateLogRepository()
        self.quick_note_repo = QuickNoteRepository()
        self.review_repo = ReviewRepository()
        self.settings_repo = SettingsRepository()

        # ==================== СЕРВИСЫ ====================
        self.time_service = TimeService()
        self.notification_service = NotificationService()
        self.hotkey_service = HotkeyService()
        self.sound_service = SoundService()

        # ==================== КОНТРОЛЛЕРЫ ====================
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

        self._initialized = True




# Глобальный экземпляр контейнера
container = Container()