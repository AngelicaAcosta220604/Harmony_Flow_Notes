from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QListWidget, QListWidgetItem, QTextEdit, QComboBox,
    QMessageBox, QDialog, QCheckBox, QDialogButtonBox
)
from PySide6.QtCore import Qt, Signal

from .controller import FlashcardController
from datebase.db_manager import db


class ReviewSetupDialog(QDialog):
    """Диалог для выбора тем и фильтров перед началом повторения"""

    def __init__(td, parent=None):
        super().__init__(parent)
        td.setWindowTitle("Настройка повторения")
        td.resize(400, 500)

        layout = QVBoxLayout(td)

        # Список тем с чекбоксами
        td.topic_list = QListWidget()
        td.topic_list.setSelectionMode(QListWidget.NoSelection)

        # Получаем все темы из БД
        rows = db.fetchall("SELECT id, name FROM topics ORDER BY name")
        for row in rows:
            item = QListWidgetItem(row['name'])
            item.setCheckState(Qt.Checked)  # По умолчанию все выбраны
            item.setData(Qt.UserRole, row['id'])
            td.topic_list.addItem(item)

        layout.addWidget(QLabel("Выберите темы для повторения:"))
        layout.addWidget(td.topic_list)

        # Фильтры
        td.cb_free = QCheckBox("Включить свободные карточки")
        td.cb_free.setChecked(True)

        td.cb_qa = QCheckBox("Включить карточки Вопрос-Ответ")
        td.cb_qa.setChecked(True)

        td.cb_skip = QCheckBox("Пропускать уже выученные (с интервалом > 0)")
        td.cb_skip.setChecked(True)

        filters_layout = QVBoxLayout()
        filters_layout.addWidget(td.cb_free)
        filters_layout.addWidget(td.cb_qa)
        filters_layout.addWidget(td.cb_skip)

        layout.addLayout(filters_layout)

        # Кнопки ОК / Отмена
        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn_box.accepted.connect(td.accept)
        btn_box.rejected.connect(td.reject)
        layout.addWidget(btn_box)

    def get_data(td):
        """Возвращает кортеж: (topic_ids, include_free, include_qa, skip_reviewed)"""
        topic_ids = []
        for i in range(td.topic_list.count()):
            item = td.topic_list.item(i)
            if item.checkState() == Qt.Checked:
                topic_ids.append(item.data(Qt.UserRole))

        return (
            topic_ids,
            td.cb_free.isChecked(),
            td.cb_qa.isChecked(),
            td.cb_skip.isChecked()
        )


class GlobalCardsView(QWidget):
    """
    Экран для просмотра карточек из всех тем
    """
    card_selected = Signal(int)  # (card_id)
    start_review_requested = Signal(list, bool, bool, bool)  # (topic_ids, include_free, include_qa, skip_reviewed)

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

        # Кнопка начала повторения (НОВАЯ)
        self.start_review_btn = QPushButton("▶ Начать повторение")
        self.start_review_btn.setStyleSheet(
            "background-color: #4caf50; color: white; font-weight: bold; "
            "padding: 6px 12px; border-radius: 4px;"
        )
        header_layout.addWidget(self.start_review_btn)

        # Фильтр по типу
        self.type_filter = QComboBox()
        self.type_filter.addItem("Все", "all")
        self.type_filter.addItem("Свободные", "free")
        self.type_filter.addItem("Вопрос-Ответ", "qa")
        header_layout.addWidget(QLabel("Фильтلر:"))
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
        self.start_review_btn.clicked.connect(self._on_start_review_clicked)  # НОВОЕ

    def _on_start_review_clicked(self):
        """Открывает диалог настройки и запускает повторение"""
        dialog = ReviewSetupDialog(self)
        if dialog.exec() == QDialog.Accepted:
            topic_ids, include_free, include_qa, skip_reviewed = dialog.get_data()

            if not topic_ids:
                QMessageBox.warning(self, "Внимание", "Выберите хотя бы одну тему для повторения.")
                return

            # Эмитим сигнал, который ловит main_window.py
            self.start_review_requested.emit(topic_ids, include_free, include_qa, skip_reviewed)

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
            from datebase.repositories.topic_repo import TopicRepository
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