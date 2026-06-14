# modules/notes/widgets.py
from PySide6.QtWidgets import (
    QTextEdit, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QComboBox, QToolBar, QColorDialog, QFontComboBox, QLabel
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import (
    QTextCursor, QTextCharFormat, QFont, QColor, QAction,
    QKeySequence
)


class RichTextEditor(QTextEdit):
    """
    Богатый текстовый редактор с поддержкой форматирования.
    Поддерживает:
    - жирный, курсив, подчёркивание, зачёркивание
    - заголовки 3 уровней
    - списки (маркированные, нумерованные)
    - чек-листы
    - цвет текста и фона
    - выравнивание
    """

    # Сигнал при изменении содержимого
    content_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_editor()
        self._connect_signals()

    def _setup_editor(self):
        """Настраивает редактор"""
        self.setAcceptRichText(True)
        self.setPlaceholderText("Начните писать здесь...")

        # Настройка шрифта по умолчанию
        font = QFont("Segoe UI", 11)
        self.setFont(font)

    def _connect_signals(self):
        """Подключает сигналы"""
        self.textChanged.connect(self.content_changed.emit)

    # ========== Форматирование ==========

    def toggle_bold(self):
        """Жирный текст"""
        fmt = self.currentCharFormat()
        fmt.setFontWeight(QFont.Bold if fmt.fontWeight() != QFont.Bold else QFont.Normal)
        self.mergeCurrentCharFormat(fmt)

    def toggle_italic(self):
        """Курсив"""
        fmt = self.currentCharFormat()
        fmt.setFontItalic(not fmt.fontItalic())
        self.mergeCurrentCharFormat(fmt)

    def toggle_underline(self):
        """Подчёркивание"""
        fmt = self.currentCharFormat()
        fmt.setFontUnderline(not fmt.fontUnderline())
        self.mergeCurrentCharFormat(fmt)

    def toggle_strikeout(self):
        """Зачёркивание"""
        fmt = self.currentCharFormat()
        fmt.setFontStrikeOut(not fmt.fontStrikeOut())
        self.mergeCurrentCharFormat(fmt)

    def set_heading(self, level: int):
        """Устанавливает заголовок (1-3)"""
        fmt = QTextCharFormat()

        if level == 1:
            font = QFont("Segoe UI", 20, QFont.Bold)
            fmt.setFont(font)
        elif level == 2:
            font = QFont("Segoe UI", 16, QFont.Bold)
            fmt.setFont(font)
        elif level == 3:
            font = QFont("Segoe UI", 14, QFont.Bold)
            fmt.setFont(font)
        else:
            # Обычный текст
            font = QFont("Segoe UI", 11)
            fmt.setFont(font)

        self.mergeCurrentCharFormat(fmt)

    def set_text_color(self, color: QColor):
        """Устанавливает цвет текста"""
        fmt = self.currentCharFormat()
        fmt.setForeground(color)
        self.mergeCurrentCharFormat(fmt)

    def set_background_color(self, color: QColor):
        """Устанавливает цвет фона"""
        fmt = self.currentCharFormat()
        fmt.setBackground(color)
        self.mergeCurrentCharFormat(fmt)

    def set_alignment(self, alignment: Qt.AlignmentFlag):
        """Устанавливает выравнивание"""
        self.setAlignment(alignment)

    # ========== Списки ==========

    def insert_bullet_list(self):
        """Вставляет маркированный список"""
        cursor = self.textCursor()

        if cursor.currentList() and cursor.currentList().format().style() == QTextListFormat.ListDisc:
            # Если уже в маркированном списке, выходим из него
            cursor.insertBlock()
            cursor.currentList().remove(cursor.block())
        else:
            # Создаём новый список
            list_format = QTextListFormat()
            list_format.setStyle(QTextListFormat.ListDisc)
            cursor.createList(list_format)

    def insert_numbered_list(self):
        """Вставляет нумерованный список"""
        cursor = self.textCursor()

        if cursor.currentList() and cursor.currentList().format().style() == QTextListFormat.ListDecimal:
            # Если уже в нумерованном списке, выходим из него
            cursor.insertBlock()
            cursor.currentList().remove(cursor.block())
        else:
            # Создаём новый список
            list_format = QTextListFormat()
            list_format.setStyle(QTextListFormat.ListDecimal)
            cursor.createList(list_format)

    def insert_checklist(self):
        """Вставляет чек-лист"""
        cursor = self.textCursor()

        # Вставляем чекбокс как символ
        cursor.insertText("[ ] ")

    # ========== Работа с выделением ==========

    def get_selected_text(self) -> str:
        """Возвращает выделенный текст"""
        cursor = self.textCursor()
        return cursor.selectedText()

    def get_selected_text_with_format(self) -> tuple:
        """
        Возвращает выделенный текст и его формат
        Returns:
            (текст, формат)
        """
        cursor = self.textCursor()
        if cursor.hasSelection():
            text = cursor.selectedText()
            fmt = cursor.charFormat()
            return text, fmt
        return "", None

    def replace_selected_text(self, new_text: str):
        """Заменяет выделенный текст"""
        cursor = self.textCursor()
        if cursor.hasSelection():
            cursor.insertText(new_text)

    # ========== Работа с содержимым ==========

    def get_html(self) -> str:
        """Возвращает содержимое в HTML формате"""
        return self.toHtml()

    def set_html(self, html: str):
        """Устанавливает содержимое из HTML"""
        self.setHtml(html)

    def get_plain_text(self) -> str:
        """Возвращает простой текст без форматирования"""
        return self.toPlainText()

    def set_plain_text(self, text: str):
        """Устанавливает простой текст"""
        self.setPlainText(text)

    def clear_content(self):
        """Очищает содержимое"""
        self.clear()

    def word_count(self) -> int:
        """Возвращает количество слов"""
        return len(self.toPlainText().split())

    def character_count(self) -> int:
        """Возвращает количество символов"""
        return len(self.toPlainText())


class EditorToolbar(QToolBar):
    """
    Панель инструментов для RichTextEditor
    """

    def __init__(self, editor: RichTextEditor, parent=None):
        super().__init__(parent)
        self._editor = editor
        self._setup_ui()

    def _setup_ui(self):
        """Настраивает панель инструментов"""
        self.setMovable(False)
        self.setFloatable(False)

        # Кнопки форматирования
        self.add_action("B", "Жирный (Ctrl+B)", self._editor.toggle_bold)
        self.add_action("I", "Курсив (Ctrl+I)", self._editor.toggle_italic)
        self.add_action("U", "Подчёркивание (Ctrl+U)", self._editor.toggle_underline)
        self.add_action("S", "Зачёркивание", self._editor.toggle_strikeout)

        self.addSeparator()

        # Заголовки
        self.heading_combo = QComboBox()
        self.heading_combo.addItem("Обычный", 0)
        self.heading_combo.addItem("Заголовок 1", 1)
        self.heading_combo.addItem("Заголовок 2", 2)
        self.heading_combo.addItem("Заголовок 3", 3)
        self.heading_combo.currentIndexChanged.connect(self._on_heading_changed)
        self.addWidget(self.heading_combo)

        self.addSeparator()

        # Списки
        self.add_action("•", "Маркированный список", self._editor.insert_bullet_list)
        self.add_action("1.", "Нумерованный список", self._editor.insert_numbered_list)
        self.add_action("☐", "Чек-лист", self._editor.insert_checklist)

        self.addSeparator()

        # Выравнивание
        self.add_action("←", "Выравнивание по левому краю",
                        lambda: self._editor.set_alignment(Qt.AlignLeft))
        self.add_action("↔", "Выравнивание по центру",
                        lambda: self._editor.set_alignment(Qt.AlignCenter))
        self.add_action("→", "Выравнивание по правому краю",
                        lambda: self._editor.set_alignment(Qt.AlignRight))

        self.addSeparator()

        # Цвета
        self.text_color_btn = QPushButton("🎨 Текст")
        self.text_color_btn.clicked.connect(self._on_text_color)
        self.addWidget(self.text_color_btn)

        self.bg_color_btn = QPushButton("🖌️ Фон")
        self.bg_color_btn.clicked.connect(self._on_bg_color)
        self.addWidget(self.bg_color_btn)

    def add_action(self, text: str, tooltip: str, callback) -> QAction:
        """Добавляет действие на панель"""
        action = QAction(text, self)
        action.setToolTip(tooltip)
        action.triggered.connect(callback)
        self.addAction(action)
        return action

    def _on_heading_changed(self, index: int):
        """Обработчик изменения заголовка"""
        level = self.heading_combo.currentData()
        if level:
            self._editor.set_heading(level)
        else:
            # Возвращаем обычный текст
            self._editor.set_heading(0)

    def _on_text_color(self):
        """Выбор цвета текста"""
        color = QColorDialog.getColor()
        if color.isValid():
            self._editor.set_text_color(color)

    def _on_bg_color(self):
        """Выбор цвета фона"""
        color = QColorDialog.getColor()
        if color.isValid():
            self._editor.set_background_color(color)