# modules/search/widgets.py
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QLineEdit, QPushButton, QCompleter,
    QListWidget, QListWidgetItem, QVBoxLayout, QLabel
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QIcon, QKeySequence
import logging

# Настройка логирования
logger = logging.getLogger(__name__)


class SearchBarWidget(QWidget):
    """
    Виджет поисковой строки с автодополнением из истории.
    """

    search_requested = Signal(str)  # (query)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._history = []
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        """Настраивает интерфейс поисковой строки"""
        try:
            # ✅ ИСПРАВЛЕНО: восстанавливаем правильный код для SearchBarWidget
            layout = QHBoxLayout(self)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(5)

            # Поле поиска
            self.search_edit = QLineEdit()
            self.search_edit.setPlaceholderText("🔍 Поиск...")
            self.search_edit.setClearButtonEnabled(True)
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
            layout.addWidget(self.search_edit, 1)

            # Кнопка поиска
            self.search_btn = QPushButton("🔍")
            self.search_btn.setFixedWidth(40)
            self.search_btn.setToolTip("Поиск (Ctrl+F)")
            self.search_btn.setStyleSheet("""
                QPushButton {
                    background-color: #3B82F6;
                    color: white;
                    border: none;
                    border-radius: 8px;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background-color: #2563EB;
                }
            """)
            layout.addWidget(self.search_btn)

            # Кнопка очистки
            self.clear_btn = QPushButton("✖")
            self.clear_btn.setFixedWidth(40)
            self.clear_btn.setToolTip("Очистить")
            self.clear_btn.setStyleSheet("""
                QPushButton {
                    background-color: #F0F4F8;
                    color: #6B7280;
                    border: 1px solid #E6EEF6;
                    border-radius: 8px;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background-color: #E2E8F0;
                }
            """)
            layout.addWidget(self.clear_btn)

            # Настройка автодополнения
            self.completer = QCompleter()
            self.completer.setCaseSensitivity(Qt.CaseInsensitive)
            self.completer.setFilterMode(Qt.MatchContains)
            self.search_edit.setCompleter(self.completer)

            logger.debug("SearchBarWidget инициализирован")
        except Exception as e:
            logger.error(f"Ошибка настройки SearchBarWidget: {e}", exc_info=True)

    def _connect_signals(self):
        """Подключает сигналы"""
        try:
            self.search_btn.clicked.connect(self._on_search)
            self.clear_btn.clicked.connect(self._on_clear)
            self.search_edit.returnPressed.connect(self._on_search)
        except Exception as e:
            logger.error(f"Ошибка подключения сигналов SearchBarWidget: {e}", exc_info=True)

    def _on_search(self):
        """Обработчик поиска"""
        try:
            query = self.search_edit.text().strip()
            if query:
                self.search_requested.emit(query)
        except Exception as e:
            logger.error(f"Ошибка обработки поиска: {e}", exc_info=True)

    def _on_clear(self):
        """Очищает поле поиска"""
        try:
            self.search_edit.clear()
            self.search_edit.setFocus()
        except Exception as e:
            logger.error(f"Ошибка очистки поля: {e}", exc_info=True)

    def set_history(self, history: list):
        """Устанавливает историю для автодополнения"""
        try:
            self._history = history if history else []
            self.completer.setModel(self._create_list_model(self._history))
            logger.debug(f"Установлена история поиска: {len(self._history)} записей")
        except Exception as e:
            logger.error(f"Ошибка установки истории: {e}", exc_info=True)

    def _create_list_model(self, items: list):
        """Создаёт модель для автодополнения"""
        from PySide6.QtCore import QStringListModel
        return QStringListModel(items if items else [])

    def get_query(self) -> str:
        """Возвращает текущий запрос"""
        try:
            return self.search_edit.text().strip()
        except Exception as e:
            logger.error(f"Ошибка получения запроса: {e}", exc_info=True)
            return ""

    def set_query(self, query: str):
        """Устанавливает запрос в поле"""
        try:
            self.search_edit.setText(query if query else "")
        except Exception as e:
            logger.error(f"Ошибка установки запроса: {e}", exc_info=True)

    def clear(self):
        """Очищает поле"""
        try:
            self.search_edit.clear()
        except Exception as e:
            logger.error(f"Ошибка очистки: {e}", exc_info=True)

    def set_focus(self):
        """Устанавливает фокус на поле поиска"""
        try:
            self.search_edit.setFocus()
            self.search_edit.selectAll()
        except Exception as e:
            logger.error(f"Ошибка установки фокуса: {e}", exc_info=True)

    def text(self) -> str:
        """Возвращает текст из поля поиска (для совместимости с view.py)"""
        try:
            return self.search_edit.text()
        except Exception as e:
            logger.error(f"Ошибка получения текста: {e}", exc_info=True)
            return ""


class SearchResultItemWidget(QWidget):
    """
    Виджет для отображения одного результата поиска.
    """

    def __init__(self, result: dict, parent=None):
        super().__init__(parent)
        self.result = result if result else {}
        self._setup_ui()

    def _setup_ui(self):
        """Настраивает интерфейс"""
        try:
            layout = QVBoxLayout(self)
            layout.setContentsMargins(12, 10, 12, 10)  # ✅ Увеличили отступы
            layout.setSpacing(6)

            # ✅ ИСПРАВЛЕНО: безопасное получение type
            result_type = self.result.get('type', '')
            if not result_type:
                logger.warning(f"Результат без типа: {self.result}")
                error_label = QLabel("❌ Некорректный результат поиска")
                error_label.setStyleSheet("color: #EF4444; font-size: 12px;")
                layout.addWidget(error_label)
                return

            # Заголовок
            header_layout = QHBoxLayout()
            header_layout.setSpacing(8)

            icon_label = QLabel(self.result.get('icon', '📄'))
            icon_label.setStyleSheet("font-size: 18px;")
            header_layout.addWidget(icon_label)

            title_label = QLabel(self.result.get('title', 'Без названия'))
            title_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #1F2937;")
            title_label.setWordWrap(True)
            header_layout.addWidget(title_label, 1)

            header_layout.addStretch()

            # Тип
            type_text = self._get_type_text(result_type)
            type_label = QLabel(type_text)
            type_label.setStyleSheet("""
                background-color: #F0F4F8;
                color: #6B7280;
                font-size: 10px;
                padding: 2px 8px;
                border-radius: 4px;
            """)
            header_layout.addWidget(type_label)

            layout.addLayout(header_layout)

            # Информация в зависимости от типа
            if result_type == 'note':
                snippet = self.result.get('snippet', '')
                if snippet:
                    snippet_label = QLabel(snippet)
                    snippet_label.setStyleSheet("color: #666666; font-size: 12px; margin-top: 4px;")
                    snippet_label.setWordWrap(True)
                    snippet_label.setMaximumHeight(60)
                    layout.addWidget(snippet_label)

                topic_name = self.result.get('topic_name')
                if topic_name:
                    topic_label = QLabel(f"📁 {topic_name}")
                    topic_label.setStyleSheet("color: #888888; font-size: 10px; margin-top: 4px;")
                    layout.addWidget(topic_label)

            elif result_type == 'task':
                status_text = self.result.get('status_text', '')
                if status_text:
                    status_label = QLabel(status_text)
                    status_label.setStyleSheet("color: #888888; font-size: 10px; margin-top: 4px;")
                    layout.addWidget(status_label)

                deadline = self.result.get('deadline')
                if deadline:
                    deadline_label = QLabel(f"⏰ Дедлайн: {str(deadline)[:10]}")
                    deadline_label.setStyleSheet("color: #888888; font-size: 10px; margin-top: 4px;")
                    layout.addWidget(deadline_label)

            elif result_type == 'flashcard':
                if self.result.get('card_type') == 'free':
                    content = self.result.get('content', '')
                    if content:
                        content_label = QLabel(content[:150] + "..." if len(content) > 150 else content)
                        content_label.setStyleSheet("color: #666666; font-size: 12px; margin-top: 4px;")
                        content_label.setWordWrap(True)
                        content_label.setMaximumHeight(60)
                        layout.addWidget(content_label)
                else:
                    question = self.result.get('question', '')
                    if question:
                        question_label = QLabel(f"Вопрос: {question[:100]}{'...' if len(question) > 100 else ''}")
                        question_label.setStyleSheet("color: #666666; font-size: 12px; margin-top: 4px;")
                        question_label.setWordWrap(True)
                        question_label.setMaximumHeight(60)
                        layout.addWidget(question_label)

                topic_name = self.result.get('topic_name')
                if topic_name:
                    topic_label = QLabel(f"📁 {topic_name}")
                    topic_label.setStyleSheet("color: #888888; font-size: 10px; margin-top: 4px;")
                    layout.addWidget(topic_label)

            elif result_type == 'topic':
                path = self.result.get('path')
                if path:
                    path_label = QLabel(f"📁 {path}")
                    path_label.setStyleSheet("color: #888888; font-size: 10px; margin-top: 4px;")
                    layout.addWidget(path_label)

            # ✅ Добавляем минимальную высоту
            self.setMinimumHeight(60)
        except Exception as e:
            logger.error(f"Ошибка настройки SearchResultItemWidget: {e}", exc_info=True)
            layout = self.layout()
            if layout is None:
                layout = QVBoxLayout(self)
            error_label = QLabel(f"❌ Ошибка отображения результата")
            error_label.setStyleSheet("color: #EF4444; font-size: 12px;")
            layout.addWidget(error_label)

    def _get_type_text(self, type_name: str) -> str:
        """Возвращает текст типа результата"""
        types = {
            'topic': 'Тема',
            'note': 'Заметка',
            'task': 'Задача',
            'flashcard': 'Карточка'
        }
        return types.get(type_name, type_name if type_name else 'Неизвестно')