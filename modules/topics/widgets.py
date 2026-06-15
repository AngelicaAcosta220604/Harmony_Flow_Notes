# modules/topics/widgets.py
from PySide6.QtWidgets import (
    QTreeWidget, QTreeWidgetItem, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QDialog, QDialogButtonBox, QLabel, QComboBox, QLineEdit,
    QStyle, QCheckBox  # Импортируем QStyle для использования стандартных иконок Qt
)
from PySide6.QtCore import Qt, Signal
from typing import List, Optional, Callable

from .controller import TopicController
from models.topic import Topic


class TreeWidget(QTreeWidget):
    """
    Кастомное дерево для отображения тем и папок
    """

    topic_selected = Signal(int)  # Сигнал при выборе темы
    topics_changed = Signal()
    topic_double_clicked = Signal(int)

    def __init__(self, controller: TopicController, parent=None):
        super().__init__(parent)
        self._controller = controller
        self._setup_ui()

    def _setup_ui(self):
        """Настраивает внешний вид"""
        self.setHeaderHidden(True)
        self.setIndentation(20)
        self.setSelectionMode(QTreeWidget.SingleSelection)
        self.itemClicked.connect(self._on_item_clicked)
        self.itemDoubleClicked.connect(self._on_item_double_clicked)

    def load_topics(self):
        """Загружает все темы из БД"""
        self.clear()
        roots = self._controller.get_tree_structure()

        for root in roots:
            self._add_topic_item(None, root)

    def _add_topic_item(self, parent_item: Optional[QTreeWidgetItem], topic: Topic) -> QTreeWidgetItem:
        """Рекурсивно добавляет тему и её детей"""
        item = QTreeWidgetItem(parent_item if parent_item else self)
        item.setText(0, topic.display_name)
        item.setData(0, Qt.UserRole, topic.id)

        # Безопасная установка стандартных системных иконок через Enum QStyle
        if topic.is_folder:
            item.setIcon(0, self.style().standardIcon(QStyle.SP_DirIcon))
        else:
            item.setIcon(0, self.style().standardIcon(QStyle.SP_FileIcon))

        for child in topic.children:
            self._add_topic_item(item, child)

        if parent_item is None:
            self.addTopLevelItem(item)

        return item

    def _on_item_clicked(self, item: QTreeWidgetItem, column: int):
        """Обработчик клика по элементу"""
        topic_id = item.data(0, Qt.UserRole)
        if topic_id:
            self.topic_selected.emit(topic_id)

    def _on_item_double_clicked(self, item: QTreeWidgetItem, column: int):
        topic_id = item.data(0, Qt.UserRole)
        if not topic_id:
            return

        topic = self._controller.get_topic(topic_id)
        if not topic:
            return

        if topic.type == "topic":
            # ОТПРАВЛЯЕМ СИГНАЛ ТОЛЬКО ДЛЯ ТЕМ
            self.topic_double_clicked.emit(topic_id)
        else:
            # Для папки — раскрываем/схлопываем
            if item.isExpanded():
                item.setExpanded(False)
            else:
                item.setExpanded(True)

    def get_selected_topic_id(self) -> Optional[int]:
        """Возвращает ID выбранной темы"""
        current = self.currentItem()
        if current:
            return current.data(0, Qt.UserRole)
        return None

    def get_selected_folder_id(self) -> Optional[int]:
        """Возвращает ID выбранной папки или None, если выбрана тема или ничего."""
        current = self.currentItem()
        if not current:
            return None

        topic_id = current.data(0, Qt.UserRole)
        if not topic_id:
            return None

        topic = self._controller.get_topic(topic_id)
        if topic and topic.is_folder:
            return topic_id
        return None

    def get_selected_item_id(self) -> Optional[int]:
        """Возвращает ID любого выбранного элемента (и папки, и темы)"""
        current = self.currentItem()
        if current:
            return current.data(0, Qt.UserRole)
        return None

    def select_topic(self, topic_id: int):
        """Выбирает тему по ID"""
        self._select_topic_recursive(self.invisibleRootItem(), topic_id)

    def _select_topic_recursive(self, parent: QTreeWidgetItem, topic_id: int) -> bool:
        """Рекурсивный поиск и выбор темы"""
        for i in range(parent.childCount()):
            child = parent.child(i)
            if child.data(0, Qt.UserRole) == topic_id:
                self.setCurrentItem(child)
                return True
            if self._select_topic_recursive(child, topic_id):
                return True
        return False

    def refresh(self):
        """Обновляет дерево"""
        current_id = self.get_selected_topic_id()
        self.load_topics()
        if current_id:
            self.select_topic(current_id)


class TopicSelectorDialog(QDialog):
    """
    Диалог для выбора темы.
    """

    topic_selected = Signal(int)  # (topic_id)

    def __init__(self, controller: TopicController, parent=None, title: str = "Выберите тему"):
        super().__init__(parent)
        self._controller = controller
        self._setup_ui(title)
        self._load_topics()

    def _setup_ui(self, title: str):
        """Настраивает интерфейс"""
        self.setWindowTitle(title)
        self.setMinimumSize(400, 500)

        layout = QVBoxLayout(self)

        # Инструкция
        label = QLabel("Выберите тему для привязки:")
        layout.addWidget(label)

        # Дерево
        self.tree = TreeWidget(self._controller)
        self.tree.topic_selected.connect(self._on_topic_selected)
        layout.addWidget(self.tree)

        # Кнопки
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def _load_topics(self):
        """Загружает темы в дерево"""
        self.tree.load_topics()

    def _on_topic_selected(self, topic_id: int):
        """Обработчик выбора темы"""
        self.topic_selected.emit(topic_id)

    def get_selected_topic_id(self) -> Optional[int]:
        """Возвращает ID выбранной темы"""
        return self.tree.get_selected_topic_id()


class TopicTreeSelector(QWidget):
    """
    Виджет для выбора темы с выпадающим списком.
    """

    topic_changed = Signal(int)  # (topic_id)

    def __init__(self, controller: TopicController, parent=None):
        super().__init__(parent)
        self._controller = controller
        self._setup_ui()
        self._load_topics()

    def _setup_ui(self):
        """Настраивает интерфейс"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.label = QLabel("Тема:")
        layout.addWidget(self.label)

        self.combo = QComboBox()
        self.combo.currentIndexChanged.connect(self._on_current_index_changed)
        layout.addWidget(self.combo)

        self.select_btn = QPushButton("📁")
        self.select_btn.setFixedWidth(30)
        self.select_btn.setToolTip("Выбрать тему из дерева")
        self.select_btn.clicked.connect(self._on_select_clicked)
        layout.addWidget(self.select_btn)

    def _load_topics(self):
        """Загружает все темы в комбобокс"""
        self.combo.clear()
        self.combo.addItem("— Общие задачи —", None)

        roots = self._controller.get_tree_structure()
        self._add_topics_to_combo(roots, "")

    def _add_topics_to_combo(self, topics: List[Topic], prefix: str):
        """Рекурсивно добавляет темы в комбобокс"""
        for topic in topics:
            if topic.is_topic:
                self.combo.addItem(f"{prefix}{topic.name}", topic.id)
            # Рекурсивно добавляем детей
            if topic.children:
                self._add_topics_to_combo(topic.children, prefix + "  ")

    def _on_current_index_changed(self, index: int):
        """Обработчик изменения выбора в комбобоксе"""
        topic_id = self.combo.currentData()
        self.topic_changed.emit(topic_id)

    def _on_select_clicked(self):
        """Открывает диалог выбора темы"""
        dialog = TopicSelectorDialog(self._controller, self)
        if dialog.exec() == QDialog.Accepted:
            topic_id = dialog.get_selected_topic_id()
            if topic_id:
                self.set_selected_topic(topic_id)

    def set_selected_topic(self, topic_id: Optional[int]):
        """Устанавливает выбранную тему"""
        if topic_id is None:
            self.combo.setCurrentIndex(0)
        else:
            index = self.combo.findData(topic_id)
            if index >= 0:
                self.combo.setCurrentIndex(index)

    def get_selected_topic_id(self) -> Optional[int]:
        """Возвращает ID выбранной темы"""
        return self.combo.currentData()

    def refresh(self):
        """Обновляет список тем"""
        current_id = self.get_selected_topic_id()
        self._load_topics()
        if current_id:
            self.set_selected_topic(current_id)

class TaskListItemWidget(QWidget):
    """Виджет для отображения задачи в списке с кнопками и чекбоксом"""

    complete_clicked = Signal(int)
    edit_clicked = Signal(int)
    delete_clicked = Signal(int)

    def __init__(self, task_id: int, title: str, deadline: str, status: str, is_overdue: bool, parent=None):
        super().__init__(parent)
        self.task_id = task_id
        self._setup_ui(title, deadline, status, is_overdue)

    def _setup_ui(self, title: str, deadline: str, status: str, is_overdue: bool):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(10)

        # Чекбокс для выполнения
        self.checkbox = QCheckBox()
        self.checkbox.setChecked(status == 'completed')
        self.checkbox.stateChanged.connect(self._on_checkbox_changed)
        layout.addWidget(self.checkbox)

        # Название задачи
        self.title_label = QLabel(title)
        if status == 'completed':
            self.title_label.setStyleSheet("text-decoration: line-through; color: #888;")
        elif is_overdue:
            self.title_label.setStyleSheet("color: #f44336; font-weight: bold;")
        layout.addWidget(self.title_label, 1)

        # Дедлайн
        self.deadline_label = QLabel(deadline)
        self.deadline_label.setStyleSheet("color: #888; font-size: 10px;")
        layout.addWidget(self.deadline_label)

        # Кнопка "Редактировать"
        self.edit_btn = QPushButton("✏️")
        self.edit_btn.setFixedSize(30, 30)
        self.edit_btn.setToolTip("Редактировать задачу")
        self.edit_btn.clicked.connect(lambda: self.edit_clicked.emit(self.task_id))
        layout.addWidget(self.edit_btn)

        # Кнопка "Удалить"
        self.delete_btn = QPushButton("🗑️")
        self.delete_btn.setFixedSize(30, 30)
        self.delete_btn.setToolTip("Удалить задачу")
        self.delete_btn.clicked.connect(lambda: self.delete_clicked.emit(self.task_id))
        layout.addWidget(self.delete_btn)

        self.setFixedHeight(50)
        self.setStyleSheet("""
            TaskListItemWidget {
                border-bottom: 1px solid #ddd;
                background-color: transparent;
            }
            TaskListItemWidget:hover {
                background-color: #f0f0f0;
            }
            QPushButton {
                border: none;
                background-color: transparent;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
                border-radius: 4px;
            }
        """)

    def _on_checkbox_changed(self, state):
        if state == Qt.Checked:
            self.complete_clicked.emit(self.task_id)