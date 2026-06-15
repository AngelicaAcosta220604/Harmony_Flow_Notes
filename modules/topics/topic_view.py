# modules/topics/topic_view.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QLabel,
    QPushButton, QScrollArea, QFrame, QMessageBox, QTextEdit, QListWidget, QListWidgetItem, QCheckBox
)
from PySide6.QtCore import Signal
from PySide6.QtCore import Qt

from widgets import SilentMessageBox
from .controller import TopicController
from .analytics_controller import TopicAnalyticsController


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

        self.title_label = QLabel(f"📝 {title}")
        self.title_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(self.title_label, 1)

        self.date_label = QLabel(date_str)
        self.date_label.setStyleSheet("color: #888888; font-size: 10px;")
        layout.addWidget(self.date_label)

        self.open_btn = QPushButton("📖")
        self.open_btn.setFixedSize(30, 30)
        self.open_btn.setToolTip("Открыть запись")
        layout.addWidget(self.open_btn)

        self.edit_btn = QPushButton("✏️")
        self.edit_btn.setFixedSize(30, 30)
        self.edit_btn.setToolTip("Редактировать запись")
        layout.addWidget(self.edit_btn)

        self.delete_btn = QPushButton("🗑️")
        self.delete_btn.setFixedSize(30, 30)
        self.delete_btn.setToolTip("Удалить запись")
        layout.addWidget(self.delete_btn)

        self.setStyleSheet("""
            NoteListItemWidget {
                border-bottom: 1px solid #ddd;
                background-color: transparent;
            }
            NoteListItemWidget:hover {
                background-color: #f0f0f0;
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
            self.title_label.setStyleSheet("text-decoration: line-through; color: #888;")
        elif is_overdue:
            self.title_label.setStyleSheet("color: #f44336; font-weight: bold;")
        layout.addWidget(self.title_label, 1)

        # Дедлайн
        self.deadline_label = QLabel(deadline)
        self.deadline_label.setStyleSheet("color: #888; font-size: 10px;")
        layout.addWidget(self.deadline_label)

        # Кнопки
        self.edit_btn = QPushButton("✏️")
        self.edit_btn.setFixedSize(30, 30)
        self.edit_btn.clicked.connect(lambda: self.edit_clicked.emit(self.task_id))
        layout.addWidget(self.edit_btn)

        self.delete_btn = QPushButton("🗑️")
        self.delete_btn.setFixedSize(30, 30)
        self.delete_btn.clicked.connect(lambda: self.delete_clicked.emit(self.task_id))
        layout.addWidget(self.delete_btn)

        self.setFixedHeight(50)
        self.setStyleSheet("""
            TaskListItemWidget {
                border-bottom: 1px solid #ddd;
                background-color: transparent;
            }
            TaskListItemWidget:hover {
                background-color: #f0f0f0;
            }
            QPushButton {
                border: none;
                background-color: transparent;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
                border-radius: 4px;
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
        self._setup_ui()

    def _setup_ui(self):
        """Настраивает интерфейс"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Верхняя панель
        self.header_widget = QWidget()
        header_layout = QHBoxLayout(self.header_widget)
        header_layout.setContentsMargins(15, 10, 15, 10)

        self.back_btn = QPushButton("← Назад")
        self.back_btn.setFixedWidth(80)
        self.back_btn.setToolTip("Вернуться к списку тем")
        header_layout.addWidget(self.back_btn)

        self.topic_name_label = QLabel()
        self.topic_name_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        header_layout.addWidget(self.topic_name_label, 1)

        self.path_label = QLabel()
        self.path_label.setStyleSheet("color: #888888;")
        header_layout.addWidget(self.path_label)

        layout.addWidget(self.header_widget)

        # Вкладки
        self.tab_widget = QTabWidget()

        # Вкладка "Обзор"
        self.overview_tab = self._create_overview_tab()
        self.tab_widget.addTab(self.overview_tab, "📊 Обзор")

        # Вкладка "Записи"
        self.notes_tab = QWidget()
        notes_layout = QVBoxLayout(self.notes_tab)
        self.notes_list = QListWidget()
        notes_layout.addWidget(self.notes_list)
        self.create_note_btn = QPushButton("➕ Создать запись")
        notes_layout.addWidget(self.create_note_btn)
        self.tab_widget.addTab(self.notes_tab, "📝 Записи")

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

        self.back_btn.clicked.connect(self.back_requested.emit)

        self.notes_list.itemDoubleClicked.connect(self._on_note_double_clicked)
        self.tasks_list.itemDoubleClicked.connect(self._on_task_double_clicked)
        self.cards_list.itemDoubleClicked.connect(self._on_card_double_clicked)
        self.sessions_list.itemDoubleClicked.connect(self._on_session_double_clicked)

    def _create_overview_tab(self) -> QWidget:
        """Создаёт вкладку обзора"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)

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
        start_btn.clicked.connect(lambda: self.start_session_requested.emit(self._current_topic_id))
        actions_layout.addWidget(start_btn)

        note_btn = QPushButton("📝 Новая запись")
        note_btn.clicked.connect(lambda: self.create_note_requested.emit(self._current_topic_id))
        actions_layout.addWidget(note_btn)

        task_btn = QPushButton("✅ Новая задача")
        task_btn.clicked.connect(lambda: self.create_task_requested.emit(self._current_topic_id))
        actions_layout.addWidget(task_btn)

        card_btn = QPushButton("🃏 Новая карточка")
        card_btn.clicked.connect(lambda: self.create_flashcard_requested.emit(self._current_topic_id))
        actions_layout.addWidget(card_btn)

        actions_layout.addStretch()
        content_layout.addLayout(actions_layout)
        content_layout.addStretch()

        scroll.setWidget(content)
        layout.addWidget(scroll)

        return widget

    def _create_stat_card(self, title: str, value: str) -> QFrame:
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
            self.notes_list.addItem("📭 Нет записей. Создайте первую запись!")
            return

        for note in notes:
            title = getattr(note, 'title', 'Без названия')
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
            self.tasks_list.addItem("✅ Нет задач. Создайте первую задачу!")
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
            self.cards_list.addItem("🃏 Нет карточек. Создайте первую карточку!")
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
            self.sessions_list.addItem("⏱️ Нет сессий. Начните первую сессию!")
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
        <h3>📊 Аналитика темы</h3>
        <b>⏱️ Сессии:</b> {stats['session_count']}<br>
        <b>⏰ Общее время:</b> {stats['total_hours']} ч<br>
        <b>🧠 Средняя концентрация:</b> {stats['avg_concentration']}/5<br>
        <b>⚡ Средняя энергия:</b> {stats['avg_energy']}/5<br>
        <b>❤️ Средний интерес:</b> {stats['avg_interest']}/5<br>
        <b>✅ Задачи:</b> {stats['completed_tasks']}/{stats['task_count']} выполнено<br>
        <b>📝 Заметки:</b> {stats['note_count']}<br>
        <b>🃏 Карточки:</b> {stats['flashcard_count']}<br>
        """
        self.analytics_text.setHtml(text)

    def _load_stats(self, topic_id: int):
        stats = self._analytics_controller.get_topic_stats(topic_id)

        self._update_stat_card(self.sessions_card, str(stats['session_count']))
        self._update_stat_card(self.time_card, f"{stats['total_hours']} ч")

        conc_percent = int(stats.get('avg_concentration', 0) * 20)
        energy_percent = int(stats.get('avg_energy', 0) * 20)
        interest_percent = int(stats.get('avg_interest', 0) * 20)

        self._update_stat_card(self.conc_card, f"{conc_percent}%")
        self._update_stat_card(self.energy_card, f"{energy_percent}%")
        self._update_stat_card(self.interest_card, f"{interest_percent}%")

        self.tasks_progress_label.setText(
            f"{stats['completed_tasks']} / {stats['task_count']} выполнено ({stats['completion_rate']}%)"
        )
        self.notes_count_label.setText(f"📝 Заметок: {stats['note_count']}")
        self.cards_count_label.setText(f"🃏 Карточек: {stats['flashcard_count']}")

    def _update_stat_card(self, card: QFrame, new_value: str):
        labels = card.findChildren(QLabel)
        if len(labels) >= 2:
            labels[1].setText(new_value)

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
        # TODO: открыть аналитику сессии
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