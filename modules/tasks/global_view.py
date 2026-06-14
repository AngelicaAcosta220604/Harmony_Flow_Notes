# modules/tasks/global_view.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QListWidget, QListWidgetItem, QStackedWidget, QTextEdit,
    QComboBox, QLineEdit, QDialog
)
from PySide6.QtCore import Qt, Signal

from modules.tasks.controller import TaskController
from modules.tasks.filters import TaskFilters
from modules.tasks.dialogs import TaskDialog, TaskViewDialog
from datebase.repositories.topic_repo import TopicRepository
from services.time_service import TimeService
from widgets import SilentMessageBox


class GlobalTasksView(QWidget):
    """
    Глобальный экран задач с фильтрацией.
    """

    task_updated = Signal()  # когда изменилась задача

    def __init__(self, controller: TaskController, parent=None):
        super().__init__(parent)
        self._controller = controller
        self._topic_repo = TopicRepository()
        self._setup_ui()
        self._connect_signals()
        self._load_tasks()

    def _setup_ui(self):
        """Настраивает интерфейс"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Заголовок
        title_layout = QHBoxLayout()
        title_label = QLabel("✅ Все задачи")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        layout.addLayout(title_layout)

        # Панель фильтров
        filter_layout = QHBoxLayout()

        filter_layout.addWidget(QLabel("Фильтр:"))

        self.status_filter = QComboBox()
        self.status_filter.addItem("Все", "all")
        self.status_filter.addItem("Активные", "active")
        self.status_filter.addItem("Выполненные", "completed")
        self.status_filter.addItem("Просроченные", "overdue")
        filter_layout.addWidget(self.status_filter)

        filter_layout.addSpacing(20)

        filter_layout.addWidget(QLabel("Тема:"))

        self.topic_filter = QComboBox()
        self.topic_filter.addItem("Все темы", None)
        self.topic_filter.addItem("📁 Общие задачи", -1)
        self._load_topics_to_filter()
        filter_layout.addWidget(self.topic_filter)

        filter_layout.addStretch()

        # Поиск
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("🔍 Поиск задач...")
        self.search_edit.setFixedWidth(200)
        filter_layout.addWidget(self.search_edit)

        # Кнопка создания
        self.new_btn = QPushButton("➕ Новая задача")
        filter_layout.addWidget(self.new_btn)

        layout.addLayout(filter_layout)

        # Основная область
        main_layout = QHBoxLayout()

        # Список задач
        self.task_list = QListWidget()
        self.task_list.setFixedWidth(350)
        main_layout.addWidget(self.task_list)

        # Область просмотра
        self.stack = QStackedWidget()

        empty_widget = QWidget()
        empty_layout = QVBoxLayout(empty_widget)
        empty_label = QLabel("Выберите задачу для просмотра")
        empty_label.setAlignment(Qt.AlignCenter)
        empty_layout.addWidget(empty_label)
        self.stack.addWidget(empty_widget)

        self.detail_widget = QWidget()
        detail_layout = QVBoxLayout(self.detail_widget)

        self.detail_title = QLabel()
        self.detail_title.setStyleSheet("font-size: 16px; font-weight: bold;")
        detail_layout.addWidget(self.detail_title)

        self.detail_desc = QTextEdit()
        self.detail_desc.setReadOnly(True)
        detail_layout.addWidget(self.detail_desc)

        self.detail_deadline = QLabel()
        detail_layout.addWidget(self.detail_deadline)

        btn_layout = QHBoxLayout()
        self.complete_btn = QPushButton("✅ Выполнить")
        self.edit_btn = QPushButton("✏️ Редактировать")
        self.delete_btn = QPushButton("🗑️ Удалить")
        btn_layout.addWidget(self.complete_btn)
        btn_layout.addWidget(self.edit_btn)
        btn_layout.addWidget(self.delete_btn)
        btn_layout.addStretch()
        detail_layout.addLayout(btn_layout)

        self.stack.addWidget(self.detail_widget)

        main_layout.addWidget(self.stack, 1)
        layout.addLayout(main_layout)

    def _connect_signals(self):
        """Подключает сигналы"""
        self.status_filter.currentIndexChanged.connect(self._load_tasks)
        self.topic_filter.currentIndexChanged.connect(self._load_tasks)
        self.search_edit.textChanged.connect(self._load_tasks)
        self.task_list.itemClicked.connect(self._on_task_selected)
        self.new_btn.clicked.connect(self._on_new_task)
        self.complete_btn.clicked.connect(self._on_complete_task)
        self.edit_btn.clicked.connect(self._on_edit_task)
        self.delete_btn.clicked.connect(self._on_delete_task)

    def _load_topics_to_filter(self):
        """Загружает темы в фильтр"""
        topics = self._topic_repo.get_all()
        for topic in topics:
            if topic['type'] == 'topic':
                self.topic_filter.addItem(topic['name'], topic['id'])

    def _load_tasks(self):
        """Загружает и отображает задачи с учётом фильтров"""
        self.task_list.clear()

        tasks = self._controller.get_all_tasks()

        # Применяем фильтры
        status = self.status_filter.currentData()
        if status != 'all':
            tasks = TaskFilters.filter_by_status(tasks, status)

        topic_id = self.topic_filter.currentData()
        if topic_id is not None:
            if topic_id == -1:
                tasks = [t for t in tasks if t.topic_id is None]
            else:
                tasks = [t for t in tasks if t.topic_id == topic_id]

        query = self.search_edit.text()
        if query:
            tasks = TaskFilters.filter_by_search(tasks, query)

        tasks = TaskFilters.sort_by_priority(tasks)

        if not tasks:
            self.task_list.addItem("📭 Нет задач")
            self.stack.setCurrentIndex(0)
            return

        for task in tasks:
            item = QListWidgetItem()

            # Получаем название темы
            topic_name = self._controller.get_topic_name(task)

            # Иконка в зависимости от статуса
            if task.status == 'completed':
                icon = "✅"
            elif task.is_overdue():
                icon = "⚠️"
            else:
                icon = "⏳"

            item.setText(f"{icon} {task.title} [{topic_name}]")
            item.setData(Qt.UserRole, task.id)
            self.task_list.addItem(item)

    def _on_task_selected(self, item: QListWidgetItem):
        """Обработчик выбора задачи"""
        task_id = item.data(Qt.UserRole)
        task = self._controller.get_task(task_id)

        if not task:
            return

        self._current_task = task
        self.stack.setCurrentIndex(1)

        # Заполняем детали
        self.detail_title.setText(task.title)
        self.detail_desc.setPlainText(task.description or "Нет описания")

        if task.deadline:
            from datetime import datetime
            deadline_dt = datetime.fromisoformat(task.deadline)
            deadline_display = deadline_dt.strftime("%d.%m.%Y %H:%M")
            self.detail_deadline.setText(f"⏰ Дедлайн: {deadline_display}")
            self.detail_deadline.setStyleSheet("color: #f44336;" if task.is_overdue() else "color: #888888;")
        else:
            self.detail_deadline.setText("⏰ Без дедлайна")

        # Обновляем кнопки
        self.complete_btn.setEnabled(task.status != 'completed')
        self.complete_btn.setText("✅ Выполнить" if task.status != 'completed' else "✅ Выполнена")

    def _on_new_task(self):
        """Создание новой задачи"""
        dialog = TaskDialog(self)
        if dialog.exec() == QDialog.Accepted:
            try:
                data = dialog.get_task_data()
                task_id = self._controller.create_task(
                    title=data['title'],
                    description=data['description'],
                    topic_id=data['topic_id'],
                    deadline=data['deadline']
                )
                if task_id:
                    self._load_tasks()
                    self.task_updated.emit()
                    SilentMessageBox.information(self, "Успех", "Задача создана")
            except ValueError as e:
                SilentMessageBox.warning(self, "Ошибка", str(e))

    def _on_complete_task(self):
        """Выполнение задачи"""
        if not hasattr(self, '_current_task'):
            return

        if self._controller.complete_task(self._current_task.id):
            self._load_tasks()
            self.task_updated.emit()
            SilentMessageBox.information(self, "Успех", "Задача выполнена!")

    def _on_edit_task(self):
        """Редактирование задачи"""
        if not hasattr(self, '_current_task'):
            return

        dialog = TaskDialog(self, self._current_task)
        if dialog.exec() == QDialog.Accepted:
            try:
                data = dialog.get_task_data()
                self._controller.update_task(
                    self._current_task.id,
                    title=data['title'],
                    description=data['description'],
                    deadline=data['deadline']
                )
                self._load_tasks()
                self.task_updated.emit()
                SilentMessageBox.information(self, "Успех", "Задача обновлена")
            except ValueError as e:
                SilentMessageBox.warning(self, "Ошибка", str(e))

    def _on_delete_task(self):
        """Удаление задачи"""
        if not hasattr(self, '_current_task'):
            return

        reply = SilentMessageBox.question(
            self, "Подтверждение удаления",
            f"Удалить задачу «{self._current_task.title}»?"
        )

        if reply == SilentMessageBox.Yes:
            if self._controller.delete_task(self._current_task.id):
                self._load_tasks()
                self.task_updated.emit()
                self.stack.setCurrentIndex(0)

    def refresh(self):
        """Обновляет список"""
        self._load_tasks()