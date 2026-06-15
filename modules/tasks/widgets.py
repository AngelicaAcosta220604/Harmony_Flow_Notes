# modules/tasks/widgets.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QCalendarWidget, QTextEdit, QCheckBox, QToolButton
)
from PySide6.QtCore import Qt, Signal, QDate
from PySide6.QtGui import QTextCharFormat, QColor, QBrush, QPen


class CalendarWidget(QCalendarWidget):
    """
    Календарь с подсветкой дней, на которые есть задачи.
    Стилизован под общий дизайн HFlow.
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

        # Скрываем навигационные кнопки (влево/вправо)
        for btn in self.findChildren(QToolButton):
            btn.hide()

        # Скрываем выпадающий список месяца/года через стиль
        self.setStyleSheet("""
            QCalendarWidget {
                background-color: #FFFFFF;
                border-radius: 16px;
                border: none;
            }
            QCalendarWidget QWidget {
                background-color: #FFFFFF;
            }
            QCalendarWidget QToolButton {
                width: 0px;
                height: 0px;
                visibility: hidden;
            }
            QCalendarWidget QSpinBox {
                width: 0px;
                height: 0px;
                visibility: hidden;
            }
            QCalendarWidget QMenu {
                background-color: #FFFFFF;
                border: 1px solid #E6EEF6;
                border-radius: 8px;
            }
        """)

    def paintCell(self, painter, rect, date: QDate):
        """Переопределённый метод для отрисовки ячейки"""
        # Шапка таблицы (дни недели) — голубая
        is_header = (date.day() == 0)  # QCalendarWidget не даёт прямого доступа, делаем через проверку

        # Рисуем фон ячейки
        if date == QDate.currentDate():
            # Активная ячейка (сегодня) — голубая обводка
            painter.save()
            painter.setBrush(Qt.white)
            painter.setPen(QPen(QColor(59, 130, 246), 2))
            painter.drawRect(rect.adjusted(1, 1, -1, -1))
            painter.restore()
        elif date == self.selectedDate():
            # Выбранная ячейка
            painter.save()
            painter.setBrush(QColor(235, 245, 255))  # #EBF5FF
            painter.setPen(Qt.NoPen)
            painter.drawRect(rect)
            painter.restore()

        # Рисуем текст
        super().paintCell(painter, rect, date)

        # Проверяем, есть ли задачи на эту дату (зелёный маркер)
        date_str = date.toString("yyyy-MM-dd")
        if date_str in self._task_dates:
            painter.save()
            painter.setBrush(QColor(16, 185, 129))  # #10B981 — зелёный
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(rect.right() - 14, rect.top() + 4, 6, 6)
            painter.restore()

    def set_task_dates(self, dates: list):
        """Устанавливает даты, на которые есть задачи"""
        self._task_dates = set(dates)
        self.updateCells()

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
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(6)

        self.setCursor(Qt.PointingHandCursor)

        # Карточка с тенью при наведении
        self.setStyleSheet("""
            TaskPreviewWidget {
                background-color: #F9FAFB;
                border-radius: 12px;
                border: none;
            }
            TaskPreviewWidget:hover {
                background-color: #F0F4F8;
            }
        """)

        header_layout = QHBoxLayout()

        title_label = QLabel(title)
        title_label.setStyleSheet("font-weight: 600; color: #1F2937; font-size: 14px;")
        if is_overdue:
            title_label.setStyleSheet("font-weight: 600; color: #EF4444; font-size: 14px;")

        header_layout.addWidget(title_label)
        header_layout.addStretch()

        info_layout = QHBoxLayout()

        topic_label = QLabel(f"📁 {topic_name}")
        topic_label.setStyleSheet("color: #6B7280; font-size: 11px;")
        info_layout.addWidget(topic_label)

        info_layout.addSpacing(20)

        deadline_label = QLabel(f"⏰ {deadline}")
        deadline_label.setStyleSheet("color: #6B7280; font-size: 11px;")
        if is_overdue:
            deadline_label.setStyleSheet("color: #EF4444; font-size: 11px;")

        info_layout.addWidget(deadline_label)
        info_layout.addStretch()

        layout.addLayout(header_layout)
        layout.addLayout(info_layout)

    def mousePressEvent(self, event):
        """Обработчик клика"""
        self.task_clicked.emit(self.task_id)
        super().mousePressEvent(event)