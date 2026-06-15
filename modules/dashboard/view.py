# modules/dashboard/view.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QMessageBox
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QFont

from .controller import DashboardController
from .widgets import KpiRow, KpiCard

from PySide6.QtGui import QPixmap, QIcon

class DashboardView(QWidget):
    """
    Главный экран (Dashboard)
    """

    # Сигналы для навигации
    create_topic_requested = Signal()
    create_note_requested = Signal()
    start_session_requested = Signal()
    open_topic_requested = Signal(int)  # topic_id
    open_task_requested = Signal(int)  # task_id.
    open_analytics_requested = Signal()
    open_tasks_requested = Signal()

    def __init__(self, controller: DashboardController, parent=None):
        super().__init__(parent)
        self._controller = controller
        self._urgent_task_buttons = {}  # для хранения кнопок задач
        self._setup_ui()
        self.refresh()

    def _setup_ui(self):
        """Настраивает интерфейс"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # Скролл-область
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        content_widget = QWidget()
        self.content_layout = QVBoxLayout(content_widget)
        self.content_layout.setSpacing(25)

        # Пустое состояние (будет показано если нет данных)
        self.empty_widget = self._create_empty_state()
        self.content_layout.addWidget(self.empty_widget)

        # Блок приветствия
        self.greeting_widget = self._create_greeting_block()
        self.content_layout.addWidget(self.greeting_widget)

        # Блок KPI (общая статистика)
        self.kpi_row = KpiRow()
        self.content_layout.addWidget(self.kpi_row)

        # Блок активной темы
        self.active_topic_widget = self._create_active_topic_block()
        self.content_layout.addWidget(self.active_topic_widget)

        # Блок последней сессии
        self.last_session_widget = self._create_last_session_block()
        self.content_layout.addWidget(self.last_session_widget)

        # Блок срочных задач
        self.urgent_tasks_widget = self._create_urgent_tasks_block()
        self.content_layout.addWidget(self.urgent_tasks_widget)

        # Блок быстрого старта
        self.quick_start_widget = self._create_quick_start_block()
        self.content_layout.addWidget(self.quick_start_widget)

        # Блок аналитики за сегодня
        self.today_analytics_widget = self._create_today_analytics_block()
        self.content_layout.addWidget(self.today_analytics_widget)

        self.content_layout.addStretch()

        scroll.setWidget(content_widget)
        layout.addWidget(scroll)

    def _create_empty_state(self) -> QWidget:
        """Создаёт виджет пустого состояния"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(15)

        icon_label = QLabel("📚")
        icon_label.setStyleSheet("font-size: 48px;")
        icon_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon_label)

        title_label = QLabel("Добро пожаловать в HFlow!")
        title_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        desc_label = QLabel("Начните с создания первой темы или первой заметки.")
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setStyleSheet("color: #888888;")
        layout.addWidget(desc_label)

        button_layout = QHBoxLayout()
        button_layout.setAlignment(Qt.AlignCenter)
        button_layout.setSpacing(20)

        create_topic_btn = QPushButton("📁 Создать тему")
        create_topic_btn.clicked.connect(self.create_topic_requested.emit)
        button_layout.addWidget(create_topic_btn)

        create_note_btn = QPushButton("📝 Создать заметку")
        create_note_btn.clicked.connect(self.create_note_requested.emit)
        button_layout.addWidget(create_note_btn)

        layout.addLayout(button_layout)

        widget.hide()
        return widget

    def _create_greeting_block(self) -> QWidget:
        """Создаёт блок приветствия"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)

        self.greeting_label = QLabel()
        self.greeting_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        layout.addWidget(self.greeting_label)

        self.stats_label = QLabel()
        self.stats_label.setStyleSheet("color: #666666;")
        layout.addWidget(self.stats_label)

        return widget

    def _create_active_topic_block(self) -> QWidget:
        """Создаёт блок активной темы"""
        widget = QFrame()
        widget.setFrameShape(QFrame.StyledPanel)
        widget.setProperty("class", "dashboard-card")

        layout = QVBoxLayout(widget)
        layout.setContentsMargins(15, 12, 15, 12)

        title_label = QLabel("resources/icons/activ_topic Активная тема") # канц.кнопка активная тема
        title_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #1976d2;")
        layout.addWidget(title_label)

        self.active_topic_name = QLabel("—")
        self.active_topic_name.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(self.active_topic_name)

        self.active_topic_info = QLabel("")
        self.active_topic_info.setStyleSheet("color: #888888; font-size: 12px;")
        layout.addWidget(self.active_topic_info)

        open_btn = QPushButton("Открыть тему")
        open_btn.clicked.connect(self._on_open_active_topic)
        layout.addWidget(open_btn)

        widget.hide()
        return widget

    def _create_last_session_block(self) -> QWidget:
        """Создаёт блок последней сессии"""
        widget = QFrame()
        widget.setFrameShape(QFrame.StyledPanel)
        widget.setProperty("class", "dashboard-card")

        layout = QVBoxLayout(widget)
        layout.setContentsMargins(15, 12, 15, 12)

        # Заголовок с иконкой
        header_layout = QHBoxLayout()
        icon_label = QLabel()
        pixmap = QPixmap("resources/icons/session.png")
        if not pixmap.isNull():
            pixmap = pixmap.scaled(20, 20, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            icon_label.setPixmap(pixmap)
        else:
            icon_label.setText("⏱️")

        title_label = QLabel("Последняя сессия")
        title_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #1976d2;")
        header_layout.addWidget(icon_label)
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        self.last_session_topic = QLabel("—")
        self.last_session_topic.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(self.last_session_topic)

        stats_layout = QHBoxLayout()
        self.last_session_duration = QLabel("")
        self.last_session_conc = QLabel("")
        stats_layout.addWidget(self.last_session_duration)
        stats_layout.addWidget(self.last_session_conc)
        stats_layout.addStretch()
        layout.addLayout(stats_layout)

        widget.hide()
        return widget

    def _create_quick_start_block(self) -> QWidget:
        """Создаёт блок быстрого старта"""
        widget = QFrame()
        widget.setFrameShape(QFrame.StyledPanel)
        widget.setProperty("class", "dashboard-card")

        layout = QVBoxLayout(widget)
        layout.setContentsMargins(15, 12, 15, 12)

        # Заголовок с иконкой
        header_layout = QHBoxLayout()
        icon_label = QLabel()
        pixmap = QPixmap("resources/icons/rocket.png")
        if not pixmap.isNull():
            pixmap = pixmap.scaled(20, 20, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            icon_label.setPixmap(pixmap)
        else:
            icon_label.setText("🚀")

        title_label = QLabel("Быстрый старт")
        title_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #1976d2;")
        header_layout.addWidget(icon_label)
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        # Кнопка с иконкой
        start_btn = QPushButton("Начать сессию")
        start_icon = QPixmap("resources/icons/play.png")
        if not start_icon.isNull():
            start_btn.setIcon(QIcon(start_icon))
            start_btn.setIconSize(QSize(20, 20))
        start_btn.setStyleSheet("font-size: 16px; padding: 10px;")
        start_btn.clicked.connect(self.start_session_requested.emit)
        layout.addWidget(start_btn)

        return widget

    def _create_urgent_tasks_block(self) -> QWidget:
        """Создаёт блок срочных задач"""
        widget = QFrame()
        widget.setFrameShape(QFrame.StyledPanel)
        widget.setProperty("class", "dashboard-card")

        layout = QVBoxLayout(widget)
        layout.setContentsMargins(15, 12, 15, 12)

        # Заголовок с иконкой
        header_layout = QHBoxLayout()
        icon_label = QLabel()
        pixmap = QPixmap("resources/icons/warning.png")
        if not pixmap.isNull():
            pixmap = pixmap.scaled(20, 20, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            icon_label.setPixmap(pixmap)
        else:
            icon_label.setText("⚠️")

        title_label = QLabel("Срочные задачи")
        title_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #d32f2f;")
        header_layout.addWidget(icon_label)
        header_layout.addWidget(title_label)
        header_layout.addStretch()

        all_tasks_btn = QPushButton("Все задачи")
        all_tasks_btn.setFlat(True)
        all_tasks_btn.setStyleSheet("color: #1976d2;")
        all_tasks_btn.clicked.connect(self.open_tasks_requested.emit)
        header_layout.addWidget(all_tasks_btn)

        layout.addLayout(header_layout)

        # Список задач
        self.tasks_layout = QVBoxLayout()
        self.tasks_layout.setSpacing(8)
        layout.addLayout(self.tasks_layout)

        self.no_tasks_label = QLabel("Нет срочных задач")
        self.no_tasks_label.setAlignment(Qt.AlignCenter)
        self.no_tasks_label.setStyleSheet("color: #888888; padding: 10px;")
        self.tasks_layout.addWidget(self.no_tasks_label)

        widget.hide()
        return widget

    def _create_active_topic_block(self) -> QWidget:
        """Создаёт блок активной темы"""
        widget = QFrame()
        widget.setFrameShape(QFrame.StyledPanel)
        widget.setProperty("class", "dashboard-card")

        layout = QVBoxLayout(widget)
        layout.setContentsMargins(15, 12, 15, 12)

        # Заголовок с иконкой
        header_layout = QHBoxLayout()
        icon_label = QLabel()
        pixmap = QPixmap("resources/icons/activ_topic.png")
        if not pixmap.isNull():
            pixmap = pixmap.scaled(20, 20, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            icon_label.setPixmap(pixmap)
        else:
            icon_label.setText("📌")

        title_label = QLabel("Активная тема")
        title_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #1976d2;")
        header_layout.addWidget(icon_label)
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        self.active_topic_name = QLabel("—")
        self.active_topic_name.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(self.active_topic_name)

        self.active_topic_info = QLabel("")
        self.active_topic_info.setStyleSheet("color: #888888; font-size: 12px;")
        layout.addWidget(self.active_topic_info)

        open_btn = QPushButton("Открыть тему")
        open_btn.clicked.connect(self._on_open_active_topic)
        layout.addWidget(open_btn)

        widget.hide()
        return widget

    def _create_today_analytics_block(self) -> QWidget:
        """Создаёт блок аналитики за сегодня"""
        widget = QFrame()
        widget.setFrameShape(QFrame.StyledPanel)
        widget.setProperty("class", "dashboard-card")

        layout = QVBoxLayout(widget)
        layout.setContentsMargins(15, 12, 15, 12)

        # Заголовок с иконкой
        header_layout = QHBoxLayout()
        icon_label = QLabel()
        pixmap = QPixmap("resources/icons/analitics.png")
        if not pixmap.isNull():
            pixmap = pixmap.scaled(20, 20, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            icon_label.setPixmap(pixmap)
        else:
            icon_label.setText("📊")

        title_label = QLabel("Сегодня")
        title_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #1976d2;")
        header_layout.addWidget(icon_label)
        header_layout.addWidget(title_label)
        header_layout.addStretch()

        analytics_btn = QPushButton("Подробнее")
        analytics_btn.setFlat(True)
        analytics_btn.setStyleSheet("color: #1976d2;")
        analytics_btn.clicked.connect(self.open_analytics_requested.emit)
        header_layout.addWidget(analytics_btn)

        layout.addLayout(header_layout)

        # Статистика
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(20)

        self.today_time_label = QLabel("0 ч")
        self.today_time_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        self.today_time_desc = QLabel("времени")
        self.today_time_desc.setStyleSheet("color: #888888; font-size: 12px;")

        time_widget = QWidget()
        time_layout = QVBoxLayout(time_widget)
        time_layout.setAlignment(Qt.AlignCenter)
        time_layout.addWidget(self.today_time_label)
        time_layout.addWidget(self.today_time_desc)
        stats_layout.addWidget(time_widget)

        self.today_conc_label = QLabel("0")
        self.today_conc_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        self.today_conc_desc = QLabel("концентрация")
        self.today_conc_desc.setStyleSheet("color: #888888; font-size: 12px;")

        conc_widget = QWidget()
        conc_layout = QVBoxLayout(conc_widget)
        conc_layout.setAlignment(Qt.AlignCenter)
        conc_layout.addWidget(self.today_conc_label)
        conc_layout.addWidget(self.today_conc_desc)
        stats_layout.addWidget(conc_widget)

        self.today_energy_label = QLabel("0")
        self.today_energy_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        self.today_energy_desc = QLabel("энергия")
        self.today_energy_desc.setStyleSheet("color: #888888; font-size: 12px;")

        energy_widget = QWidget()
        energy_layout = QVBoxLayout(energy_widget)
        energy_layout.setAlignment(Qt.AlignCenter)
        energy_layout.addWidget(self.today_energy_label)
        energy_layout.addWidget(self.today_energy_desc)
        stats_layout.addWidget(energy_widget)

        stats_layout.addStretch()
        layout.addLayout(stats_layout)

        widget.hide()
        return widget

    def _on_open_active_topic(self):
        """Открывает активную тему"""
        if hasattr(self, '_active_topic_id') and self._active_topic_id:
            self.open_topic_requested.emit(self._active_topic_id)

    def _on_task_clicked(self, task_id: int):
        """Обработчик клика по задаче"""
        self.open_task_requested.emit(task_id)

    def refresh(self):
        """Обновляет все данные на дашборде"""
        has_data = self._controller.has_data()

        # Показываем/скрываем пустое состояние
        self.empty_widget.setVisible(not has_data)

        if not has_data:
            return

        # Показываем остальные блоки
        for widget in [self.greeting_widget, self.kpi_row, self.active_topic_widget,
                       self.last_session_widget, self.urgent_tasks_widget,
                       self.quick_start_widget, self.today_analytics_widget]:
            widget.show()

        # Обновляем приветствие
        greeting = self._controller.get_greeting()
        user_name = self._controller.get_user_name()
        self.greeting_label.setText(f"{greeting}, {user_name}!")

        today_stats = self._controller.get_today_stats()
        self.stats_label.setText(
            f"✅ Выполнено задач сегодня: {today_stats['completed_tasks_today']} | "
            f"⏱️ Отработано: {today_stats['worked_hours_today']} ч"
        )

        # Обновляем KPI
        total_stats = self._controller.get_total_stats()
        self.kpi_row.clear()
        self.kpi_row.add_card("Темы", str(total_stats['total_topics']), "resources/icons/tema_topic.png")
        self.kpi_row.add_card("Заметки", str(total_stats['total_notes']), "resources/icons/notes.png")
        self.kpi_row.add_card("Карточки", str(total_stats['total_flashcards']), "resources/icons/flashcard.png")
        self.kpi_row.add_card("Задачи", f"{total_stats['completed_tasks']}/{total_stats['total_tasks']}", "resources/icons/task.png")
        self.kpi_row.add_card("Сессии", str(total_stats['total_sessions']), "resources/icons/session.png")
        self.kpi_row.add_card("Время", f"{total_stats['total_hours']} ч", "resources/icons/time.png")

        # Активная тема
        active_topic = self._controller.get_active_topic()
        if active_topic:
            self.active_topic_widget.show()
            self.active_topic_name.setText(active_topic['name'])
            self._active_topic_id = active_topic['id']

            last_activity = active_topic.get('last_activity', '')
            if last_activity:
                date_str = last_activity[:10]
                self.active_topic_info.setText(f"Последняя активность: {date_str}")
        else:
            self.active_topic_widget.hide()

        # Последняя сессия
        last_session = self._controller.get_last_session()
        if last_session and last_session.get('duration_minutes', 0) > 0:
            self.last_session_widget.show()
            self.last_session_topic.setText(last_session['topic_name'])
            self.last_session_duration.setText(f"️resources/icons/session.png {last_session['duration_display']}")     #время последней сессии
            self.last_session_conc.setText(f"resources/icons/brain.png {last_session['avg_concentration']}/5")
        else:
            self.last_session_widget.hide()

        # Срочные задачи
        urgent_tasks = self._controller.get_urgent_tasks()
        self._update_urgent_tasks(urgent_tasks)

        # Аналитика за сегодня
        today_analytics = self._controller.get_today_analytics()
        if today_analytics['has_data']:
            self.today_analytics_widget.show()
            self.today_time_label.setText(f"{today_analytics['total_hours']} ч")
            self.today_conc_label.setText(str(today_analytics['avg_concentration']))
            self.today_energy_label.setText(str(today_analytics['avg_energy']))
        else:
            self.today_analytics_widget.hide()

    def _update_urgent_tasks(self, tasks: list):
        """Обновляет список срочных задач"""
        try:
            # Очищаем старые кнопки
            for btn in self._urgent_task_buttons.values():
                btn.deleteLater()
            self._urgent_task_buttons.clear()

            # Очищаем layout
            while self.tasks_layout.count():
                child = self.tasks_layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()

            if not tasks:
                if hasattr(self, 'no_tasks_label') and self.no_tasks_label:
                    self.no_tasks_label.show()
                if self.urgent_tasks_widget:
                    self.urgent_tasks_widget.hide()
                return

            if hasattr(self, 'no_tasks_label') and self.no_tasks_label:
                self.no_tasks_label.hide()
            if self.urgent_tasks_widget:
                self.urgent_tasks_widget.show()

            for task in tasks:
                task_widget = self._create_task_widget(task)
                self.tasks_layout.addWidget(task_widget)
        except RuntimeError:
            # Виджет уже удалён, просто игнорируем
            pass

    def _create_task_widget(self, task: dict) -> QWidget:
        """Создаёт виджет для одной задачи"""
        widget = QPushButton()

        if task['is_overdue']:
            style = """
                QPushButton {
                    text-align: left;
                    padding: 8px;
                    background-color: #ffebee;
                    border-left: 4px solid #d32f2f;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #ffcdd2;
                }
            """
            prefix = "⚠️ "
        else:
            style = """
                QPushButton {
                    text-align: left;
                    padding: 8px;
                    background-color: #fff3e0;
                    border-left: 4px solid #ff9800;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #ffe0b2;
                }
            """
            prefix = "📋 "

        widget.setStyleSheet(style)
        widget.setText(f"{prefix}{task['title']} — {task['topic_name']} (до {task['deadline_display']})")
        widget.clicked.connect(lambda checked, tid=task['id']: self._on_task_clicked(tid))

        self._urgent_task_buttons[task['id']] = widget
        return widget