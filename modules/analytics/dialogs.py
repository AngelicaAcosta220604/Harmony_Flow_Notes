# modules/analytics/dialogs.py
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QListWidget,
    QListWidgetItem, QPushButton, QDialogButtonBox
)
from PySide6.QtCore import Qt, Signal

from database.repositories.topic_repo import TopicRepository


class AnalyticsSelectorDialog(QDialog):
    """
    Диалог выбора тем для аналитики с чекбоксами.
    """

    topics_selected = Signal(list)  # list of topic_ids

    def __init__(self, parent=None):
        super().__init__(parent)
        self._topic_repo = TopicRepository()
        self._setup_ui()
        self._load_topics()

    def _setup_ui(self):
        """Настраивает интерфейс"""
        self.setWindowTitle("Выбор тем для аналитики")
        self.setMinimumSize(450, 550)

        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # Инструкция
        label = QLabel("✅ Отметьте темы для анализа (можно несколько):")
        label.setStyleSheet("font-weight: bold; color: #1E2A3E;")
        layout.addWidget(label)

        # Список тем с чекбоксами
        self.topic_list = QListWidget()
        self.topic_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #E5E7EB;
                border-radius: 8px;
                padding: 8px;
                background-color: #FFFFFF;
            }
            QListWidget::item {
                padding: 8px;
                border-radius: 4px;
                spacing: 10px;
            }
            QListWidget::item:selected {
                background-color: #EFF6FF;
                color: #1E2A3E;
            }
            QListWidget::item:hover {
                background-color: #F3F4F6;
            }
        """)
        layout.addWidget(self.topic_list)

        # Кнопки выбора всех/очистить
        btn_layout = QHBoxLayout()

        self.select_all_btn = QPushButton("✓ Выбрать все")
        self.clear_all_btn = QPushButton("✗ Очистить")

        self.select_all_btn.setStyleSheet("""
            QPushButton {
                background-color: #10B981;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #059669;
            }
        """)

        self.clear_all_btn.setStyleSheet("""
            QPushButton {
                background-color: #EF4444;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #DC2626;
            }
        """)

        btn_layout.addWidget(self.select_all_btn)
        btn_layout.addWidget(self.clear_all_btn)
        btn_layout.addStretch()

        layout.addLayout(btn_layout)

        # Кнопки OK/Cancel
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.setStyleSheet("""
            QPushButton {
                background-color: #3B82F6;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 20px;
                font-weight: 500;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #2563EB;
            }
            QPushButton:disabled {
                background-color: #9CA3AF;
            }
        """)
        self.button_box.accepted.connect(self._on_accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

        # Подключаем сигналы
        self.select_all_btn.clicked.connect(self._select_all)
        self.clear_all_btn.clicked.connect(self._clear_all)

    def _load_topics(self):
        """Загружает темы в список с чекбоксами"""
        topics = self._topic_repo.get_all()

        self.topic_list.clear()

        # Добавляем пункт "Все темы"
        all_item = QListWidgetItem("📚 Все темы")
        all_item.setData(Qt.UserRole, -1)
        all_item.setCheckState(Qt.Checked)
        all_item.setFlags(all_item.flags() | Qt.ItemIsUserCheckable)
        # Отключаем возможность снять "Все темы"
        all_item.setFlags(all_item.flags() & ~Qt.ItemIsUserCheckable)
        self.topic_list.addItem(all_item)

        # Добавляем разделитель
        separator = QListWidgetItem()
        separator.setFlags(Qt.NoItemFlags)
        separator.setText("---")
        separator.setBackground(QColor("#F3F4F6"))
        self.topic_list.addItem(separator)

        for topic in topics:
            if topic['type'] == 'topic':
                item = QListWidgetItem(f"📁 {topic['name']}")
                item.setData(Qt.UserRole, topic['id'])
                item.setCheckState(Qt.Unchecked)
                item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
                self.topic_list.addItem(item)

    def _select_all(self):
        """Выбирает все темы"""
        for i in range(self.topic_list.count()):
            item = self.topic_list.item(i)
            if item.data(Qt.UserRole) != -1 and item.flags() & Qt.ItemIsUserCheckable:
                item.setCheckState(Qt.Checked)

    def _clear_all(self):
        """Очищает выбор"""
        for i in range(self.topic_list.count()):
            item = self.topic_list.item(i)
            if item.data(Qt.UserRole) != -1 and item.flags() & Qt.ItemIsUserCheckable:
                item.setCheckState(Qt.Unchecked)

    def _on_accept(self):
        """Обработчик OK"""
        selected = []

        for i in range(self.topic_list.count()):
            item = self.topic_list.item(i)
            topic_id = item.data(Qt.UserRole)

            # Пропускаем "Все темы" и разделители
            if topic_id == -1 or topic_id is None:
                continue

            if item.checkState() == Qt.Checked:
                selected.append(topic_id)

        self.topics_selected.emit(selected)
        self.accept()

    def get_selected_topics(self) -> list:
        """Возвращает список выбранных ID тем"""
        selected = []
        for i in range(self.topic_list.count()):
            item = self.topic_list.item(i)
            topic_id = item.data(Qt.UserRole)
            if topic_id and topic_id != -1 and item.checkState() == Qt.Checked:
                selected.append(topic_id)
        return selected
# class AnalyticsSelectorDialog(QDialog):
#     """
#     Диалог выбора тем для аналитики.
#     """
#
#     topics_selected = Signal(list)  # list of topic_ids
#
#     def __init__(self, parent=None):
#         super().__init__(parent)
#         self._topic_repo = TopicRepository()
#         self._selected_topics = []
#         self._setup_ui()
#         self._load_topics()
#
#     def _setup_ui(self):
#         """Настраивает интерфейс"""
#         self.setWindowTitle("Выбор тем для аналитики")
#         self.setMinimumSize(400, 500)
#
#         layout = QVBoxLayout(self)
#         layout.setSpacing(10)
#
#         # Инструкция
#         label = QLabel("Выберите темы для анализа (можно несколько):")
#         layout.addWidget(label)
#
#         # Список тем
#         self.topic_list = QListWidget()
#         self.topic_list.setSelectionMode(QListWidget.MultiSelection)
#         layout.addWidget(self.topic_list)
#
#         # Кнопки выбора всех/очистить
#         btn_layout = QHBoxLayout()
#
#         self.select_all_btn = QPushButton("Выбрать все")
#         self.clear_all_btn = QPushButton("Очистить")
#
#         btn_layout.addWidget(self.select_all_btn)
#         btn_layout.addWidget(self.clear_all_btn)
#         btn_layout.addStretch()
#
#         layout.addLayout(btn_layout)
#
#         # Кнопки OK/Cancel
#         self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
#         self.button_box.accepted.connect(self._on_accept)
#         self.button_box.rejected.connect(self.reject)
#         layout.addWidget(self.button_box)
#
#         # Подключаем сигналы
#         self.select_all_btn.clicked.connect(self._select_all)
#         self.clear_all_btn.clicked.connect(self._clear_all)
#
#     def _load_topics(self):
#         """Загружает темы в список с чекбоксами"""
#         topics = self._topic_repo.get_all()
#
#         self.topic_list.clear()
#
#         # Добавляем пункт "Все темы"
#         all_item = QListWidgetItem("📚 Все темы")
#         all_item.setData(Qt.UserRole, -1)
#         all_item.setCheckState(Qt.Checked)
#         self.topic_list.addItem(all_item)
#
#         for topic in topics:
#             if topic['type'] == 'topic':
#                 item = QListWidgetItem(f"📁 {topic['name']}")
#                 item.setData(Qt.UserRole, topic['id'])
#                 item.setCheckState(Qt.Unchecked)
#                 item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
#                 self.topic_list.addItem(item)
#
#     def _select_all(self):
#         """Выбирает все темы"""
#         for i in range(self.topic_list.count()):
#             self.topic_list.item(i).setSelected(True)
#
#     def _clear_all(self):
#         """Очищает выбор"""
#         self.topic_list.clearSelection()
#
#     def _on_accept(self):
#         """Обработчик OK"""
#         selected = []
#         all_checked = False
#
#         for i in range(self.topic_list.count()):
#             item = self.topic_list.item(i)
#             topic_id = item.data(Qt.UserRole)
#
#             if topic_id == -1:
#                 if item.checkState() == Qt.Checked:
#                     all_checked = True
#             else:
#                 if item.checkState() == Qt.Checked:
#                     selected.append(topic_id)
#
#         if all_checked:
#             # Если выбрано "Все темы", возвращаем пустой список (все темы)
#             selected = []
#
#         self.topics_selected.emit(selected)
#         self.accept()
#
#     def get_selected_topics(self) -> list:
#         """Возвращает список выбранных ID тем"""
#         return self._selected_topics