# modules/topics/tree_view.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QMenu, QTreeWidgetItem
)
from widgets import SilentMessageBox, SilentInputDialog

from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QAction, QIcon, QPixmap

from .controller import TopicController
from .widgets import TreeWidget


class TopicsView(QWidget):
    topic_selected = Signal(int)
    topic_created = Signal(int)
    topic_deleted = Signal(int)

    def __init__(self, controller: TopicController, parent=None):
        super().__init__(parent)
        self._controller = controller
        self._setup_ui()
        self._connect_signals()
        self.refresh()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # Заголовок
        title_widget = QWidget()
        title_widget.setStyleSheet("""
            QWidget {
                background-color: #FFFFFF;
                border-radius: 16px;
                border: none;
            }
        """)
        title_widget.setFixedHeight(80)

        title_layout = QHBoxLayout(title_widget)
        title_layout.setSpacing(12)
        title_layout.setAlignment(Qt.AlignCenter)

        title_icon_label = QLabel()
        title_pixmap = QPixmap("resources/icons/notes_topic.png")
        if not title_pixmap.isNull():
            title_pixmap = title_pixmap.scaled(32, 32, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            title_icon_label.setPixmap(title_pixmap)
        else:
            title_icon_label.setText("📚")
            title_icon_label.setStyleSheet("font-size: 28px;")

        title_label = QLabel("Структура знаний")
        title_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #1F2937; background-color: transparent;")

        title_layout.addWidget(title_icon_label)
        title_layout.addWidget(title_label)

        layout.addSpacing(24)
        layout.addWidget(title_widget)
        layout.addSpacing(16)

        # Кнопки
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        self.new_folder_btn = QPushButton("Новая папка")
        self.new_folder_btn.setIcon(QIcon("resources/icons/folder.png"))
        self.new_folder_btn.setIconSize(QSize(18, 18))
        self.new_folder_btn.setFixedWidth(140)
        self.new_folder_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(245, 158, 11, 0.15);
                color: #D97706;
                border: 1px solid #F59E0B;
                border-radius: 12px;
                padding: 8px 14px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: rgba(245, 158, 11, 0.25);
                border: 1px solid #D97706;
                color: #B45309;
            }
            QPushButton:disabled {
                opacity: 0.5;
            }
        """)
        button_layout.addWidget(self.new_folder_btn)

        self.new_topic_btn = QPushButton("Новая тема")
        self.new_topic_btn.setIcon(QIcon("resources/icons/notes_topic.png"))
        self.new_topic_btn.setIconSize(QSize(18, 18))
        self.new_topic_btn.setFixedWidth(140)
        self.new_topic_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(59, 130, 246, 0.15);
                color: #3B82F6;
                border: 1px solid #3B82F6;
                border-radius: 12px;
                padding: 8px 14px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: rgba(59, 130, 246, 0.25);
                border: 1px solid #2563EB;
                color: #2563EB;
            }
            QPushButton:disabled {
                opacity: 0.5;
            }
        """)
        button_layout.addWidget(self.new_topic_btn)

        self.rename_btn = QPushButton("Переименовать")
        self.rename_btn.setIcon(QIcon("resources/icons/pen.png"))
        self.rename_btn.setIconSize(QSize(18, 18))
        self.rename_btn.setFixedWidth(140)
        self.rename_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(16, 185, 129, 0.15);
                color: #059669;
                border: 1px solid #10B981;
                border-radius: 12px;
                padding: 8px 14px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: rgba(16, 185, 129, 0.25);
                border: 1px solid #059669;
                color: #047857;
            }
            QPushButton:disabled {
                opacity: 0.5;
            }
        """)
        button_layout.addWidget(self.rename_btn)

        self.delete_btn = QPushButton("Удалить")
        self.delete_btn.setIcon(QIcon("resources/icons/urna.png"))
        self.delete_btn.setIconSize(QSize(18, 18))
        self.delete_btn.setFixedWidth(140)
        self.delete_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(239, 68, 68, 0.15);
                color: #EF4444;
                border: 1px solid #EF4444;
                border-radius: 12px;
                padding: 8px 14px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: rgba(239, 68, 68, 0.25);
                border: 1px solid #DC2626;
                color: #DC2626;
            }
            QPushButton:disabled {
                opacity: 0.5;
            }
        """)
        button_layout.addWidget(self.delete_btn)

        button_layout.addStretch()
        layout.addLayout(button_layout)
        layout.addSpacing(16)

        self.tree = TreeWidget(self._controller)
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._show_context_menu)
        layout.addWidget(self.tree)

    def _connect_signals(self):
        self.new_folder_btn.clicked.connect(self._on_new_folder)
        self.new_topic_btn.clicked.connect(self._on_new_topic)
        self.rename_btn.clicked.connect(self._on_rename)
        self.delete_btn.clicked.connect(self._on_delete)
        self.tree.topic_double_clicked.connect(self._on_topic_double_clicked)

    def _on_topic_double_clicked(self, topic_id: int):
        topic = self._controller.get_topic(topic_id)
        if topic and topic.is_topic:
            self.topic_selected.emit(topic_id)

    def _on_new_folder(self):
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
        reply = SilentMessageBox.question(self, "Подтверждение удаления", msg)
        if reply == SilentMessageBox.Yes:
            if self._controller.delete(topic_id):
                self.refresh()
                self.topic_deleted.emit(topic_id)
            else:
                SilentMessageBox.warning(self, "Ошибка", "Не удалось удалить элемент")

    def _show_context_menu(self, position):
        item = self.tree.itemAt(position)
        if not item:
            return
        menu = QMenu()
        menu.setStyleSheet("""
            QMenu {
                background-color: #FFFFFF;
                border: 1px solid #E6EEF6;
                border-radius: 12px;
                padding: 4px;
            }
            QMenu::item {
                padding: 6px 12px;
                border-radius: 6px;
            }
            QMenu::item:selected {
                background-color: rgba(59, 130, 246, 0.08);
                color: #3B82F6;
            }
        """)
        new_folder_action = QAction("Новая папка", self)
        new_folder_action.setIcon(QIcon("resources/icons/folder.png"))
        new_folder_action.triggered.connect(self._on_new_folder)
        menu.addAction(new_folder_action)
        new_topic_action = QAction("Новая тема", self)
        new_topic_action.setIcon(QIcon("resources/icons/notes_topic.png"))
        new_topic_action.triggered.connect(self._on_new_topic)
        menu.addAction(new_topic_action)
        menu.addSeparator()
        rename_action = QAction("Переименовать", self)
        rename_action.setIcon(QIcon("resources/icons/pen.png"))
        rename_action.triggered.connect(self._on_rename)
        menu.addAction(rename_action)
        delete_action = QAction("Удалить", self)
        delete_action.setIcon(QIcon("resources/icons/urna.png"))
        delete_action.triggered.connect(self._on_delete)
        menu.addAction(delete_action)
        menu.exec(self.tree.viewport().mapToGlobal(position))

    def refresh(self):
        self.tree.load_topics()
        has_selection = self.tree.get_selected_topic_id() is not None
        self.rename_btn.setEnabled(has_selection)
        self.delete_btn.setEnabled(has_selection)

    def get_selected_topic_id(self):
        return self.tree.get_selected_topic_id()

    def select_topic(self, topic_id: int):
        self.tree.select_topic(topic_id)