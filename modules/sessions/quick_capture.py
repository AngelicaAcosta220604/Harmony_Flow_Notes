# modules/sessions/quick_capture.py
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton,
    QLabel, QListWidget, QListWidgetItem, QWidget, QMessageBox
)
from PySide6.QtCore import Qt, Signal


class QuickNoteDialog(QDialog):
    """
    Диалог для быстрой записи во время сессии.
    """

    note_saved = Signal(str)  # content

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        """Настраивает интерфейс"""
        self.setWindowTitle("Быстрая запись")
        self.setModal(True)
        self.setFixedSize(400, 250)

        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # Заголовок
        title_label = QLabel("✏️ Быстрая запись")
        title_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(title_label)

        # Поле ввода
        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText("Введите мысль, идею или заметку...")
        self.text_edit.setMinimumHeight(120)
        layout.addWidget(self.text_edit)

        # Кнопки
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.save_btn = QPushButton("💾 Сохранить")
        self.cancel_btn = QPushButton("Отмена")

        button_layout.addWidget(self.save_btn)
        button_layout.addWidget(self.cancel_btn)

        layout.addLayout(button_layout)

    def _connect_signals(self):
        """Подключает сигналы"""
        self.save_btn.clicked.connect(self._on_save)
        self.cancel_btn.clicked.connect(self.reject)

    def _on_save(self):
        """Обработчик сохранения"""
        content = self.text_edit.toPlainText().strip()
        if content:
            self.note_saved.emit(content)
            self.accept()
        else:
            QMessageBox.warning(self, "Ошибка", "Введите текст записи")

    def clear(self):
        """Очищает поле ввода"""
        self.text_edit.clear()


class QuickNotesViewer(QWidget):
    """
    Виджет для просмотра быстрых записей после сессии.
    """

    note_converted = Signal(int, str, int)  # (note_id, convert_type, target_id)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        """Настраивает интерфейс"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.title_label = QLabel("📝 Быстрые записи")
        self.title_label.setStyleSheet("font-weight: bold; margin-bottom: 5px;")
        layout.addWidget(self.title_label)

        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget)

    def set_quick_notes(self, notes: list):
        """
        Устанавливает список быстрых записей

        Args:
            notes: Список словарей с ключами 'id', 'content', 'created_at'
        """
        self.list_widget.clear()
        self._notes = notes

        for note in notes:
            item = QListWidgetItem()

            # Отображаем время и текст
            time_str = note.get('created_at', '')[:16] if note.get('created_at') else ""
            preview = note['content'][:60] + "..." if len(note['content']) > 60 else note['content']

            item.setText(f"[{time_str}] {preview}")
            item.setData(Qt.UserRole, note['id'])
            item.setToolTip(note['content'])

            self.list_widget.addItem(item)

    def get_selected_note_id(self) -> int:
        """Возвращает ID выбранной записи"""
        current = self.list_widget.currentItem()
        if current:
            return current.data(Qt.UserRole)
        return -1

    def get_selected_note_content(self) -> str:
        """Возвращает содержимое выбранной записи"""
        current = self.list_widget.currentItem()
        if current:
            note_id = current.data(Qt.UserRole)
            for note in self._notes:
                if note['id'] == note_id:
                    return note['content']
        return ""

    def clear(self):
        """Очищает список"""
        self.list_widget.clear()
        self._notes = []