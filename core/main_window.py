# core/main_window.py
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QListWidget, QListWidgetItem, QStackedWidget, QLabel,
    QPushButton, QFrame, QApplication
)
from PySide6.QtCore import Qt, QSize, QTimer, Signal
from PySide6.QtGui import QFont, QKeySequence, QShortcut

from core.navigation import Navigation, NavSection

from .di.container import container
from .navigation import NavSection, Navigation
from .event_bus import event_bus

# Импортируем все вьюхи
from modules.dashboard.view import DashboardView
from modules.topics.tree_view import TopicsView
from modules.topics.topic_view import TopicView
from modules.tasks.global_view import GlobalTasksView
from modules.tasks.calendar_view import CalendarView
from modules.flashcards.global_view import GlobalCardsView
from modules.flashcards.review_view import ReviewSessionView
from modules.sessions.setup_view import FocusSetupView
from modules.sessions.active_view import FocusActiveView
from modules.sessions.history_view import SessionsView
from modules.analytics.view import AnalyticsView
from modules.search.view import SearchView
from modules.settings.view import SettingsView
from onboarding.wizard import OnboardingWizard


class MainWindow(QMainWindow):
    """
    Главное окно приложения.
    Содержит левый сайдбар с навигацией и центральную область с контентом.
    """

    def __init__(self):
        super().__init__()
        self._setup_ui()
        self._setup_navigation()
        self._setup_hotkeys()
        self._connect_signals()

        # Проверяем, нужно ли показать онбординг
        self._check_onboarding()

    def _setup_ui(self):
        """Настраивает интерфейс главного окна"""
        self.setWindowTitle("HFlow — Harmony & Flow Notes")
        self.setMinimumSize(1000, 700)
        self.resize(1200, 800)

        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ========== Левый сайдбар ==========
        self.sidebar = QListWidget()
        self.sidebar.setFixedWidth(180)
        self.sidebar.setFrameShape(QFrame.NoFrame)
        self.sidebar.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.sidebar.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.sidebar.setSpacing(2)

        # Пункты меню
        self.menu_items = {
            NavSection.DASHBOARD: self._add_menu_item("🏠", "Главная"),
            NavSection.TOPICS: self._add_menu_item("📚", "Темы"),
            NavSection.FOCUS: self._add_menu_item("⏱️", "Фокус"),
            NavSection.TASKS: self._add_menu_item("✅", "Задачи"),
            NavSection.CALENDAR: self._add_menu_item("📅", "Календарь"),
            NavSection.FLASHCARDS: self._add_menu_item("🃏", "Карточки"),
            NavSection.ANALYTICS: self._add_menu_item("📊", "Аналитика"),
            NavSection.SEARCH: self._add_menu_item("🔍", "Поиск"),
            NavSection.SETTINGS: self._add_menu_item("⚙️", "Настройки"),
        }

        main_layout.addWidget(self.sidebar)

        # ========== Центральная область ==========
        self.content_stack = QStackedWidget()
        self.content_stack.setFrameShape(QFrame.NoFrame)

        # Создаём все вьюхи
        self._create_views()

        main_layout.addWidget(self.content_stack, 1)

        # Статус бар
        self.statusBar().showMessage("Готов к работе")

    def _add_menu_item(self, icon: str, text: str) -> QListWidgetItem:
        """Добавляет пункт меню в сайдбар"""
        item = QListWidgetItem(f"{icon}  {text}")
        item.setSizeHint(QSize(0, 40))
        self.sidebar.addItem(item)
        return item

    def _create_views(self):
        """Создаёт все вьюхи модулей"""
        c = container

        # Dashboard
        self.dashboard_view = DashboardView(c.dashboard_controller)
        self.content_stack.addWidget(self.dashboard_view)

        # Topics (дерево)
        self.topics_view = TopicsView(c.topic_controller)
        self.content_stack.addWidget(self.topics_view)

        # Topic (экран темы)
        self.topic_view = TopicView(c.topic_controller, c.topic_analytics_controller)
        self.content_stack.addWidget(self.topic_view)

        # Focus Setup
        self.focus_setup_view = FocusSetupView(
            c.topic_controller, c.music_controller, c.settings_controller
        )
        self.content_stack.addWidget(self.focus_setup_view)

        # Focus Active
        self.focus_active_view = FocusActiveView(
            c.session_controller, c.music_controller
        )
        self.content_stack.addWidget(self.focus_active_view)

        # Tasks (глобальные)
        self.tasks_view = GlobalTasksView(c.task_controller)
        self.content_stack.addWidget(self.tasks_view)

        # Calendar
        self.calendar_view = CalendarView(c.calendar_controller)
        self.content_stack.addWidget(self.calendar_view)

        # Flashcards (глобальные)
        self.flashcards_view = GlobalCardsView(c.flashcard_controller)
        self.content_stack.addWidget(self.flashcards_view)

        # Analytics
        self.analytics_view = AnalyticsView(c.analytics_controller, c.topic_controller)
        self.content_stack.addWidget(self.analytics_view)

        # Search
        self.search_view = SearchView(c.search_controller)
        self.content_stack.addWidget(self.search_view)

        # Settings
        self.settings_view = SettingsView(c.settings_controller)
        self.content_stack.addWidget(self.settings_view)

        # Sessions History (дополнительно)
        self.sessions_history_view = SessionsView(c.session_controller)
        self.content_stack.addWidget(self.sessions_history_view)

        # Review Session
        self.review_session_view = ReviewSessionView(c.review_controller)
        self.content_stack.addWidget(self.review_session_view)

    def _setup_navigation(self):
        from core.navigation import Navigation  # <-- добавить эту строку в начало метода
        self.navigation = Navigation()
        self.navigation.section_changed.connect(self._on_navigation_changed)
        self.sidebar.currentRowChanged.connect(self._on_sidebar_clicked)
        self.sidebar.setCurrentRow(0)
        self.navigation.navigate_to(NavSection.DASHBOARD)

    def _on_sidebar_clicked(self, row: int):
        """Обработчик клика по сайдбару"""
        section_map = {
            0: NavSection.DASHBOARD,
            1: NavSection.TOPICS,
            2: NavSection.FOCUS,
            3: NavSection.TASKS,
            4: NavSection.CALENDAR,
            5: NavSection.FLASHCARDS,
            6: NavSection.ANALYTICS,
            7: NavSection.SEARCH,
            8: NavSection.SETTINGS,
        }
        section = section_map.get(row)
        if section:
            self.navigation.navigate_to(section)

    def _on_navigation_changed(self, section: NavSection, data=None):
        """Обработчик смены секции"""
        self.statusBar().showMessage(f"Переход в раздел: {section.value}")

        # Обновляем выделение в сайдбаре
        section_to_row = {
            NavSection.DASHBOARD: 0,
            NavSection.TOPICS: 1,
            NavSection.FOCUS: 2,
            NavSection.TASKS: 3,
            NavSection.CALENDAR: 4,
            NavSection.FLASHCARDS: 5,
            NavSection.ANALYTICS: 6,
            NavSection.SEARCH: 7,
            NavSection.SETTINGS: 8,
        }
        row = section_to_row.get(section)
        if row is not None:
            self.sidebar.blockSignals(True)
            self.sidebar.setCurrentRow(row)
            self.sidebar.blockSignals(False)

        # Показываем нужную вьюху
        view = self._get_view_for_section(section)
        if view:
            self.content_stack.setCurrentWidget(view)

            # Передаём дополнительные данные если есть
            self._handle_navigation_data(section, data)

    def _get_view_for_section(self, section: NavSection):
        """Возвращает вьюху для секции"""
        views = {
            NavSection.DASHBOARD: self.dashboard_view,
            NavSection.TOPICS: self.topics_view,
            NavSection.FOCUS: self.focus_setup_view,
            NavSection.TASKS: self.tasks_view,
            NavSection.CALENDAR: self.calendar_view,
            NavSection.FLASHCARDS: self.flashcards_view,
            NavSection.ANALYTICS: self.analytics_view,
            NavSection.SEARCH: self.search_view,
            NavSection.SETTINGS: self.settings_view,
        }
        return views.get(section)

    def _handle_navigation_data(self, section: NavSection, data=None):
        """Обрабатывает дополнительные данные навигации"""
        if data is None:
            return

        if section == NavSection.TOPICS and isinstance(data, int):
            # Открываем конкретную тему
            self.topic_view.set_topic(data)
            # Переключаем на экран темы (временно добавляем в стек)
            if self.content_stack.indexOf(self.topic_view) == -1:
                self.content_stack.addWidget(self.topic_view)
            self.content_stack.setCurrentWidget(self.topic_view)

        elif section == NavSection.FLASHCARDS and isinstance(data, dict):
            # Запускаем сессию повторения
            if data.get('action') == 'review':
                topic_id = data.get('topic_id')
                if topic_id:
                    self.review_session_view.start_session(topic_id)
                    self.content_stack.setCurrentWidget(self.review_session_view)

        elif section == NavSection.FOCUS and isinstance(data, dict):
            # Запускаем активную сессию
            if data.get('action') == 'start':
                topic_id = data.get('topic_id')
                topic_name = data.get('topic_name')
                interval = data.get('interval', 15)
                self.focus_active_view.start(topic_id, topic_name, interval)
                self.content_stack.setCurrentWidget(self.focus_active_view)

    def _setup_hotkeys(self):
        """Настраивает глобальные горячие клавиши"""
        # Ctrl+F - поиск
        search_shortcut = QShortcut(QKeySequence("Ctrl+F"), self)
        search_shortcut.activated.connect(self._on_search_hotkey)

        # Ctrl+N - новая заметка (если есть активная тема)
        new_note_shortcut = QShortcut(QKeySequence("Ctrl+N"), self)
        new_note_shortcut.activated.connect(self._on_new_note_hotkey)

        # Ctrl+T - новая задача
        new_task_shortcut = QShortcut(QKeySequence("Ctrl+T"), self)
        new_task_shortcut.activated.connect(self._on_new_task_hotkey)

        # Ctrl+Shift+S - начать сессию
        start_session_shortcut = QShortcut(QKeySequence("Ctrl+Shift+S"), self)
        start_session_shortcut.activated.connect(self._on_start_session_hotkey)

        # F5 - обновить текущий вид
        refresh_shortcut = QShortcut(QKeySequence("F5"), self)
        refresh_shortcut.activated.connect(self._on_refresh_hotkey)

    def _connect_signals(self):
        """Подключает сигналы от вьюх к навигации"""
        c = container

        # Topic view signals
        self.topic_view.create_note_requested.connect(
            lambda topic_id: self._open_note_editor(topic_id)
        )
        self.topic_view.create_task_requested.connect(
            lambda topic_id: self._open_task_creator(topic_id)
        )
        self.topic_view.create_flashcard_requested.connect(
            lambda topic_id: self._open_flashcard_creator(topic_id)
        )
        self.topic_view.start_session_requested.connect(
            lambda topic_id: self._start_focus_session_from_topic(topic_id)
        )

        # Dashboard
        self.dashboard_view.create_topic_requested.connect(
            lambda: self.navigation.navigate_to(NavSection.TOPICS)
        )
        self.dashboard_view.open_topic_requested.connect(
            lambda topic_id: self.navigation.navigate_to(NavSection.TOPICS, topic_id)
        )
        self.dashboard_view.start_session_requested.connect(
            lambda: self.navigation.navigate_to(NavSection.FOCUS)
        )
        self.dashboard_view.open_analytics_requested.connect(
            lambda: self.navigation.navigate_to(NavSection.ANALYTICS)
        )
        self.dashboard_view.open_tasks_requested.connect(
            lambda: self.navigation.navigate_to(NavSection.TASKS)
        )

        # Topics tree
        self.topics_view.topic_selected.connect(
            lambda topic_id: self.navigation.navigate_to(NavSection.TOPICS, topic_id)
        )
        self.topics_view.topic_created.connect(
            lambda topic_id: self.navigation.navigate_to(NavSection.TOPICS, topic_id)
        )

        # Focus Setup
        self.focus_setup_view.start_session.connect(
            lambda topic_id, interval: self._start_focus_session(topic_id, interval)
        )

        # Focus Active
        self.focus_active_view.session_ended.connect(self._on_session_ended)
        self.focus_active_view.back_to_dashboard.connect(
            lambda: self.navigation.navigate_to(NavSection.DASHBOARD)
        )

        # Global Tasks
        self.tasks_view.task_updated.connect(self._refresh_dashboard)

        # Calendar
        self.calendar_view.task_clicked.connect(self._open_task)

        # Flashcards
        self.flashcards_view.card_selected.connect(self._open_flashcard)

        # Search
        self.search_view.topic_selected.connect(
            lambda topic_id: self.navigation.navigate_to(NavSection.TOPICS, topic_id)
        )
        self.search_view.note_selected.connect(self._open_note)
        self.search_view.task_selected.connect(self._open_task)
        self.search_view.flashcard_selected.connect(self._open_flashcard)

        # Settings
        self.settings_view.theme_changed.connect(self._on_theme_changed)
        self.settings_view.settings_changed.connect(self._on_settings_changed)

        # ===== Кнопка назад =====
        self.topic_view.back_requested.connect(
            lambda: self.navigation.navigate_to(NavSection.TOPICS)
        )

        # Event bus
        event_bus.topic_created.connect(lambda tid: self._refresh_topics())
        event_bus.topic_deleted.connect(lambda tid: self._refresh_topics())
        event_bus.task_created.connect(lambda tid: self._refresh_dashboard())
        event_bus.task_completed.connect(lambda tid: self._refresh_dashboard())

    def _start_focus_session(self, topic_id: int, interval: int):
        """Запускает фокус-сессию"""
        topic = container.topic_controller.get_topic(topic_id)
        if topic:
            self.navigation.navigate_to(NavSection.FOCUS, {
                'action': 'start',
                'topic_id': topic_id,
                'topic_name': topic.name,
                'interval': interval
            })

    def _on_session_ended(self, duration_minutes: int):
        """Обработчик завершения сессии"""
        self.statusBar().showMessage(f"Сессия завершена! Длительность: {duration_minutes} минут")
        self.navigation.navigate_to(NavSection.DASHBOARD)

        # Обновляем аналитику
        self.analytics_view.refresh()
        self.dashboard_view.refresh()

    def _on_search_hotkey(self):
        """Глобальный поиск по Ctrl+F"""
        self.navigation.navigate_to(NavSection.SEARCH)
        self.search_view.search_bar.set_focus()

    def _on_new_note_hotkey(self):
        """Новая заметка по Ctrl+N"""
        # TODO: открыть редактор заметок для текущей темы
        pass

    def _on_new_task_hotkey(self):
        """Новая задача по Ctrl+T"""
        self.navigation.navigate_to(NavSection.TASKS)
        self.tasks_view._on_new_task()

    def _on_start_session_hotkey(self):
        """Начать сессию по Ctrl+Shift+S"""
        self.navigation.navigate_to(NavSection.FOCUS)

    def _on_refresh_hotkey(self):
        """Обновить текущий вид по F5"""
        current = self.content_stack.currentWidget()
        if hasattr(current, 'refresh'):
            current.refresh()
        self.statusBar().showMessage("Обновлено", 2000)

    def _on_theme_changed(self, theme: str):
        """Обработчик смены темы"""
        from modules.settings.themes import ThemeManager
        theme_manager = ThemeManager()
        style = theme_manager.get_style(theme)
        QApplication.instance().setStyleSheet(style)

    def _on_settings_changed(self):
        """Обработчик изменения настроек"""
        # Обновляем уведомления
        enabled = container.settings_controller.get_notifications_enabled()
        container.notification_service.set_enabled(enabled)

    def _refresh_dashboard(self):
        """Обновляет дашборд"""
        self.dashboard_view.refresh()

    def _refresh_topics(self):
        """Обновляет дерево тем"""
        self.topics_view.refresh()

    def _open_note(self, note_id: int):
        """Открывает заметку для редактирования"""
        # TODO: перейти к редактору заметок
        pass

    def _open_task(self, task_id: int):
        """Открывает задачу"""
        self.navigation.navigate_to(NavSection.TASKS)
        # TODO: выделить задачу в списке
        pass

    def _open_flashcard(self, card_id: int):
        """Открывает карточку"""
        self.navigation.navigate_to(NavSection.FLASHCARDS)
        # TODO: выделить карточку в списке
        pass

    def _check_onboarding(self):
        """Проверяет, нужно ли показать онбординг при первом запуске"""
        # Проверяем наличие данных
        topics = container.topic_repo.get_all()
        user_name = container.settings_controller.get_user_name()

        # Если нет тем и имя по умолчанию (или пустое) — запускаем онбординг
        if len(topics) == 0 and user_name == "Пользователь":
            self._show_onboarding()

    def _show_onboarding(self):
        """Показывает мастер первого запуска"""
        wizard = OnboardingWizard(
            container.topic_controller,
            container.note_controller,
            container.settings_controller
        )

        if wizard.exec():
            # Онбординг завершён, обновляем дашборд
            self._refresh_topics()
            self.dashboard_view.refresh()
            self.statusBar().showMessage("Добро пожаловать в HFlow!", 3000)

    def closeEvent(self, event):
        """Обработчик закрытия окна"""
        # Корректно завершаем приложение
        app = QApplication.instance()
        from core import HFlowApp
        if isinstance(app, HFlowApp):
            app.shutdown()
        event.accept()

    def _open_note_editor(self, topic_id: int):
        from modules.notes.editor import NoteEditorView
        self.note_editor = NoteEditorView(container.note_controller)
        self.note_editor.create_new_note(topic_id)
        self.content_stack.addWidget(self.note_editor)
        self.content_stack.setCurrentWidget(self.note_editor)

    def _open_task_creator(self, topic_id: int):
        from modules.tasks.dialogs import TaskDialog
        dialog = TaskDialog(self, topic_id=topic_id)
        if dialog.exec():
            self._refresh_topics()

    def _open_flashcard_creator(self, topic_id: int):
        from modules.flashcards.dialogs import CardTypeDialog
        dialog = CardTypeDialog(self)
        if dialog.exec():
            data = dialog.get_card_data()
            if data['type'] == 'free':
                container.flashcard_controller.create_free_card(topic_id, data['content'])
            else:
                container.flashcard_controller.create_qa_card(topic_id, data['question'], data['answer'])
            self._refresh_dashboard()

    def _start_focus_session_from_topic(self, topic_id: int):
        self.navigation.navigate_to(NavSection.FOCUS, {
            'action': 'start',
            'topic_id': topic_id,
            'topic_name': container.topic_controller.get_topic(topic_id).name,
            'interval': 15
        })