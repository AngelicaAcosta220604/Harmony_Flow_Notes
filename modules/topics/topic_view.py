# modules/topics/topic_view.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QLabel,
    QPushButton, QScrollArea, QFrame, QMessageBox, QTextEdit, QListWidget, QListWidgetItem, QCheckBox,
    QSizePolicy, QProgressBar
)
from PySide6.QtCore import Signal, Qt, QSize
from PySide6.QtGui import QIcon, QPixmap, QColor

from widgets import SilentMessageBox
from .controller import TopicController
from .analytics_controller import TopicAnalyticsController
import re

def remove_emojis(text: str) -> str:
    emoji_pattern = re.compile("["
                               u"\U0001F600-\U0001F64F"
                               u"\U0001F300-\U0001F5FF"
                               u"\U0001F680-\U0001F6FF"
                               u"\U0001F700-\U0001F77F"
                               u"\U0001F780-\U0001F7FF"
                               u"\U0001F800-\U0001F8FF"
                               u"\U0001F900-\U0001F9FF"
                               u"\U0001FA00-\U0001FA6F"
                               u"\U0001FA70-\U0001FAFF"
                               u"\U00002702-\U000027B0"
                               u"\U000024C2-\U0001F251"
                               "]+", flags=re.UNICODE)
    return emoji_pattern.sub(r'', text).strip()

class NoteListItemWidget(QWidget):
    """Виджет для отображения записи в списке с кнопками"""

    def __init__(self, note_id: int, title: str, date_str: str, parent=None):
        super().__init__(parent)
        self.note_id = note_id
        self._setup_ui(title, date_str)

    def _setup_ui(self, title: str, date_str: str):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(10)

        self.title_label = QLabel(title)
        self.title_label.setStyleSheet("font-weight: 500; color: #1F2937;")
        layout.addWidget(self.title_label, 1)

        self.date_label = QLabel(date_str)
        self.date_label.setStyleSheet("color: #6B7280; font-size: 10px;")
        layout.addWidget(self.date_label)

        self.open_btn = QPushButton()
        self.open_btn.setIcon(QIcon("resources/icons/open.png"))
        self.open_btn.setIconSize(QSize(16, 16))
        self.open_btn.setFixedSize(30, 30)
        self.open_btn.setToolTip("Открыть запись")
        layout.addWidget(self.open_btn)

        self.edit_btn = QPushButton()
        self.edit_btn.setIcon(QIcon("resources/icons/pen.png"))
        self.edit_btn.setIconSize(QSize(16, 16))
        self.edit_btn.setFixedSize(30, 30)
        self.edit_btn.setToolTip("Редактировать запись")
        layout.addWidget(self.edit_btn)

        self.delete_btn = QPushButton()
        self.delete_btn.setIcon(QIcon("resources/icons/urna.png"))
        self.delete_btn.setIconSize(QSize(16, 16))
        self.delete_btn.setFixedSize(30, 30)
        self.delete_btn.setToolTip("Удалить запись")
        layout.addWidget(self.delete_btn)

        self.setStyleSheet("""
            NoteListItemWidget {
                border-bottom: 1px solid #E6EEF6;
                background-color: transparent;
            }
            NoteListItemWidget:hover {
                background-color: #F9FAFB;
            }
            QPushButton {
                border: none;
                background-color: transparent;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #F0F4F8;
            }
        """)
        self.setFixedHeight(50)


class TaskListItemWidget(QWidget):
    """Виджет для отображения задачи в списке с чекбоксом и кнопками"""

    complete_clicked = Signal(int)
    edit_clicked = Signal(int)
    delete_clicked = Signal(int)

    def __init__(self, task_id: int, title: str, deadline: str, status: str, is_overdue: bool, parent=None):
        super().__init__(parent)
        self.task_id = task_id
        self._setup_ui(title, deadline, status, is_overdue)

    def _setup_ui(self, title: str, deadline: str, status: str, is_overdue: bool):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(10)

        # Чекбокс для выполнения
        self.checkbox = QCheckBox()
        self.checkbox.setChecked(status == 'completed')
        self.checkbox.stateChanged.connect(self._on_checkbox_changed)
        layout.addWidget(self.checkbox)

        # Название
        self.title_label = QLabel(title)
        if status == 'completed':
            self.title_label.setStyleSheet("text-decoration: line-through; color: #9CA3AF;")
        elif is_overdue:
            self.title_label.setStyleSheet("color: #EF4444; font-weight: 500;")
        else:
            self.title_label.setStyleSheet("color: #1F2937;")
        layout.addWidget(self.title_label, 1)

        # Дедлайн
        self.deadline_label = QLabel(deadline)
        self.deadline_label.setStyleSheet("color: #6B7280; font-size: 10px;")
        layout.addWidget(self.deadline_label)

        # Кнопки
        self.edit_btn = QPushButton()
        self.edit_btn.setIcon(QIcon("resources/icons/pen.png"))
        self.edit_btn.setIconSize(QSize(16, 16))
        self.edit_btn.setFixedSize(30, 30)
        self.edit_btn.clicked.connect(lambda: self.edit_clicked.emit(self.task_id))
        layout.addWidget(self.edit_btn)

        self.delete_btn = QPushButton()
        self.delete_btn.setIcon(QIcon("resources/icons/urna.png"))
        self.delete_btn.setIconSize(QSize(16, 16))
        self.delete_btn.setFixedSize(30, 30)
        self.delete_btn.clicked.connect(lambda: self.delete_clicked.emit(self.task_id))
        layout.addWidget(self.delete_btn)

        self.setFixedHeight(50)
        self.setStyleSheet("""
            TaskListItemWidget {
                border-bottom: 1px solid #E6EEF6;
                background-color: transparent;
            }
            TaskListItemWidget:hover {
                background-color: #F9FAFB;
            }
            QPushButton {
                border: none;
                background-color: transparent;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #F0F4F8;
            }
        """)

    def _on_checkbox_changed(self, state):
        if state == Qt.Checked:
            self.complete_clicked.emit(self.task_id)


class TopicView(QWidget):
    """
    Экран темы с вкладками:
    - Обзор
    - Записи
    - Задачи
    - Карточки
    - Сессии
    - Аналитика.
    """

    # Сигналы для навигации к другим модулям
    create_note_requested = Signal(int)
    create_task_requested = Signal(int)
    create_flashcard_requested = Signal(int)
    start_session_requested = Signal(int)
    show_all_tasks_requested = Signal(int)
    show_all_notes_requested = Signal(int)
    show_all_cards_requested = Signal(int)
    edit_note_requested = Signal(int)
    edit_task_requested = Signal(int)
    delete_task_requested = Signal(int)
    complete_task_requested = Signal(int)

    back_requested = Signal()

    def __init__(
            self,
            topic_controller: TopicController,
            analytics_controller: TopicAnalyticsController,
            parent=None
    ):
        super().__init__(parent)
        self._topic_controller = topic_controller
        self._analytics_controller = analytics_controller
        self._current_topic_id = None
        self._stat_value_labels = {}
        self._setup_ui()

    def _setup_ui(self):
        """Настраивает интерфейс"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # ========== ЗАГОЛОВОК (белая плашка без обводки) ==========
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
        header_layout.setSpacing(16)

        # Кнопка "Назад"
        self.back_btn = QPushButton("← Назад")
        self.back_btn.setFixedWidth(80)
        self.back_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(59, 130, 246, 0.15);
                color: #3B82F6;
                border: 1px solid #3B82F6;
                border-radius: 12px;
                padding: 8px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: rgba(59, 130, 246, 0.25);
                border: 1px solid #2563EB;
                color: #2563EB;
            }
        """)
        self.back_btn.setToolTip("Вернуться к списку тем")
        header_layout.addWidget(self.back_btn)

        header_layout.addStretch()

        # Иконка темы
        topic_icon = QLabel()
        topic_pixmap = QPixmap("resources/icons/notes.png")
        if not topic_pixmap.isNull():
            topic_pixmap = topic_pixmap.scaled(32, 32, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            topic_icon.setPixmap(topic_pixmap)
        header_layout.addWidget(topic_icon)

        # Название
        self.topic_name_label = QLabel()
        self.topic_name_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #1F2937;")
        header_layout.addWidget(self.topic_name_label)

        header_layout.addStretch()

        # Путь
        self.path_label = QLabel()
        self.path_label.setStyleSheet("color: #6B7280; font-size: 11px;")
        header_layout.addWidget(self.path_label)

        layout.addWidget(header_widget)

        # ========== ВКЛАДКИ ==========
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                background-color: #FFFFFF;
                border-radius: 16px;
                border: 1px solid #E6EEF6;
            }
            QTabBar::tab {
                background-color: #F0F4F8;
                color: #1F2937;
                padding: 8px 20px;
                margin-right: 4px;
                border-top-left-radius: 12px;
                border-top-right-radius: 12px;
                font-weight: 500;
                min-height: 36px;
            }
            QTabBar::tab:selected {
                background-color: #FFFFFF;
                color: #3B82F6;
                border-bottom: 2px solid #3B82F6;
            }
            QTabBar::tab:hover:!selected {
                background-color: #E2E8F0;
            }
        """)

        # Вкладка "Обзор"
        self.overview_tab = self._create_overview_tab()
        self.tab_widget.addTab(self.overview_tab, "Обзор")

        # Вкладка "Записи"
        self.notes_tab = QWidget()
        notes_layout = QVBoxLayout(self.notes_tab)
        notes_layout.setContentsMargins(16, 16, 16, 16)
        self.notes_list = QListWidget()
        self.notes_list.setStyleSheet("border: none;")
        notes_layout.addWidget(self.notes_list)
        self.create_note_btn = QPushButton("Новая запись")
        self.create_note_btn.setIcon(QIcon("resources/icons/notes.png"))
        self.create_note_btn.setIconSize(QSize(18, 18))
        self.create_note_btn.setStyleSheet("""
            QPushButton {
                background-color: #3B82F6;
                color: white;
                border: none;
                border-radius: 12px;
                padding: 10px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #2563EB;
            }
        """)
        notes_layout.addWidget(self.create_note_btn)
        self.tab_widget.addTab(self.notes_tab, "Записи")

        # Вкладка "Задачи"
        self.tasks_tab = QWidget()
        tasks_layout = QVBoxLayout(self.tasks_tab)
        tasks_layout.setContentsMargins(16, 16, 16, 16)
        self.tasks_list = QListWidget()
        self.tasks_list.setStyleSheet("border: none;")
        tasks_layout.addWidget(self.tasks_list)
        self.create_task_btn = QPushButton("Новая задача")
        self.create_task_btn.setIcon(QIcon("resources/icons/tack.png"))
        self.create_task_btn.setIconSize(QSize(18, 18))
        self.create_task_btn.setStyleSheet("""
            QPushButton {
                background-color: #3B82F6;
                color: white;
                border: none;
                border-radius: 12px;
                padding: 10px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #2563EB;
            }
        """)
        tasks_layout.addWidget(self.create_task_btn)
        self.tab_widget.addTab(self.tasks_tab, "Задачи")

        # Вкладка "Карточки"
        self.cards_tab = QWidget()
        cards_layout = QVBoxLayout(self.cards_tab)
        cards_layout.setContentsMargins(16, 16, 16, 16)
        self.cards_list = QListWidget()
        self.cards_list.setStyleSheet("border: none;")
        cards_layout.addWidget(self.cards_list)
        self.create_card_btn = QPushButton("Новая карточка")
        self.create_card_btn.setIcon(QIcon("resources/icons/flashcard.png"))
        self.create_card_btn.setIconSize(QSize(18, 18))
        self.create_card_btn.setStyleSheet("""
            QPushButton {
                background-color: #3B82F6;
                color: white;
                border: none;
                border-radius: 12px;
                padding: 10px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #2563EB;
            }
        """)
        cards_layout.addWidget(self.create_card_btn)
        self.tab_widget.addTab(self.cards_tab, "Карточки")

        # Вкладка "Сессии"
        self.sessions_tab = QWidget()
        sessions_layout = QVBoxLayout(self.sessions_tab)
        sessions_layout.setContentsMargins(16, 16, 16, 16)
        self.sessions_list = QListWidget()
        self.sessions_list.setStyleSheet("border: none;")
        sessions_layout.addWidget(self.sessions_list)
        self.start_session_btn = QPushButton("Начать сессию")
        self.start_session_btn.setIcon(QIcon("resources/icons/play.png"))
        self.start_session_btn.setIconSize(QSize(18, 18))
        self.start_session_btn.setStyleSheet("""
            QPushButton {
                background-color: #3B82F6;
                color: white;
                border: none;
                border-radius: 12px;
                padding: 10px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #2563EB;
            }
        """)
        sessions_layout.addWidget(self.start_session_btn)
        self.tab_widget.addTab(self.sessions_tab, "Сессии")

        # Вкладка "Аналитика"
        self.analytics_tab = QWidget()
        analytics_layout = QVBoxLayout(self.analytics_tab)
        analytics_layout.setContentsMargins(16, 16, 16, 16)
        self.analytics_text = QTextEdit()
        self.analytics_text.setReadOnly(True)
        self.analytics_text.setStyleSheet(
            "border: none; background-color: #F9FAFB; border-radius: 12px; padding: 16px;")
        analytics_layout.addWidget(self.analytics_text)
        self.tab_widget.addTab(self.analytics_tab, "Аналитика")

        layout.addWidget(self.tab_widget)

        # Подключаем сигналы
        self.create_note_btn.clicked.connect(
            lambda: self.create_note_requested.emit(self._current_topic_id)
        )
        self.create_task_btn.clicked.connect(
            lambda: self.create_task_requested.emit(self._current_topic_id)
        )
        self.create_card_btn.clicked.connect(
            lambda: self.create_flashcard_requested.emit(self._current_topic_id)
        )
        self.start_session_btn.clicked.connect(
            lambda: self.start_session_requested.emit(self._current_topic_id)
        )

        self.back_btn.clicked.connect(self.back_requested.emit)

        self.notes_list.itemDoubleClicked.connect(self._on_note_double_clicked)
        self.tasks_list.itemDoubleClicked.connect(self._on_task_double_clicked)
        self.cards_list.itemDoubleClicked.connect(self._on_card_double_clicked)
        self.sessions_list.itemDoubleClicked.connect(self._on_session_double_clicked)

    def _create_overview_tab(self) -> QWidget:
        """Создаёт вкладку обзора"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(20)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("background-color: transparent; border: none;")

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setSpacing(20)

        # Ряд 1: Карточки статистики
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(16)

        self.sessions_card = self._create_stat_card("resources/icons/session.png", "Сессии", "0", "#3B82F6")
        self.time_card = self._create_stat_card("resources/icons/time.png", "Время", "0 ч", "#F59E0B")
        self.conc_card = self._create_stat_card("resources/icons/brain.png", "Концентрация", "0%", "#10B981")
        self.energy_card = self._create_stat_card("resources/icons/energy.png", "Энергия", "0%", "#EF4444")

        stats_layout.addWidget(self.sessions_card)
        stats_layout.addWidget(self.time_card)
        stats_layout.addWidget(self.conc_card)
        stats_layout.addWidget(self.energy_card)
        content_layout.addLayout(stats_layout)

        # Ряд 2: Прогресс задач
        tasks_progress_widget = QFrame()
        tasks_progress_widget.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border-radius: 16px;
                border: none;
            }
        """)
        tasks_progress_widget.setMinimumHeight(80)
        tasks_progress_layout = QVBoxLayout(tasks_progress_widget)
        tasks_progress_layout.setContentsMargins(16, 12, 16, 12)
        tasks_progress_layout.setSpacing(8)

        tasks_title_layout = QHBoxLayout()
        tasks_icon = QLabel()
        tasks_icon_pixmap = QPixmap("resources/icons/tack.png")
        if not tasks_icon_pixmap.isNull():
            tasks_icon_pixmap = tasks_icon_pixmap.scaled(18, 18, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            tasks_icon.setPixmap(tasks_icon_pixmap)
        tasks_title = QLabel("Прогресс задач")
        tasks_title.setStyleSheet("font-weight: 600; color: #1F2937;")
        tasks_title_layout.addWidget(tasks_icon)
        tasks_title_layout.addWidget(tasks_title)
        tasks_title_layout.addStretch()
        tasks_progress_layout.addLayout(tasks_title_layout)

        self.tasks_progress_bar = QProgressBar()
        self.tasks_progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: #F0F4F8;
                border-radius: 8px;
                height: 8px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #3B82F6;
                border-radius: 8px;
            }
        """)
        self.tasks_progress_bar.setTextVisible(False)
        self.tasks_progress_bar.setMinimum(0)
        self.tasks_progress_bar.setMaximum(100)
        tasks_progress_layout.addWidget(self.tasks_progress_bar)

        self.tasks_progress_label = QLabel("0 / 0 выполнено")
        self.tasks_progress_label.setStyleSheet("color: #6B7280; font-size: 12px;")
        tasks_progress_layout.addWidget(self.tasks_progress_label)

        content_layout.addWidget(tasks_progress_widget)

        # Ряд 3: Заметки и карточки
        materials_widget = QFrame()
        materials_widget.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border-radius: 16px;
                border: none;
            }
        """)
        materials_widget.setMinimumHeight(80)
        materials_layout = QHBoxLayout(materials_widget)
        materials_layout.setContentsMargins(16, 12, 16, 12)
        materials_layout.setSpacing(24)

        notes_icon = QLabel()
        notes_icon_pixmap = QPixmap("resources/icons/notes.png")
        if not notes_icon_pixmap.isNull():
            notes_icon_pixmap = notes_icon_pixmap.scaled(18, 18, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            notes_icon.setPixmap(notes_icon_pixmap)
        materials_layout.addWidget(notes_icon)

        self.notes_count_label = QLabel("Заметок: 0")
        self.notes_count_label.setStyleSheet("color: #1F2937; font-weight: 500;")
        materials_layout.addWidget(self.notes_count_label)

        cards_icon = QLabel()
        cards_icon_pixmap = QPixmap("resources/icons/flashcard.png")
        if not cards_icon_pixmap.isNull():
            cards_icon_pixmap = cards_icon_pixmap.scaled(18, 18, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            cards_icon.setPixmap(cards_icon_pixmap)
        materials_layout.addWidget(cards_icon)

        self.cards_count_label = QLabel("Карточек: 0")
        self.cards_count_label.setStyleSheet("color: #1F2937; font-weight: 500;")
        materials_layout.addWidget(self.cards_count_label)

        materials_layout.addStretch()
        content_layout.addWidget(materials_widget)

        # Ряд 4: Кнопки действий
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(12)

        start_btn = QPushButton("Начать сессию")
        start_btn.setIcon(QIcon("resources/icons/play.png"))
        start_btn.setIconSize(QSize(18, 18))
        start_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(245, 158, 11, 0.15);
                color: #D97706;
                border: 1px solid #F59E0B;
                border-radius: 12px;
                padding: 10px 16px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: rgba(245, 158, 11, 0.25);
                border: 1px solid #D97706;
                color: #B45309;
            }
        """)
        start_btn.clicked.connect(lambda: self.start_session_requested.emit(self._current_topic_id))
        actions_layout.addWidget(start_btn)

        note_btn = QPushButton("Новая запись")
        note_btn.setIconSize(QSize(18, 18))
        note_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(59, 130, 246, 0.15);
                color: #3B82F6;
                border: 1px solid #3B82F6;
                border-radius: 12px;
                padding: 10px 16px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: rgba(59, 130, 246, 0.25);
                border: 1px solid #2563EB;
                color: #2563EB;
            }
        """)
        note_btn.clicked.connect(lambda: self.create_note_requested.emit(self._current_topic_id))
        actions_layout.addWidget(note_btn)

        task_btn = QPushButton("Новая задача")
        task_btn.setIcon(QIcon("resources/icons/tack.png"))
        task_btn.setIconSize(QSize(18, 18))
        task_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(16, 185, 129, 0.15);
                color: #059669;
                border: 1px solid #10B981;
                border-radius: 12px;
                padding: 10px 16px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: rgba(16, 185, 129, 0.25);
                border: 1px solid #059669;
                color: #047857;
            }
        """)
        task_btn.clicked.connect(lambda: self.create_task_requested.emit(self._current_topic_id))
        actions_layout.addWidget(task_btn)

        card_btn = QPushButton("Новая карточка")
        card_btn.setIcon(QIcon("resources/icons/flashcard.png"))
        card_btn.setIconSize(QSize(18, 18))
        card_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(239, 68, 68, 0.15);
                color: #EF4444;
                border: 1px solid #EF4444;
                border-radius: 12px;
                padding: 10px 16px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: rgba(239, 68, 68, 0.25);
                border: 1px solid #DC2626;
                color: #DC2626;
            }
        """)
        card_btn.clicked.connect(lambda: self.create_flashcard_requested.emit(self._current_topic_id))
        actions_layout.addWidget(card_btn)

        actions_layout.addStretch()
        content_layout.addLayout(actions_layout)
        content_layout.addStretch()

        scroll.setWidget(content)
        layout.addWidget(scroll)

        return widget

    def _create_stat_card(self, icon_path: str, title: str, value: str, color: str = "#3B82F6") -> QFrame:
        """Создаёт карточку статистики с цветным кругом для иконки"""
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border-radius: 20px;
                border: none;
            }
        """)
        card.setMinimumHeight(130)
        card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(8)

        # Цветной круг с иконкой
        icon_container = QLabel()
        icon_container.setFixedSize(52, 52)
        icon_container.setAlignment(Qt.AlignCenter)

        # Парсим цвет для прозрачного фона
        r = int(color[1:3], 16)
        g = int(color[3:5], 16)
        b = int(color[5:7], 16)

        icon_container.setStyleSheet(f"""
            background-color: rgba({r}, {g}, {b}, 0.15);
            border-radius: 26px;
        """)

        icon_label = QLabel()
        pixmap = QPixmap(icon_path)
        if not pixmap.isNull():
            pixmap = pixmap.scaled(28, 28, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            icon_label.setPixmap(pixmap)
        icon_label.setAlignment(Qt.AlignCenter)

        icon_layout = QVBoxLayout(icon_container)
        icon_layout.setContentsMargins(0, 0, 0, 0)
        icon_layout.addWidget(icon_label)

        layout.addWidget(icon_container)

        # Название
        title_label = QLabel(title)
        title_label.setStyleSheet("color: #6B7280; font-size: 13px;")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        # Значение
        value_label = QLabel(value)
        value_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #1F2937;")
        value_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(value_label)

        self._stat_value_labels[title] = value_label

        return card

    def _update_stat_card_value(self, title: str, new_value: str):
        """Обновляет значение в карточке статистики"""
        if title in self._stat_value_labels:
            self._stat_value_labels[title].setText(new_value)

    def set_topic(self, topic_id: int):
        self._current_topic_id = topic_id

        topic = self._topic_controller.get_topic(topic_id)
        if not topic:
            self.topic_name_label.setText("Тема не найдена")
            return

        self.topic_name_label.setText(topic.display_name)
        path = self._topic_controller.get_path_string(topic_id)
        self.path_label.setText(path)

        self._load_stats(topic_id)
        self._load_notes(topic_id)
        self._load_tasks(topic_id)
        self._load_cards(topic_id)
        self._load_sessions(topic_id)
        self._load_analytics(topic_id)

    def _load_notes(self, topic_id: int):
        notes = self._topic_controller.get_notes_by_topic(topic_id)
        self.notes_list.clear()
        self.notes_list.setSpacing(2)

        if not notes:
            item = QListWidgetItem("📭 Нет записей. Создайте первую запись!")
            item.setForeground(Qt.gray)
            self.notes_list.addItem(item)
            return

        for note in notes:
            title = remove_emojis(getattr(note, 'title', 'Без названия'))
            updated_at = getattr(note, 'updated_at', '')
            created_at = getattr(note, 'created_at', '')
            date_str = updated_at[:16] if updated_at else (created_at[:16] if created_at else "")

            item_widget = NoteListItemWidget(note.id, title, date_str)
            item_widget.open_btn.clicked.connect(lambda checked, nid=note.id: self.show_all_notes_requested.emit(nid))
            item_widget.edit_btn.clicked.connect(lambda checked, nid=note.id: self.edit_note_requested.emit(nid))
            item_widget.delete_btn.clicked.connect(lambda checked, nid=note.id: self._delete_note_by_id(nid))

            item = QListWidgetItem()
            item.setSizeHint(item_widget.sizeHint())
            self.notes_list.addItem(item)
            self.notes_list.setItemWidget(item, item_widget)

    def _load_tasks(self, topic_id: int):
        tasks = self._topic_controller.get_tasks_by_topic(topic_id)
        self.tasks_list.clear()
        self.tasks_list.setSpacing(2)

        if not tasks:
            item = QListWidgetItem("✅ Нет задач. Создайте первую задачу!")
            item.setForeground(Qt.gray)
            self.tasks_list.addItem(item)
            return

        for task in tasks:
            item_widget = TaskListItemWidget(
                task.id, task.title, task.deadline_display, task.status, task.is_overdue()
            )
            item_widget.complete_clicked.connect(self.complete_task_requested.emit)
            item_widget.edit_clicked.connect(self.edit_task_requested.emit)
            item_widget.delete_clicked.connect(self.delete_task_requested.emit)

            item = QListWidgetItem()
            item.setSizeHint(item_widget.sizeHint())
            self.tasks_list.addItem(item)
            self.tasks_list.setItemWidget(item, item_widget)

    def _load_cards(self, topic_id: int):
        cards = self._topic_controller.get_cards_by_topic(topic_id)
        self.cards_list.clear()

        if not cards:
            item = QListWidgetItem("🃏 Нет карточек. Создайте первую карточку!")
            item.setForeground(Qt.gray)
            self.cards_list.addItem(item)
            return

        for card in cards:
            item = QListWidgetItem()
            if card.is_free:
                preview = card.content[:50] + "..." if len(card.content) > 50 else card.content
                item.setText(f"📝 {preview}")
            else:
                preview = card.question[:50] + "..." if len(card.question) > 50 else card.question
                item.setText(f"❓ {preview}")
            item.setData(Qt.UserRole, card.id)
            self.cards_list.addItem(item)

    def _load_sessions(self, topic_id: int):
        sessions = self._topic_controller.get_sessions_by_topic(topic_id)
        self.sessions_list.clear()

        if not sessions:
            item = QListWidgetItem("⏱️ Нет сессий. Начните первую сессию!")
            item.setForeground(Qt.gray)
            self.sessions_list.addItem(item)
            return

        for session in sessions:
            item = QListWidgetItem()
            date_str = session.start_time[:10] if session.start_time else "—"
            duration = session.duration_display if session.duration_minutes else "—"
            item.setText(f"📅 {date_str} | ⏱️ {duration}")
            item.setData(Qt.UserRole, session.id)
            self.sessions_list.addItem(item)

    def _load_analytics(self, topic_id: int):
        stats = self._analytics_controller.get_topic_stats(topic_id)
        text = f"""
        <style>
            p {{ color: #1F2937; font-size: 13px; line-height: 1.6; }}
            h3 {{ color: #1F2937; font-size: 16px; font-weight: 600; margin-bottom: 12px; }}
        </style>
        <h3>📊 Аналитика темы</h3>
        <p>📅 <b>Сессии:</b> {stats['session_count']}</p>
        <p>⏰ <b>Общее время:</b> {stats['total_hours']} ч</p>
        <p>🧠 <b>Средняя концентрация:</b> {stats['avg_concentration']}/5</p>
        <p>⚡ <b>Средняя энергия:</b> {stats['avg_energy']}/5</p>
        <p>❤️ <b>Средний интерес:</b> {stats['avg_interest']}/5</p>
        <p>✅ <b>Задачи:</b> {stats['completed_tasks']}/{stats['task_count']} выполнено</p>
        <p>📝 <b>Заметки:</b> {stats['note_count']}</p>
        <p>🃏 <b>Карточки:</b> {stats['flashcard_count']}</p>
        """
        self.analytics_text.setHtml(text)

    def _load_stats(self, topic_id: int):
        stats = self._analytics_controller.get_topic_stats(topic_id)

        self._update_stat_card_value("Сессии", str(stats['session_count']))
        self._update_stat_card_value("Время", f"{stats['total_hours']} ч")
        self._update_stat_card_value("Концентрация", f"{stats['avg_concentration']}/5")
        self._update_stat_card_value("Энергия", f"{stats['avg_energy']}/5")

        # Обновляем прогресс-бар
        completed = stats.get('completed_tasks', 0)
        total = stats.get('task_count', 1)
        if total == 0:
            total = 1
        percent = int((completed / total) * 100)
        self.tasks_progress_bar.setValue(percent)
        self.tasks_progress_label.setText(f"{completed} / {stats['task_count']} выполнено ({percent}%)")

        self.notes_count_label.setText(f"Заметок: {stats['note_count']}")
        self.cards_count_label.setText(f"Карточек: {stats['flashcard_count']}")

    def refresh(self):
        if self._current_topic_id:
            self._load_stats(self._current_topic_id)

    def get_current_topic_id(self) -> int:
        return self._current_topic_id

    def _on_note_double_clicked(self, item):
        note_id = item.data(Qt.UserRole)
        if note_id:
            self.show_all_notes_requested.emit(note_id)

    def _on_task_double_clicked(self, item):
        task_id = item.data(Qt.UserRole)
        if task_id:
            self.show_all_tasks_requested.emit(task_id)

    def _on_card_double_clicked(self, item):
        card_id = item.data(Qt.UserRole)
        if card_id:
            self.show_all_cards_requested.emit(card_id)

    def _on_session_double_clicked(self, item):
        session_id = item.data(Qt.UserRole)
        pass

    def _delete_note_by_id(self, note_id: int):
        note = self._topic_controller.get_note_by_id(note_id)
        if not note:
            return

        reply = SilentMessageBox.question(
            self, "Подтверждение удаления",
            f"Удалить запись «{note.title}»?"
        )

        if reply == SilentMessageBox.Yes:
            from core.di.container import container
            if container.note_controller.delete_note(note_id):
                self._load_notes(self._current_topic_id)
                SilentMessageBox.information(self, "Успех", "Запись удалена")