# modules/tasks/widgets.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QCalendarWidget, QTextEdit, QCheckBox
)
from PySide6.QtCore import Qt, Signal, QDate
from PySide6.QtGui import QTextCharFormat, QColor


class CalendarWidget(QCalendarWidget):
    """
    Календарь с подсветкой дней, на которые есть задачи.
    """

    date_selected = Signal(QDate)  # (date)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._task_dates = set()

    def _setup_ui(self):
        """Настраивает календарь"""
        self.clicked.connect(self.date_selected.emit)
        self.setGridVisible(True)
        self.setVerticalHeaderFormat(QCalendarWidget.NoVerticalHeader)

    def set_task_dates(self, dates: list):
        """
        Устанавливает даты, на которые есть задачи

        Args:
            dates: Список строк в формате YYYY-MM-DD
        """
        self._task_dates = set(dates)
        self.updateCells()

    def paintCell(self, painter, rect, date: QDate):
        """Переопределённый метод для отрисовки ячейки"""
        super().paintCell(painter, rect, date)

        # Проверяем, есть ли задачи на эту дату
        date_str = date.toString("yyyy-MM-dd")

        if date_str in self._task_dates:
            # Рисуем маркер
            painter.save()
            painter.setBrush(QColor(76, 175, 80))  # зелёный
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(rect.right() - 12, rect.top() + 4, 6, 6)
            painter.restore()

    def clear_task_dates(self):
        """Очищает подсвеченные даты"""
        self._task_dates.clear()
        self.updateCells()


class TaskPreviewWidget(QWidget):
    """
    Виджет предпросмотра задачи для списка.
    """

    task_clicked = Signal(int)  # (task_id)

    def __init__(self, task_id: int, title: str, topic_name: str, deadline: str, is_overdue: bool, parent=None):
        super().__init__(parent)
        self.task_id = task_id
        self._setup_ui(title, topic_name, deadline, is_overdue)

    def _setup_ui(self, title: str, topic_name: str, deadline: str, is_overdue: bool):
        """Настраивает интерфейс"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(4)

        # Заголовок
        self.setCursor(Qt.PointingHandCursor)

        header_layout = QHBoxLayout()

        title_label = QLabel(title)
        title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        if is_overdue:
            title_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #f44336;")

        header_layout.addWidget(title_label)
        header_layout.addStretch()

        # Тема и дедлайн
        info_layout = QHBoxLayout()

        topic_label = QLabel(f"📁 {topic_name}")
        topic_label.setStyleSheet("color: #666666; font-size: 11px;")
        info_layout.addWidget(topic_label)

        info_layout.addSpacing(20)

        deadline_label = QLabel(f"⏰ {deadline}")
        deadline_label.setStyleSheet("color: #666666; font-size: 11px;")
        if is_overdue:
            deadline_label.setStyleSheet("color: #f44336; font-size: 11px;")

        info_layout.addWidget(deadline_label)
        info_layout.addStretch()

        layout.addLayout(header_layout)
        layout.addLayout(info_layout)

        self.setProperty("class", "task-preview")

    def mousePressEvent(self, event):
        """Обработчик клика"""
        self.task_clicked.emit(self.task_id)
        super().mousePressEvent(event)

