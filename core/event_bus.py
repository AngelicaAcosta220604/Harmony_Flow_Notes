# core/event_bus.py
import logging
from typing import Dict, List, Callable, Any
from PySide6.QtCore import QObject, Signal

# Настройка логирования
logger = logging.getLogger(__name__)


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
    task_updated = Signal(int)  # task_id

    flashcard_created = Signal(int)  # (flashcard_id)
    flashcard_deleted = Signal(int)  # (flashcard_id)
    flashcard_updated = Signal(int)  # flashcard_id

    # Навигация
    navigate_to = Signal(str, object)  # section_name, data

    session_started = Signal(int)  # (session_id)
    session_ended = Signal(int)  # (session_id)

    settings_changed = Signal(str)  # (setting_key)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._custom_handlers: Dict[str, List[Callable]] = {}
        logger.debug("EventBus инициализирован")

    def on(self, event_name: str, callback: Callable):
        """Подписывается на пользовательское событие"""
        try:
            if event_name not in self._custom_handlers:
                self._custom_handlers[event_name] = []
            self._custom_handlers[event_name].append(callback)
            logger.debug(f"Подписка на событие: {event_name}")
        except Exception as e:
            logger.error(f"Ошибка подписки на событие {event_name}: {e}")

    def off(self, event_name: str, callback: Callable):
        """Отписывается от события"""
        try:
            if event_name in self._custom_handlers:
                if callback in self._custom_handlers[event_name]:
                    self._custom_handlers[event_name].remove(callback)
                    logger.debug(f"Отписка от события: {event_name}")
        except Exception as e:
            logger.error(f"Ошибка отписки от события {event_name}: {e}")

    def emit(self, event_name: str, *args, **kwargs):
        """Отправляет пользовательское событие"""
        try:
            if event_name in self._custom_handlers:
                for callback in self._custom_handlers[event_name]:
                    try:
                        callback(*args, **kwargs)
                    except Exception as e:
                        logger.error(f"Ошибка в обработчике события {event_name}: {e}")
        except Exception as e:
            logger.error(f"Ошибка отправки события {event_name}: {e}")


# Глобальный экземпляр - создаем лениво
_event_bus_instance = None


def get_event_bus() -> EventBus:
    """Возвращает глобальный экземпляр EventBus"""
    global _event_bus_instance
    try:
        if _event_bus_instance is None:
            _event_bus_instance = EventBus()
            logger.info("Глобальный EventBus создан")
        return _event_bus_instance
    except Exception as e:
        logger.critical(f"Критическая ошибка при создании EventBus: {e}", exc_info=True)
        raise RuntimeError(f"Невозможно создать EventBus: {e}") from e


# Для обратной совместимости создаем прокси
class EventBusProxy:
    """Прокси для ленивой инициализации EventBus"""

    def __getattr__(self, name):
        """Делегирует все атрибуты к реальному EventBus"""
        try:
            return getattr(get_event_bus(), name)
        except Exception as e:
            logger.error(f"Ошибка доступа к атрибуту {name} EventBus: {e}")
            raise


# Глобальный экземпляр для удобного импорта
event_bus = EventBusProxy()