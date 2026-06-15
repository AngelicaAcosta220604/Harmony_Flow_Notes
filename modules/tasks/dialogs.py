# modules/tasks/dialogs.py
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QTextEdit, QPushButton, QComboBox, QCalendarWidget, QWidget, QFrame
)
from PySide6.QtCore import Qt, QDate, QTime
from datetime import datetime, date, timedelta

from models.task import Task
from widgets import SilentMessageBox


class TaskDialog(QDialog):
    """Диалог создания/редактирования задачи с удобным выбором даты и времени."""

    def __init__(self, parent=None, task: Task = None, topic_id: int = None):
        super().__init__(parent)
        self.setWindowTitle("Создание задачи" if task is None else "Редактирование задачи")
        self.setMinimumSize(550, 600)
        self.setModal(True)
        self._task = task
        self._topic_id = topic_id
        self._setup_ui()
        self._connect_signals()

        if task:
            self._load_task()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Название
        title_label = QLabel("Название *")
        title_label.setStyleSheet("color: #ff9800;")
        layout.addWidget(title_label)

        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("Введите название задачи...")
        layout.addWidget(self.title_edit)

        # Описание
        desc_label = QLabel("Описание")
        layout.addWidget(desc_label)

        self.desc_edit = QTextEdit()
        self.desc_edit.setPlaceholderText("Введите описание (необязательно)...")
        self.desc_edit.setMaximumHeight(120)
        layout.addWidget(self.desc_edit)

        # Дедлайн
        deadline_label = QLabel("Дедлайн")
        deadline_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(deadline_label)

        # Чекбокс "установить дедлайн"
        self.has_deadline_check = QPushButton("📅 Установить дедлайн")
        self.has_deadline_check.setCheckable(True)
        self.has_deadline_check.setChecked(True)
        layout.addWidget(self.has_deadline_check)

        # Блок выбора даты и времени
        self.datetime_widget = QWidget()
        datetime_layout = QVBoxLayout(self.datetime_widget)
        datetime_layout.setContentsMargins(0, 5, 0, 0)
        datetime_layout.setSpacing(10)

        # Календарь
        self.calendar = QCalendarWidget()
        self.calendar.setMinimumDate(QDate.currentDate())
        datetime_layout.addWidget(self.calendar)

        # Выбор времени (часы и минуты отдельными комбобоксами)
        time_layout = QHBoxLayout()
        time_layout.setSpacing(10)

        time_label = QLabel("Время:")
        time_label.setStyleSheet("font-weight: bold;")
        time_layout.addWidget(time_label)

        # Часы (00-23)
        self.hour_combo = QComboBox()
        for h in range(24):
            self.hour_combo.addItem(f"{h:02d}", h)
        self.hour_combo.setCurrentIndex(datetime.now().hour)
        time_layout.addWidget(self.hour_combo)

        time_layout.addWidget(QLabel(":"))

        # Минуты (00-59 с шагом 5)
        self.minute_combo = QComboBox()
        for m in range(0, 60, 5):
            self.minute_combo.addItem(f"{m:02d}", m)
        # Устанавливаем ближайшее значение (округляем до 5 минут)
        current_minute = datetime.now().minute
        nearest_minute = (current_minute // 5) * 5
        self.minute_combo.setCurrentIndex(nearest_minute // 5)
        time_layout.addWidget(self.minute_combo)

        time_layout.addStretch()
        datetime_layout.addLayout(time_layout)

        self.datetime_widget.setLayout(datetime_layout)
        layout.addWidget(self.datetime_widget)

        layout.addStretch()

        # Кнопки
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.save_btn = QPushButton("💾 Сохранить")
        self.save_btn.setStyleSheet("background-color: #4caf50; color: white; font-weight: bold;")
        button_layout.addWidget(self.save_btn)

        self.cancel_btn = QPushButton("❌ Отмена")
        button_layout.addWidget(self.cancel_btn)

        layout.addLayout(button_layout)

    def _connect_signals(self):
        self.save_btn.clicked.connect(self._on_save)
        self.cancel_btn.clicked.connect(self.reject)
        self.has_deadline_check.toggled.connect(self._on_deadline_toggled)

    def _on_deadline_toggled(self, checked: bool):
        self.datetime_widget.setEnabled(checked)
        if not checked:
            self.datetime_widget.setStyleSheet("QWidget { opacity: 0.5; }")
        else:
            self.datetime_widget.setStyleSheet("")

    def _load_task(self):
        self.title_edit.setText(self._task.title)
        self.desc_edit.setPlainText(self._task.description)

        if self._task.deadline:
            self.has_deadline_check.setChecked(True)
            dt = datetime.fromisoformat(self._task.deadline)
            self.calendar.setSelectedDate(QDate(dt.year, dt.month, dt.day))
            self.hour_combo.setCurrentIndex(self.hour_combo.findData(dt.hour))
            # минуты с шагом 5
            minute_val = (dt.minute // 5) * 5
            self.minute_combo.setCurrentIndex(self.minute_combo.findData(minute_val))

    def _on_save(self):
        title = self.title_edit.text().strip()
        if not title:
            SilentMessageBox.warning(self, "Ошибка", "Введите название задачи")
            return

        deadline = None
        if self.has_deadline_check.isChecked():
            date_val = self.calendar.selectedDate()
            hour = self.hour_combo.currentData()
            minute = self.minute_combo.currentData()
            deadline = f"{date_val.toString('yyyy-MM-dd')}T{hour:02d}:{minute:02d}:00"

        self._result = {
            'title': title,
            'description': self.desc_edit.toPlainText(),
            'deadline': deadline,
            'topic_id': self._topic_id if not self._task else self._task.topic_id
        }
        self.accept()

    def get_task_data(self) -> dict:
        return getattr(self, '_result', {})


class TaskViewDialog(QDialog):
    """Диалог просмотра задачи (только чтение)."""

    def __init__(self, task: Task, parent=None):
        super().__init__(parent)
        self._task = task
        self.setWindowTitle(f"Задача: {task.title}")
        self.setMinimumSize(500, 400)
        self.setModal(True)
        self._setup_ui()

    def _setup_ui(self):
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
            dt = datetime.fromisoformat(self._task.deadline)
            deadline_value = QLabel(dt.strftime("%d.%m.%Y %H:%M"))
            layout.addWidget(deadline_value)

        # Даты
        dates_layout = QHBoxLayout()
        created_label = QLabel(f"Создана: {self._task.created_at[:16]}")
        created_label.setStyleSheet("color: #888888; font-size: 10px;")
        dates_layout.addWidget(created_label)

        if self._task.completed_at:
            completed_label = QLabel(f"Выполнена: {self._task.completed_at[:16]}")
            completed_label.setStyleSheet("color: #888888; font-size: 10px;")
            dates_layout.addWidget(completed_label)

        dates_layout.addStretch()
        layout.addLayout(dates_layout)

        close_btn = QPushButton("Закрыть")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

    def _get_status_text(self) -> str:
        if self._task.status == 'completed':
            return "✅ Выполнена"
        if self._task.is_overdue():
            return "⚠️ Просрочена"
        return "⏳ Активна"

    def _get_status_style(self) -> str:
        if self._task.status == 'completed':
            return "color: #4caf50; font-weight: bold;"
        if self._task.is_overdue():
            return "color: #f44336; font-weight: bold;"
        return "color: #ff9800; font-weight: bold;"