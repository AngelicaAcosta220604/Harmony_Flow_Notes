# services/hotkey_service.py
from typing import Dict, Callable, Optional
from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QKeySequence, QShortcut


class HotkeyService(QObject):
    """Сервис для управления горячими клавишами"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._shortcuts: Dict[str, QShortcut] = {}
        self._parent_widget = parent

    def set_parent(self, parent_widget):
        """Устанавливает родительский виджет для шорткатов"""
        self._parent_widget = parent_widget

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
        if not self._parent_widget:
            return False

        try:
            sequence = QKeySequence(key)
            shortcut = QShortcut(sequence, self._parent_widget)
            shortcut.activated.connect(callback)

            shortcut_name = name or key
            self._shortcuts[shortcut_name] = shortcut
            return True
        except Exception as e:
            print(f"[HotkeyService] Ошибка регистрации {key}: {e}")
            return False

    def unregister(self, name: str) -> bool:
        """Удаляет горячую клавишу по имени"""
        if name in self._shortcuts:
            self._shortcuts[name].activated.disconnect()
            self._shortcuts[name].deleteLater()
            del self._shortcuts[name]
            return True
        return False

    def unregister_all(self):
        """Удаляет все горячие клавиши"""
        for name, shortcut in self._shortcuts.items():
            shortcut.activated.disconnect()
            shortcut.deleteLater()
        self._shortcuts.clear()

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
        standard_keys = self.get_shortcut_keys()
        results = {}

        for name, callback in callbacks.items():
            if name in standard_keys:
                results[name] = self.register(standard_keys[name], callback, name)

        return results