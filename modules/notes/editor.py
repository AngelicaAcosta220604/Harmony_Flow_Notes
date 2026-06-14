# modules/notes/editor.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
    QFileDialog, QLabel
)
from PySide6.QtCore import Qt, Signal, QTimer

from .controller import NoteController
from .widgets import RichTextEditor, EditorToolbar
from widgets import SilentMessageBox


class NoteEditorView(QWidget):
    """Редактор заметок с полноценным текстовым редактором."""

    note_saved = Signal(int)
    note_deleted = Signal(int)

    def __init__(self, controller: NoteController, parent=None):
        super().__init__(parent)
        self._controller = controller
        self._current_note_id = None
        self._current_topic_id = None
        self._auto_save_timer = QTimer()
        self._is_modified = False
        self._setup_ui()
        self._connect_signals()
        self._setup_auto_save()

    def _setup_ui(self):
        """Настраивает интерфейс"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Сначала создаём редактор
        self.editor = RichTextEditor()

        # Потом панель инструментов (передаём редактор)
        self.toolbar = EditorToolbar(self.editor)

        layout.addWidget(self.toolbar)
        layout.addWidget(self.editor)

        # Нижняя панель
        bottom_layout = QHBoxLayout()
        bottom_layout.setContentsMargins(10, 5, 10, 5)

        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("Заголовок заметки...")
        bottom_layout.addWidget(self.title_edit, 1)

        self.save_btn = QPushButton("💾 Сохранить (Ctrl+S)")
        self.save_btn.setFixedWidth(150)
        bottom_layout.addWidget(self.save_btn)

        self.delete_btn = QPushButton("🗑️ Удалить")
        self.delete_btn.setFixedWidth(100)
        bottom_layout.addWidget(self.delete_btn)

        self.import_btn = QPushButton("📁 Импорт из .txt")
        self.import_btn.setFixedWidth(120)
        bottom_layout.addWidget(self.import_btn)

        layout.addLayout(bottom_layout)

        # Статус бар
        self.status_label = QLabel("Готов к работе")
        self.status_label.setStyleSheet("color: #888888; font-size: 10px; padding: 2px 5px;")
        layout.addWidget(self.status_label)

    def _connect_signals(self):
        self.save_btn.clicked.connect(self.save_note)
        self.delete_btn.clicked.connect(self.delete_note)
        self.import_btn.clicked.connect(self.import_from_file)
        self.editor.content_changed.connect(self._on_content_changed)
        self.title_edit.textChanged.connect(self._on_content_changed)

    def _setup_auto_save(self):
        self._auto_save_timer.timeout.connect(self._auto_save)
        self._auto_save_timer.setInterval(60000)

    def set_auto_save_interval(self, seconds: int):
        self._auto_save_timer.setInterval(seconds * 1000)

    def _on_content_changed(self):
        self._is_modified = True
        self.status_label.setText("✏️ Есть несохранённые изменения")
        if not self._auto_save_timer.isActive():
            self._auto_save_timer.start()

    def _auto_save(self):
        if self._is_modified and self._current_note_id:
            self.save_note(silent=True)

    def save_note(self, silent: bool = False):
        title = self.title_edit.text().strip()
        if not title:
            title = f"Заметка от {self._get_current_date()}"

        content = self.editor.get_html()

        if self._current_note_id:
            success = self._controller.update_note(
                self._current_note_id,
                title=title,
                content=content
            )
            if success:
                self._is_modified = False
                self.status_label.setText("✅ Сохранено")
                if not silent:
                    self.note_saved.emit(self._current_note_id)
                self._auto_save_timer.stop()
                QTimer.singleShot(2000, lambda: self.status_label.setText("Готов к работе"))
        else:
            self.status_label.setText("⚠️ Выберите тему для сохранения")

    def create_new_note(self, topic_id: int):
        self._current_note_id = None
        self._current_topic_id = topic_id
        self.title_edit.clear()
        self.editor.clear_content()
        self._is_modified = False
        self.status_label.setText("Новая заметка. Начните писать...")

    def load_note(self, note_id: int):
        note = self._controller.get_note(note_id)
        if not note:
            SilentMessageBox.warning(self, "Ошибка", "Заметка не найдена")
            return

        self._current_note_id = note.id
        self._current_topic_id = note.topic_id
        self.title_edit.setText(note.title)
        self.editor.set_html(note.content)
        self._is_modified = False
        self.status_label.setText(f"Заметка «{note.title}» загружена")
        self._auto_save_timer.stop()

    def delete_note(self):
        if not self._current_note_id:
            return

        reply = SilentMessageBox.question(
            self, "Подтверждение удаления",
            f"Удалить заметку «{self.title_edit.text()}»?"
        )

        if reply == SilentMessageBox.Yes:
            success = self._controller.delete_note(self._current_note_id)
            if success:
                note_id = self._current_note_id
                self._current_note_id = None
                self.title_edit.clear()
                self.editor.clear_content()
                self._is_modified = False
                self.status_label.setText("Заметка удалена")
                self.note_deleted.emit(note_id)
            else:
                SilentMessageBox.warning(self, "Ошибка", "Не удалось удалить заметку")

    def import_from_file(self):
        if not self._current_topic_id:
            SilentMessageBox.warning(self, "Ошибка", "Сначала выберите тему для заметки")
            return

        file_path, _ = QFileDialog.getOpenFileName(
            self, "Выберите текстовый файл", "", "Текстовые файлы (*.txt)"
        )

        if not file_path:
            return

        note_id = self._controller.import_from_text(self._current_topic_id, file_path)
        if note_id:
            self.load_note(note_id)
            self.status_label.setText(f"Импортировано из {file_path}")
        else:
            SilentMessageBox.warning(self, "Ошибка", "Не удалось импортировать файл")

    def get_current_note_id(self) -> int:
        return self._current_note_id

    def _get_current_date(self) -> str:
        from datetime import datetime
        return datetime.now().strftime("%d.%m.%Y %H:%M")

    def has_unsaved_changes(self) -> bool:
        return self._is_modified