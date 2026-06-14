# modules/tasks/calendar_view.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame
)
from PySide6.QtCore import Qt, Signal, QDate

from .calendar_controller import CalendarController
from .widgets import CalendarWidget
from models.task import Task


class CalendarView(QWidget):
    """
    Календарь задач с отображением задач по дням.
    """

    task_clicked = Signal(int)  # (task_id)

    def __init__(self, controller: CalendarController, parent=None):
        super().__init__(parent)
        self._controller = controller
        self._current_date = QDate.currentDate()
        self._setup_ui()
        self._connect_signals()
        self._load_month_tasks()

    def _setup_ui(self):
        """Настраивает интерфейс"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Заголовок
        header_layout = QHBoxLayout()

        title_label = QLabel("📅 Календарь задач")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        header_layout.addWidget(title_label)

        header_layout.addStretch()

        layout.addLayout(header_layout)

        # Основная область (календарь + список задач)
        main_layout = QHBoxLayout()

        # Календарь
        self.calendar = CalendarWidget()
        main_layout.addWidget(self.calendar, 2)

        # Список задач на выбранный день
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(10, 0, 0, 0)

        self.selected_date_label = QLabel()
        self.selected_date_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        right_layout.addWidget(self.selected_date_label)

        self.tasks_scroll = QScrollArea()
        self.tasks_scroll.setWidgetResizable(True)
        self.tasks_scroll.setFrameShape(QFrame.NoFrame)

        self.tasks_container = QWidget()
        self.tasks_layout = QVBoxLayout(self.tasks_container)
        self.tasks_layout.setAlignment(Qt.AlignTop)

        self.tasks_scroll.setWidget(self.tasks_container)
        right_layout.addWidget(self.tasks_scroll)

        main_layout.addWidget(right_widget, 1)
        layout.addLayout(main_layout)

    def _connect_signals(self):
        """Подключает сигналы"""
        self.calendar.date_selected.connect(self._on_date_selected)

    def _load_month_tasks(self):
        """Загружает задачи на текущий месяц для подсветки"""
        year = self._current_date.year()
        month = self._current_date.month()

        task_counts = self._controller.get_task_count_for_month(year, month)
        self.calendar.set_task_dates(list(task_counts.keys()))

    def _on_date_selected(self, date: QDate):
        """Обработчик выбора даты в календаре"""
        self._current_date = date

        # Обновляем заголовок
        self.selected_date_label.setText(date.toString("dddd, d MMMM yyyy"))

        # Загружаем задачи на выбранный день
        tasks = self._controller.get_tasks_for_day(date.toPython())
        self._display_tasks(tasks)

    def _display_tasks(self, tasks: list):
        """Отображает задачи для выбранного дня"""
        # Очищаем
        while self.tasks_layout.count():
            child = self.tasks_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        if not tasks:
            empty_label = QLabel("Нет задач на этот день")
            empty_label.setAlignment(Qt.AlignCenter)
            empty_label.setStyleSheet("color: #888888; padding: 20px;")
            self.tasks_layout.addWidget(empty_label)
            return

        for task in tasks:
            task_widget = self._create_task_widget(task)
            self.tasks_layout.addWidget(task_widget)

    def _create_task_widget(self, task: Task) -> QWidget:
        """Создаёт виджет задачи"""
        from .dialogs import TaskViewDialog

        widget = QFrame()
        widget.setFrameShape(QFrame.StyledPanel)
        widget.setCursor(Qt.PointingHandCursor)

        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(4)

        # Название
        title_label = QLabel(task.title)
        title_label.setStyleSheet("font-weight: bold;")
        if task.is_overdue():
            title_label.setStyleSheet("font-weight: bold; color: #f44336;")
        layout.addWidget(title_label)

        # Описание (если есть)
        if task.description:
            desc_label = QLabel(task.description[:100])
            desc_label.setStyleSheet("color: #666666; font-size: 11px;")
            desc_label.setWordWrap(True)
            layout.addWidget(desc_label)

        # Время дедлайна
        if task.deadline:
            from services.time_service import TimeService
            time_label = QLabel(f"🕐 {TimeService.format_time_from_iso(task.deadline)}")
            time_label.setStyleSheet("color: #888888; font-size: 10px;")
            layout.addWidget(time_label)

        widget.mousePressEvent = lambda e: self.task_clicked.emit(task.id)

        return widget

    def refresh(self):
        """Обновляет календарь"""
        self._load_month_tasks()
        self._on_date_selected(self._current_date)