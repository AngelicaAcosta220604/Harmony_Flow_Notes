# modules/tasks/global_view.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QListWidget, QListWidgetItem, QStackedWidget, QTextEdit,
    QComboBox, QLineEdit, QDialog, QFrame, QScrollArea, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QIcon, QPixmap
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
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("background-color: transparent; border: none;")

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setSpacing(20)

        # ========== ЗАГОЛОВОК (белая плашка) ==========
        header_widget = QWidget()
        header_widget.setStyleSheet("""
            QWidget {
                background-color: #FFFFFF;
                border-radius: 16px;
                border: none;
            }
        """)
        header_widget.setFixedHeight(80)

        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(20, 0, 20, 0)
        header_layout.setSpacing(12)
        header_layout.setAlignment(Qt.AlignCenter)

        header_icon = QLabel()
        header_pixmap = QPixmap("resources/icons/task1.png")
        if not header_pixmap.isNull():
            header_pixmap = header_pixmap.scaled(32, 32, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            header_icon.setPixmap(header_pixmap)
        header_layout.addWidget(header_icon)

        header_title = QLabel("Все задачи")
        header_title.setStyleSheet("font-size: 20px; font-weight: bold; color: #1F2937;")
        header_layout.addWidget(header_title)

        content_layout.addWidget(header_widget)

        # ========== ПЛАШКА ФИЛЬТРОВ (Статус, Тема, Период) ==========
        filters_widget = QFrame()
        filters_widget.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border-radius: 16px;
                border: none;
            }
        """)
        filters_widget.setMinimumHeight(70)

        filters_layout = QHBoxLayout(filters_widget)
        filters_layout.setContentsMargins(20, 12, 20, 12)
        filters_layout.setSpacing(24)

        # Статус
        status_layout = QHBoxLayout()
        status_layout.setSpacing(8)
        status_label = QLabel("Статус:")
        status_label.setStyleSheet("color: #6B7280; font-size: 13px; font-weight: 500;")
        self.status_filter = QComboBox()
        self.status_filter.addItem("Все", "all")
        self.status_filter.addItem("Активные", "active")
        self.status_filter.addItem("Выполненные", "completed")
        self.status_filter.addItem("Просроченные", "overdue")
        self.status_filter.setStyleSheet("""
            QComboBox {
                background-color: #F0F4F8;
                border: 1px solid #E6EEF6;
                border-radius: 8px;
                padding: 6px 12px;
                min-width: 120px;
                font-size: 13px;
            }
            QComboBox:hover {
                border: 1px solid #3B82F6;
            }
        """)
        status_layout.addWidget(status_label)
        status_layout.addWidget(self.status_filter)
        filters_layout.addLayout(status_layout)

        # Тема
        topic_layout = QHBoxLayout()
        topic_layout.setSpacing(8)
        topic_label = QLabel("Тема:")
        topic_label.setStyleSheet("color: #6B7280; font-size: 13px; font-weight: 500;")
        self.topic_filter = QComboBox()
        self.topic_filter.addItem("Все темы", None)
        self.topic_filter.addItem("Общие задачи", -1)
        self.topic_filter.setStyleSheet("""
            QComboBox {
                background-color: #F0F4F8;
                border: 1px solid #E6EEF6;
                border-radius: 8px;
                padding: 6px 12px;
                min-width: 150px;
                font-size: 13px;
            }
            QComboBox:hover {
                border: 1px solid #3B82F6;
            }
        """)
        topic_layout.addWidget(topic_label)
        topic_layout.addWidget(self.topic_filter)
        filters_layout.addLayout(topic_layout)

        # Период
        period_layout = QHBoxLayout()
        period_layout.setSpacing(8)
        period_label = QLabel("Период:")
        period_label.setStyleSheet("color: #6B7280; font-size: 13px; font-weight: 500;")
        self.period_filter = QComboBox()
        self.period_filter.addItem("Все", "all")
        self.period_filter.addItem("Сегодня", "today")
        self.period_filter.addItem("Завтра", "tomorrow")
        self.period_filter.addItem("Эта неделя", "week")
        self.period_filter.addItem("Этот месяц", "month")
        self.period_filter.addItem("Просроченные", "overdue_only")
        self.period_filter.setStyleSheet("""
            QComboBox {
                background-color: #F0F4F8;
                border: 1px solid #E6EEF6;
                border-radius: 8px;
                padding: 6px 12px;
                min-width: 140px;
                font-size: 13px;
            }
            QComboBox:hover {
                border: 1px solid #3B82F6;
            }
        """)
        period_layout.addWidget(period_label)
        period_layout.addWidget(self.period_filter)
        filters_layout.addLayout(period_layout)

        filters_layout.addStretch()
        content_layout.addWidget(filters_widget)

        # ========== ПЛАШКА ПОИСКА И НОВОЙ ЗАДАЧИ ==========
        search_widget = QFrame()
        search_widget.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border-radius: 16px;
                border: none;
            }
        """)
        search_widget.setMinimumHeight(70)

        search_layout = QHBoxLayout(search_widget)
        search_layout.setContentsMargins(20, 12, 20, 12)
        search_layout.setSpacing(16)

        # Поиск
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Поиск задач...")
        self.search_edit.setFixedWidth(300)
        self.search_edit.setStyleSheet("""
            QLineEdit {
                background-color: #F0F4F8;
                border: 1px solid #E6EEF6;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border: 1px solid #3B82F6;
                background-color: #FFFFFF;
            }
        """)
        search_layout.addWidget(self.search_edit)

        search_layout.addStretch()

        # Новая задача
        self.new_btn = QPushButton("Новая задача")
        self.new_btn.setIcon(QIcon("resources/icons/task1.png"))
        self.new_btn.setIconSize(QSize(18, 18))
        self.new_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(59, 130, 246, 0.15);
                color: #3B82F6;
                border: 1px solid #3B82F6;
                border-radius: 12px;
                padding: 8px 20px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: rgba(59, 130, 246, 0.25);
                border: 1px solid #2563EB;
                color: #2563EB;
            }
        """)
        search_layout.addWidget(self.new_btn)

        content_layout.addWidget(search_widget)

        # ========== ОСНОВНАЯ ОБЛАСТЬ (список задач + детали) ==========
        main_layout = QHBoxLayout()
        main_layout.setSpacing(20)

        # Список задач
        self.task_list = QListWidget()
        self.task_list.setStyleSheet("""
            QListWidget {
                background-color: #FFFFFF;
                border-radius: 16px;
                border: none;
                padding: 8px;
                min-height: 400px;
            }
            QListWidget::item {
                padding: 10px 12px;
                border-radius: 8px;
                margin: 2px;
            }
            QListWidget::item:hover {
                background-color: #F9FAFB;
            }
            QListWidget::item:selected {
                background-color: #EBF5FF;
                color: #3B82F6;
            }
        """)
        main_layout.addWidget(self.task_list, 1)

        # Область просмотра
        self.stack = QStackedWidget()
        self.stack.setStyleSheet("""
            QStackedWidget {
                background-color: #FFFFFF;
                border-radius: 16px;
                border: none;
            }
        """)

        empty_widget = QWidget()
        empty_layout = QVBoxLayout(empty_widget)
        empty_layout.setAlignment(Qt.AlignCenter)
        empty_label = QLabel("Выберите задачу для просмотра")
        empty_label.setStyleSheet("color: #6B7280; font-size: 14px;")
        empty_layout.addWidget(empty_label)
        self.stack.addWidget(empty_widget)

        self.detail_widget = QWidget()
        detail_layout = QVBoxLayout(self.detail_widget)
        detail_layout.setContentsMargins(24, 24, 24, 24)
        detail_layout.setSpacing(16)

        self.detail_title = QLabel()
        self.detail_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #1F2937;")
        detail_layout.addWidget(self.detail_title)

        self.detail_desc = QTextEdit()
        self.detail_desc.setReadOnly(True)
        self.detail_desc.setMinimumHeight(150)
        self.detail_desc.setStyleSheet("""
            QTextEdit {
                border: 1px solid #E6EEF6;
                border-radius: 12px;
                padding: 12px;
                background-color: #F9FAFB;
                color: #1F2937;
            }
        """)
        detail_layout.addWidget(self.detail_desc)

        self.detail_deadline = QLabel()
        self.detail_deadline.setStyleSheet("color: #6B7280; font-size: 13px;")
        detail_layout.addWidget(self.detail_deadline)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)

        self.complete_btn = QPushButton("Выполнить")
        self.complete_btn.setIcon(QIcon("resources/icons/check.png"))
        self.complete_btn.setIconSize(QSize(16, 16))
        self.complete_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(16, 185, 129, 0.15);
                color: #059669;
                border: 1px solid #10B981;
                border-radius: 12px;
                padding: 8px 16px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: rgba(16, 185, 129, 0.25);
                border: 1px solid #059669;
                color: #047857;
            }
        """)
        btn_layout.addWidget(self.complete_btn)

        self.edit_btn = QPushButton("Редактировать")
        self.edit_btn.setIcon(QIcon("resources/icons/rename1.png"))
        self.edit_btn.setIconSize(QSize(16, 16))
        self.edit_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(245, 158, 11, 0.15);
                color: #D97706;
                border: 1px solid #F59E0B;
                border-radius: 12px;
                padding: 8px 16px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: rgba(245, 158, 11, 0.25);
                border: 1px solid #D97706;
                color: #B45309;
            }
        """)
        btn_layout.addWidget(self.edit_btn)

        self.delete_btn = QPushButton("Удалить")
        self.delete_btn.setIcon(QIcon("resources/icons/delete1.png"))
        self.delete_btn.setIconSize(QSize(16, 16))
        self.delete_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(239, 68, 68, 0.15);
                color: #EF4444;
                border: 1px solid #EF4444;
                border-radius: 12px;
                padding: 8px 16px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: rgba(239, 68, 68, 0.25);
                border: 1px solid #DC2626;
                color: #DC2626;
            }
        """)
        btn_layout.addWidget(self.delete_btn)

        btn_layout.addStretch()
        detail_layout.addLayout(btn_layout)

        self.stack.addWidget(self.detail_widget)

        main_layout.addWidget(self.stack, 1)
        content_layout.addLayout(main_layout)

        content_layout.addStretch()

        scroll.setWidget(content)
        layout.addWidget(scroll)

        self._load_topics_to_filter()

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
            empty_item = QListWidgetItem("Нет задач")
            empty_item.setForeground(Qt.gray)
            self.task_list.addItem(empty_item)
            self.stack.setCurrentIndex(0)
            return

        for task in tasks:
            item = QListWidgetItem()
            topic_name = self._controller.get_topic_name(task)

            if task.status == 'completed':
                icon = "✅"
            elif task.is_overdue():
                icon = "⚠️"
            else:
                icon = "🟢"

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
            self.detail_deadline.setStyleSheet("color: #EF4444;" if task.is_overdue() else "color: #6B7280;")
        else:
            self.detail_deadline.setText("⏰ Без дедлайна")

        self.complete_btn.setEnabled(task.status != 'completed')
        self.complete_btn.setText("Выполнить" if task.status != 'completed' else "Выполнена")

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