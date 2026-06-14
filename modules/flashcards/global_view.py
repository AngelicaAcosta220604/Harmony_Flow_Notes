# modules/flashcards/global_view.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QListWidget, QListWidgetItem, QStackedWidget, QTextEdit,
    QComboBox, QMessageBox
)
from PySide6.QtCore import Qt, Signal

from .controller import FlashcardController
from models.flashcard import Flashcard


class GlobalCardsView(QWidget):
    """
    Экран для просмотра карточек из всех тем.
    """

    card_selected = Signal(int)  # (card_id)

    def __init__(self, controller: FlashcardController, parent=None):
        super().__init__(parent)
        self._controller = controller
        self._current_card = None
        self._setup_ui()
        self._connect_signals()
        self._load_cards()

    def _setup_ui(self):
        """Настраивает интерфейс"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Заголовок и фильтры
        header_layout = QHBoxLayout()

        title_label = QLabel("🃏 Все карточки")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        header_layout.addWidget(title_label)

        header_layout.addStretch()

        # Фильтр по типу
        self.type_filter = QComboBox()
        self.type_filter.addItem("Все", "all")
        self.type_filter.addItem("Свободные", "free")
        self.type_filter.addItem("Вопрос-Ответ", "qa")
        header_layout.addWidget(QLabel("Фильтр:"))
        header_layout.addWidget(self.type_filter)

        # Кнопка обновления
        refresh_btn = QPushButton("🔄 Обновить")
        header_layout.addWidget(refresh_btn)
        refresh_btn.clicked.connect(self._load_cards)

        layout.addLayout(header_layout)

        # Основная область
        main_layout = QHBoxLayout()

        # Список карточек
        self.card_list = QListWidget()
        self.card_list.setFixedWidth(300)
        main_layout.addWidget(self.card_list)

        # Область просмотра
        self.card_display = QTextEdit()
        self.card_display.setReadOnly(True)
        main_layout.addWidget(self.card_display, 1)

        layout.addLayout(main_layout)

    def _connect_signals(self):
        """Подключает сигналы"""
        self.card_list.itemClicked.connect(self._on_card_selected)
        self.type_filter.currentIndexChanged.connect(self._load_cards)

    def _load_cards(self):
        """Загружает карточки с учётом фильтра"""
        self.card_list.clear()

        cards = self._controller.get_all_cards()

        # Применяем фильтр
        filter_type = self.type_filter.currentData()
        if filter_type != 'all':
            cards = [c for c in cards if c.type == filter_type]

        if not cards:
            self.card_list.addItem("📭 Нет карточек")
            self.card_display.clear()
            return

        for card in cards:
            item = QListWidgetItem()

            # Получаем название темы
            from database.repositories.topic_repo import TopicRepository
            topic_repo = TopicRepository()
            topic = topic_repo.get_by_id(card.topic_id)
            topic_name = topic['name'] if topic else "—"

            if card.is_free:
                preview = card.content[:50] + "..." if len(card.content) > 50 else card.content
                item.setText(f"📝 [{topic_name}] {preview}")
            else:
                preview = card.question[:50] + "..." if len(card.question) > 50 else card.question
                item.setText(f"❓ [{topic_name}] {preview}")

            item.setData(Qt.UserRole, card.id)
            self.card_list.addItem(item)

    def _on_card_selected(self, item: QListWidgetItem):
        """Обработчик выбора карточки"""
        card_id = item.data(Qt.UserRole)
        card = self._controller.get_card(card_id)

        if not card:
            return

        self._current_card = card
        self.card_selected.emit(card_id)

        # Отображаем карточку
        if card.is_free:
            self.card_display.setPlainText(f"📝 Свободная карточка\n\n{card.content}")
        else:
            self.card_display.setPlainText(
                f"❓ Карточка вопрос-ответ\n\n"
                f"Вопрос:\n{card.question}\n\n"
                f"Ответ:\n{card.answer}"
            )

    def refresh(self):
        """Обновляет список"""
        self._load_cards()