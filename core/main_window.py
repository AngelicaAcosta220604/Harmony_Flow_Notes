# core/main_window.py
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QListWidget, QListWidgetItem, QStackedWidget, QLabel,
    QPushButton, QFrame, QApplication, QTextEdit, QDialog
)
from PySide6.QtCore import Qt, QSize, QTimer, Signal
from PySide6.QtGui import QFont, QKeySequence, QShortcut, QIcon, QPixmap
import logging

from core.navigation import Navigation, NavSection

from .di.container import container
from .event_bus import event_bus
from utils.resource_paths import get_resource_path
from widgets import SilentMessageBox

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

# Настройка логирования
logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """
    Главное окно приложения.
    Содержит левый сайдбар с навигацией и центральную область с контентом.
    """

    def __init__(self):
        super().__init__()
        try:
            self._setup_ui()
            self._setup_navigation()
            self._setup_hotkeys()
            self._connect_signals()
            self.focus_setup_view.resume_session.connect(self._resume_session_from_setup)

            # Проверяем, нужно ли показать онбординг
            self._check_onboarding()
            logger.info("MainWindow инициализирован")
        except Exception as e:
            logger.critical(f"Критическая ошибка инициализации MainWindow: {e}", exc_info=True)
            raise

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

        # ✅ ИСПРАВЛЕНО: используем get_resource_path для всех иконок
        self.menu_items = {
            NavSection.DASHBOARD: self._add_menu_item(str(get_resource_path("resources/icons/home1.png")), "Главная"),
            NavSection.TOPICS: self._add_menu_item(str(get_resource_path("resources/icons/tema1.png")), "Темы"),
            NavSection.FOCUS: self._add_menu_item(str(get_resource_path("resources/icons/session1.png")), "Фокус"),
            NavSection.TASKS: self._add_menu_item(str(get_resource_path("resources/icons/task1.png")), "Задачи"),
            NavSection.CALENDAR: self._add_menu_item(str(get_resource_path("resources/icons/calendar1.png")),
                                                     "Календарь"),
            NavSection.FLASHCARDS: self._add_menu_item(str(get_resource_path("resources/icons/flashcard1.png")),
                                                       "Карточки"),
            NavSection.ANALYTICS: self._add_menu_item(str(get_resource_path("resources/icons/analytics1.png")),
                                                      "Аналитика"),
            NavSection.SEARCH: self._add_menu_item(str(get_resource_path("resources/icons/search1.png")), "Поиск"),
            NavSection.SETTINGS: self._add_menu_item(str(get_resource_path("resources/icons/setting1.png")),
                                                     "Настройки"),
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

    def _add_menu_item(self, icon_path: str, text: str) -> QListWidgetItem:
        """Добавляет пункт меню в сайдбар с иконкой из файла"""
        try:
            widget = QWidget()
            layout = QHBoxLayout(widget)
            layout.setContentsMargins(10, 5, 10, 5)
            layout.setSpacing(12)

            icon_label = QLabel()
            # ✅ ИСПРАВЛЕНО: icon_path уже абсолютный благодаря get_resource_path
            pixmap = QPixmap(icon_path)
            if not pixmap.isNull():
                pixmap = pixmap.scaled(16, 16, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                icon_label.setPixmap(pixmap)
                icon_label.setProperty("icon_path", icon_path)
            else:
                logger.warning(f"Не удалось загрузить иконку: {icon_path}")
                icon_label.setText("◉")
                icon_label.setStyleSheet("font-size: 18px;")

            icon_label.setStyleSheet("background-color: transparent;")

            text_label = QLabel(text)
            text_label.setStyleSheet("font-size: 14px; background-color: transparent;")

            layout.addWidget(icon_label)
            layout.addWidget(text_label)
            layout.addStretch()

            widget.setStyleSheet("background-color: transparent;")

            item = QListWidgetItem()
            item.setSizeHint(QSize(0, 45))
            self.sidebar.addItem(item)
            self.sidebar.setItemWidget(item, widget)
            return item
        except Exception as e:
            logger.error(f"Ошибка создания пункта меню '{text}': {e}", exc_info=True)
            # Возвращаем пустой item чтобы не сломать навигацию
            return QListWidgetItem(text)

    def _create_new_note(self, topic_id: int):
        """Создаёт новую заметку в теме"""
        try:
            from modules.notes.editor import NoteEditorView

            # Удаляем старый редактор, если есть
            if hasattr(self, '_current_editor') and self._current_editor:
                self.content_stack.removeWidget(self._current_editor)
                self._current_editor.deleteLater()

            self._current_editor = NoteEditorView(container.note_controller)

            # ✅ Создаём новую заметку с topic_id
            self._current_editor.create_new_note(topic_id)
            logger.debug(f"Создание новой заметки для темы {topic_id}")

            # Подключаем кнопку "Назад"
            self._current_editor.back_btn.clicked.connect(self._close_editor)

            self.content_stack.addWidget(self._current_editor)
            self.content_stack.setCurrentWidget(self._current_editor)
        except Exception as e:
            logger.error(f"Ошибка создания новой заметки: {e}", exc_info=True)
            SilentMessageBox.warning(self, "Ошибка", f"Не удалось создать заметку: {e}")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        try:
            sidebar_width = self.sidebar.width()
            new_size = max(16, min(24, sidebar_width // 12))
            if new_size != getattr(self, '_last_icon_size', 0):
                self._last_icon_size = new_size
                self._update_menu_icons_size(new_size)
        except Exception as e:
            logger.error(f"Ошибка в resizeEvent: {e}", exc_info=True)

    def _update_menu_icons_size(self, icon_size: int):
        """Обновляет размер всех иконок в меню"""
        try:
            for i in range(self.sidebar.count()):
                item = self.sidebar.item(i)
                widget = self.sidebar.itemWidget(item)
                if widget:
                    for child in widget.children():
                        if isinstance(child, QLabel) and child.pixmap():
                            icon_path = child.property("icon_path")
                            if icon_path:
                                # ✅ ИСПРАВЛЕНО: icon_path уже абсолютный
                                pixmap = QPixmap(icon_path)
                                if not pixmap.isNull():
                                    pixmap = pixmap.scaled(icon_size, icon_size, Qt.KeepAspectRatio,
                                                           Qt.SmoothTransformation)
                                    child.setPixmap(pixmap)
                            break
        except Exception as e:
            logger.error(f"Ошибка обновления размера иконок: {e}", exc_info=True)

    def _resume_session_from_setup(self, session_id: int, topic_id: int, topic_name: str):
        """Возобновляет сессию из setup_view"""
        try:
            self.focus_active_view.resume_existing_session(session_id, topic_id, topic_name)
            self.content_stack.setCurrentWidget(self.focus_active_view)
            self.statusBar().showMessage(f"Сессия возобновлена: {topic_name}", 2000)
        except Exception as e:
            logger.error(f"Ошибка возобновления сессии: {e}", exc_info=True)

    def _create_views(self):
        """Создаёт все вьюхи модулей"""
        c = container

        try:
            # Dashboard
            self.dashboard_view = DashboardView(c.dashboard_controller)
            self.content_stack.addWidget(self.dashboard_view)
            logger.debug("DashboardView создан")

            # Topics (дерево)
            self.topics_view = TopicsView(c.topic_controller)
            self.content_stack.addWidget(self.topics_view)
            logger.debug("TopicsView создан")

            # ✅ ДОБАВЬ ЭТО: Topic (экран конкретной темы)
            self.topic_view = TopicView(c.topic_controller, c.topic_analytics_controller)
            # НЕ добавляем в content_stack сразу — добавим лениво в _handle_navigation_data()
            logger.debug("TopicView создан")

            # Focus Setup
            self.focus_setup_view = FocusSetupView(
                c.topic_controller, c.music_controller, c.settings_controller
            )
            self.content_stack.addWidget(self.focus_setup_view)
            logger.debug("FocusSetupView создан")

            # Focus Active
            self.focus_active_view = FocusActiveView(
                c.session_controller, c.music_controller
            )
            self.content_stack.addWidget(self.focus_active_view)
            logger.debug("FocusActiveView создан")

            # Tasks (глобальные)
            self.tasks_view = GlobalTasksView(c.task_controller)
            self.content_stack.addWidget(self.tasks_view)
            logger.debug("GlobalTasksView создан")

            # Calendar
            self.calendar_view = CalendarView(c.calendar_controller)
            self.content_stack.addWidget(self.calendar_view)
            logger.debug("CalendarView создан")

            # Flashcards (глобальные)
            self.flashcards_view = GlobalCardsView(c.flashcard_controller)
            self.content_stack.addWidget(self.flashcards_view)
            logger.debug("GlobalCardsView создан")

            # Analytics
            self.analytics_view = AnalyticsView(c.analytics_controller, c.topic_controller)
            self.content_stack.addWidget(self.analytics_view)
            logger.debug("AnalyticsView создан")

            # Search
            self.search_view = SearchView(c.search_controller)
            self.content_stack.addWidget(self.search_view)
            logger.debug("SearchView создан")

            # Settings
            self.settings_view = SettingsView(c.settings_controller)
            self.content_stack.addWidget(self.settings_view)
            logger.debug("SettingsView создан")

            # Sessions History
            self.sessions_history_view = SessionsView(c.session_controller)
            self.content_stack.addWidget(self.sessions_history_view)
            logger.debug("SessionsView создан")

            # Review Session
            self.review_session_view = ReviewSessionView(c.review_controller)
            self.content_stack.addWidget(self.review_session_view)
            logger.debug("ReviewSessionView создан")

            logger.info(f"Создано {self.content_stack.count()} view")
        except Exception as e:
            logger.critical(f"Ошибка создания view: {e}", exc_info=True)
            SilentMessageBox.warning(self, "Критическая ошибка",
                                     f"Не удалось создать компоненты интерфейса:\n{e}")

    def _setup_navigation(self):
        try:
            from core.navigation import Navigation
            self.navigation = Navigation()
            self.navigation.section_changed.connect(self._on_navigation_changed)
            self.sidebar.currentRowChanged.connect(self._on_sidebar_clicked)
            self.sidebar.setCurrentRow(0)
            self.navigation.navigate_to(NavSection.DASHBOARD)
        except Exception as e:
            logger.error(f"Ошибка настройки навигации: {e}", exc_info=True)

    def _on_sidebar_clicked(self, row: int):
        """Обработчик клика по сайдбару"""
        try:
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
                # ✅ ИСПРАВЛЕНО: проверяем, активна ли уже эта секция
                current_view = self.content_stack.currentWidget()
                target_view = self._get_view_for_section(section)

                if current_view == target_view:
                    # Если кликнули на активную вкладку — сбрасываем view
                    if hasattr(current_view, 'reset_view'):
                        current_view.reset_view()
                    elif hasattr(current_view, 'refresh'):
                        current_view.refresh()
                else:
                    self.navigation.navigate_to(section)
        except Exception as e:
            logger.error(f"Ошибка клика по сайдбару (row={row}): {e}", exc_info=True)

    def _on_navigation_changed(self, section: NavSection, data=None):
        """Обработчик смены секции"""
        try:
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
                self._handle_navigation_data(section, data)

                # 🆕 При переключении на вкладку карточек - обновляем и сворачиваем папки
                if section == NavSection.FLASHCARDS:
                    self.flashcards_view.refresh()

            logger.debug(f"Переход в секцию: {section.value}")
        except Exception as e:
            logger.error(f"Ошибка смены секции {section}: {e}", exc_info=True)

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
        try:
            if data is None:
                return

            if section == NavSection.TOPICS and isinstance(data, int):
                self.topic_view.set_topic(data)
                if self.content_stack.indexOf(self.topic_view) == -1:
                    self.content_stack.addWidget(self.topic_view)
                self.content_stack.setCurrentWidget(self.topic_view)

            elif section == NavSection.FLASHCARDS and isinstance(data, dict):
                if data.get('action') == 'review':
                    topic_id = data.get('topic_id')
                    if topic_id:
                        self.review_session_view.start_session(topic_id)
                        self.content_stack.setCurrentWidget(self.review_session_view)

            elif section == NavSection.FOCUS and isinstance(data, dict):
                if data.get('action') == 'start':
                    topic_id = data.get('topic_id')
                    topic_name = data.get('topic_name')
                    interval = data.get('interval', 15)

                    # 🆕 Проверяем, есть ли уже активная сессия
                    if not container.session_controller.is_session_active() and not container.session_controller.is_session_paused():
                        self.focus_active_view.start(topic_id, topic_name, interval)

                    self.content_stack.setCurrentWidget(self.focus_active_view)
        except Exception as e:
            logger.error(f"Ошибка обработки данных навигации: {e}", exc_info=True)

    def _setup_hotkeys(self):
        """Настраивает глобальные горячие клавиши"""
        try:
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

            logger.debug("Горячие клавиши настроены")
        except Exception as e:
            logger.error(f"Ошибка настройки горячих клавиш: {e}", exc_info=True)

    def _connect_signals(self):
        """Подключает сигналы от вьюх к навигации"""
        try:
            c = container

            # Topic view signals (записи)
            self.topic_view.create_note_requested.connect(
                lambda topic_id: self._create_new_note(topic_id)  # ✅ ИСПРАВЛЕНО: было _open_note_editor
            )
            self.topic_view.edit_note_requested.connect(self._open_note_editor)
            self.topic_view.show_all_notes_requested.connect(self._open_note_reader)

            # Topic view signals (задачи)
            self.topic_view.create_task_requested.connect(
                lambda topic_id: self._open_task_creator(topic_id)
            )
            self.topic_view.edit_task_requested.connect(self._open_task_editor)
            self.topic_view.delete_task_requested.connect(self._delete_task)
            self.topic_view.complete_task_requested.connect(self._complete_task)

            # Topic view signals (карточки)
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

            # Dashboard обновление при изменении задач
            event_bus.task_created.connect(lambda tid: self._refresh_dashboard())
            event_bus.task_completed.connect(lambda tid: self._refresh_dashboard())
            event_bus.task_deleted.connect(lambda tid: self._refresh_dashboard())

            # Dashboard обновление при изменении заметок
            event_bus.note_created.connect(lambda nid: self._refresh_dashboard())
            event_bus.note_deleted.connect(lambda nid: self._refresh_dashboard())

            # Dashboard обновление при изменении карточек
            event_bus.flashcard_created.connect(lambda cid: self._refresh_dashboard())
            event_bus.flashcard_deleted.connect(lambda cid: self._refresh_dashboard())

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
            self.calendar_view.new_task_requested.connect(self._on_new_task_from_calendar)

            # Flashcards
            self.flashcards_view.start_review_requested.connect(self._start_review_session)

            # Review Session
            self.review_session_view.session_completed.connect(self._on_review_session_completed)
            self.review_session_view.session_cancelled.connect(self._on_review_session_cancelled)

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

            # Кнопка назад
            self.topic_view.back_requested.connect(
                lambda: self.navigation.navigate_to(NavSection.TOPICS)
            )

            # Event bus
            event_bus.topic_created.connect(lambda tid: self._refresh_topics())
            event_bus.topic_deleted.connect(lambda tid: self._refresh_topics())
            event_bus.topic_updated.connect(lambda tid: self._refresh_topics())
            event_bus.note_created.connect(lambda nid: self._refresh_notes())
            event_bus.note_deleted.connect(lambda nid: self._refresh_notes())
            event_bus.note_updated.connect(lambda nid: self._refresh_notes())
            event_bus.task_created.connect(lambda tid: self._refresh_tasks())
            event_bus.task_deleted.connect(lambda tid: self._refresh_tasks())
            event_bus.task_completed.connect(lambda tid: self._refresh_tasks())
            event_bus.task_updated.connect(lambda tid: self._refresh_tasks())
            event_bus.flashcard_created.connect(lambda cid: self._refresh_flashcards())
            event_bus.flashcard_deleted.connect(lambda cid: self._refresh_flashcards())
            event_bus.task_updated.connect(lambda tid: self._refresh_dashboard())
            event_bus.note_updated.connect(lambda nid: self._refresh_dashboard())

            # Sessions History
            self.sessions_history_view.session_resumed.connect(self._resume_session_from_history)
            self.sessions_history_view.session_selected.connect(self._show_session_analytics)
            self.sessions_history_view.session_deleted.connect(self._on_session_deleted)

            # Topic view - сессии
            self.topic_view.session_resumed_in_topic.connect(self._resume_session_from_topic)
            self.topic_view.session_deleted_in_topic.connect(self._on_session_deleted_in_topic)
            self.topic_view.session_analytics_requested.connect(self._show_session_analytics_from_topic)

            logger.debug("Все сигналы подключены")
        except Exception as e:
            logger.error(f"Ошибка подключения сигналов: {e}", exc_info=True)

    def _start_focus_session(self, topic_id: int, interval: int):
        try:
            topic = container.topic_controller.get_topic(topic_id)
            if not topic:
                logger.warning(f"Тема {topic_id} не найдена для сессии")
                return

            # Проверяем на незавершённые сессии
            has_session, session_id, status, existing_topic_id = container.session_controller.has_active_or_paused_session(
                topic_id)

            if has_session:
                reply = SilentMessageBox.question(
                    self,
                    "Незавершённая сессия",
                    f"У вас есть {status} сессия для этой темы.\n\n"
                    "• Нажмите «Да» — чтобы завершить её и начать новую\n"
                    "• Нажмите «Нет» — чтобы продолжить существующую сессию",
                    SilentMessageBox.Yes | SilentMessageBox.No,
                    SilentMessageBox.No
                )

                if reply == SilentMessageBox.Yes:
                    container.session_controller.end_session()
                    self.focus_active_view.start(topic_id, topic.name, interval)
                else:
                    self.focus_active_view.resume_existing_session(session_id, topic_id, topic.name)
            else:
                self.focus_active_view.start(topic_id, topic.name, interval)

            self.content_stack.setCurrentWidget(self.focus_active_view)
        except Exception as e:
            logger.error(f"Ошибка запуска фокус-сессии: {e}", exc_info=True)
            SilentMessageBox.warning(self, "Ошибка", f"Не удалось запустить сессию: {e}")

    def _on_session_ended(self, duration_minutes: int):
        """Обработчик завершения сессии"""
        try:
            self.statusBar().showMessage(f"Сессия завершена! Длительность: {duration_minutes} минут")
            self.navigation.navigate_to(NavSection.DASHBOARD)
            self.analytics_view.refresh()
            self.dashboard_view.refresh()
            logger.info(f"Сессия завершена: {duration_minutes} минут")
        except Exception as e:
            logger.error(f"Ошибка обработки завершения сессии: {e}", exc_info=True)

    def _start_review_session(self, topic_ids: list, include_free: bool,
                              include_qa: bool, skip_reviewed: bool,
                              card_ids: list = None):
        """Запускает сессию повторения для выбранных тем/карточек"""
        try:
            self.review_session_view.start_session(
                topic_ids=topic_ids,
                mode='sequential',
                include_free=include_free,
                include_qa=include_qa,
                skip_reviewed=skip_reviewed,
                card_ids=card_ids
            )
            self.content_stack.setCurrentWidget(self.review_session_view)
        except Exception as e:
            logger.error(f"Ошибка запуска сессии повторения: {e}", exc_info=True)
            SilentMessageBox.warning(self, "Ошибка", f"Не удалось начать повторение: {e}")

    def _on_search_hotkey(self):
        """Глобальный поиск по Ctrl+F"""
        try:
            self.navigation.navigate_to(NavSection.SEARCH)
            self.search_view.search_bar.set_focus()
        except Exception as e:
            logger.error(f"Ошибка горячих клавиш поиска: {e}", exc_info=True)

    def _on_new_note_hotkey(self):
        """Новая заметка по Ctrl+N"""
        pass

    def _on_new_task_hotkey(self):
        """Новая задача по Ctrl+T"""
        try:
            self.navigation.navigate_to(NavSection.TASKS)
            self.tasks_view._on_new_task()
        except Exception as e:
            logger.error(f"Ошибка горячих клавиш новой задачи: {e}", exc_info=True)

    def _on_start_session_hotkey(self):
        """Начать сессию по Ctrl+Shift+S"""
        try:
            self.navigation.navigate_to(NavSection.FOCUS)
        except Exception as e:
            logger.error(f"Ошибка горячих клавиш сессии: {e}", exc_info=True)

    def _on_refresh_hotkey(self):
        """Обновить текущий вид по F5"""
        try:
            current = self.content_stack.currentWidget()
            if hasattr(current, 'refresh'):
                current.refresh()
            self.statusBar().showMessage("Обновлено", 2000)
        except Exception as e:
            logger.error(f"Ошибка обновления по F5: {e}", exc_info=True)

    def _on_theme_changed(self, theme: str):
        """Обработчик смены темы"""
        try:
            from modules.settings.themes import ThemeManager
            theme_manager = ThemeManager()
            style = theme_manager.get_style(theme)
            QApplication.instance().setStyleSheet(style)
            logger.info(f"Тема изменена на: {theme}")
        except Exception as e:
            logger.error(f"Ошибка смены темы: {e}", exc_info=True)

    def _on_settings_changed(self):
        """Обработчик изменения настроек"""
        try:
            enabled = container.settings_controller.get_notifications_enabled()
            container.notification_service.set_enabled(enabled)
            logger.debug(f"Уведомления {'включены' if enabled else 'отключены'}")
        except Exception as e:
            logger.error(f"Ошибка применения настроек: {e}", exc_info=True)

    def _refresh_dashboard(self):
        """Обновляет дашборд"""
        try:
            self.dashboard_view.refresh()
        except Exception as e:
            logger.error(f"Ошибка обновления дашборда: {e}", exc_info=True)

    def _refresh_topics(self):
        """Обновляет дерево тем и экран подготовки к сессии"""
        try:
            self.topics_view.refresh()
            self.focus_setup_view.refresh_topics()
        except Exception as e:
            logger.error(f"Ошибка обновления тем: {e}", exc_info=True)

    def _open_note(self, note_id: int):
        """Открывает заметку для редактирования"""
        try:
            self._open_note_editor(note_id)
        except Exception as e:
            logger.error(f"Ошибка открытия заметки {note_id}: {e}", exc_info=True)

    def _open_task(self, task_id: int):
        """Открывает задачу"""
        try:
            self.navigation.navigate_to(NavSection.TASKS)
        except Exception as e:
            logger.error(f"Ошибка открытия задачи {task_id}: {e}", exc_info=True)

    def _open_flashcard(self, card_id: int):
        """Открывает карточку"""
        try:
            self.navigation.navigate_to(NavSection.FLASHCARDS)
        except Exception as e:
            logger.error(f"Ошибка открытия карточки {card_id}: {e}", exc_info=True)

    def _check_onboarding(self):
        """Проверяет, нужно ли показать онбординг при первом запуске"""
        try:
            onboarding_completed = container.settings_controller.get_onboarding_completed()
            if not onboarding_completed:
                self._show_onboarding()
        except Exception as e:
            logger.error(f"Ошибка проверки онбординга: {e}", exc_info=True)

    def _show_onboarding(self):
        """Показывает мастер первого запуска"""
        try:
            wizard = OnboardingWizard(
                container.topic_controller,
                container.note_controller,
                container.settings_controller
            )
            if wizard.exec():
                self._refresh_topics()
                self.dashboard_view.refresh()
                self.statusBar().showMessage("Добро пожаловать в HFlow!", 3000)
        except Exception as e:
            logger.error(f"Ошибка показа онбординга: {e}", exc_info=True)

    def closeEvent(self, event):
        try:
            # Если есть активная сессия — сохраняем её состояние
            session_id = container.session_controller.get_current_session_id()
            if session_id and container.session_controller.is_session_active():
                self.focus_active_view.force_save_time()
                self.focus_active_view.force_save_state()
                container.session_controller.pause_session()

            app = QApplication.instance()
            from core import HFlowApp
            if isinstance(app, HFlowApp):
                app.shutdown()
            event.accept()
            logger.info("Приложение закрыто")
        except Exception as e:
            logger.error(f"Ошибка при закрытии: {e}", exc_info=True)
            event.accept()

    # ==================== РАБОТА С ЗАПИСЯМИ ====================

    def _open_note_reader(self, note_id: int):
        """Открыть запись в режиме чтения"""
        try:
            from core.di.container import container
            from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton
            from modules.notes.reader import NoteReader  # ✅ Импортируем NoteReader

            note = container.note_controller.get_note(note_id)
            if not note:
                logger.warning(f"Заметка {note_id} не найдена")
                return

            # Удаляем старый виджет чтения, если есть
            if hasattr(self, '_current_reader') and self._current_reader:
                self.content_stack.removeWidget(self._current_reader)
                self._current_reader.deleteLater()

            # Создаём новый виджет
            self._current_reader = QWidget()
            layout = QVBoxLayout(self._current_reader)
            layout.setContentsMargins(20, 20, 20, 20)
            layout.setSpacing(15)

            title_label = QLabel(note.title)
            title_label.setStyleSheet("font-size: 20px; font-weight: bold;")
            layout.addWidget(title_label)

            # ✅ ИСПРАВЛЕНО: используем NoteReader вместо QTextEdit
            content_reader = NoteReader()
            content_reader.display_note(note.title, note.content)
            content_reader.setStyleSheet("""
                QTextBrowser {
                    font-size: 12px;
                    background-color: #fafafa;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    padding: 10px;
                }
            """)
            layout.addWidget(content_reader, 1)

            back_btn = QPushButton("← Назад к теме")
            back_btn.setFixedWidth(150)
            back_btn.clicked.connect(self._close_reader)
            layout.addWidget(back_btn)

            self.content_stack.addWidget(self._current_reader)
            self.content_stack.setCurrentWidget(self._current_reader)

            logger.debug(f"Открыта заметка {note_id} в режиме чтения")
        except Exception as e:
            logger.error(f"Ошибка открытия читалки заметки {note_id}: {e}", exc_info=True)
            SilentMessageBox.warning(self, "Ошибка", f"Не удалось открыть заметку: {e}")

    def _close_reader(self):
        """Закрывает виджет чтения и возвращает к теме"""
        try:
            if hasattr(self, '_current_reader') and self._current_reader:
                self.content_stack.removeWidget(self._current_reader)
                self._current_reader.deleteLater()
                self._current_reader = None
            self.content_stack.setCurrentWidget(self.topic_view)
            self.topic_view.refresh()
        except Exception as e:
            logger.error(f"Ошибка закрытия читалки: {e}", exc_info=True)

    def _open_note_editor(self, note_id: int):
        """Открыть редактор для существующей заметки"""
        try:
            from modules.notes.editor import NoteEditorView

            # Удаляем старый редактор, если есть
            if hasattr(self, '_current_editor') and self._current_editor:
                self.content_stack.removeWidget(self._current_editor)
                self._current_editor.deleteLater()

            self._current_editor = NoteEditorView(container.note_controller)

            # ✅ Загружаем существующую заметку
            note = container.note_controller.get_note(note_id)
            if note:
                self._current_editor.load_note(note_id)
                logger.debug(f"Открыт редактор для заметки {note_id}")
            else:
                logger.warning(f"Заметка {note_id} не найдена")
                SilentMessageBox.warning(self, "Ошибка", "Заметка не найдена")
                return

            # Подключаем кнопку "Назад"
            self._current_editor.back_btn.clicked.connect(self._close_editor)

            self.content_stack.addWidget(self._current_editor)
            self.content_stack.setCurrentWidget(self._current_editor)
        except Exception as e:
            logger.error(f"Ошибка открытия редактора заметки {note_id}: {e}", exc_info=True)
            SilentMessageBox.warning(self, "Ошибка", f"Не удалось открыть редактор: {e}")


    def _close_editor(self):
        """Закрывает редактор и возвращает к теме"""
        try:
            if hasattr(self, '_current_editor') and self._current_editor:
                self.content_stack.removeWidget(self._current_editor)
                self._current_editor.deleteLater()
                self._current_editor = None
            self.content_stack.setCurrentWidget(self.topic_view)
            self.topic_view.refresh()
        except Exception as e:
            logger.error(f"Ошибка закрытия редактора: {e}", exc_info=True)

    # ==================== РАБОТА С ЗАДАЧАМИ ====================

    def _open_task_creator(self, topic_id: int):
        """Открывает диалог создания задачи и сохраняет её"""
        try:
            from modules.tasks.dialogs import TaskDialog

            dialog = TaskDialog(self, topic_id=topic_id)
            if dialog.exec() == QDialog.Accepted:
                task_data = dialog.get_task_data()

                task_id = container.task_controller.create_task(
                    title=task_data['title'],
                    description=task_data.get('description', ''),
                    topic_id=task_data.get('topic_id'),
                    deadline=task_data.get('deadline')
                )

                if task_id:
                    self.statusBar().showMessage(f"✅ Задача «{task_data['title']}» создана!", 3000)
                    from core.event_bus import event_bus
                    event_bus.task_created.emit(task_id)

                    if self.content_stack.currentWidget() == self.topic_view:
                        self.topic_view.refresh()

                    # ✅ ИСПРАВЛЕНО: обновляем все связанные view
                    self._refresh_dashboard()
                    self._refresh_tasks()
        except Exception as e:
            logger.error(f"Ошибка создания задачи: {e}", exc_info=True)
            SilentMessageBox.warning(self, "Ошибка", f"Не удалось создать задачу: {e}")

    def _open_task_editor(self, task_id: int):
        """Открыть редактор задачи"""
        try:
            from modules.tasks.dialogs import TaskDialog
            task = container.task_controller.get_task(task_id)
            if task:
                dialog = TaskDialog(self, task=task)
                if dialog.exec():
                    self._refresh_topics()
                    self.topic_view.refresh()
                    # ✅ ИСПРАВЛЕНО: обновляем tasks_view
                    self._refresh_tasks()
        except Exception as e:
            logger.error(f"Ошибка редактирования задачи {task_id}: {e}", exc_info=True)

    def _delete_task(self, task_id: int):
        """Удалить задачу"""
        try:
            reply = SilentMessageBox.question(self, "Подтверждение удаления", "Удалить задачу?")
            if reply == SilentMessageBox.Yes:
                container.task_controller.delete_task(task_id)
                self._refresh_topics()
                self.topic_view.refresh()
                # ✅ ИСПРАВЛЕНО: обновляем tasks_view
                self._refresh_tasks()
        except Exception as e:
            logger.error(f"Ошибка удаления задачи {task_id}: {e}", exc_info=True)

    def _complete_task(self, task_id: int):
        """Отметить задачу выполненной"""
        try:
            container.task_controller.complete_task(task_id)
            self._refresh_topics()
            self.topic_view.refresh()
            # ✅ ИСПРАВЛЕНО: обновляем tasks_view
            self._refresh_tasks()
        except Exception as e:
            logger.error(f"Ошибка завершения задачи {task_id}: {e}", exc_info=True)

    # ==================== РАБОТА С КАРТОЧКАМИ ====================

    def _open_flashcard_creator(self, topic_id: int):
        """Создать новую карточку в теме"""
        try:
            from modules.flashcards.dialogs import CardTypeDialog
            dialog = CardTypeDialog(self)
            if dialog.exec():
                data = dialog.get_card_data()
                if data['type'] == 'free':
                    container.flashcard_controller.create_free_card(topic_id, data['content'])
                else:
                    container.flashcard_controller.create_qa_card(topic_id, data['question'], data['answer'])

                # ✅ ИСПРАВЛЕНО: обновляем все связанные view
                self._refresh_dashboard()
                self._refresh_flashcards()  # ← ДОБАВЛЕНО

                # Если открыта тема - обновляем её
                if self.content_stack.currentWidget() == self.topic_view:
                    self.topic_view.refresh()
        except Exception as e:
            logger.error(f"Ошибка создания карточки: {e}", exc_info=True)

    # ==================== ФОКУС-СЕССИИ ====================

    def _start_focus_session_from_topic(self, topic_id: int):
        """Запустить фокус-сессию из темы"""
        try:
            topic = container.topic_controller.get_topic(topic_id)
            if topic:
                self.navigation.navigate_to(NavSection.FOCUS, {
                    'action': 'start',
                    'topic_id': topic_id,
                    'topic_name': topic.name,
                    'interval': 15
                })
        except Exception as e:
            logger.error(f"Ошибка запуска сессии из темы {topic_id}: {e}", exc_info=True)

    def _on_review_session_completed(self, completed: int, total: int):
        """Обработчик завершения сессии повторения"""
        try:
            self.statusBar().showMessage(f"Повторение завершено: {completed} из {total} карточек", 3000)
            self.navigation.navigate_to(NavSection.FLASHCARDS)
        except Exception as e:
            logger.error(f"Ошибка обработки завершения повторения: {e}", exc_info=True)

    def _on_review_session_cancelled(self):
        """Обработчик отмены сессии повторения"""
        try:
            self.statusBar().showMessage("Сессия повторения отменена", 2000)
            self.navigation.navigate_to(NavSection.FLASHCARDS)
        except Exception as e:
            logger.error(f"Ошибка обработки отмены повторения: {e}", exc_info=True)

    # ==================== ИСТОРИЯ СЕССИЙ ====================

    def _resume_session_from_history(self, session_id: int):
        """Возобновляет сессию из глобальной истории"""
        try:
            session = container.session_controller.get_session(session_id)
            if not session:
                SilentMessageBox.warning(self, "Ошибка", "Сессия не найдена")
                return

            topic = container.topic_controller.get_topic(session.topic_id)
            if not topic:
                SilentMessageBox.warning(self, "Ошибка", "Тема не найдена")
                return

            self.focus_active_view.resume_existing_session(session_id, session.topic_id, topic.name)
            self.content_stack.setCurrentWidget(self.focus_active_view)
            self.statusBar().showMessage(f"Сессия возобновлена: {topic.name}", 2000)
        except Exception as e:
            logger.error(f"Ошибка возобновления сессии {session_id}: {e}", exc_info=True)

    def _show_session_analytics(self, session_id: int):
        """Показывает аналитику сессии из глобальной истории"""
        try:
            stats = container.session_controller.get_session_stats(session_id)
            if not stats:
                SilentMessageBox.warning(self, "Ошибка", "Не удалось загрузить статистику")
                return

            intervals = container.session_controller.get_session_intervals(session_id)
            quick_notes = container.session_controller._quick_note_repo.get_by_session(session_id)

            topic = container.topic_controller.get_topic(stats['topic_id'])
            topic_name = topic.name if topic else "Неизвестная тема"

            analytics_text = self._build_analytics_text(stats, intervals, quick_notes, topic_name)
            self._show_analytics_dialog(analytics_text)
        except Exception as e:
            logger.error(f"Ошибка показа аналитики сессии {session_id}: {e}", exc_info=True)
            SilentMessageBox.warning(self, "Ошибка", f"Не удалось загрузить аналитику: {e}")

    def _on_session_deleted(self):
        """После удаления сессии из глобальной истории"""
        try:
            self.dashboard_view.refresh()
            self.analytics_view.refresh()
            self.statusBar().showMessage("Сессия удалена", 2000)
        except Exception as e:
            logger.error(f"Ошибка обработки удаления сессии: {e}", exc_info=True)

    # ==================== СЕССИИ ВНУТРИ ТЕМЫ ====================

    def _resume_session_from_topic(self, session_id: int):
        """Возобновляет сессию из вкладки темы"""
        try:
            session = container.session_controller.get_session(session_id)
            if not session:
                SilentMessageBox.warning(self, "Ошибка", "Сессия не найдена")
                return

            topic = container.topic_controller.get_topic(session.topic_id)
            if not topic:
                SilentMessageBox.warning(self, "Ошибка", "Тема не найдена")
                return

            self.focus_active_view.resume_existing_session(session_id, session.topic_id, topic.name)
            self.content_stack.setCurrentWidget(self.focus_active_view)
            self.statusBar().showMessage(f"Сессия возобновлена: {topic.name}", 2000)
        except Exception as e:
            logger.error(f"Ошибка возобновления сессии из темы {session_id}: {e}", exc_info=True)

    def _on_session_deleted_in_topic(self):
        """После удаления сессии из вкладки темы"""
        try:
            self.dashboard_view.refresh()
            self.analytics_view.refresh()
            self.statusBar().showMessage("Сессия удалена", 2000)
        except Exception as e:
            logger.error(f"Ошибка обработки удаления сессии из темы: {e}", exc_info=True)

    def _show_session_analytics_from_topic(self, session_id: int):
        """Показывает аналитику сессии из вкладки темы"""
        try:
            stats = container.session_controller.get_session_stats(session_id)
            if not stats:
                SilentMessageBox.warning(self, "Ошибка", "Не удалось загрузить статистику")
                return

            intervals = container.session_controller.get_session_intervals(session_id)
            quick_notes = container.session_controller._quick_note_repo.get_by_session(session_id)

            topic = container.topic_controller.get_topic(stats['topic_id'])
            topic_name = topic.name if topic else "Неизвестная тема"

            analytics_text = self._build_analytics_text(stats, intervals, quick_notes, topic_name)
            self._show_analytics_dialog(analytics_text)
        except Exception as e:
            logger.error(f"Ошибка показа аналитики сессии из темы {session_id}: {e}", exc_info=True)
            SilentMessageBox.warning(self, "Ошибка", f"Не удалось загрузить аналитику: {e}")

    # ==================== ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ ДЛЯ АНАЛИТИКИ ====================

    def _build_analytics_text(self, stats: dict, intervals: list, quick_notes: list, topic_name: str) -> str:
        """Формирует HTML-текст аналитики сессии с анализом пиков"""
        try:
            from utils.local_time import format_datetime
            start_time_formatted = format_datetime(stats.get('start_time', '')) if stats.get('start_time') else '—'

            # Получаем таймлайн метрик
            logs = container.session_controller._state_log_repo.get_by_session(stats['id'])

            # Анализируем каждый показатель
            focus_data = [log for log in logs if log['metric'] == 'focus']
            energy_data = [log for log in logs if log['metric'] == 'energy']
            interest_data = [log for log in logs if log['metric'] == 'interest']

            def analyze_metric(data: list, metric_name: str) -> dict:
                """Анализирует метрику и возвращает статистику"""
                if not data:
                    return {
                        'name': metric_name,
                        'avg': 0,
                        'max': 0,
                        'min': 0,
                        'max_minute': 0,
                        'min_minute': 0,
                        'trend': 'нет данных'
                    }

                values = [log['value'] for log in data]
                minutes = [log['minute'] for log in data]

                max_val = max(values)
                min_val = min(values)
                max_minute = minutes[values.index(max_val)]
                min_minute = minutes[values.index(min_val)]
                avg_val = sum(values) / len(values)

                # Определяем тренд
                if len(values) >= 2:
                    first_half = values[:len(values) // 2]
                    second_half = values[len(values) // 2:]
                    first_avg = sum(first_half) / len(first_half)
                    second_avg = sum(second_half) / len(second_half)

                    if second_avg > first_avg + 5:
                        trend = '📈 растёт'
                    elif second_avg < first_avg - 5:
                        trend = '📉 падает'
                    else:
                        trend = '➡️ стабильно'
                else:
                    trend = 'недостаточно данных'

                return {
                    'name': metric_name,
                    'avg': round(avg_val, 1),
                    'max': max_val,
                    'min': min_val,
                    'max_minute': max_minute,
                    'min_minute': min_minute,
                    'trend': trend
                }

            focus_analysis = analyze_metric(focus_data, '🧠 Концентрация')
            energy_analysis = analyze_metric(energy_data, '⚡ Энергия')
            interest_analysis = analyze_metric(interest_data, '❤️ Интерес')

            # Генерируем рекомендацию
            recommendations = []

            # Анализируем синергию
            all_avgs = [focus_analysis['avg'], energy_analysis['avg'], interest_analysis['avg']]
            overall_avg = sum(all_avgs) / len(all_avgs) if all_avgs else 0

            if overall_avg >= 70:
                recommendations.append("🌟 <b>Отличная сессия!</b> Все показатели на высоком уровне.")
            elif overall_avg >= 50:
                recommendations.append("✅ <b>Хорошая сессия.</b> Есть потенциал для улучшения.")
            else:
                recommendations.append("💡 <b>Сессия была сложной.</b> Попробуйте сделать перерыв перед следующей.")

            if focus_analysis['trend'] == '📉 падает':
                recommendations.append(
                    f"🧠 Концентрация падала (пик на {focus_analysis['max_minute']} мин). Попробуйте технику Pomodoro: 25 мин работа + 5 мин отдых.")

            if energy_analysis['avg'] < 40:
                recommendations.append(
                    "⚡ Низкая энергия. Перед сессией проверьте сон, питание и физическую активность.")

            if interest_analysis['max_minute'] < 5 and len(interest_data) > 3:
                recommendations.append(
                    "❤️ Интерес был высоким только в начале. Разбейте тему на подтемы для поддержания вовлечённости.")

            if focus_analysis['max'] - focus_analysis['min'] > 40:
                recommendations.append("📊 Сильные колебания концентрации. Найдите оптимальное время суток для работы.")

            analytics_text = f"""
            <style>
                body {{ font-family: Arial, sans-serif; }}
                h2 {{ color: #1F2937; margin-bottom: 16px; }}
                h3 {{ color: #3B82F6; margin-top: 20px; margin-bottom: 12px; }}
                .stat {{ margin: 8px 0; padding: 8px; background-color: #F9FAFB; border-radius: 8px; }}
                .metric {{ margin: 12px 0; padding: 12px; background-color: #EFF6FF; border-radius: 8px; border-left: 4px solid #3B82F6; }}
                .interval {{ margin: 4px 0; padding: 6px; background-color: #F0F4F8; border-radius: 6px; font-size: 13px; }}
                .note {{ margin: 8px 0; padding: 10px; background-color: #FEF3C7; border-radius: 8px; }}
                .recommendation {{ margin: 8px 0; padding: 12px; background-color: #D1FAE5; border-radius: 8px; border-left: 4px solid #10B981; }}
            </style>

            <h2>📊 Аналитика сессии</h2>

            <div class="stat">
                <b>Тема:</b> {topic_name}<br>
                <b>Дата:</b> {start_time_formatted}<br>
                <b>Длительность:</b> {stats.get('duration_display', '—')}<br>
                <b>Статус:</b> {stats.get('status', '—')}
            </div>

            <h3>📈 Анализ показателей</h3>

            <div class="metric">
                <b>{focus_analysis['name']}</b><br>
                Среднее: <b>{focus_analysis['avg']}/100</b> | 
                Пик: <b>{focus_analysis['max']}</b> (на {focus_analysis['max_minute']} мин) | 
                Мин: <b>{focus_analysis['min']}</b> (на {focus_analysis['min_minute']} мин)<br>
                Тренд: {focus_analysis['trend']}
            </div>

            <div class="metric">
                <b>{energy_analysis['name']}</b><br>
                Среднее: <b>{energy_analysis['avg']}/100</b> | 
                Пик: <b>{energy_analysis['max']}</b> (на {energy_analysis['max_minute']} мин) | 
                Мин: <b>{energy_analysis['min']}</b> (на {energy_analysis['min_minute']} мин)<br>
                Тренд: {energy_analysis['trend']}
            </div>

            <div class="metric">
                <b>{interest_analysis['name']}</b><br>
                Среднее: <b>{interest_analysis['avg']}/100</b> | 
                Пик: <b>{interest_analysis['max']}</b> (на {interest_analysis['max_minute']} мин) | 
                Мин: <b>{interest_analysis['min']}</b> (на {interest_analysis['min_minute']} мин)<br>
                Тренд: {interest_analysis['trend']}
            </div>

            <h3>💡 Рекомендации</h3>
            """

            for rec in recommendations:
                analytics_text += f'<div class="recommendation">{rec}</div>'

            analytics_text += f"""
            <h3>📋 Интервалы работы ({len(intervals)})</h3>
            """

            if intervals:
                for i, interval in enumerate(intervals):
                    start = format_datetime(interval.get('start_time', '')) if interval.get('start_time') else '—'
                    end = format_datetime(interval.get('end_time', '')) if interval.get('end_time') else '—'
                    duration = interval.get('duration_seconds', 0)
                    duration_min = duration // 60
                    duration_sec = duration % 60
                    analytics_text += f"""
                    <div class="interval">
                        #{i + 1}: {start} → {end} ({duration_min}м {duration_sec}с)
                    </div>
                    """
            else:
                analytics_text += "<p style='color: #9CA3AF;'>Нет данных об интервалах</p>"

            analytics_text += "<h3>✏️ Быстрые записи</h3>"

            if quick_notes:
                for note in quick_notes:
                    time = format_datetime(note.get('created_at', '')) if note.get('created_at') else '—'
                    content = note.get('content', '')
                    analytics_text += f"""
                    <div class="note">
                        <b>{time}</b><br>
                        {content}
                    </div>
                    """
            else:
                analytics_text += "<p style='color: #9CA3AF;'>Нет быстрых записей</p>"

            return analytics_text
        except Exception as e:
            logger.error(f"Ошибка построения аналитики: {e}", exc_info=True)
            return f"<h2>Ошибка аналитики</h2><p>{e}</p>"

    def _show_analytics_dialog(self, analytics_text: str):
        """Показывает диалог с аналитикой"""
        try:
            from PySide6.QtWidgets import QDialog, QVBoxLayout, QTextBrowser, QDialogButtonBox
            dialog = QDialog(self)
            dialog.setWindowTitle("Аналитика сессии")
            dialog.resize(700, 600)

            layout = QVBoxLayout(dialog)

            browser = QTextBrowser()
            browser.setHtml(analytics_text)
            browser.setOpenExternalLinks(True)
            layout.addWidget(browser)

            button_box = QDialogButtonBox(QDialogButtonBox.Close)
            button_box.rejected.connect(dialog.reject)
            layout.addWidget(button_box)

            dialog.exec()
        except Exception as e:
            logger.error(f"Ошибка показа диалога аналитики: {e}", exc_info=True)
            SilentMessageBox.warning(self, "Ошибка", f"Не удалось показать аналитику: {e}")

    def _on_new_task_from_calendar(self):
        """Создание задачи из календаря"""
        try:
            from modules.tasks.dialogs import TaskDialog

            # Получаем выбранную дату из календаря
            selected_date = self.calendar_view._current_date

            dialog = TaskDialog(self, initial_date=selected_date)
            if dialog.exec() == QDialog.Accepted:
                try:
                    data = dialog.get_task_data()
                    task_id = container.task_controller.create_task(
                        title=data['title'],
                        description=data['description'],
                        topic_id=data['topic_id'],
                        deadline=data['deadline']
                    )
                    if task_id:
                        from core.event_bus import event_bus
                        event_bus.task_created.emit(task_id)
                        self.calendar_view.refresh()
                        self.tasks_view.refresh()
                        self.statusBar().showMessage(f"✅ Задача «{data['title']}» создана!", 3000)
                except ValueError as e:
                    SilentMessageBox.warning(self, "Ошибка", str(e))
        except Exception as e:
            logger.error(f"Ошибка создания задачи из календаря: {e}", exc_info=True)

    def _refresh_notes(self):
        """Обновляет все view, связанные с заметками"""
        try:
            if self.content_stack.currentWidget() == self.topic_view:
                self.topic_view.refresh()

            if hasattr(self, 'search_view') and hasattr(self.search_view, 'refresh'):
                self.search_view.refresh()

            if hasattr(self, 'dashboard_view') and hasattr(self.dashboard_view, 'refresh'):
                self.dashboard_view.refresh()
        except Exception as e:
            logger.error(f"Ошибка обновления заметок: {e}", exc_info=True)

    def _refresh_tasks(self):
        """Обновляет все view, связанные с задачами"""
        try:
            if hasattr(self, 'tasks_view') and hasattr(self.tasks_view, 'refresh'):
                self.tasks_view.refresh()

            if hasattr(self, 'calendar_view') and hasattr(self.calendar_view, 'refresh'):
                self.calendar_view.refresh()

            if self.content_stack.currentWidget() == self.topic_view:
                self.topic_view.refresh()

            if hasattr(self, 'search_view') and hasattr(self.search_view, 'refresh'):
                self.search_view.refresh()

            if hasattr(self, 'dashboard_view') and hasattr(self.dashboard_view, 'refresh'):
                self.dashboard_view.refresh()
        except Exception as e:
            logger.error(f"Ошибка обновления задач: {e}", exc_info=True)

    def _refresh_flashcards(self):
        """Обновляет все view, связанные с карточками"""
        try:
            if hasattr(self, 'flashcards_view') and hasattr(self.flashcards_view, 'refresh'):
                self.flashcards_view.refresh()

            if self.content_stack.currentWidget() == self.topic_view:
                self.topic_view.refresh()

            if hasattr(self, 'search_view') and hasattr(self.search_view, 'refresh'):
                self.search_view.refresh()

            if hasattr(self, 'dashboard_view') and hasattr(self.dashboard_view, 'refresh'):
                self.dashboard_view.refresh()
        except Exception as e:
            logger.error(f"Ошибка обновления карточек: {e}", exc_info=True)