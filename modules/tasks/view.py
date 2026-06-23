# modules/tasks/view.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QListWidget, QListWidgetItem, QStackedWidget, QTextEdit,
    QDialog
)
from PySide6.QtCore import Qt, Signal
import logging

from modules.tasks.controller import TaskController
from modules.tasks.dialogs import TaskDialog
from widgets import SilentMessageBox

# Настройка логирования
logger = logging.getLogger(__name__)


class TasksView(QWidget):
    """Экран задач для конкретной темы."""

    task_updated = Signal()

    def __init__(self, controller: TaskController, parent=None):
        super().__init__(parent)
        self._controller = controller
        self._current_topic_id = None
        self._current_task = None
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        """Настраивает интерфейс"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        header_layout = QHBoxLayout()
        self.title_label = QLabel("✅ Задачи")
        self.title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        header_layout.addWidget(self.title_label)
        header_layout.addStretch()
        self.new_btn = QPushButton("➕ Новая задача")
        header_layout.addWidget(self.new_btn)
        layout.addLayout(header_layout)

        main_layout = QHBoxLayout()

        self.task_list = QListWidget()
        self.task_list.setFixedWidth(300)
        main_layout.addWidget(self.task_list)

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
        self.task_list.itemClicked.connect(self._on_task_selected)
        self.new_btn.clicked.connect(self._on_new_task)
        self.complete_btn.clicked.connect(self._on_complete_task)
        self.edit_btn.clicked.connect(self._on_edit_task)
        self.delete_btn.clicked.connect(self._on_delete_task)

    def set_topic(self, topic_id: int):
        self._current_topic_id = topic_id
        self._load_tasks()

    def _load_tasks(self):
        try:
            self.task_list.clear()
            self.stack.setCurrentIndex(0)
            self._current_task = None

            if not self._current_topic_id:
                return

            tasks = self._controller.get_tasks_by_topic(self._current_topic_id)

            if not tasks:
                self.task_list.addItem("📭 Нет задач в этой теме")
                return

            for task in tasks:
                item = QListWidgetItem()
                if task.status == 'completed':
                    icon = "✅"
                elif task.is_overdue():
                    icon = "⚠️"
                else:
                    icon = "⏳"
                item.setText(f"{icon} {task.title}")
                item.setData(Qt.UserRole, task.id)
                self.task_list.addItem(item)

            logger.debug(f"Загружено {len(tasks)} задач для темы {self._current_topic_id}")
        except Exception as e:
            logger.error(f"Ошибка загрузки задач для темы {self._current_topic_id}: {e}", exc_info=True)
            SilentMessageBox.warning(self, "Ошибка", f"Не удалось загрузить задачи: {e}")

    def _on_task_selected(self, item: QListWidgetItem):
        try:
            task_id = item.data(Qt.UserRole)
            self._current_task = self._controller.get_task(task_id)
            if not self._current_task:
                logger.warning(f"Задача {task_id} не найдена при выборе")
                return

            self.stack.setCurrentIndex(1)
            self.detail_title.setText(self._current_task.title)
            self.detail_desc.setPlainText(self._current_task.description or "Нет описания")

            if self._current_task.deadline:
                from datetime import datetime
                try:
                    deadline_dt = datetime.fromisoformat(self._current_task.deadline)
                    deadline_display = deadline_dt.strftime("%d.%m.%Y %H:%M")
                    self.detail_deadline.setText(f"⏰ Дедлайн: {deadline_display}")
                except (ValueError, TypeError) as e:
                    logger.warning(f"Неверный формат дедлайна для задачи {task_id}: {e}")
                    self.detail_deadline.setText(f"⏰ Дедлайн: {self._current_task.deadline}")
            else:
                self.detail_deadline.setText("⏰ Без дедлайна")

            self.complete_btn.setEnabled(self._current_task.status != 'completed')
        except Exception as e:
            logger.error(f"Ошибка выбора задачи: {e}", exc_info=True)

    def _on_new_task(self):
        try:
            if not self._current_topic_id:
                SilentMessageBox.warning(self, "Ошибка", "Сначала выберите тему")
                return

            dialog = TaskDialog(self, topic_id=self._current_topic_id)
            if dialog.exec() == QDialog.Accepted:
                try:
                    data = dialog.get_task_data()
                    task_id = self._controller.create_task(
                        title=data['title'],
                        description=data['description'],
                        topic_id=self._current_topic_id,
                        deadline=data['deadline']
                    )
                    if task_id:
                        self._load_tasks()
                        self.task_updated.emit()
                        SilentMessageBox.information(self, "Успех", "Задача создана")
                        logger.info(f"Создана задача {task_id} в теме {self._current_topic_id}")
                except ValueError as e:
                    SilentMessageBox.warning(self, "Ошибка", str(e))
                    logger.warning(f"Ошибка валидации данных задачи: {e}")
        except Exception as e:
            logger.error(f"Ошибка создания задачи: {e}", exc_info=True)
            SilentMessageBox.warning(self, "Ошибка", f"Не удалось создать задачу: {e}")

    def _on_complete_task(self):
        try:
            if not self._current_task:
                return
            if self._controller.complete_task(self._current_task.id):
                self._load_tasks()
                self.task_updated.emit()
                SilentMessageBox.information(self, "Успех", "Задача выполнена!")
                logger.info(f"Задача {self._current_task.id} выполнена")
        except Exception as e:
            logger.error(f"Ошибка выполнения задачи: {e}", exc_info=True)
            SilentMessageBox.warning(self, "Ошибка", f"Не удалось выполнить задачу: {e}")

    def _on_edit_task(self):
        try:
            if not self._current_task:
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
                    logger.info(f"Задача {self._current_task.id} обновлена")
                except ValueError as e:
                    SilentMessageBox.warning(self, "Ошибка", str(e))
                    logger.warning(f"Ошибка валидации данных задачи: {e}")
        except Exception as e:
            logger.error(f"Ошибка редактирования задачи: {e}", exc_info=True)
            SilentMessageBox.warning(self, "Ошибка", f"Не удалось обновить задачу: {e}")

    def _on_delete_task(self):
        try:
            if not self._current_task:
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
                    logger.info(f"Задача {self._current_task.id} удалена")
        except Exception as e:
            logger.error(f"Ошибка удаления задачи: {e}", exc_info=True)
            SilentMessageBox.warning(self, "Ошибка", f"Не удалось удалить задачу: {e}")

    def refresh(self):
        self._load_tasks()