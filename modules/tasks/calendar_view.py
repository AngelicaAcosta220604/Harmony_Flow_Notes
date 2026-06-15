# modules/tasks/calendar_view.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QComboBox, QSizePolicy, QLineEdit
)
from PySide6.QtCore import Qt, Signal, QDate, QSize
from PySide6.QtGui import QIcon, QPixmap

from .calendar_controller import CalendarController
from .widgets import CalendarWidget
from models.task import Task


class CalendarView(QWidget):
    """
    Календарь задач с отображением задач по дням.
    """

    task_clicked = Signal(int)
    new_task_requested = Signal()

    def __init__(self, controller: CalendarController, parent=None):
        super().__init__(parent)
        self._controller = controller
        self._current_date = QDate.currentDate()
        self._setup_ui()
        self._connect_signals()
        self._load_month_tasks()

    def _setup_ui(self):
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

        # ========== ЗАГОЛОВОК ==========
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
        header_pixmap = QPixmap("resources/icons/calendar.png")
        if not header_pixmap.isNull():
            header_pixmap = header_pixmap.scaled(32, 32, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            header_icon.setPixmap(header_pixmap)
        header_layout.addWidget(header_icon)

        header_title = QLabel("Календарь задач")
        header_title.setStyleSheet("font-size: 20px; font-weight: bold; color: #1F2937;")
        header_layout.addWidget(header_title)

        content_layout.addWidget(header_widget)

        # ========== РЯД ИЗ ДВУХ ПЛАШЕК ==========
        row_layout = QHBoxLayout()
        row_layout.setSpacing(20)

        # ----- ПЛАШКА 1: Выбор месяца и года -----
        date_widget = QFrame()
        date_widget.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border-radius: 16px;
                border: none;
            }
        """)
        date_widget.setMinimumHeight(70)
        date_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        date_layout = QHBoxLayout(date_widget)
        date_layout.setContentsMargins(20, 12, 20, 12)
        date_layout.setSpacing(16)

        # Месяц
        month_label = QLabel("Месяц:")
        month_label.setStyleSheet("color: #6B7280; font-size: 13px; font-weight: 500;")
        self.month_combo = QComboBox()
        months = ["Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
                  "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"]
        for m in months:
            self.month_combo.addItem(m)
        self.month_combo.setCurrentIndex(self._current_date.month() - 1)
        self.month_combo.setStyleSheet("""
            QComboBox {
                background-color: #F0F4F8;
                border: 1px solid #E6EEF6;
                border-radius: 8px;
                padding: 6px 12px;
                min-width: 120px;
                font-size: 13px;
                color: #1F2937;
            }
            QComboBox:hover {
                border: 1px solid #3B82F6;
            }
        """)
        date_layout.addWidget(month_label)
        date_layout.addWidget(self.month_combo)

        # Год
        year_label = QLabel("Год:")
        year_label.setStyleSheet("color: #6B7280; font-size: 13px; font-weight: 500;")
        self.year_combo = QComboBox()
        current_year = self._current_date.year()
        for y in range(current_year - 5, current_year + 5):
            self.year_combo.addItem(str(y))
        self.year_combo.setCurrentText(str(current_year))
        self.year_combo.setStyleSheet("""
            QComboBox {
                background-color: #F0F4F8;
                border: 1px solid #E6EEF6;
                border-radius: 8px;
                padding: 6px 12px;
                min-width: 80px;
                font-size: 13px;
                color: #1F2937;
            }
            QComboBox:hover {
                border: 1px solid #3B82F6;
            }
        """)
        date_layout.addWidget(year_label)
        date_layout.addWidget(self.year_combo)
        date_layout.addStretch()

        row_layout.addWidget(date_widget, 1)

        # ----- ПЛАШКА 2: Поиск и новая задача -----
        search_widget = QFrame()
        search_widget.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border-radius: 16px;
                border: none;
            }
        """)
        search_widget.setMinimumHeight(70)
        search_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        search_layout = QHBoxLayout(search_widget)
        search_layout.setContentsMargins(20, 12, 20, 12)
        search_layout.setSpacing(16)

        # Поле поиска
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Поиск задач...")
        self.search_edit.setFixedWidth(250)
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

        # Кнопка новой задачи
        self.new_task_btn = QPushButton("Новая задача")
        self.new_task_btn.setIcon(QIcon("resources/icons/notes.png"))
        self.new_task_btn.setIconSize(QSize(18, 18))
        self.new_task_btn.setStyleSheet("""
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
        search_layout.addWidget(self.new_task_btn)

        row_layout.addWidget(search_widget, 1)
        content_layout.addLayout(row_layout)

        # ========== ОСНОВНАЯ ОБЛАСТЬ ==========
        main_layout = QHBoxLayout()
        main_layout.setSpacing(20)

        # Календарь
        self.calendar = CalendarWidget()
        main_layout.addWidget(self.calendar, 2)

        # Плашка задач на день
        tasks_widget = QFrame()
        tasks_widget.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border-radius: 16px;
                border: none;
            }
        """)

        tasks_layout = QVBoxLayout(tasks_widget)
        tasks_layout.setContentsMargins(16, 16, 16, 16)
        tasks_layout.setSpacing(12)

        tasks_title_layout = QHBoxLayout()
        tasks_icon = QLabel()
        tasks_icon_pixmap = QPixmap("resources/icons/tack.png")
        if not tasks_icon_pixmap.isNull():
            tasks_icon_pixmap = tasks_icon_pixmap.scaled(20, 20, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            tasks_icon.setPixmap(tasks_icon_pixmap)
        tasks_title = QLabel("Задачи на день")
        tasks_title.setStyleSheet("font-weight: 600; color: #1F2937; font-size: 14px;")
        tasks_title_layout.addWidget(tasks_icon)
        tasks_title_layout.addWidget(tasks_title)
        tasks_title_layout.addStretch()
        tasks_layout.addLayout(tasks_title_layout)

        self.selected_date_label = QLabel()
        self.selected_date_label.setStyleSheet("font-size: 13px; color: #6B7280; margin-bottom: 8px;")
        tasks_layout.addWidget(self.selected_date_label)

        self.tasks_scroll = QScrollArea()
        self.tasks_scroll.setWidgetResizable(True)
        self.tasks_scroll.setFrameShape(QFrame.NoFrame)
        self.tasks_scroll.setStyleSheet("background-color: transparent; border: none;")

        self.tasks_container = QWidget()
        self.tasks_container.setStyleSheet("background-color: transparent;")
        self.tasks_layout_inner = QVBoxLayout(self.tasks_container)
        self.tasks_layout_inner.setAlignment(Qt.AlignTop)
        self.tasks_layout_inner.setSpacing(8)

        self.tasks_scroll.setWidget(self.tasks_container)
        tasks_layout.addWidget(self.tasks_scroll)

        main_layout.addWidget(tasks_widget, 1)
        content_layout.addLayout(main_layout)

        scroll.setWidget(content)
        layout.addWidget(scroll)

        # Подключаем сигналы
        self.month_combo.currentIndexChanged.connect(self._on_date_range_changed)
        self.year_combo.currentIndexChanged.connect(self._on_date_range_changed)
        self.search_edit.textChanged.connect(self._on_search_changed)

    def _connect_signals(self):
        self.calendar.date_selected.connect(self._on_date_selected)
        self.new_task_btn.clicked.connect(self.new_task_requested.emit)

    def _on_search_changed(self):
        self._load_month_tasks()

    def _on_date_range_changed(self):
        month = self.month_combo.currentIndex() + 1
        year = int(self.year_combo.currentText())
        self.calendar.setCurrentPage(year, month)
        self._load_month_tasks()
        new_date = QDate(year, month, 1)
        self._on_date_selected(new_date)

    def _load_month_tasks(self):
        current_date = self.calendar.selectedDate()
        year = current_date.year()
        month = current_date.month()
        task_counts = self._controller.get_task_count_for_month(year, month)
        self.calendar.set_task_dates(list(task_counts.keys()))

    def _on_date_selected(self, date: QDate):
        self._current_date = date
        self.selected_date_label.setText(date.toString("dddd, d MMMM yyyy"))
        tasks = self._controller.get_tasks_for_day(date.toPython())
        self._display_tasks(tasks)

    def _display_tasks(self, tasks: list):
        while self.tasks_layout_inner.count():
            child = self.tasks_layout_inner.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        if not tasks:
            empty_label = QLabel("Нет задач на этот день")
            empty_label.setAlignment(Qt.AlignCenter)
            empty_label.setStyleSheet("color: #9CA3AF; padding: 20px;")
            self.tasks_layout_inner.addWidget(empty_label)
            return

        for task in tasks:
            task_widget = self._create_task_widget(task)
            self.tasks_layout_inner.addWidget(task_widget)

    def _create_task_widget(self, task: Task) -> QWidget:
        widget = QFrame()
        widget.setCursor(Qt.PointingHandCursor)
        widget.setStyleSheet("""
            QFrame {
                background-color: #F9FAFB;
                border-radius: 12px;
                border: none;
            }
            QFrame:hover {
                background-color: #F0F4F8;
            }
        """)

        layout = QVBoxLayout(widget)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(6)

        title_label = QLabel(task.title)
        title_label.setStyleSheet("font-weight: 600; color: #1F2937;")
        if task.is_overdue():
            title_label.setStyleSheet("font-weight: 600; color: #EF4444;")
        layout.addWidget(title_label)

        if task.description:
            desc_label = QLabel(task.description[:80] + ("..." if len(task.description) > 80 else ""))
            desc_label.setStyleSheet("color: #6B7280; font-size: 11px;")
            desc_label.setWordWrap(True)
            layout.addWidget(desc_label)

        if task.deadline:
            from services.time_service import TimeService
            time_label = QLabel(f"⏰ {TimeService.format_time_from_iso(task.deadline)}")
            time_label.setStyleSheet("color: #6B7280; font-size: 10px;")
            layout.addWidget(time_label)

        if task.status == 'completed':
            status_label = QLabel("✓ Выполнена")
            status_label.setStyleSheet("color: #10B981; font-size: 10px;")
            layout.addWidget(status_label)

        widget.mousePressEvent = lambda e: self.task_clicked.emit(task.id)

        return widget

    def refresh(self):
        self._load_month_tasks()
        self._on_date_selected(self._current_date)