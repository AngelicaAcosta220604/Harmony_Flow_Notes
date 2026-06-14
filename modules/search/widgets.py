# modules/search/widgets.py
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QLineEdit, QPushButton, QCompleter,
    QListWidget, QListWidgetItem, QVBoxLayout, QLabel
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QIcon, QKeySequence


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
        """Настраивает интерфейс"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        # Поле поиска
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("🔍 Поиск...")
        self.search_edit.setClearButtonEnabled(True)
        layout.addWidget(self.search_edit, 1)

        # Кнопка поиска
        self.search_btn = QPushButton("🔍")
        self.search_btn.setFixedWidth(30)
        self.search_btn.setToolTip("Поиск (Ctrl+F)")
        layout.addWidget(self.search_btn)

        # Кнопка очистки
        self.clear_btn = QPushButton("✖")
        self.clear_btn.setFixedWidth(30)
        self.clear_btn.setToolTip("Очистить")
        layout.addWidget(self.clear_btn)

        # Настройка автодополнения
        self.completer = QCompleter()
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.completer.setFilterMode(Qt.MatchContains)
        self.search_edit.setCompleter(self.completer)

    def _connect_signals(self):
        """Подключает сигналы"""
        self.search_btn.clicked.connect(self._on_search)
        self.clear_btn.clicked.connect(self._on_clear)
        self.search_edit.returnPressed.connect(self._on_search)

    def _on_search(self):
        """Обработчик поиска"""
        query = self.search_edit.text().strip()
        if query:
            self.search_requested.emit(query)

    def _on_clear(self):
        """Очищает поле поиска"""
        self.search_edit.clear()
        self.search_edit.setFocus()

    def set_history(self, history: list):
        """Устанавливает историю для автодополнения"""
        self._history = history
        self.completer.setModel(self._create_list_model(history))

    def _create_list_model(self, items: list):
        """Создаёт модель для автодополнения"""
        from PySide6.QtCore import QStringListModel
        return QStringListModel(items)

    def get_query(self) -> str:
        """Возвращает текущий запрос"""
        return self.search_edit.text().strip()

    def set_query(self, query: str):
        """Устанавливает запрос в поле"""
        self.search_edit.setText(query)

    def clear(self):
        """Очищает поле"""
        self.search_edit.clear()

    def set_focus(self):
        """Устанавливает фокус на поле поиска"""
        self.search_edit.setFocus()
        self.search_edit.selectAll()


class SearchResultItemWidget(QWidget):
    """
    Виджет для отображения одного результата поиска.
    """

    def __init__(self, result: dict, parent=None):
        super().__init__(parent)
        self.result = result
        self._setup_ui()

    def _setup_ui(self):
        """Настраивает интерфейс"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(4)

        # Заголовок
        header_layout = QHBoxLayout()

        icon_label = QLabel(result.get('icon', '📄'))
        icon_label.setStyleSheet("font-size: 16px;")
        header_layout.addWidget(icon_label)

        title_label = QLabel(result.get('title', ''))
        title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        header_layout.addWidget(title_label)

        header_layout.addStretch()

        # Тип и тема
        type_text = self._get_type_text(result['type'])
        type_label = QLabel(type_text)
        type_label.setStyleSheet("color: #888888; font-size: 10px;")
        header_layout.addWidget(type_label)

        layout.addLayout(header_layout)

        # Информация в зависимости от типа
        if result['type'] == 'note':
            snippet_label = QLabel(result.get('snippet', ''))
            snippet_label.setStyleSheet("color: #666666; font-size: 12px;")
            snippet_label.setWordWrap(True)
            layout.addWidget(snippet_label)

            topic_label = QLabel(f"📁 {result.get('topic_name', '—')}")
            topic_label.setStyleSheet("color: #888888; font-size: 10px;")
            layout.addWidget(topic_label)

        elif result['type'] == 'task':
            status_label = QLabel(result.get('status_text', ''))
            status_label.setStyleSheet("color: #888888; font-size: 10px;")
            layout.addWidget(status_label)

            if result.get('deadline'):
                deadline_label = QLabel(f"⏰ Дедлайн: {result.get('deadline', '')[:10]}")
                deadline_label.setStyleSheet("color: #888888; font-size: 10px;")
                layout.addWidget(deadline_label)

        elif result['type'] == 'flashcard':
            if result.get('card_type') == 'free':
                content_label = QLabel(result.get('content', '')[:100])
                content_label.setStyleSheet("color: #666666; font-size: 12px;")
                content_label.setWordWrap(True)
                layout.addWidget(content_label)
            else:
                question_label = QLabel(f"Вопрос: {result.get('question', '')[:80]}")
                question_label.setStyleSheet("color: #666666; font-size: 12px;")
                question_label.setWordWrap(True)
                layout.addWidget(question_label)

            topic_label = QLabel(f"📁 {result.get('topic_name', '—')}")
            topic_label.setStyleSheet("color: #888888; font-size: 10px;")
            layout.addWidget(topic_label)

        elif result['type'] == 'topic':
            if result.get('path'):
                path_label = QLabel(f"📁 {result.get('path', '')}")
                path_label.setStyleSheet("color: #888888; font-size: 10px;")
                layout.addWidget(path_label)

    def _get_type_text(self, type_name: str) -> str:
        """Возвращает текст типа результата"""
        types = {
            'topic': 'Тема',
            'note': 'Заметка',
            'task': 'Задача',
            'flashcard': 'Карточка'
        }
        return types.get(type_name, type_name)