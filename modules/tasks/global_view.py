# modules/tasks/global_view.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QListWidget, QListWidgetItem, QStackedWidget, QTextEdit,
    QComboBox, QLineEdit, QDialog, QFrame, QScrollArea, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QIcon, QPixmap
from datetime import datetime, timedelta, date
import logging
from modules.topics.topic_view import TaskListItemWidget
from utils.resource_paths import get_resource_path
from modules.tasks.controller import TaskController
from modules.tasks.filters import TaskFilters
from modules.tasks.dialogs import TaskDialog
from datebase.repositories.topic_repo import TopicRepository
from widgets import SilentMessageBox

# Настройка логирования
logger = logging.getLogger(__name__)


# class TaskListItem(QWidget):
#     """Кастомный виджет для элемента списка задач с обрезкой текста через ..."""
#
#     def __init__(self, text: str, parent=None):
#         super().__init__(parent)
#         self._full_text = text
#
#         layout = QHBoxLayout(self)
#         layout.setContentsMargins(8, 4, 8, 4)
#
#         self.label = QLabel(text)
#         self.label.setStyleSheet("color: #1F2937; font-size: 13px;")
#         layout.addWidget(self.label)
#
#     def setText(self, text: str):
#         self._full_text = text
#         self.label.setText(text)
#
#     def resizeEvent(self, event):
#         super().resizeEvent(event)
#         self._elide_text()
#
#     def _elide_text(self):
#         """Обрезает текст через ... если не влезает"""
#         metrics = self.label.fontMetrics()
#         # Оставляем запас для отступов
#         available_width = self.label.width() - 10
#         elided = metrics.elidedText(self._full_text, Qt.ElideRight, available_width)
#         self.label.setText(elided)


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
        self._period_offset = 0
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
        # ✅ ИСПРАВЛЕНО: используем get_resource_path
        header_pixmap = QPixmap(str(get_resource_path("resources/icons/task1.png")))
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
        self.period_filter.addItem("Без дедлайна", "no_deadline")
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

        # 🆕 Кнопки навигации по периоду
        self.prev_period_btn = QPushButton("←")
        self.prev_period_btn.setFixedSize(32, 32)
        self.prev_period_btn.setToolTip("Предыдущий период")
        self.prev_period_btn.setStyleSheet("""
                    QPushButton {
                        background-color: rgba(59, 130, 246, 0.15);
                        color: #3B82F6;
                        border: 1px solid #3B82F6;
                        border-radius: 8px;
                        font-weight: bold;
                        font-size: 16px;
                    }
                    QPushButton:hover {
                        background-color: rgba(59, 130, 246, 0.25);
                    }
                    QPushButton:disabled {
                        background-color: #F0F4F8;
                        color: #9CA3AF;
                        border: 1px solid #E6EEF6;
                    }
                """)
        period_layout.addWidget(self.prev_period_btn)

        self.next_period_btn = QPushButton("→")
        self.next_period_btn.setFixedSize(32, 32)
        self.next_period_btn.setToolTip("Следующий период")
        self.next_period_btn.setStyleSheet("""
                    QPushButton {
                        background-color: rgba(59, 130, 246, 0.15);
                        color: #3B82F6;
                        border: 1px solid #3B82F6;
                        border-radius: 8px;
                        font-weight: bold;
                        font-size: 16px;
                    }
                    QPushButton:hover {
                        background-color: rgba(59, 130, 246, 0.25);
                    }
                    QPushButton:disabled {
                        background-color: #F0F4F8;
                        color: #9CA3AF;
                        border: 1px solid #E6EEF6;
                    }
                """)
        period_layout.addWidget(self.next_period_btn)

        # 🆕 Метка текущего периода
        self.period_label = QLabel("Текущий")
        self.period_label.setStyleSheet("color: #3B82F6; font-size: 12px; font-weight: 500; min-width: 100px;")
        period_layout.addWidget(self.period_label)

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
        # ✅ ИСПРАВЛЕНО: используем get_resource_path
        self.new_btn.setIcon(QIcon(str(get_resource_path("resources/icons/task1.png"))))
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
        # ✅ ИСПРАВЛЕНО: используем get_resource_path
        self.complete_btn.setIcon(QIcon(str(get_resource_path("resources/icons/check.png"))))
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
        # ✅ ИСПРАВЛЕНО: используем get_resource_path
        self.edit_btn.setIcon(QIcon(str(get_resource_path("resources/icons/rename1.png"))))
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
        # ✅ ИСПРАВЛЕНО: используем get_resource_path
        self.delete_btn.setIcon(QIcon(str(get_resource_path("resources/icons/delete1.png"))))
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
        # 🆕 Навигация по периодам
        self.prev_period_btn.clicked.connect(self._navigate_previous)
        self.next_period_btn.clicked.connect(self._navigate_next)

    def _load_topics_to_filter(self):
        try:
            topics = self._topic_repo.get_all()
            for topic in topics:
                if topic['type'] == 'topic':
                    self.topic_filter.addItem(topic['name'], topic['id'])
            logger.debug(f"Загружено {len(topics)} тем в фильтр")
        except Exception as e:
            logger.error(f"Ошибка загрузки тем в фильтр: {e}", exc_info=True)

    def _on_period_changed(self):
        """Обработчик изменения фильтра периода"""
        self._period_offset = 0  # Сбрасываем смещение при смене периода
        self._update_period_label()
        self._update_navigation_buttons()
        self._load_tasks()

    def _navigate_previous(self):
        """Переход к предыдущему периоду"""
        self._period_offset -= 1
        self._update_period_label()
        self._load_tasks()

    def _navigate_next(self):
        """Переход к следующему периоду"""
        self._period_offset += 1
        self._update_period_label()
        self._load_tasks()

    def _update_period_label(self):
        """Обновляет метку текущего периода"""
        period = self.period_filter.currentData()

        if period == 'all' or period == 'overdue_only' or period == 'no_deadline':
            self.period_label.setText("")
            return

        if self._period_offset == 0:
            if period == 'today':
                self.period_label.setText("Сегодня")
            elif period == 'tomorrow':
                self.period_label.setText("Завтра")
            elif period == 'week':
                self.period_label.setText("Эта неделя")
            elif period == 'month':
                self.period_label.setText("Этот месяц")
        else:
            from datetime import timedelta
            today = date.today()

            if period == 'today':
                target_date = today + timedelta(days=self._period_offset)
                self.period_label.setText(target_date.strftime("%d.%m.%Y"))
            elif period == 'tomorrow':
                target_date = today + timedelta(days=1 + self._period_offset)
                self.period_label.setText(target_date.strftime("%d.%m.%Y"))
            elif period == 'week':
                start_date = today + timedelta(weeks=self._period_offset)
                end_date = start_date + timedelta(days=6)
                self.period_label.setText(f"{start_date.strftime('%d.%m')} - {end_date.strftime('%d.%m')}")
            elif period == 'month':
                target_month = today.month + self._period_offset
                target_year = today.year

                while target_month > 12:
                    target_month -= 12
                    target_year += 1
                while target_month < 1:
                    target_month += 12
                    target_year -= 1

                months = ["Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
                          "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"]
                self.period_label.setText(f"{months[target_month - 1]} {target_year}")

    def _update_navigation_buttons(self):
        """Обновляет состояние кнопок навигации"""
        period = self.period_filter.currentData()

        # Кнопки активны только для периодов с навигацией
        can_navigate = period in ('today', 'tomorrow', 'week', 'month')
        self.prev_period_btn.setEnabled(can_navigate)
        self.next_period_btn.setEnabled(can_navigate)

    def _load_tasks(self):
        try:
            self.task_list.clear()
            self._update_navigation_buttons()

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
                # ✅ ИСПРАВЛЕНО: используем TaskListItemWidget с чекбоксом и кнопками
                item_widget = TaskListItemWidget(
                    task.id,
                    task.title,
                    task.deadline_display if task.deadline else "Без дедлайна",
                    task.status,
                    task.is_overdue()
                )

                # ✅ Подключаем сигналы виджета
                item_widget.complete_clicked.connect(self._on_task_complete_from_widget)
                item_widget.edit_clicked.connect(self._on_task_edit_from_widget)
                item_widget.delete_clicked.connect(self._on_task_delete_from_widget)

                item = QListWidgetItem()
                item.setSizeHint(item_widget.sizeHint())
                item.setData(Qt.UserRole, task.id)

                self.task_list.addItem(item)
                self.task_list.setItemWidget(item, item_widget)

            logger.debug(f"Загружено {len(tasks)} задач")
        except Exception as e:
            logger.error(f"Ошибка загрузки задач: {e}", exc_info=True)
            SilentMessageBox.warning(self, "Ошибка", f"Не удалось загрузить задачи: {e}")

    def _on_task_complete_from_widget(self, task_id: int):
        """Обработчик выполнения задачи из виджета"""
        try:
            if self._controller.complete_task(task_id):
                self._load_tasks()
                self.task_updated.emit()
                logger.info(f"Задача {task_id} выполнена")
        except Exception as e:
            logger.error(f"Ошибка выполнения задачи {task_id}: {e}", exc_info=True)

    def _on_task_edit_from_widget(self, task_id: int):
        """Обработчик редактирования задачи из виджета"""
        try:
            task = self._controller.get_task(task_id)
            if not task:
                return
            dialog = TaskDialog(self, task)
            if dialog.exec() == QDialog.Accepted:
                try:
                    data = dialog.get_task_data()
                    self._controller.update_task(
                        task_id,
                        title=data['title'],
                        description=data['description'],
                        deadline=data['deadline']
                    )
                    self._load_tasks()
                    self.task_updated.emit()
                    logger.info(f"Задача {task_id} обновлена")
                except ValueError as e:
                    SilentMessageBox.warning(self, "Ошибка", str(e))
        except Exception as e:
            logger.error(f"Ошибка редактирования задачи {task_id}: {e}", exc_info=True)

    def _on_task_delete_from_widget(self, task_id: int):
        """Обработчик удаления задачи из виджета"""
        try:
            task = self._controller.get_task(task_id)
            if not task:
                return
            reply = SilentMessageBox.question(
                self, "Подтверждение удаления",
                f"Удалить задачу «{task.title}»?"
            )
            if reply == SilentMessageBox.Yes:
                if self._controller.delete_task(task_id):
                    self._load_tasks()
                    self.task_updated.emit()
                    self.stack.setCurrentIndex(0)
                    logger.info(f"Задача {task_id} удалена")
        except Exception as e:
            logger.error(f"Ошибка удаления задачи {task_id}: {e}", exc_info=True)

    def _filter_by_period(self, tasks, period):
        today = date.today()

        # 🆕 Фильтр "без дедлайна"
        if period == 'no_deadline':
            return [t for t in tasks if not t.deadline]

        # 🆕 Применяем смещение
        offset = self._period_offset

        if period == 'today':
            target_date = today + timedelta(days=offset)
            return [t for t in tasks if t.deadline and t.deadline[:10] == target_date.isoformat()]
        elif period == 'tomorrow':
            target_date = today + timedelta(days=1 + offset)
            return [t for t in tasks if t.deadline and t.deadline[:10] == target_date.isoformat()]
        elif period == 'week':
            start_date = today + timedelta(weeks=offset)
            end_date = start_date + timedelta(days=6)
            return [t for t in tasks if t.deadline and
                    start_date.isoformat() <= t.deadline[:10] <= end_date.isoformat()]
        elif period == 'month':
            target_month = today.month + offset
            target_year = today.year

            while target_month > 12:
                target_month -= 12
                target_year += 1
            while target_month < 1:
                target_month += 12
                target_year -= 1

            if target_month == 12:
                end_date = date(target_year + 1, 1, 1) - timedelta(days=1)
            else:
                end_date = date(target_year, target_month + 1, 1) - timedelta(days=1)

            start_date = date(target_year, target_month, 1)
            return [t for t in tasks if t.deadline and
                    start_date.isoformat() <= t.deadline[:10] <= end_date.isoformat()]
        elif period == 'overdue_only':
            return [t for t in tasks if t.is_overdue()]
        return tasks

    def _on_task_selected(self, item):
        try:
            task_id = item.data(Qt.UserRole)
            task = self._controller.get_task(task_id)
            if not task:
                logger.warning(f"Задача {task_id} не найдена при выборе")
                return

            self._current_task = task
            self.stack.setCurrentIndex(1)

            # 🆕 Настраиваем перенос текста
            self.detail_title.setWordWrap(True)
            self.detail_title.setText(task.title)

            self.detail_desc.setPlainText(task.description or "Нет описания")
            # QTextEdit уже переносит строки по умолчанию

            if task.deadline:
                try:
                    deadline_dt = datetime.fromisoformat(task.deadline)
                    deadline_display = deadline_dt.strftime("%d.%m.%Y %H:%M")
                    self.detail_deadline.setText(f"⏰ Дедлайн: {deadline_display}")
                    self.detail_deadline.setStyleSheet("color: #EF4444;" if task.is_overdue() else "color: #6B7280;")
                except (ValueError, TypeError) as e:
                    logger.warning(f"Неверный формат дедлайна для задачи {task_id}: {e}")
                    self.detail_deadline.setText(f"⏰ Дедлайн: {task.deadline}")
            else:
                self.detail_deadline.setText("⏰ Без дедлайна")

            self.complete_btn.setEnabled(task.status != 'completed')
            self.complete_btn.setText("Выполнить" if task.status != 'completed' else "Выполнена")
        except Exception as e:
            logger.error(f"Ошибка выбора задачи: {e}", exc_info=True)

    def _on_new_task(self):
        try:
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
                        logger.info(f"Создана задача {task_id}")
                except ValueError as e:
                    SilentMessageBox.warning(self, "Ошибка", str(e))
                    logger.warning(f"Ошибка валидации данных задачи: {e}")
        except Exception as e:
            logger.error(f"Ошибка создания задачи: {e}", exc_info=True)
            SilentMessageBox.warning(self, "Ошибка", f"Не удалось создать задачу: {e}")

    def _on_complete_task(self):
        try:
            if not hasattr(self, '_current_task'):
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
                    logger.info(f"Задача {self._current_task.id} обновлена")
                except ValueError as e:
                    SilentMessageBox.warning(self, "Ошибка", str(e))
                    logger.warning(f"Ошибка валидации данных задачи: {e}")
        except Exception as e:
            logger.error(f"Ошибка редактирования задачи: {e}", exc_info=True)
            SilentMessageBox.warning(self, "Ошибка", f"Не удалось обновить задачу: {e}")

    def _on_delete_task(self):
        try:
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
                    logger.info(f"Задача {self._current_task.id} удалена")
        except Exception as e:
            logger.error(f"Ошибка удаления задачи: {e}", exc_info=True)
            SilentMessageBox.warning(self, "Ошибка", f"Не удалось удалить задачу: {e}")

    def refresh(self):
        self._load_tasks()