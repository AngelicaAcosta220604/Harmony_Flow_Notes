# services/hotkey_service.py
from typing import Dict, Callable, Optional
from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QKeySequence, QShortcut
import logging

# Настройка логирования
logger = logging.getLogger(__name__)


class HotkeyService(QObject):
    """Сервис для управления горячими клавишами"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._shortcuts: Dict[str, QShortcut] = {}
        self._parent_widget = parent
        logger.debug("HotkeyService инициализирован")

    def set_parent(self, parent_widget):
        """Устанавливает родительский виджет для шорткатов"""
        self._parent_widget = parent_widget
        logger.debug(f"Установлен родительский виджет для шорткатов")

    def register(self, key: str, callback: Callable, name: str = None) -> bool:
        """
        Регистрирует горячую клавишу

        Args:
            key: Комбинация клавиш (например, "Ctrl+S")
            callback: Функция для вызова
            name: Идентификатор шортката

        Returns:
            True если успешно, иначе False
        """
        try:
            if not self._parent_widget:
                logger.warning(f"Невозможно зарегистрировать {key}: нет родительского виджета")
                return False

            sequence = QKeySequence(key)
            shortcut = QShortcut(sequence, self._parent_widget)
            shortcut.activated.connect(callback)

            shortcut_name = name or key
            self._shortcuts[shortcut_name] = shortcut
            logger.info(f"Зарегистрирована горячая клавиша '{shortcut_name}': {key}")
            return True
        except Exception as e:
            logger.error(f"Ошибка регистрации горячей клавиши '{key}': {e}", exc_info=True)
            return False

    def unregister(self, name: str) -> bool:
        """Удаляет горячую клавишу по имени"""
        try:
            if name in self._shortcuts:
                self._shortcuts[name].activated.disconnect()
                self._shortcuts[name].deleteLater()
                del self._shortcuts[name]
                logger.info(f"Удалена горячая клавиша '{name}'")
                return True
            else:
                logger.warning(f"Горячая клавиша '{name}' не найдена для удаления")
            return False
        except Exception as e:
            logger.error(f"Ошибка удаления горячей клавиши '{name}': {e}", exc_info=True)
            return False

    def unregister_all(self):
        """Удаляет все горячие клавиши"""
        try:
            for name, shortcut in self._shortcuts.items():
                try:
                    shortcut.activated.disconnect()
                    shortcut.deleteLater()
                except Exception as e:
                    logger.warning(f"Ошибка удаления шортката '{name}': {e}")
            self._shortcuts.clear()
            logger.info(f"Удалены все горячие клавиши ({len(self._shortcuts)} было)")
        except Exception as e:
            logger.error(f"Ошибка удаления всех горячих клавиш: {e}", exc_info=True)

    def is_registered(self, name: str) -> bool:
        """Проверяет, зарегистрирована ли горячая клавиша"""
        return name in self._shortcuts

    def get_shortcut_keys(self) -> Dict[str, str]:
        """
        Возвращает словарь стандартных горячих клавиш
        """
        return {
            "save": "Ctrl+S",
            "new_note": "Ctrl+N",
            "new_task": "Ctrl+T",
            "new_flashcard": "Ctrl+F",
            "start_session": "Ctrl+Shift+S",
            "pause_session": "Ctrl+Shift+P",
            "quick_note": "Ctrl+Shift+Q",
            "search": "Ctrl+F",
            "undo": "Ctrl+Z",
            "redo": "Ctrl+Y",
            "bold": "Ctrl+B",
            "italic": "Ctrl+I",
            "underline": "Ctrl+U",
        }

    def register_all_standard(self, callbacks: Dict[str, Callable]) -> Dict[str, bool]:
        """
        Регистрирует все стандартные горячие клавиши

        Args:
            callbacks: Словарь {имя_функции: callback}

        Returns:
            Словарь результатов регистрации
        """
        try:
            standard_keys = self.get_shortcut_keys()
            results = {}

            for name, callback in callbacks.items():
                if name in standard_keys:
                    results[name] = self.register(standard_keys[name], callback, name)
                else:
                    logger.warning(f"Неизвестная стандартная клавиша: {name}")
                    results[name] = False

            logger.info(f"Зарегистрировано {sum(results.values())} из {len(results)} стандартных горячих клавиш")
            return results
        except Exception as e:
            logger.error(f"Ошибка регистрации всех стандартных горячих клавиш: {e}", exc_info=True)
            return {}