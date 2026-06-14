# modules/topics/topic_view.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QLabel,
    QPushButton, QScrollArea, QFrame, QMessageBox, QTextEdit, QListWidget
)
from PySide6.QtCore import Signal
from PySide6.QtCore import Qt
from .controller import TopicController
from .analytics_controller import TopicAnalyticsController


class TopicView(QWidget):
    """
    Экран темы с вкладками:
    - Обзор
    - Заметки
    - Задачи
    - Карточки
    - Сессии
    - Аналитика
    """

    # Сигналы для навигации к другим модулям
    create_note_requested = Signal(int)  # topic_id
    create_task_requested = Signal(int)  # topic_id
    create_flashcard_requested = Signal(int)  # topic_id
    start_session_requested = Signal(int)  # topic_id
    show_all_tasks_requested = Signal(int)  # topic_id
    show_all_notes_requested = Signal(int)  # topic_id
    show_all_cards_requested = Signal(int)  # topic_id

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
        self._setup_ui()

    def _setup_ui(self):
        """Настраивает интерфейс"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Верхняя панель с названием темы
        self.header_widget = QWidget()
        header_layout = QHBoxLayout(self.header_widget)
        header_layout.setContentsMargins(15, 10, 15, 10)

        self.topic_name_label = QLabel()
        self.topic_name_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        header_layout.addWidget(self.topic_name_label)

        header_layout.addStretch()

        self.path_label = QLabel()
        self.path_label.setStyleSheet("color: #888888;")
        header_layout.addWidget(self.path_label)

        layout.addWidget(self.header_widget)

        # Вкладки
        self.tab_widget = QTabWidget()

        # Вкладка "Обзор"
        self.overview_tab = self._create_overview_tab()
        self.tab_widget.addTab(self.overview_tab, "📊 Обзор")

        # Вкладка "Заметки"
        self.notes_tab = QWidget()
        notes_layout = QVBoxLayout(self.notes_tab)
        self.notes_list = QListWidget()
        notes_layout.addWidget(self.notes_list)
        self.create_note_btn = QPushButton("➕ Создать заметку")
        notes_layout.addWidget(self.create_note_btn)
        self.tab_widget.addTab(self.notes_tab, "📝 Заметки")

        # Вкладка "Задачи"
        self.tasks_tab = QWidget()
        tasks_layout = QVBoxLayout(self.tasks_tab)
        self.tasks_list = QListWidget()
        tasks_layout.addWidget(self.tasks_list)
        self.create_task_btn = QPushButton("➕ Создать задачу")
        tasks_layout.addWidget(self.create_task_btn)
        self.tab_widget.addTab(self.tasks_tab, "✅ Задачи")

        # Вкладка "Карточки"
        self.cards_tab = QWidget()
        cards_layout = QVBoxLayout(self.cards_tab)
        self.cards_list = QListWidget()
        cards_layout.addWidget(self.cards_list)
        self.create_card_btn = QPushButton("➕ Создать карточку")
        cards_layout.addWidget(self.create_card_btn)
        self.tab_widget.addTab(self.cards_tab, "🃏 Карточки")

        # Вкладка "Сессии"
        self.sessions_tab = QWidget()
        sessions_layout = QVBoxLayout(self.sessions_tab)
        self.sessions_list = QListWidget()
        sessions_layout.addWidget(self.sessions_list)
        self.start_session_btn = QPushButton("▶ Начать сессию")
        sessions_layout.addWidget(self.start_session_btn)
        self.tab_widget.addTab(self.sessions_tab, "⏱️ Сессии")

        # Вкладка "Аналитика"
        self.analytics_tab = QWidget()
        analytics_layout = QVBoxLayout(self.analytics_tab)
        self.analytics_text = QTextEdit()
        self.analytics_text.setReadOnly(True)
        analytics_layout.addWidget(self.analytics_text)
        self.tab_widget.addTab(self.analytics_tab, "📈 Аналитика")

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

    def _create_overview_tab(self) -> QWidget:
        """Создаёт вкладку обзора"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)

        # Скролл-область
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setSpacing(20)

        # Карточки статистики
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(15)

        self.sessions_card = self._create_stat_card("⏱️ Сессии", "0")
        self.time_card = self._create_stat_card("⏰ Время", "0 ч")
        self.conc_card = self._create_stat_card("🧠 Концентрация", "0%")
        self.energy_card = self._create_stat_card("⚡ Энергия", "0%")
        self.interest_card = self._create_stat_card("❤️ Интерес", "0%")

        stats_layout.addWidget(self.sessions_card)
        stats_layout.addWidget(self.time_card)
        stats_layout.addWidget(self.conc_card)
        stats_layout.addWidget(self.energy_card)
        stats_layout.addStretch()

        content_layout.addLayout(stats_layout)

        # Прогресс задач
        tasks_progress_widget = QFrame()
        tasks_progress_widget.setFrameShape(QFrame.StyledPanel)
        tasks_progress_layout = QVBoxLayout(tasks_progress_widget)

        tasks_title = QLabel("✅ Прогресс задач")
        tasks_title.setStyleSheet("font-weight: bold;")
        tasks_progress_layout.addWidget(tasks_title)

        self.tasks_progress_label = QLabel("0 / 0 выполнено")
        tasks_progress_layout.addWidget(self.tasks_progress_label)

        content_layout.addWidget(tasks_progress_widget)

        # Количество материалов
        materials_widget = QFrame()
        materials_widget.setFrameShape(QFrame.StyledPanel)
        materials_layout = QHBoxLayout(materials_widget)

        self.notes_count_label = QLabel("📝 Заметок: 0")
        self.cards_count_label = QLabel("🃏 Карточек: 0")

        materials_layout.addWidget(self.notes_count_label)
        materials_layout.addWidget(self.cards_count_label)
        materials_layout.addStretch()

        content_layout.addWidget(materials_widget)

        # Кнопки действий
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(15)

        start_btn = QPushButton("▶ Начать сессию")
        start_btn.clicked.connect(
            lambda: self.start_session_requested.emit(self._current_topic_id)
        )
        actions_layout.addWidget(start_btn)

        note_btn = QPushButton("📝 Новая заметка")
        note_btn.clicked.connect(
            lambda: self.create_note_requested.emit(self._current_topic_id)
        )
        actions_layout.addWidget(note_btn)

        task_btn = QPushButton("✅ Новая задача")
        task_btn.clicked.connect(
            lambda: self.create_task_requested.emit(self._current_topic_id)
        )
        actions_layout.addWidget(task_btn)

        card_btn = QPushButton("🃏 Новая карточка")
        card_btn.clicked.connect(
            lambda: self.create_flashcard_requested.emit(self._current_topic_id)
        )
        actions_layout.addWidget(card_btn)

        actions_layout.addStretch()
        content_layout.addLayout(actions_layout)

        content_layout.addStretch()
        scroll.setWidget(content)
        layout.addWidget(scroll)

        return widget

    def _create_stat_card(self, title: str, value: str) -> QFrame:
        """Создаёт карточку статистики"""
        card = QFrame()
        card.setFrameShape(QFrame.StyledPanel)
        card.setFixedWidth(120)

        layout = QVBoxLayout(card)
        layout.setAlignment(Qt.AlignCenter)

        title_label = QLabel(title)
        title_label.setStyleSheet("color: #888888; font-size: 11px;")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        value_label = QLabel(value)
        value_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        value_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(value_label)

        return card

    def set_topic(self, topic_id: int):
        """
        Устанавливает текущую тему и загружает её данные.
        """
        self._current_topic_id = topic_id

        topic = self._topic_controller.get_topic(topic_id)
        if not topic:
            self.topic_name_label.setText("Тема не найдена")
            return

        self.topic_name_label.setText(topic.display_name)

        # Показываем путь
        path = self._topic_controller.get_path_string(topic_id)
        self.path_label.setText(path)

        # Загружаем статистику
        self._load_stats(topic_id)

    def _load_stats(self, topic_id: int):
        stats = self._analytics_controller.get_topic_stats(topic_id)

        self._update_stat_card(self.sessions_card, str(stats['session_count']))
        self._update_stat_card(self.time_card, f"{stats['total_hours']} ч")

        # Конвертируем 0-5 в 0-100 для отображения
        conc_percent = int(stats.get('avg_concentration', 0) * 20)
        energy_percent = int(stats.get('avg_energy', 0) * 20)
        interest_percent = int(stats.get('avg_interest', 0) * 20)

        self._update_stat_card(self.conc_card, f"{conc_percent}%")
        self._update_stat_card(self.energy_card, f"{energy_percent}%")
        self._update_stat_card(self.interest_card, f"{interest_percent}%")  # <-- ДОБАВИТЬ

        self.tasks_progress_label.setText(
            f"{stats['completed_tasks']} / {stats['task_count']} выполнено ({stats['completion_rate']}%)"
        )
        self.notes_count_label.setText(f"📝 Заметок: {stats['note_count']}")
        self.cards_count_label.setText(f"🃏 Карточек: {stats['flashcard_count']}")

    def _update_stat_card(self, card: QFrame, new_value: str):
        """Обновляет значение в карточке статистики"""
        # Ищем label со значением (второй label в card)
        labels = card.findChildren(QLabel)
        if len(labels) >= 2:
            labels[1].setText(new_value)

    def refresh(self):
        """Обновляет текущую тему"""
        if self._current_topic_id:
            self._load_stats(self._current_topic_id)

    def get_current_topic_id(self) -> int:
        """Возвращает ID текущей темы"""
        return self._current_topic_id