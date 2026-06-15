from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QMessageBox, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QFont, QPixmap, QIcon, QColor

from .controller import DashboardController
from .widgets import KpiRow, KpiCard


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
        self.content_layout.setSpacing(20)

        # Пустое состояние (будет показано если нет данных)
        self.empty_widget = self._create_empty_state()
        self.content_layout.addWidget(self.empty_widget)

        # Блок приветствия
        self.greeting_widget = self._create_greeting_block()
        self.content_layout.addWidget(self.greeting_widget)

        # Блок KPI (общая статистика) — 6 карточек в ряд
        self.kpi_row = KpiRow()
        self.content_layout.addWidget(self.kpi_row)

        # Ряд 1: Активная тема + Последняя сессия (2 блока в строке)
        row1_layout = QHBoxLayout()
        row1_layout.setSpacing(20)

        self.active_topic_widget = self._create_active_topic_block()
        self.last_session_widget = self._create_last_session_block()

        # Даём обоим блокам одинаковый коэффициент растяжения
        row1_layout.addWidget(self.active_topic_widget, 1)
        row1_layout.addWidget(self.last_session_widget, 1)

        self.content_layout.addLayout(row1_layout)

        # Блок срочных задач (на всю ширину)
        self.urgent_tasks_widget = self._create_urgent_tasks_block()
        self.content_layout.addWidget(self.urgent_tasks_widget)

        # Ряд 2: Быстрый старт + Сегодня (2 блока в строке)
        row2_layout = QHBoxLayout()
        row2_layout.setSpacing(20)

        self.quick_start_widget = self._create_quick_start_block()
        self.today_analytics_widget = self._create_today_analytics_block()

        # Даём обоим блокам одинаковый коэффициент растяжения
        row2_layout.addWidget(self.quick_start_widget, 1)
        row2_layout.addWidget(self.today_analytics_widget, 1)

        self.content_layout.addLayout(row2_layout)

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
        """Создаёт блок приветствия в стиле плашки с иконками и цветными кружками"""
        widget = QFrame()
        widget.setFrameShape(QFrame.StyledPanel)
        widget.setProperty("class", "dashboard-card")

        widget.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border-radius: 16px;
                border: none;
            }
        """)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setOffset(2, 2)
        shadow.setColor(QColor(0, 0, 0, 30))
        widget.setGraphicsEffect(shadow)

        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)
        layout.setAlignment(Qt.AlignCenter)

        # Приветствие
        self.greeting_label = QLabel()
        self.greeting_label.setAlignment(Qt.AlignCenter)
        self.greeting_label.setStyleSheet("""
            font-size: 22px; 
            font-weight: bold; 
            color: #1E2A3E; 
            background-color: transparent;
        """)
        layout.addWidget(self.greeting_label)

        # Контейнер для статистики с иконками
        stats_container = QWidget()
        stats_container.setStyleSheet("background-color: transparent;")
        stats_layout = QVBoxLayout(stats_container)
        stats_layout.setSpacing(8)
        stats_layout.setAlignment(Qt.AlignCenter)

        # Строка "Выполнено задач" с зелёным кружком
        completed_row = QHBoxLayout()
        completed_row.setSpacing(8)
        completed_row.setAlignment(Qt.AlignCenter)

        # Зелёный кружок для задачи
        completed_icon_container = QLabel()
        completed_icon_container.setFixedSize(32, 32)
        completed_icon_container.setAlignment(Qt.AlignCenter)
        completed_icon_container.setStyleSheet("""
            background-color: rgba(16, 185, 129, 0.15);
            border-radius: 16px;
        """)

        completed_icon = QLabel()
        completed_pixmap = QPixmap("resources/icons/task1.png")
        if not completed_pixmap.isNull():
            completed_pixmap = completed_pixmap.scaled(18, 18, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            completed_icon.setPixmap(completed_pixmap)
        else:
            completed_icon.setText("📋")
            completed_icon.setStyleSheet("font-size: 14px;")
        completed_icon.setAlignment(Qt.AlignCenter)

        completed_icon_layout = QVBoxLayout(completed_icon_container)
        completed_icon_layout.setContentsMargins(0, 0, 0, 0)
        completed_icon_layout.addWidget(completed_icon)

        self.completed_label = QLabel("Выполнено задач сегодня: 0")
        self.completed_label.setStyleSheet("font-size: 14px; color: #2C3E50; background-color: transparent;")

        completed_row.addWidget(completed_icon_container)
        completed_row.addWidget(self.completed_label)
        stats_layout.addLayout(completed_row)

        # Строка "Отработано" с красным кружком
        worked_row = QHBoxLayout()
        worked_row.setSpacing(8)
        worked_row.setAlignment(Qt.AlignCenter)

        # Красный кружок для времени
        worked_icon_container = QLabel()
        worked_icon_container.setFixedSize(32, 32)
        worked_icon_container.setAlignment(Qt.AlignCenter)
        worked_icon_container.setStyleSheet("""
            background-color: rgba(239, 68, 68, 0.15);
            border-radius: 16px;
        """)

        worked_icon = QLabel()
        worked_pixmap = QPixmap("resources/icons/time1.png")
        if not worked_pixmap.isNull():
            worked_pixmap = worked_pixmap.scaled(18, 18, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            worked_icon.setPixmap(worked_pixmap)
        else:
            worked_icon.setText("⏱️")
            worked_icon.setStyleSheet("font-size: 14px;")
        worked_icon.setAlignment(Qt.AlignCenter)

        worked_icon_layout = QVBoxLayout(worked_icon_container)
        worked_icon_layout.setContentsMargins(0, 0, 0, 0)
        worked_icon_layout.addWidget(worked_icon)

        self.worked_label = QLabel("Отработано: 0 ч")
        self.worked_label.setStyleSheet("font-size: 14px; color: #2C3E50; background-color: transparent;")

        worked_row.addWidget(worked_icon_container)
        worked_row.addWidget(self.worked_label)
        stats_layout.addLayout(worked_row)

        layout.addWidget(stats_container)

        return widget

    def _create_active_topic_block(self) -> QWidget:
        """Создаёт блок активной темы"""
        widget = QFrame()
        widget.setFrameShape(QFrame.StyledPanel)
        widget.setProperty("class", "dashboard-card")

        widget.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border-radius: 16px;
                border: none;
            }
        """)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setOffset(2, 2)
        shadow.setColor(QColor(0, 0, 0, 30))
        widget.setGraphicsEffect(shadow)

        layout = QVBoxLayout(widget)
        layout.setContentsMargins(15, 12, 15, 12)
        layout.setSpacing(8)

        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)

        # Круг для иконки
        icon_container = QLabel()
        icon_container.setFixedSize(36, 36)
        icon_container.setAlignment(Qt.AlignCenter)
        icon_container.setStyleSheet("""
            background-color: rgba(59, 130, 246, 0.15);
            border-radius: 18px;
        """)

        # Иконка внутри круга — по центру
        icon_label = QLabel()
        icon_label.setAlignment(Qt.AlignCenter)
        pixmap = QPixmap("resources/icons/activ_topic.png")
        if not pixmap.isNull():
            pixmap = pixmap.scaled(20, 20, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            icon_label.setPixmap(pixmap)
        else:
            icon_label.setText("📌")
            icon_label.setStyleSheet("font-size: 16px; background-color: transparent;")

        container_layout = QVBoxLayout(icon_container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.addWidget(icon_label)

        title_label = QLabel("Активная тема")
        title_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #1E2A3E; background-color: transparent;")

        header_layout.addWidget(icon_container)
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        self.active_topic_name = QLabel("—")
        self.active_topic_name.setStyleSheet(
            "font-size: 18px; font-weight: bold; color: #1E2A3E; background-color: transparent;")
        layout.addWidget(self.active_topic_name)

        self.active_topic_info = QLabel("")
        self.active_topic_info.setStyleSheet("color: #5A6B7C; font-size: 12px; background-color: transparent;")
        layout.addWidget(self.active_topic_info)

        open_btn = QPushButton("Открыть тему")
        open_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(59, 130, 246, 0.15);
                color: #3B82F6;
                border: 1px solid #3B82F6;
                border-radius: 12px;
                padding: 6px;
                font-size: 13px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: rgba(59, 130, 246, 0.25);
                border: 1px solid #2563EB;
                color: #2563EB;
            }
            QPushButton:pressed {
                background-color: rgba(59, 130, 246, 0.35);
            }
        """)
        open_btn.clicked.connect(self._on_open_active_topic)
        layout.addWidget(open_btn)

        widget.hide()
        return widget

    def _create_last_session_block(self) -> QWidget:
        """Создаёт блок последней сессии"""
        widget = QFrame()
        widget.setFrameShape(QFrame.StyledPanel)
        widget.setProperty("class", "dashboard-card")

        widget.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border-radius: 16px;
                border: none;
            }
        """)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setOffset(2, 2)
        shadow.setColor(QColor(0, 0, 0, 30))
        widget.setGraphicsEffect(shadow)

        layout = QVBoxLayout(widget)
        layout.setContentsMargins(15, 12, 15, 12)
        layout.setSpacing(8)

        # Заголовок с иконкой на круге
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)

        # Жёлтый круг для иконки сессии
        icon_container = QLabel()
        icon_container.setFixedSize(36, 36)
        icon_container.setAlignment(Qt.AlignCenter)
        icon_container.setStyleSheet("""
            background-color: rgba(245, 158, 11, 0.15);
            border-radius: 18px;
        """)

        icon_label = QLabel()
        icon_label.setAlignment(Qt.AlignCenter)
        pixmap = QPixmap("resources/icons/session.png")
        if not pixmap.isNull():
            pixmap = pixmap.scaled(20, 20, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            icon_label.setPixmap(pixmap)
        else:
            icon_label.setText("⏱️")
            icon_label.setStyleSheet("font-size: 16px; background-color: transparent;")

        container_layout = QVBoxLayout(icon_container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.addWidget(icon_label)

        title_label = QLabel("Последняя сессия")
        title_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #1E2A3E; background-color: transparent;")

        header_layout.addWidget(icon_container)
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        # Название темы
        self.last_session_topic = QLabel("—")
        self.last_session_topic.setStyleSheet(
            "font-size: 16px; font-weight: bold; color: #1E2A3E; background-color: transparent;")
        layout.addWidget(self.last_session_topic)

        # Время и концентрация
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(16)

        self.last_session_duration = QWidget()
        self.last_session_conc = QWidget()
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

        widget.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border-radius: 16px;
                border: none;
                Color: #ffffff;
            }
        """)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setOffset(2, 2)
        shadow.setColor(QColor(0, 0, 0, 30))
        widget.setGraphicsEffect(shadow)

        layout = QVBoxLayout(widget)
        layout.setContentsMargins(15, 12, 15, 12)

        header_layout = QHBoxLayout()
        icon_label = QLabel()
        pixmap = QPixmap("resources/icons/rocket.png")
        if not pixmap.isNull():
            pixmap = pixmap.scaled(20, 20, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            icon_label.setPixmap(pixmap)
        else:
            icon_label.setText("🚀")
            icon_label.setStyleSheet("font-size: 16px; background-color: transparent;")

        title_label = QLabel("Быстрый старт")
        title_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #1E2A3E; background-color: transparent;")
        header_layout.addWidget(icon_label)
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        start_btn = QPushButton("Начать сессию")
        start_icon = QPixmap("resources/icons/play1.png")
        if not start_icon.isNull():
            start_btn.setIcon(QIcon(start_icon))
            start_btn.setIconSize(QSize(20, 20))
        start_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(59, 130, 246, 0.15);
                color: #3B82F6;
                border: 1px solid #3B82F6;
                border-radius: 12px;
                padding: 8px;
                font-size: 14px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: rgba(59, 130, 246, 0.25);
                border: 1px solid #2563EB;
                color: #2563EB;
            }
        """)
        start_btn.clicked.connect(self.start_session_requested.emit)
        layout.addWidget(start_btn)

        return widget

    def _create_urgent_tasks_block(self) -> QWidget:
        """Создаёт блок срочных задач"""
        widget = QFrame()
        widget.setFrameShape(QFrame.StyledPanel)
        widget.setProperty("class", "dashboard-card")

        widget.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border-radius: 16px;
                border: none;
                Color: #ffffff;
            }
        """)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setOffset(2, 2)
        shadow.setColor(QColor(0, 0, 0, 30))
        widget.setGraphicsEffect(shadow)

        layout = QVBoxLayout(widget)
        layout.setContentsMargins(15, 12, 15, 12)

        header_layout = QHBoxLayout()
        icon_label = QLabel()
        pixmap = QPixmap("resources/icons/warning.png")
        if not pixmap.isNull():
            pixmap = pixmap.scaled(20, 20, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            icon_label.setPixmap(pixmap)
        else:
            icon_label.setText("⚠️")
            icon_label.setStyleSheet("font-size: 16px; background-color: transparent;")

        title_label = QLabel("Срочные задачи")
        title_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #1E2A3E; background-color: transparent;")
        header_layout.addWidget(icon_label)
        header_layout.addWidget(title_label)
        header_layout.addStretch()

        all_tasks_btn = QPushButton("Все задачи")
        all_tasks_btn.setFlat(True)
        all_tasks_btn.setStyleSheet("""
            QPushButton {
                color: #3B82F6;
                background-color: rgba(59, 130, 246, 0.1);
                border-radius: 8px;
                padding: 4px 8px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: rgba(59, 130, 246, 0.2);
            }
        """)
        all_tasks_btn.clicked.connect(self.open_tasks_requested.emit)
        header_layout.addWidget(all_tasks_btn)

        layout.addLayout(header_layout)

        self.tasks_layout = QVBoxLayout()
        self.tasks_layout.setSpacing(8)
        layout.addLayout(self.tasks_layout)

        self.no_tasks_label = QLabel("Нет срочных задач")
        self.no_tasks_label.setAlignment(Qt.AlignCenter)
        self.no_tasks_label.setStyleSheet("color: #5A6B7C; background-color: transparent; padding: 10px;")
        self.tasks_layout.addWidget(self.no_tasks_label)

        widget.hide()
        return widget

    def _create_today_analytics_block(self) -> QWidget:
        """Создаёт блок аналитики за сегодня с прогресс-барами"""
        widget = QFrame()
        widget.setFrameShape(QFrame.StyledPanel)
        widget.setProperty("class", "dashboard-card")

        # Белый фон, скругление 16px
        widget.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border-radius: 16px;
                border: none;
            }
        """)

        # Лёгкая тень
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(12)
        shadow.setOffset(0, 2)
        shadow.setColor(QColor(0, 0, 0, 10))
        widget.setGraphicsEffect(shadow)

        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 14, 16, 14)

        # Заголовок с иконкой и кнопкой "Подробнее"
        header_layout = QHBoxLayout()
        icon_label = QLabel()
        pixmap = QPixmap("resources/icons/analitics.png")
        if not pixmap.isNull():
            pixmap = pixmap.scaled(20, 20, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            icon_label.setPixmap(pixmap)
        else:
            icon_label.setText("📊")
            icon_label.setStyleSheet("font-size: 16px; background-color: transparent;")

        title_label = QLabel("Сегодня")
        title_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #1E2A3E; background-color: transparent;")
        header_layout.addWidget(icon_label)
        header_layout.addWidget(title_label)
        header_layout.addStretch()

        analytics_btn = QPushButton("Подробнее")
        analytics_btn.setFlat(True)
        analytics_btn.setStyleSheet("""
            QPushButton {
                color: #3B82F6;
                background-color: rgba(59, 130, 246, 0.1);
                border-radius: 8px;
                padding: 4px 12px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: rgba(59, 130, 246, 0.2);
            }
        """)
        analytics_btn.clicked.connect(self.open_analytics_requested.emit)
        header_layout.addWidget(analytics_btn)

        layout.addLayout(header_layout)

        # Три карточки: Время, Концентрация, Энергия
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(16)

        # --- Карточка времени ---
        time_card = QFrame()
        time_card.setStyleSheet("""
            QFrame {
                background-color: #F9FAFB;
                border-radius: 12px;
                border: none;
            }
        """)
        time_layout = QVBoxLayout(time_card)
        time_layout.setContentsMargins(12, 10, 12, 10)
        time_layout.setSpacing(4)

        self.today_time_label = QLabel("0.0 ч")
        self.today_time_label.setStyleSheet(
            "font-size: 22px; font-weight: bold; color: #1F2937; background-color: transparent;")
        time_layout.addWidget(self.today_time_label)

        time_icon_layout = QHBoxLayout()
        time_icon_layout.setSpacing(4)
        hourglass_label = QLabel("⏳")
        hourglass_label.setStyleSheet("font-size: 14px; background-color: transparent;")
        self.today_time_desc = QLabel("времени")
        self.today_time_desc.setStyleSheet("color: #6B7280; font-size: 12px; background-color: transparent;")
        time_icon_layout.addWidget(hourglass_label)
        time_icon_layout.addWidget(self.today_time_desc)
        time_icon_layout.addStretch()
        time_layout.addLayout(time_icon_layout)

        stats_layout.addWidget(time_card, 1)

        # --- Карточка концентрации с прогресс-баром ---
        conc_card = QFrame()
        conc_card.setStyleSheet("""
            QFrame {
                background-color: #F9FAFB;
                border-radius: 12px;
                border: none;
            }
        """)
        conc_layout = QVBoxLayout(conc_card)
        conc_layout.setContentsMargins(12, 10, 12, 10)
        conc_layout.setSpacing(4)

        self.today_conc_label = QLabel("0")
        self.today_conc_label.setStyleSheet(
            "font-size: 22px; font-weight: bold; color: #1F2937; background-color: transparent;")
        conc_layout.addWidget(self.today_conc_label)

        self.today_conc_desc = QLabel("концентрация")
        self.today_conc_desc.setStyleSheet("color: #6B7280; font-size: 12px; background-color: transparent;")
        conc_layout.addWidget(self.today_conc_desc)

        # Прогресс-бар для концентрации
        self.conc_progress = QFrame()
        self.conc_progress.setFixedHeight(4)
        self.conc_progress.setStyleSheet("""
            QFrame {
                background-color: #F0F4F8;
                border-radius: 2px;
                border: none;
            }
        """)
        conc_layout.addWidget(self.conc_progress)

        # Заполненная часть (будет обновляться в refresh)
        self.conc_fill = QFrame(self.conc_progress)
        self.conc_fill.setFixedHeight(4)
        self.conc_fill.setStyleSheet("""
            QFrame {
                background-color: #10B981;
                border-radius: 2px;
                border: none;
            }
        """)
        self.conc_fill.setParent(self.conc_progress)

        stats_layout.addWidget(conc_card, 1)

        # --- Карточка энергии с прогресс-баром ---
        energy_card = QFrame()
        energy_card.setStyleSheet("""
            QFrame {
                background-color: #F9FAFB;
                border-radius: 12px;
                border: none;
            }
        """)
        energy_layout = QVBoxLayout(energy_card)
        energy_layout.setContentsMargins(12, 10, 12, 10)
        energy_layout.setSpacing(4)

        self.today_energy_label = QLabel("0")
        self.today_energy_label.setStyleSheet(
            "font-size: 22px; font-weight: bold; color: #1F2937; background-color: transparent;")
        energy_layout.addWidget(self.today_energy_label)

        self.today_energy_desc = QLabel("энергия")
        self.today_energy_desc.setStyleSheet("color: #6B7280; font-size: 12px; background-color: transparent;")
        energy_layout.addWidget(self.today_energy_desc)

        # Прогресс-бар для энергии
        self.energy_progress = QFrame()
        self.energy_progress.setFixedHeight(4)
        self.energy_progress.setStyleSheet("""
            QFrame {
                background-color: #F0F4F8;
                border-radius: 2px;
                border: none;
            }
        """)
        energy_layout.addWidget(self.energy_progress)

        # Заполненная часть
        self.energy_fill = QFrame(self.energy_progress)
        self.energy_fill.setFixedHeight(4)
        self.energy_fill.setStyleSheet("""
            QFrame {
                background-color: #F59E0B;
                border-radius: 2px;
                border: none;
            }
        """)
        self.energy_fill.setParent(self.energy_progress)

        stats_layout.addWidget(energy_card, 1)

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

        self.empty_widget.setVisible(not has_data)

        if not has_data:
            return

        for widget in [self.greeting_widget, self.kpi_row, self.active_topic_widget,
                       self.last_session_widget, self.urgent_tasks_widget,
                       self.quick_start_widget, self.today_analytics_widget]:
            widget.show()

        greeting = self._controller.get_greeting()
        user_name = self._controller.get_user_name()
        self.greeting_label.setText(f"{greeting}, {user_name}!")

        today_stats = self._controller.get_today_stats()
        self.completed_label.setText(f"Выполнено задач сегодня: {today_stats['completed_tasks_today']}")
        self.worked_label.setText(f"Отработано: {today_stats['worked_hours_today']} ч")

        total_stats = self._controller.get_total_stats()
        self.kpi_row.clear()
        self.kpi_row.add_card("Темы", str(total_stats['total_topics']), "resources/icons/tema1.png")
        self.kpi_row.add_card("Заметки", str(total_stats['total_notes']), "resources/icons/notes1.png")
        self.kpi_row.add_card("Карточки", str(total_stats['total_flashcards']), "resources/icons/flashcard1.png")
        self.kpi_row.add_card("Задачи", f"{total_stats['completed_tasks']}/{total_stats['total_tasks']}","resources/icons/task1.png")
        self.kpi_row.add_card("Сессии", str(total_stats['total_sessions']), "resources/icons/session1.png")
        self.kpi_row.add_card("Время", f"{total_stats['total_hours']} ч", "resources/icons/time1.png")

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

        last_session = self._controller.get_last_session()
        if last_session is not None:
            self.last_session_widget.show()
            self.last_session_topic.setText(last_session.get('topic_name', 'Нет данных'))
            # ... остальной код ...

            # ... остальное
            self.last_session_widget.show()
            self.last_session_topic.setText(last_session['topic_name'])

            # Время — розовый круг
            duration_layout = self.last_session_duration.layout() if self.last_session_duration.layout() else QHBoxLayout(
                self.last_session_duration)
            self.last_session_duration.setLayout(duration_layout)
            self.last_session_duration.setStyleSheet("border: none; outline: none; background-color: transparent;")
            for i in reversed(range(duration_layout.count())):
                duration_layout.itemAt(i).widget().deleteLater()

            # Розовый круг для времени
            time_container = QLabel()
            time_container.setFixedSize(28, 28)
            time_container.setAlignment(Qt.AlignCenter)
            time_container.setStyleSheet("""
                background-color: rgba(239, 68, 68, 0.15);
                border-radius: 14px;
                border: none;
                outline: none;
            """)

            time_icon = QLabel()
            time_icon.setAlignment(Qt.AlignCenter)
            time_icon.setStyleSheet("border: none; outline: none; background-color: transparent;")
            time_pixmap = QPixmap("resources/icons/time1.png")
            if not time_pixmap.isNull():
                time_pixmap = time_pixmap.scaled(16, 16, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                time_icon.setPixmap(time_pixmap)
            else:
                time_icon.setText("⏱️")
                time_icon.setStyleSheet("font-size: 12px; border: none;")

            time_container_layout = QVBoxLayout(time_container)
            time_container_layout.setContentsMargins(0, 0, 0, 0)
            time_container_layout.addWidget(time_icon)

            time_label = QLabel(last_session['duration_display'])
            time_label.setStyleSheet("color: #5A6B7C; background-color: transparent; border: none;")

            duration_layout.addWidget(time_container)
            duration_layout.addWidget(time_label)

            # Концентрация — зелёный круг
            conc_layout = self.last_session_conc.layout() if self.last_session_conc.layout() else QHBoxLayout(
                self.last_session_conc)
            self.last_session_conc.setLayout(conc_layout)
            self.last_session_conc.setStyleSheet("border: none; outline: none; background-color: transparent;")
            for i in reversed(range(conc_layout.count())):
                conc_layout.itemAt(i).widget().deleteLater()

            # Зелёный круг для мозга
            brain_container = QLabel()
            brain_container.setFixedSize(28, 28)
            brain_container.setAlignment(Qt.AlignCenter)
            brain_container.setStyleSheet("""
                background-color: rgba(16, 185, 129, 0.15);
                border-radius: 14px;
                border: none;
                outline: none;
            """)

            brain_icon = QLabel()
            brain_icon.setAlignment(Qt.AlignCenter)
            brain_icon.setStyleSheet("border: none; outline: none; background-color: transparent;")
            brain_pixmap = QPixmap("resources/icons/brain1.png")
            if not brain_pixmap.isNull():
                brain_pixmap = brain_pixmap.scaled(16, 16, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                brain_icon.setPixmap(brain_pixmap)
            else:
                brain_icon.setText("🧠")
                brain_icon.setStyleSheet("font-size: 12px; border: none;")

            brain_container_layout = QVBoxLayout(brain_container)
            brain_container_layout.setContentsMargins(0, 0, 0, 0)
            brain_container_layout.addWidget(brain_icon)

            conc_label = QLabel(f"{last_session['avg_concentration']}/5")
            conc_label.setStyleSheet("color: #5A6B7C; background-color: transparent; border: none;")

            conc_layout.addWidget(brain_container)
            conc_layout.addWidget(conc_label)

        else:

            self.last_session_widget.hide()

            def resizeEvent(self, event):
                super().resizeEvent(event)
                self._update_progress_bars_width()

    def _update_urgent_tasks(self, tasks: list):
        """Обновляет список срочных задач"""
        try:
            for btn in self._urgent_task_buttons.values():
                btn.deleteLater()
            self._urgent_task_buttons.clear()

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
            pass

    def _create_task_widget(self, task: dict) -> QWidget:
        """Создаёт виджет для одной задачи"""
        widget = QPushButton()

        # Определяем цвет маркера и иконку в зависимости от статуса
        if task['is_overdue']:
            marker_color = "#EF4444"  # красный для просроченных
            prefix = "⚠️ "
            bg_color = "#FFFFFF"
            hover_color = "#FEF2F2"
        else:
            marker_color = "#F59E0B"  # оранжевый для срочных
            prefix = "📋 "
            bg_color = "#FFFFFF"
            hover_color = "#FFFBEB"

        style = f"""
            QPushButton {{
                text-align: left;
                padding: 12px;
                background-color: {bg_color};
                border-left: 4px solid {marker_color};
                border-radius: 12px;
                color: #1F2937;
                font-size: 13px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: {hover_color};
            }}
        """

        widget.setStyleSheet(style)
        widget.setText(f"{prefix}{task['title']} — {task['topic_name']} (до {task['deadline_display']})")
        widget.clicked.connect(lambda checked, tid=task['id']: self._on_task_clicked(tid))

        self._urgent_task_buttons[task['id']] = widget
        return widget