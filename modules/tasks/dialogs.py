# modules/tasks/dialogs.py
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QTextEdit, QPushButton, QDateTimeEdit, QComboBox,
)
from widgets import SilentMessageBox
from PySide6.QtCore import Qt, QDateTime
from datetime import datetime

from models.task import Task


class TaskDialog(QDialog):
    """
    Диалог создания/редактирования задачи.
    """

    def __init__(self, parent=None, task: Task = None, topic_id: int = None):
        super().__init__(parent)
        self._task = task
        self._topic_id = topic_id
        self._setup_ui()

        if task:
            self._load_task()

        self._connect_signals()

    def _setup_ui(self):
        """Настраивает интерфейс"""
        self.setWindowTitle("Задача" if not self._task else "Редактирование задачи")
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Название
        title_label = QLabel("Название *")
        layout.addWidget(title_label)

        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("Введите название задачи...")
        layout.addWidget(self.title_edit)

        # Описание
        desc_label = QLabel("Описание")
        layout.addWidget(desc_label)

        self.desc_edit = QTextEdit()
        self.desc_edit.setPlaceholderText("Введите описание (необязательно)...")
        self.desc_edit.setMaximumHeight(150)
        layout.addWidget(self.desc_edit)

        # Дедлайн
        deadline_label = QLabel("Дедлайн")
        layout.addWidget(deadline_label)

        deadline_layout = QHBoxLayout()

        self.deadline_check = QPushButton("📅 Установить дедлайн")
        self.deadline_check.setCheckable(True)
        deadline_layout.addWidget(self.deadline_check)

        self.datetime_edit = QDateTimeEdit()
        self.datetime_edit.setCalendarPopup(True)
        self.datetime_edit.setDateTime(QDateTime.currentDateTime())
        self.datetime_edit.setEnabled(False)
        deadline_layout.addWidget(self.datetime_edit)

        deadline_layout.addStretch()
        layout.addLayout(deadline_layout)

        # Кнопки
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.save_btn = QPushButton("💾 Сохранить")
        self.cancel_btn = QPushButton("Отмена")

        button_layout.addWidget(self.save_btn)
        button_layout.addWidget(self.cancel_btn)

        layout.addLayout(button_layout)

    def _connect_signals(self):
        """Подключает сигналы"""
        self.save_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)
        self.deadline_check.toggled.connect(self.datetime_edit.setEnabled)

    def _load_task(self):
        """Загружает данные задачи в поля"""
        self.title_edit.setText(self._task.title)
        self.desc_edit.setPlainText(self._task.description)

        if self._task.deadline:
            self.deadline_check.setChecked(True)
            dt = datetime.fromisoformat(self._task.deadline)
            self.datetime_edit.setDateTime(QDateTime(dt))

    def get_task_data(self) -> dict:
        """Возвращает данные из формы"""
        title = self.title_edit.text().strip()
        if not title:
            raise ValueError("Название задачи не может быть пустым")

        deadline = None
        if self.deadline_check.isChecked():
            deadline = self.datetime_edit.dateTime().toString("yyyy-MM-ddTHH:mm:ss")

        return {
            'title': title,
            'description': self.desc_edit.toPlainText(),
            'deadline': deadline,
            'topic_id': self._topic_id if not self._task else self._task.topic_id
        }


class TaskViewDialog(QDialog):
    """
    Диалог просмотра задачи (только чтение).
    """

    def __init__(self, task: Task, parent=None):
        super().__init__(parent)
        self._task = task
        self._setup_ui()

    def _setup_ui(self):
        """Настраивает интерфейс"""
        self.setWindowTitle(f"Задача: {self._task.title}")
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Статус
        status_layout = QHBoxLayout()
        status_label = QLabel("Статус:")
        self.status_value = QLabel(self._get_status_text())
        self.status_value.setStyleSheet(self._get_status_style())
        status_layout.addWidget(status_label)
        status_layout.addWidget(self.status_value)
        status_layout.addStretch()
        layout.addLayout(status_layout)

        # Название
        title_label = QLabel("Название:")
        title_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(title_label)

        title_value = QLabel(self._task.title)
        title_value.setWordWrap(True)
        layout.addWidget(title_value)

        # Описание
        if self._task.description:
            desc_label = QLabel("Описание:")
            desc_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
            layout.addWidget(desc_label)

            desc_value = QLabel(self._task.description)
            desc_value.setWordWrap(True)
            layout.addWidget(desc_value)

        # Дедлайн
        if self._task.deadline:
            deadline_label = QLabel("Дедлайн:")
            deadline_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
            layout.addWidget(deadline_label)

            from services.time_service import TimeService
            deadline_value = QLabel(TimeService.format_datetime_from_iso(self._task.deadline))
            layout.addWidget(deadline_value)

        # Даты создания/выполнения
        dates_layout = QHBoxLayout()
        dates_layout.setSpacing(20)

        created_label = QLabel(f"Создана: {self._task.created_at[:16]}")
        created_label.setStyleSheet("color: #888888; font-size: 10px;")
        dates_layout.addWidget(created_label)

        if self._task.completed_at:
            completed_label = QLabel(f"Выполнена: {self._task.completed_at[:16]}")
            completed_label.setStyleSheet("color: #888888; font-size: 10px;")
            dates_layout.addWidget(completed_label)

        dates_layout.addStretch()
        layout.addLayout(dates_layout)

        # Кнопка закрытия
        close_btn = QPushButton("Закрыть")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

    def _get_status_text(self) -> str:
        """Возвращает текст статуса"""
        if self._task.status == 'completed':
            return "✅ Выполнена"
        if self._task.is_overdue():
            return "⚠️ Просрочена"
        return "⏳ Активна"

    def _get_status_style(self) -> str:
        """Возвращает стиль для статуса"""
        if self._task.status == 'completed':
            return "color: #4caf50; font-weight: bold;"
        if self._task.is_overdue():
            return "color: #f44336; font-weight: bold;"
        return "color: #ff9800; font-weight: bold;"