# modules/flashcards/view.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QListWidget, QListWidgetItem, QStackedWidget, QTextEdit,
    QDialog
)
from PySide6.QtCore import Qt, Signal
import logging

from modules.flashcards.controller import FlashcardController
from modules.flashcards.dialogs import CardTypeDialog
from widgets import SilentMessageBox

# Настройка логирования
logger = logging.getLogger(__name__)


class FlashcardsView(QWidget):
    """Экран для просмотра и управления карточками."""

    card_created = Signal(int)
    card_deleted = Signal(int)

    def __init__(self, controller: FlashcardController, parent=None):
        super().__init__(parent)
        self._controller = controller
        self._current_topic_id = None
        self._current_card = None
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        self.title_label = QLabel("🃏 Карточки")
        self.title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(self.title_label)

        button_layout = QHBoxLayout()
        self.new_btn = QPushButton("➕ Новая карточка")
        self.delete_btn = QPushButton("🗑️ Удалить")
        self.edit_btn = QPushButton("✏️ Редактировать")
        button_layout.addWidget(self.new_btn)
        button_layout.addWidget(self.delete_btn)
        button_layout.addWidget(self.edit_btn)
        button_layout.addStretch()
        layout.addLayout(button_layout)

        main_layout = QHBoxLayout()
        self.card_list = QListWidget()
        self.card_list.setFixedWidth(250)
        main_layout.addWidget(self.card_list)

        self.stack = QStackedWidget()
        empty_widget = QWidget()
        empty_layout = QVBoxLayout(empty_widget)
        empty_label = QLabel("Нет карточек в этой теме")
        empty_label.setAlignment(Qt.AlignCenter)
        empty_layout.addWidget(empty_label)
        self.stack.addWidget(empty_widget)

        self.card_widget = QWidget()
        card_layout = QVBoxLayout(self.card_widget)
        self.card_display = QTextEdit()
        self.card_display.setReadOnly(True)
        self.card_display.setMinimumHeight(300)
        card_layout.addWidget(self.card_display)
        self.show_answer_btn = QPushButton("Показать ответ")
        self.show_answer_btn.hide()
        card_layout.addWidget(self.show_answer_btn)
        self.stack.addWidget(self.card_widget)

        main_layout.addWidget(self.stack, 1)
        layout.addLayout(main_layout)

    def _connect_signals(self):
        self.new_btn.clicked.connect(self._on_new_card)
        self.delete_btn.clicked.connect(self._on_delete_card)
        self.edit_btn.clicked.connect(self._on_edit_card)
        self.card_list.itemClicked.connect(self._on_card_selected)
        self.show_answer_btn.clicked.connect(self._on_show_answer)

    def set_topic(self, topic_id: int):
        self._current_topic_id = topic_id
        self._load_cards()

    def _load_cards(self):
        try:
            self.card_list.clear()
            if not self._current_topic_id:
                return

            cards = self._controller.get_cards_by_topic(self._current_topic_id)
            if not cards:
                self.stack.setCurrentIndex(0)
                return

            self.stack.setCurrentIndex(1)
            for card in cards:
                item = QListWidgetItem()
                if card.is_free:
                    preview = card.content[:50] + "..." if len(card.content) > 50 else card.content
                    item.setText(f"📝 {preview}")
                else:
                    preview = card.question[:50] + "..." if len(card.question) > 50 else card.question
                    item.setText(f"❓ {preview}")
                item.setData(Qt.UserRole, card.id)
                self.card_list.addItem(item)
        except Exception as e:
            logger.error(f"Ошибка загрузки карточек для темы {self._current_topic_id}: {e}", exc_info=True)
            SilentMessageBox.warning(self, "Ошибка", f"Не удалось загрузить карточки: {e}")

    def _on_new_card(self):
        try:
            if not self._current_topic_id:
                SilentMessageBox.warning(self, "Ошибка", "Сначала выберите тему")
                return

            dialog = CardTypeDialog(self)
            if dialog.exec() == QDialog.Accepted:
                data = dialog.get_card_data()
                if data['type'] == 'free':
                    card_id = self._controller.create_free_card(self._current_topic_id, data['content'])
                else:
                    card_id = self._controller.create_qa_card(self._current_topic_id, data['question'], data['answer'])

                if card_id:
                    self._load_cards()
                    self.card_created.emit(card_id)
                    SilentMessageBox.information(self, "Успех", "Карточка создана")
        except Exception as e:
            logger.error(f"Ошибка создания карточки: {e}", exc_info=True)
            SilentMessageBox.warning(self, "Ошибка", f"Не удалось создать карточку: {e}")

    def _on_delete_card(self):
        try:
            current = self.card_list.currentItem()
            if not current:
                SilentMessageBox.information(self, "Информация", "Выберите карточку для удаления")
                return

            card_id = current.data(Qt.UserRole)
            card = self._controller.get_card(card_id)
            if not card:
                logger.warning(f"Карточка {card_id} не найдена")
                return

            reply = SilentMessageBox.question(
                self, "Подтверждение удаления",
                f"Удалить карточку?\n\n{card.display_front[:100]}"
            )

            if reply == SilentMessageBox.Yes:
                if self._controller.delete_card(card_id):
                    self._load_cards()
                    self.card_deleted.emit(card_id)
                    self._current_card = None
                    self.card_display.clear()
        except Exception as e:
            logger.error(f"Ошибка удаления карточки: {e}", exc_info=True)
            SilentMessageBox.warning(self, "Ошибка", f"Не удалось удалить карточку: {e}")

    def _on_edit_card(self):
        try:
            current = self.card_list.currentItem()
            if not current:
                SilentMessageBox.information(self, "Информация", "Выберите карточку для редактирования")
                return
            SilentMessageBox.information(self, "Информация", "Редактирование карточек будет в следующей версии")
        except Exception as e:
            logger.error(f"Ошибка редактирования карточки: {e}", exc_info=True)

    def _on_card_selected(self, item: QListWidgetItem):
        try:
            card_id = item.data(Qt.UserRole)
            self._current_card = self._controller.get_card(card_id)
            if not self._current_card:
                logger.warning(f"Карточка {card_id} не найдена при выборе")
                return

            if self._current_card.is_free:
                self.card_display.setPlainText(self._current_card.content)
                self.show_answer_btn.hide()
            else:
                self.card_display.setPlainText(f"❓ {self._current_card.question}\n\n[Скрыто]\n\nНажмите «Показать ответ»")
                self.show_answer_btn.show()
        except Exception as e:
            logger.error(f"Ошибка выбора карточки: {e}", exc_info=True)

    def _on_show_answer(self):
        try:
            if self._current_card and self._current_card.is_qa:
                self.card_display.setPlainText(
                    f"❓ {self._current_card.question}\n\n"
                    f"📝 Ответ:\n{self._current_card.answer}"
                )
                self.show_answer_btn.hide()
        except Exception as e:
            logger.error(f"Ошибка показа ответа: {e}", exc_info=True)

    def refresh(self):
        self._load_cards()