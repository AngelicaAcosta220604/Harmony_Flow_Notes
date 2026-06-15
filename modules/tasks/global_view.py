# modules/tasks/global_view.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QListWidget, QListWidgetItem, QStackedWidget, QTextEdit,
    QComboBox, QLineEdit, QDialog
)
from PySide6.QtCore import Qt, Signal
from datetime import datetime, timedelta, date

from modules.tasks.controller import TaskController
from modules.tasks.filters import TaskFilters
from modules.tasks.dialogs import TaskDialog
from datebase.repositories.topic_repo import TopicRepository
from widgets import SilentMessageBox


class GlobalTasksView(QWidget):
    """
    Глобальный экран задач с фильтрацией.
    """

    task_updated = Signal()

    def __init__(self, controller: TaskController, parent=None):
        super().__init__(parent)
        self._controller = controller
        self._topic_repo = TopicRepository()
        self._current_task = None
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

        filter_layout.addWidget(QLabel("Статус:"))
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

        filter_layout.addSpacing(20)

        filter_layout.addWidget(QLabel("Период:"))
        self.period_filter = QComboBox()
        self.period_filter.addItem("Все", "all")
        self.period_filter.addItem("Сегодня", "today")
        self.period_filter.addItem("Завтра", "tomorrow")
        self.period_filter.addItem("Эта неделя", "week")
        self.period_filter.addItem("Этот месяц", "month")
        self.period_filter.addItem("Просроченные", "overdue_only")
        filter_layout.addWidget(self.period_filter)

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
        self.task_list.setFixedWidth(400)
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
        self.status_filter.currentIndexChanged.connect(self._load_tasks)
        self.topic_filter.currentIndexChanged.connect(self._load_tasks)
        self.period_filter.currentIndexChanged.connect(self._load_tasks)
        self.search_edit.textChanged.connect(self._load_tasks)
        self.task_list.itemClicked.connect(self._on_task_selected)
        self.new_btn.clicked.connect(self._on_new_task)
        self.complete_btn.clicked.connect(self._on_complete_task)
        self.edit_btn.clicked.connect(self._on_edit_task)
        self.delete_btn.clicked.connect(self._on_delete_task)

    def _load_topics_to_filter(self):
        topics = self._topic_repo.get_all()
        for topic in topics:
            if topic['type'] == 'topic':
                self.topic_filter.addItem(topic['name'], topic['id'])

    def _load_tasks(self):
        self.task_list.clear()

        tasks = self._controller.get_all_tasks()

        # Фильтр по статусу
        status = self.status_filter.currentData()
        if status != 'all':
            tasks = TaskFilters.filter_by_status(tasks, status)

        # Фильтр по теме
        topic_id = self.topic_filter.currentData()
        if topic_id is not None:
            if topic_id == -1:
                tasks = [t for t in tasks if t.topic_id is None]
            else:
                tasks = [t for t in tasks if t.topic_id == topic_id]

        # Фильтр по периоду
        period = self.period_filter.currentData()
        if period != 'all':
            tasks = self._filter_by_period(tasks, period)

        # Поиск
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

            deadline_str = f" (до {task.deadline_display})" if task.deadline else ""
            item.setText(f"{icon} {task.title} [{topic_name}]{deadline_str}")
            item.setData(Qt.UserRole, task.id)
            self.task_list.addItem(item)

    def _filter_by_period(self, tasks, period):
        today = date.today()

        if period == 'today':
            return [t for t in tasks if t.deadline and t.deadline[:10] == today.isoformat()]
        elif period == 'tomorrow':
            tomorrow = today + timedelta(days=1)
            return [t for t in tasks if t.deadline and t.deadline[:10] == tomorrow.isoformat()]
        elif period == 'week':
            end_week = today + timedelta(days=7)
            return [t for t in tasks if t.deadline and today.isoformat() <= t.deadline[:10] <= end_week.isoformat()]
        elif period == 'month':
            if today.month == 12:
                end_month = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                end_month = today.replace(month=today.month + 1, day=1) - timedelta(days=1)
            return [t for t in tasks if t.deadline and today.isoformat() <= t.deadline[:10] <= end_month.isoformat()]
        elif period == 'overdue_only':
            return [t for t in tasks if t.is_overdue()]
        return tasks

    def _on_task_selected(self, item):
        task_id = item.data(Qt.UserRole)
        task = self._controller.get_task(task_id)
        if not task:
            return

        self._current_task = task
        self.stack.setCurrentIndex(1)

        self.detail_title.setText(task.title)
        self.detail_desc.setPlainText(task.description or "Нет описания")

        if task.deadline:
            deadline_dt = datetime.fromisoformat(task.deadline)
            deadline_display = deadline_dt.strftime("%d.%m.%Y %H:%M")
            self.detail_deadline.setText(f"⏰ Дедлайн: {deadline_display}")
            self.detail_deadline.setStyleSheet("color: #f44336;" if task.is_overdue() else "color: #888888;")
        else:
            self.detail_deadline.setText("⏰ Без дедлайна")

        self.complete_btn.setEnabled(task.status != 'completed')
        self.complete_btn.setText("✅ Выполнить" if task.status != 'completed' else "✅ Выполнена")

    def _on_new_task(self):
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
        if not hasattr(self, '_current_task'):
            return
        if self._controller.complete_task(self._current_task.id):
            self._load_tasks()
            self.task_updated.emit()
            SilentMessageBox.information(self, "Успех", "Задача выполнена!")

    def _on_edit_task(self):
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
        self._load_tasks()