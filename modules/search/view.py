# modules/search/view.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QListWidget,
    QListWidgetItem, QScrollArea, QFrame, QPushButton
)
from widgets import SilentMessageBox
from PySide6.QtCore import Qt, Signal
import logging

from .controller import SearchController
from .widgets import SearchBarWidget, SearchResultItemWidget

# Настройка логирования
logger = logging.getLogger(__name__)


class SearchView(QWidget):
    """
    Экран поиска с отображением результатов по категориям.
    """

    # Сигналы для навигации
    topic_selected = Signal(int)  # (topic_id)
    note_selected = Signal(int)  # (note_id)
    task_selected = Signal(int)  # (task_id)
    flashcard_selected = Signal(int)  # (flashcard_id)

    def __init__(self, controller: SearchController, parent=None):
        super().__init__(parent)
        self._controller = controller
        self._setup_ui()
        self._connect_signals()
        self._load_history()

    def _setup_ui(self):
        """Настраивает интерфейс"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Заголовок
        header_layout = QHBoxLayout()

        title_label = QLabel("🔍 Поиск")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        header_layout.addWidget(title_label)

        header_layout.addStretch()

        # Кнопка очистки истории
        self.clear_history_btn = QPushButton("🗑️ Очистить историю")
        self.clear_history_btn.setFlat(True)
        self.clear_history_btn.setVisible(False)
        header_layout.addWidget(self.clear_history_btn)

        layout.addLayout(header_layout)

        # Поисковая строка
        self.search_bar = SearchBarWidget()
        layout.addWidget(self.search_bar)

        # Область результатов
        self.results_scroll = QScrollArea()
        self.results_scroll.setWidgetResizable(True)
        self.results_scroll.setFrameShape(QFrame.NoFrame)

        self.results_container = QWidget()
        self.results_layout = QVBoxLayout(self.results_container)
        self.results_layout.setAlignment(Qt.AlignTop)
        self.results_layout.setSpacing(15)

        # Пустое состояние
        self.empty_label = QLabel("Введите поисковый запрос...")
        self.empty_label.setAlignment(Qt.AlignCenter)
        self.empty_label.setStyleSheet("color: #888888; padding: 40px;")
        self.results_layout.addWidget(self.empty_label)

        # Блок "Темы"
        self.topics_section = self._create_section("📚 Темы")
        self.results_layout.addWidget(self.topics_section['widget'])

        # Блок "Заметки"
        self.notes_section = self._create_section("📝 Заметки")
        self.results_layout.addWidget(self.notes_section['widget'])

        # Блок "Задачи"
        self.tasks_section = self._create_section("✅ Задачи")
        self.results_layout.addWidget(self.tasks_section['widget'])

        # Блок "Карточки"
        self.cards_section = self._create_section("🃏 Карточки")
        self.results_layout.addWidget(self.cards_section['widget'])

        self.results_scroll.setWidget(self.results_container)
        layout.addWidget(self.results_scroll)

        # Изначально скрываем все секции
        self._hide_all_sections()

    def _create_section(self, title: str) -> dict:
        """Создаёт секцию с заголовком и списком"""
        widget = QWidget()
        widget.hide()

        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Заголовок
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #1976d2;")
        layout.addWidget(title_label)

        # Разделитель
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        layout.addWidget(separator)

        # Список
        list_widget = QListWidget()
        list_widget.setFrameShape(QFrame.NoFrame)
        list_widget.setSpacing(5)
        list_widget.setSelectionMode(QListWidget.NoSelection)
        layout.addWidget(list_widget)

        return {
            'widget': widget,
            'list': list_widget,
            'title_label': title_label,
            'base_title': title  # ✅ Сохраняем базовый заголовок
        }

    def _connect_signals(self):
        """Подключает сигналы"""
        self.search_bar.search_requested.connect(self._on_search)
        self.clear_history_btn.clicked.connect(self._on_clear_history)

    def _hide_all_sections(self):
        """Скрывает все секции результатов"""
        self.topics_section['widget'].hide()
        self.notes_section['widget'].hide()
        self.tasks_section['widget'].hide()
        self.cards_section['widget'].hide()

    def _load_history(self):
        """Загружает историю поиска"""
        try:
            history = self._controller.get_search_history(10)
            self.search_bar.set_history(history)
            self.clear_history_btn.setVisible(len(history) > 0)
            logger.debug(f"Загружена история поиска: {len(history)} записей")
        except Exception as e:
            logger.error(f"Ошибка загрузки истории поиска: {e}", exc_info=True)

    def _on_search(self, query: str):
        """Обработчик поиска"""
        try:
            if len(query) < 2:
                self.empty_label.setText("Введите минимум 2 символа для поиска")
                self.empty_label.show()
                self._hide_all_sections()
                return

            # Сохраняем запрос в историю
            self._controller.save_search_query(query)
            self._load_history()

            # Выполняем поиск
            results = self._controller.search_all(query)
            total_count = self._controller.get_result_count(results)

            if total_count == 0:
                self.empty_label.setText(f"Ничего не найдено по запросу «{query}»")
                self.empty_label.show()
                self._hide_all_sections()
                logger.debug(f"Поиск '{query}': ничего не найдено")
                return

            self.empty_label.hide()

            # Отображаем результаты по категориям
            self._display_results('topics', results['topics'], self.topics_section)
            self._display_results('notes', results['notes'], self.notes_section)
            self._display_results('tasks', results['tasks'], self.tasks_section)
            self._display_results('flashcards', results['flashcards'], self.cards_section)

            logger.info(f"Поиск '{query}': найдено {total_count} результатов")
        except Exception as e:
            logger.error(f"Ошибка поиска '{query}': {e}", exc_info=True)
            self.empty_label.setText(f"Ошибка поиска: {e}")
            self.empty_label.show()
            self._hide_all_sections()

    def _display_results(self, result_type: str, results: list, section: dict):
        """Отображает результаты в секции"""
        try:
            section['list'].clear()

            # ✅ ИСПРАВЛЕНО: восстанавливаем базовый заголовок
            base_title = section.get('base_title', section['title_label'].text().split(' (')[0])

            if not results:
                section['widget'].hide()
                section['title_label'].setText(base_title)
                return

            for result in results:
                item = QListWidgetItem()

                # ✅ ИСПРАВЛЕНО: сначала создаём виджет, потом устанавливаем sizeHint
                widget = SearchResultItemWidget(result)
                item.setSizeHint(widget.sizeHint())

                # Подключаем сигнал клика
                widget.mousePressEvent = lambda e, r=result: self._on_result_clicked(r)

                section['list'].addItem(item)
                section['list'].setItemWidget(item, widget)

            # Обновляем заголовок с количеством
            section['title_label'].setText(f"{base_title} ({len(results)})")
            section['widget'].show()
        except Exception as e:
            logger.error(f"Ошибка отображения результатов {result_type}: {e}", exc_info=True)

    def _on_result_clicked(self, result: dict):
        """Обработчик клика по результату"""
        try:
            result_type = result.get('type')
            result_id = result.get('id')

            if not result_id:
                logger.warning(f"Результат без ID: {result}")
                return

            if result_type == 'topic':
                self.topic_selected.emit(result_id)
            elif result_type == 'note':
                self.note_selected.emit(result_id)
            elif result_type == 'task':
                self.task_selected.emit(result_id)
            elif result_type == 'flashcard':
                self.flashcard_selected.emit(result_id)
            else:
                logger.warning(f"Неизвестный тип результата: {result_type}")

            logger.debug(f"Клик по результату: тип={result_type}, id={result_id}")
        except Exception as e:
            logger.error(f"Ошибка обработки клика по результату: {e}", exc_info=True)

    def _on_clear_history(self):
        """Очищает историю поиска"""
        try:
            reply = SilentMessageBox.question(
                self, "Очистить историю",
                "Вы действительно хотите очистить историю поиска?",
                SilentMessageBox.Yes | SilentMessageBox.No, SilentMessageBox.No
            )

            if reply == SilentMessageBox.Yes:
                self._controller.clear_search_history()
                self._load_history()
                self.search_bar.set_history([])
                SilentMessageBox.information(self, "Готово", "История поиска очищена")
                logger.info("История поиска очищена")
        except Exception as e:
            logger.error(f"Ошибка очистки истории: {e}", exc_info=True)
            SilentMessageBox.warning(self, "Ошибка", f"Не удалось очистить историю: {e}")

    def perform_search(self, query: str):
        """
        Внешний вызов поиска (например, из главного окна по глобальному хоткею)
        """
        try:
            self.search_bar.set_query(query)
            self._on_search(query)
        except Exception as e:
            logger.error(f"Ошибка внешнего вызова поиска: {e}", exc_info=True)

    def refresh(self):
        """Обновляет результаты поиска"""
        try:
            # ✅ ИСПРАВЛЕНО: _perform_search → _on_search
            if hasattr(self, 'search_bar') and self.search_bar.text():
                self._on_search(self.search_bar.text())
        except Exception as e:
            logger.error(f"Ошибка обновления поиска: {e}", exc_info=True)