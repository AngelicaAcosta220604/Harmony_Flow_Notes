# modules/notes/reader.py
from PySide6.QtWidgets import QTextBrowser, QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt


class NoteReader(QTextBrowser):
    """
    Виджет для просмотра заметки (только чтение).
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_reader()

    def _setup_reader(self):
        """Настраивает виджет"""
        self.setOpenExternalLinks(True)
        self.setReadOnly(True)

        # Настройка шрифта
        font = self.font()
        font.setPointSize(11)
        self.setFont(font)

    def display_note(self, title: str, content: str):
        """
        Отображает заметку с заголовком и содержимым
        """
        html = f"""
        <h1>{self._escape_html(title)}</h1>
        <hr>
        {content}
        """
        self.setHtml(html)

    def _escape_html(self, text: str) -> str:
        """Экранирует HTML-спецсимволы"""
        return (text.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace('"', "&quot;")
                .replace("'", "&#39;"))

    def clear_display(self):
        """Очищает отображаемое содержимое"""
        self.clear()


class NotePreviewWidget(QWidget):
    """
    Виджет для предпросмотра заметки в списке
    """

    def __init__(self, note_id: int, title: str, preview: str, updated_at: str, parent=None):
        super().__init__(parent)
        self.note_id = note_id
        self._setup_ui(title, preview, updated_at)

    def _setup_ui(self, title: str, preview: str, updated_at: str):
        """Настраивает интерфейс"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(4)

        # Заголовок и дата
        header_layout = QHBoxLayout()

        title_label = QLabel(title)
        title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        header_layout.addWidget(title_label)

        header_layout.addStretch()

        date_label = QLabel(updated_at[:10] if updated_at else "")
        date_label.setStyleSheet("color: #888888; font-size: 10px;")
        header_layout.addWidget(date_label)

        layout.addLayout(header_layout)

        # Превью
        if preview:
            preview_label = QLabel(preview)
            preview_label.setStyleSheet("color: #666666; font-size: 12px;")
            preview_label.setWordWrap(True)
            preview_label.setMaximumHeight(60)
            layout.addWidget(preview_label)

        self.setProperty("class", "note-preview")