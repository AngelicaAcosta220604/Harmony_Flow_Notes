# core/navigation.py
from enum import Enum
from typing import Optional, Callable, Any
from PySide6.QtCore import QObject, Signal


class NavSection(Enum):
    """Секции навигации в главном окне"""
    DASHBOARD = "dashboard"
    TOPICS = "topics"
    FOCUS = "focus"
    TASKS = "tasks"
    CALENDAR = "calendar"
    FLASHCARDS = "flashcards"
    ANALYTICS = "analytics"
    SEARCH = "search"
    SETTINGS = "settings"


class Navigation(QObject):
    """
    Менеджер навигации между экранами.
    """

    # Сигнал при смене секции
    section_changed = Signal(NavSection, object)  # (section, data)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_section: Optional[NavSection] = None
        self._history: list = []

    def navigate_to(self, section: NavSection, data: Any = None):
        """
        Переходит к указанной секции

        Args:
            section: Целевая секция
            data: Дополнительные данные (например, ID темы для открытия)
        """
        # Сохраняем в историю
        if self._current_section is not None:
            self._history.append({
                'section': self._current_section,
                'data': None
            })

        self._current_section = section
        self.section_changed.emit(section, data)

    def go_back(self) -> bool:
        """Возвращается к предыдущей секции"""
        if not self._history:
            return False

        previous = self._history.pop()
        self._current_section = previous['section']
        self.section_changed.emit(previous['section'], previous['data'])
        return True

    def get_current_section(self) -> Optional[NavSection]:
        """Возвращает текущую секцию"""
        return self._current_section

    def clear_history(self):
        """Очищает историю навигации"""
        self._history.clear()