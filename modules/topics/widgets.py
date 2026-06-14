# modules/topics/widgets.py
from PySide6.QtWidgets import (
    QTreeWidget, QTreeWidgetItem, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QDialog, QDialogButtonBox, QLabel, QComboBox, QLineEdit,
    QStyle  # Импортируем QStyle для использования стандартных иконок Qt
)
from PySide6.QtCore import Qt, Signal
from typing import List, Optional, Callable

from .controller import TopicController
from models.topic import Topic


class TreeWidget(QTreeWidget):
    """
    Кастомное дерево для отображения тем и папок.
    """

    topic_selected = Signal(int)  # Сигнал при выборе темы

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

    def get_selected_topic_id(self) -> Optional[int]:
        """Возвращает ID выбранной темы"""
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