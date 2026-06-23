# modules/notes/widgets.py
from PySide6.QtWidgets import (
    QTextEdit, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QComboBox, QToolBar, QColorDialog, QFontComboBox, QLabel, QMenu, QSizePolicy, QFrame, QGraphicsDropShadowEffect
)
from widgets import SilentMessageBox
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import (
    QTextCursor, QTextCharFormat, QFont, QColor, QAction,
    QKeySequence, QTextListFormat, QPixmap
)
import logging

# Настройка логирования
logger = logging.getLogger(__name__)


class RichTextEditor(QTextEdit):
    """
    Богатый текстовый редактор с поддержкой форматирования.
    """

    # Сигналы для создания задач и карточек из выделенного текста.
    create_task_from_selection = Signal(str)
    create_card_from_selection = Signal(str)

    # Сигнал при изменении содержимого
    content_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_editor()
        self._connect_signals()

        # 🆕 Минимальная высота для редактора
        self.setMinimumHeight(400)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def _setup_editor(self):
        """Настраивает редактор"""
        try:
            self.setAcceptRichText(True)
            self.setPlaceholderText("Начните писать здесь...")

            # Включаем контекстное меню
            self.setContextMenuPolicy(Qt.CustomContextMenu)
            self.customContextMenuRequested.connect(self._show_context_menu)

            font = QFont("Segoe UI", 11)
            self.setFont(font)
        except Exception as e:
            logger.error(f"Ошибка настройки редактора: {e}", exc_info=True)

    def _show_context_menu(self, position):
        """Показывает контекстное меню при выделении текста"""
        try:
            cursor = self.textCursor()
            if not cursor.hasSelection():
                self._show_standard_context_menu(position)
                return

            selected_text = cursor.selectedText()
            if not selected_text:
                return

            # Создаём кастомное меню
            menu = QMenu(self)

            copy_action = QAction("📋 Копировать", self)
            copy_action.triggered.connect(self.copy)
            menu.addAction(copy_action)

            cut_action = QAction("✂️ Вырезать", self)
            cut_action.triggered.connect(self.cut)
            menu.addAction(cut_action)

            menu.addSeparator()

            card_action = QAction("🃏 Создать карточку", self)
            card_action.triggered.connect(lambda: self.create_card_from_selection.emit(selected_text))
            menu.addAction(card_action)

            task_action = QAction("✅ Создать задачу", self)
            task_action.triggered.connect(lambda: self.create_task_from_selection.emit(selected_text))
            menu.addAction(task_action)

            menu.exec(self.viewport().mapToGlobal(position))
        except Exception as e:
            logger.error(f"Ошибка показа контекстного меню: {e}", exc_info=True)

    def _show_standard_context_menu(self, position):
        """Показывает стандартное контекстное меню (без выделения)"""
        try:
            menu = self.createStandardContextMenu()
            menu.exec(self.viewport().mapToGlobal(position))
        except Exception as e:
            logger.error(f"Ошибка показа стандартного контекстного меню: {e}", exc_info=True)

    def _connect_signals(self):
        self.textChanged.connect(self.content_changed.emit)

    # ========== Форматирование ==========

    def toggle_bold(self):
        try:
            fmt = self.currentCharFormat()
            fmt.setFontWeight(QFont.Bold if fmt.fontWeight() != QFont.Bold else QFont.Normal)
            self.mergeCurrentCharFormat(fmt)
        except Exception as e:
            logger.error(f"Ошибка toggle_bold: {e}", exc_info=True)

    def toggle_italic(self):
        try:
            fmt = self.currentCharFormat()
            fmt.setFontItalic(not fmt.fontItalic())
            self.mergeCurrentCharFormat(fmt)
        except Exception as e:
            logger.error(f"Ошибка toggle_italic: {e}", exc_info=True)

    def toggle_underline(self):
        try:
            fmt = self.currentCharFormat()
            fmt.setFontUnderline(not fmt.fontUnderline())
            self.mergeCurrentCharFormat(fmt)
        except Exception as e:
            logger.error(f"Ошибка toggle_underline: {e}", exc_info=True)

    def toggle_strikeout(self):
        try:
            fmt = self.currentCharFormat()
            fmt.setFontStrikeOut(not fmt.fontStrikeOut())
            self.mergeCurrentCharFormat(fmt)
        except Exception as e:
            logger.error(f"Ошибка toggle_strikeout: {e}", exc_info=True)

    def set_heading(self, level: int):
        try:
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
                font = QFont("Segoe UI", 11)
                fmt.setFont(font)
            self.mergeCurrentCharFormat(fmt)
        except Exception as e:
            logger.error(f"Ошибка set_heading: {e}", exc_info=True)

    def set_text_color(self, color: QColor):
        try:
            fmt = self.currentCharFormat()
            fmt.setForeground(color)
            self.mergeCurrentCharFormat(fmt)
        except Exception as e:
            logger.error(f"Ошибка set_text_color: {e}", exc_info=True)

    def set_background_color(self, color: QColor):
        try:
            fmt = self.currentCharFormat()
            fmt.setBackground(color)
            self.mergeCurrentCharFormat(fmt)
        except Exception as e:
            logger.error(f"Ошибка set_background_color: {e}", exc_info=True)

    def set_alignment(self, alignment: Qt.AlignmentFlag):
        try:
            self.setAlignment(alignment)
        except Exception as e:
            logger.error(f"Ошибка set_alignment: {e}", exc_info=True)

    # ========== Списки ==========

    def insert_bullet_list(self):
        try:
            cursor = self.textCursor()
            if cursor.currentList() and cursor.currentList().format().style() == QTextListFormat.ListDisc:
                cursor.insertBlock()
                cursor.currentList().remove(cursor.block())
            else:
                list_format = QTextListFormat()
                list_format.setStyle(QTextListFormat.ListDisc)
                cursor.createList(list_format)
        except Exception as e:
            logger.error(f"Ошибка insert_bullet_list: {e}", exc_info=True)

    def insert_numbered_list(self):
        try:
            cursor = self.textCursor()
            if cursor.currentList() and cursor.currentList().format().style() == QTextListFormat.ListDecimal:
                cursor.insertBlock()
                cursor.currentList().remove(cursor.block())
            else:
                list_format = QTextListFormat()
                list_format.setStyle(QTextListFormat.ListDecimal)
                cursor.createList(list_format)
        except Exception as e:
            logger.error(f"Ошибка insert_numbered_list: {e}", exc_info=True)

    def insert_checklist(self):
        try:
            cursor = self.textCursor()
            cursor.insertText("[ ] ")
        except Exception as e:
            logger.error(f"Ошибка insert_checklist: {e}", exc_info=True)

    # ========== Работа с выделением ==========

    def get_selected_text(self) -> str:
        try:
            cursor = self.textCursor()
            return cursor.selectedText()
        except Exception as e:
            logger.error(f"Ошибка get_selected_text: {e}", exc_info=True)
            return ""

    # ========== Работа с содержимым ==========

    def get_html(self) -> str:
        try:
            return self.toHtml()
        except Exception as e:
            logger.error(f"Ошибка get_html: {e}", exc_info=True)
            return ""

    def set_html(self, html: str):
        try:
            self.setHtml(html)
        except Exception as e:
            logger.error(f"Ошибка set_html: {e}", exc_info=True)

    def get_plain_text(self) -> str:
        try:
            return self.toPlainText()
        except Exception as e:
            logger.error(f"Ошибка get_plain_text: {e}", exc_info=True)
            return ""

    def set_plain_text(self, text: str):
        try:
            self.setPlainText(text)
        except Exception as e:
            logger.error(f"Ошибка set_plain_text: {e}", exc_info=True)

    def clear_content(self):
        try:
            self.clear()
        except Exception as e:
            logger.error(f"Ошибка clear_content: {e}", exc_info=True)

    def word_count(self) -> int:
        try:
            return len(self.toPlainText().split())
        except Exception as e:
            logger.error(f"Ошибка word_count: {e}", exc_info=True)
            return 0

    def character_count(self) -> int:
        try:
            return len(self.toPlainText())
        except Exception as e:
            logger.error(f"Ошибка character_count: {e}", exc_info=True)
            return 0


class EditorToolbar(QToolBar):
    """Панель инструментов для RichTextEditor"""

    def __init__(self, editor: RichTextEditor, parent=None):
        super().__init__(parent)
        self._editor = editor
        self._setup_ui()

    def _setup_ui(self):
        try:
            self.setMovable(False)
            self.setFloatable(False)

            # 🆕 Разрешаем перенос инструментов
            self.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)

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

            self.addSeparator()

            # ===== КНОПКИ ДЛЯ СОЗДАНИЯ ИЗ ВЫДЕЛЕННОГО ТЕКСТА =====
            self.create_task_btn = QPushButton("✅ Создать задачу")
            self.create_task_btn.setToolTip("Создать задачу из выделенного текста")
            self.create_task_btn.clicked.connect(self._on_create_task)
            self.addWidget(self.create_task_btn)

            self.create_card_btn = QPushButton("🃏 Создать карточку")
            self.create_card_btn.setToolTip("Создать карточку из выделенного текста")
            self.create_card_btn.clicked.connect(self._on_create_card)
            self.addWidget(self.create_card_btn)

            # Подсказка пользователю
            self.hint_label = QLabel("💡 Выделите текст → нажмите кнопку")
            self.hint_label.setStyleSheet("color: #888888; font-size: 10px; margin-left: 10px;")
            self.addWidget(self.hint_label)

            #  Добавляем растягивающийся spacer в конец
            spacer = QWidget()
            spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            self.addWidget(spacer)
        except Exception as e:
            logger.error(f"Ошибка настройки EditorToolbar: {e}", exc_info=True)

    def add_action(self, text: str, tooltip: str, callback) -> QAction:
        action = QAction(text, self)
        action.setToolTip(tooltip)
        action.triggered.connect(callback)
        self.addAction(action)
        return action

    def _on_heading_changed(self, index: int):
        try:
            level = self.heading_combo.currentData()
            if level:
                self._editor.set_heading(level)
            else:
                self._editor.set_heading(0)
        except Exception as e:
            logger.error(f"Ошибка _on_heading_changed: {e}", exc_info=True)

    def _on_text_color(self):
        try:
            color = QColorDialog.getColor()
            if color.isValid():
                self._editor.set_text_color(color)
        except Exception as e:
            logger.error(f"Ошибка _on_text_color: {e}", exc_info=True)

    def _on_bg_color(self):
        try:
            color = QColorDialog.getColor()
            if color.isValid():
                self._editor.set_background_color(color)
        except Exception as e:
            logger.error(f"Ошибка _on_bg_color: {e}", exc_info=True)

    def _on_create_task(self):
        try:
            selected = self._editor.get_selected_text()
            if not selected:
                SilentMessageBox.information(
                    self, "Нет выделения",
                    "Сначала выделите текст в заметке, из которого хотите создать задачу"
                )
                return
            self._editor.create_task_from_selection.emit(selected)
        except Exception as e:
            logger.error(f"Ошибка _on_create_task: {e}", exc_info=True)

    def _on_create_card(self):
        try:
            selected = self._editor.get_selected_text()
            if not selected:
                SilentMessageBox.information(
                    self, "Нет выделения",
                    "Сначала выделите текст в заметке, из которого хотите создать карточку"
                )
                return
            self._editor.create_card_from_selection.emit(selected)
        except Exception as e:
            logger.error(f"Ошибка _on_create_card: {e}", exc_info=True)