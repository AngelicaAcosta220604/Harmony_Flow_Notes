# modules/analytics/dialogs.py
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QListWidget,
    QListWidgetItem, QPushButton, QDialogButtonBox
)
from PySide6.QtCore import Qt, Signal

from datebase.repositories.topic_repo import TopicRepository


class AnalyticsSelectorDialog(QDialog):
    """
    Диалог выбора тем для аналитики.
    """

    topics_selected = Signal(list)  # list of topic_ids

    def __init__(self, parent=None):
        super().__init__(parent)
        self._topic_repo = TopicRepository()
        self._selected_topics = []
        self._setup_ui()
        self._load_topics()

    def _setup_ui(self):
        """Настраивает интерфейс"""
        self.setWindowTitle("Выбор тем для аналитики")
        self.setMinimumSize(400, 500)

        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # Инструкция
        label = QLabel("Выберите темы для анализа (можно несколько):")
        layout.addWidget(label)

        # Список тем
        self.topic_list = QListWidget()
        self.topic_list.setSelectionMode(QListWidget.MultiSelection)
        layout.addWidget(self.topic_list)

        # Кнопки выбора всех/очистить
        btn_layout = QHBoxLayout()

        self.select_all_btn = QPushButton("Выбрать все")
        self.clear_all_btn = QPushButton("Очистить")

        btn_layout.addWidget(self.select_all_btn)
        btn_layout.addWidget(self.clear_all_btn)
        btn_layout.addStretch()

        layout.addLayout(btn_layout)

        # Кнопки OK/Cancel
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self._on_accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

        # Подключаем сигналы
        self.select_all_btn.clicked.connect(self._select_all)
        self.clear_all_btn.clicked.connect(self._clear_all)

    def _load_topics(self):
        """Загружает темы в список"""
        topics = self._topic_repo.get_all()

        self.topic_list.clear()

        # Добавляем пункт "Все темы"
        all_item = QListWidgetItem("📚 Все темы")
        all_item.setData(Qt.UserRole, -1)
        all_item.setSelected(True)
        self.topic_list.addItem(all_item)

        for topic in topics:
            if topic['type'] == 'topic':
                item = QListWidgetItem(f"📁 {topic['name']}")
                item.setData(Qt.UserRole, topic['id'])
                self.topic_list.addItem(item)

    def _select_all(self):
        """Выбирает все темы"""
        for i in range(self.topic_list.count()):
            self.topic_list.item(i).setSelected(True)

    def _clear_all(self):
        """Очищает выбор"""
        self.topic_list.clearSelection()

    def _on_accept(self):
        """Обработчик OK"""
        selected = []
        for item in self.topic_list.selectedItems():
            topic_id = item.data(Qt.UserRole)
            if topic_id == -1:
                # Все темы
                selected = []
                for i in range(self.topic_list.count()):
                    tid = self.topic_list.item(i).data(Qt.UserRole)
                    if tid != -1:
                        selected.append(tid)
                break
            else:
                selected.append(topic_id)

        self.topics_selected.emit(selected)
        self.accept()

    def get_selected_topics(self) -> list:
        """Возвращает список выбранных ID тем"""
        return self._selected_topics