# core/event_bus.py
from typing import Dict, List, Callable, Any
from PySide6.QtCore import QObject, Signal


class EventBus(QObject):
    """
    Простая событийная шина для взаимодействия между модулями.
    Позволяет отправлять и подписываться на события без прямой связи.
    """

    # Сигналы для основных событий
    topic_created = Signal(int)  # (topic_id)
    topic_deleted = Signal(int)  # (topic_id)
    topic_updated = Signal(int)  # (topic_id)

    note_created = Signal(int)  # (note_id)
    note_deleted = Signal(int)  # (note_id)
    note_updated = Signal(int)  # (note_id)

    task_created = Signal(int)  # (task_id)
    task_completed = Signal(int)  # (task_id)
    task_deleted = Signal(int)  # (task_id)

    flashcard_created = Signal(int)  # (flashcard_id)
    flashcard_deleted = Signal(int)  # (flashcard_id)

    session_started = Signal(int)  # (session_id)
    session_ended = Signal(int)  # (session_id)

    settings_changed = Signal(str)  # (setting_key)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._custom_handlers: Dict[str, List[Callable]] = {}

    def on(self, event_name: str, callback: Callable):
        """Подписывается на пользовательское событие"""
        if event_name not in self._custom_handlers:
            self._custom_handlers[event_name] = []
        self._custom_handlers[event_name].append(callback)

    def off(self, event_name: str, callback: Callable):
        """Отписывается от события"""
        if event_name in self._custom_handlers:
            if callback in self._custom_handlers[event_name]:
                self._custom_handlers[event_name].remove(callback)

    def emit(self, event_name: str, *args, **kwargs):
        """Отправляет пользовательское событие"""
        if event_name in self._custom_handlers:
            for callback in self._custom_handlers[event_name]:
                callback(*args, **kwargs)


# Глобальный экземпляр шины событий
event_bus = EventBus()