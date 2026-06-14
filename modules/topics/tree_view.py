# modules/topics/tree_view.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QMenu, QTreeWidgetItem
)
from widgets import SilentMessageBox, SilentInputDialog

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction

from .controller import TopicController
from .widgets import TreeWidget


class TopicsView(QWidget):
    """
    Экран с древовидной структурой тем.
    """

    # Сигналы
    topic_selected = Signal(int)  # (topic_id).
    topic_created = Signal(int)  # (topic_id)
    topic_deleted = Signal(int)  # (topic_id)

    def __init__(self, controller: TopicController, parent=None):
        super().__init__(parent)
        self._controller = controller
        self._setup_ui()
        self._connect_signals()
        self.refresh()

    def _setup_ui(self):
        """Настраивает интерфейс"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Заголовок
        title_layout = QHBoxLayout()
        title_label = QLabel("📚 Структура знаний")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        layout.addLayout(title_layout)

        # Кнопки управления
        button_layout = QHBoxLayout()

        self.new_folder_btn = QPushButton("📁 Новая папка")
        self.new_topic_btn = QPushButton("📚 Новая тема")
        self.rename_btn = QPushButton("✏️ Переименовать")
        self.delete_btn = QPushButton("🗑️ Удалить")

        button_layout.addWidget(self.new_folder_btn)
        button_layout.addWidget(self.new_topic_btn)
        button_layout.addWidget(self.rename_btn)
        button_layout.addWidget(self.delete_btn)
        button_layout.addStretch()

        layout.addLayout(button_layout)

        # Дерево тем (используем улучшенный TreeWidget)
        self.tree = TreeWidget(self._controller)
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._show_context_menu)
        layout.addWidget(self.tree)

    def _connect_signals(self):
        """Подключает сигналы"""
        self.new_folder_btn.clicked.connect(self._on_new_folder)
        self.new_topic_btn.clicked.connect(self._on_new_topic)
        self.rename_btn.clicked.connect(self._on_rename)
        self.delete_btn.clicked.connect(self._on_delete)

        # ВАЖНО: Подключаем СИГНАЛ ДВОЙНОГО КЛИКА из виджета дерева
        self.tree.topic_double_clicked.connect(self._on_topic_double_clicked)

    def _on_topic_double_clicked(self, topic_id: int):
        """Обработчик двойного клика по элементу дерева"""
        topic = self._controller.get_topic(topic_id)
        if topic and topic.is_topic:
            # Только темы отправляют сигнал, папки игнорируются
            self.topic_selected.emit(topic_id)

    def _on_new_folder(self):
        """Создание новой папки"""
        parent_id = self.tree.get_selected_folder_id()

        name, ok = SilentInputDialog.getText(self, "Новая папка", "Введите название папки:")
        if ok and name.strip():
            topic_id = self._controller.create_folder(name.strip(), parent_id)
            if topic_id:
                self.refresh()
                self.topic_created.emit(topic_id)
                self.tree.select_topic(topic_id)
            else:
                SilentMessageBox.warning(self, "Ошибка", "Не удалось создать папку")

    def _on_new_topic(self):
        """Создание новой темы"""
        parent_id = self.tree.get_selected_folder_id()

        name, ok = SilentInputDialog.getText(self, "Новая тема", "Введите название темы:")
        if ok and name.strip():
            topic_id = self._controller.create_topic(name.strip(), parent_id)
            if topic_id:
                self.refresh()
                self.topic_created.emit(topic_id)
                self.tree.select_topic(topic_id)
            else:
                SilentMessageBox.warning(self, "Ошибка", "Не удалось создать тему")

    def _on_rename(self):
        """Переименование элемента"""
        topic_id = self.tree.get_selected_topic_id()
        if not topic_id:
            SilentMessageBox.information(self, "Информация", "Выберите элемент для переименования")
            return

        topic = self._controller.get_topic(topic_id)
        if not topic:
            return

        new_name, ok = SilentInputDialog.getText(self, "Переименовать", "Введите новое название:", text=topic.name)
        if ok and new_name.strip() and new_name.strip() != topic.name:
            if self._controller.rename(topic_id, new_name.strip()):
                self.refresh()
                self.tree.select_topic(topic_id)
            else:
                SilentMessageBox.warning(self, "Ошибка", "Не удалось переименовать")

    def _on_delete(self):
        """Удаление элемента"""
        topic_id = self.tree.get_selected_topic_id()
        if not topic_id:
            SilentMessageBox.information(self, "Информация", "Выберите элемент для удаления")
            return

        topic = self._controller.get_topic(topic_id)
        if not topic:
            return

        msg = f"Вы действительно хотите удалить «{topic.name}»?\n\n"
        msg += "Вместе с ним будут удалены все:\n"
        msg += "• заметки\n• задачи\n• карточки\n• сессии\n• аналитика"

        reply = SilentMessageBox.question(
            self, "Подтверждение удаления", msg
        )

        if reply == SilentMessageBox.Yes:
            if self._controller.delete(topic_id):
                self.refresh()
                self.topic_deleted.emit(topic_id)
            else:
                SilentMessageBox.warning(self, "Ошибка", "Не удалось удалить элемент")

    def _show_context_menu(self, position):
        """Показывает контекстное меню"""
        item = self.tree.itemAt(position)  # <-- ИСПРАВЛЕНО
        if not item:
            return

        menu = QMenu()

        new_folder_action = QAction("📁 Новая папка", self)
        new_folder_action.triggered.connect(self._on_new_folder)
        menu.addAction(new_folder_action)

        new_topic_action = QAction("📚 Новая тема", self)
        new_topic_action.triggered.connect(self._on_new_topic)
        menu.addAction(new_topic_action)

        menu.addSeparator()

        rename_action = QAction("✏️ Переименовать", self)
        rename_action.triggered.connect(self._on_rename)
        menu.addAction(rename_action)

        delete_action = QAction("🗑️ Удалить", self)
        delete_action.triggered.connect(self._on_delete)
        menu.addAction(delete_action)

        menu.exec(self.tree.viewport().mapToGlobal(position))  # <-- ИСПРАВЛЕНО (убрали .tree)

    def refresh(self):
        """Обновляет дерево"""
        self.tree.load_topics()

        has_selection = self.tree.get_selected_topic_id() is not None
        self.rename_btn.setEnabled(has_selection)
        self.delete_btn.setEnabled(has_selection)

    def get_selected_topic_id(self):
        """Возвращает ID выбранной темы"""
        return self.tree.get_selected_topic_id()

    def select_topic(self, topic_id: int):
        """Выбирает тему"""
        self.tree.select_topic(topic_id)