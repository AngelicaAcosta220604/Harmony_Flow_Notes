from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QListWidget, QListWidgetItem, QTextEdit, QSplitter,
    QTreeWidget, QTreeWidgetItem, QFrame, QMessageBox, QComboBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from .controller import FlashcardController
from datebase.db_manager import db


class TopicCheckboxTree(QTreeWidget):
    """
    Дерево тем с чекбоксами.
    Правило: можно выбирать только внутри ОДНОГО контейнера первого уровня.
    Контейнер первого уровня - это либо папка (содержит children), либо тема в корне.
    """
    selection_changed = Signal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setHeaderHidden(True)
        self.setContextMenuPolicy(Qt.NoContextMenu)
        self.itemChanged.connect(self._on_item_changed)

        self._active_first_level_id = None  # ID активного контейнера первого уровня
        self._items_by_id = {}

        self._load_topics()

    def _load_topics(self):
        """Загружает темы из БД, строя правильную иерархию"""
        self.clear()
        self._items_by_id.clear()
        self._active_first_level_id = None

        rows = db.fetchall("SELECT id, name, parent_id FROM topics ORDER BY parent_id, name")

        # 1. Создаем все элементы
        for row in rows:
            item = QTreeWidgetItem()
            item.setData(0, Qt.UserRole, row['id'])
            item.setText(0, row['name'])
            item.setCheckState(0, Qt.Unchecked)
            self._items_by_id[row['id']] = item

        # 2. Строим иерархию
        for row in rows:
            item = self._items_by_id[row['id']]
            parent_id = row.get('parent_id')

            if not parent_id or parent_id == 0 or parent_id not in self._items_by_id:
                self.addTopLevelItem(item)
            else:
                parent_item = self._items_by_id[parent_id]
                parent_item.addChild(item)

        # 3. Стилизация
        for item in self._items_by_id.values():
            if item.childCount() > 0:
                self._style_as_folder(item)
            else:
                self._style_as_topic(item)

        self.expandAll()

    def _style_as_folder(self, item: QTreeWidgetItem):
        font = item.font(0)
        font.setBold(True)
        item.setFont(0, font)
        text = item.text(0).replace('📁 ', '').replace('📝 ', '')
        item.setText(0, f"📁 {text}")

    def _style_as_topic(self, item: QTreeWidgetItem):
        font = item.font(0)
        font.setBold(False)
        item.setFont(0, font)
        text = item.text(0).replace('📁 ', '').replace('📝 ', '')
        item.setText(0, f"📝 {text}")

    def _get_first_level_container_id(self, item: QTreeWidgetItem) -> int:
        """
        Возвращает ID контейнера первого уровня для данного элемента.
        Если элемент сам на первом уровне - возвращает его ID.
        Если элемент вложен - поднимается до первого уровня.
        """
        current = item
        while current.parent() is not None:
            current = current.parent()
        return current.data(0, Qt.UserRole)

    def _has_checked_items_in_container(self, container_id: int) -> bool:
        """Проверяет, есть ли выбранные элементы в контейнере"""
        container_item = self._items_by_id.get(container_id)
        if not container_item:
            return False

        def check_recursive(it: QTreeWidgetItem) -> bool:
            if it.checkState(0) == Qt.Checked:
                return True
            for i in range(it.childCount()):
                if check_recursive(it.child(i)):
                    return True
            return False

        return check_recursive(container_item)

    def _get_all_items_in_container(self, container_id: int) -> list:
        """Возвращает все элементы в контейнере (рекурсивно)"""
        result = []
        container_item = self._items_by_id.get(container_id)
        if not container_item:
            return result

        def collect_recursive(it: QTreeWidgetItem):
            result.append(it)
            for i in range(it.childCount()):
                collect_recursive(it.child(i))

        collect_recursive(container_item)
        return result

    def _on_item_changed(self, item: QTreeWidgetItem, column: int):
        """Логика ограничения выбора одним контейнером первого уровня"""
        first_level_id = self._get_first_level_container_id(item)

        if item.checkState(0) == Qt.Checked:
            # Пользователь пытается выбрать элемент

            # Если уже есть активный контейнер
            if self._active_first_level_id is not None:
                # Проверяем, тот ли это контейнер
                if self._active_first_level_id != first_level_id:
                    # КОНФЛИКТ: пытаемся выбрать в ДРУГОМ контейнере первого уровня!
                    item.setCheckState(0, Qt.Unchecked)
                    QMessageBox.warning(
                        self,
                        "Ограничение выбора",
                        "Нельзя выбирать карточки из разных разделов первого уровня.\n\n"
                        "Например, нельзя смешивать:\n"
                        "• Папку 'ПДД' и папку 'Испанский'\n"
                        "• Папку 'Учёба' и тему 'Хобби' (если она в корне)\n\n"
                        "Сначала снимите все галочки в текущем разделе."
                    )
                    return

            # Всё ок, запоминаем контейнер
            self._active_first_level_id = first_level_id

            # Если это папка первого уровня - разворачиваем её
            first_level_item = self._items_by_id.get(first_level_id)
            if first_level_item:
                first_level_item.setExpanded(True)

        else:
            # Пользователь снял галочку
            if self._active_first_level_id is not None:
                # Проверяем, остались ли ещё выбранные в этом контейнере
                if not self._has_checked_items_in_container(self._active_first_level_id):
                    self._active_first_level_id = None  # Освобождаем

        self._emit_selection()

    def _emit_selection(self):
        """Собирает ID всех отмеченных тем"""
        selected_ids = []
        for item in self._items_by_id.values():
            if item.checkState(0) == Qt.Checked:
                selected_ids.append(item.data(0, Qt.UserRole))

        self.selection_changed.emit(selected_ids)

    def get_selected_topic_ids(self) -> list:
        return [item.data(0, Qt.UserRole) for item in self._items_by_id.values() if item.checkState(0) == Qt.Checked]

    def reset_selection(self):
        for item in self._items_by_id.values():
            item.setCheckState(0, Qt.Unchecked)
        self._active_first_level_id = None

class GlobalCardsView(QWidget):
    card_selected = Signal(int)
    start_review_requested = Signal(list, bool, bool, bool)

    def __init__(self, controller: FlashcardController, parent=None):
        super().__init__(parent)
        self._controller = controller
        self._current_card = None
        self._setup_ui()
        self._connect_signals()
        self._load_data()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        # Заголовок и сортировка
        header_layout = QHBoxLayout()
        title_label = QLabel("🃏 Глобальные карточки")
        title_label.setFont(QFont("Arial", 16, QFont.Bold))
        header_layout.addWidget(title_label)

        header_layout.addStretch()

        # Сортировка
        self.sort_combo = QComboBox()
        self.sort_combo.addItem("По дате создания", "created_at")
        self.sort_combo.addItem("По названию темы", "topic")
        self.sort_combo.addItem("По статусу", "status")
        header_layout.addWidget(QLabel("Сортировка:"))
        header_layout.addWidget(self.sort_combo)

        self.start_review_btn = QPushButton("▶ Начать повторение")
        self.start_review_btn.setStyleSheet(
            "background-color: #4caf50; color: white; font-weight: bold; "
            "padding: 8px 16px; border-radius: 6px; font-size: 14px;"
        )
        header_layout.addWidget(self.start_review_btn)
        layout.addLayout(header_layout)

        # Сплиттер
        main_splitter = QSplitter(Qt.Horizontal)

        # Левая часть: Дерево
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.addWidget(QLabel("Выберите темы:"))
        self.topic_tree = TopicCheckboxTree()
        left_layout.addWidget(self.topic_tree)
        main_splitter.addWidget(left_panel)

        # Правая часть: Аналитика + Список
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(10)

        # Аналитика
        self.analytics_frame = QFrame()
        self.analytics_frame.setFrameShape(QFrame.StyledPanel)
        self.analytics_frame.setStyleSheet("background-color: #f0f4f8; border-radius: 8px;")
        analytics_layout = QHBoxLayout(self.analytics_frame)

        self.stat_total = QLabel("Всего: 0")
        self.stat_new = QLabel("Новые: 0")
        self.stat_review = QLabel("На повторении: 0")

        for lbl in (self.stat_total, self.stat_new, self.stat_review):
            lbl.setFont(QFont("Arial", 11, QFont.Bold))
            analytics_layout.addWidget(lbl)
        right_layout.addWidget(self.analytics_frame)

        # Список карточек
        self.card_list = QListWidget()
        self.card_list.setFixedHeight(250)

        self.card_display = QTextEdit()
        self.card_display.setReadOnly(True)
        self.card_display.setStyleSheet("font-size: 14px; padding: 10px;")

        right_layout.addWidget(self.card_list)
        right_layout.addWidget(self.card_display)
        main_splitter.addWidget(right_panel)

        main_splitter.setSizes([350, 850])
        layout.addWidget(main_splitter, 1)

    def _connect_signals(self):
        self.topic_tree.selection_changed.connect(self._on_topics_selection_changed)
        self.card_list.itemClicked.connect(self._on_card_selected)
        self.start_review_btn.clicked.connect(self._on_start_review_clicked)
        self.sort_combo.currentIndexChanged.connect(self._load_data)

    def _load_data(self):
        selected_ids = self.topic_tree.get_selected_topic_ids()
        self._update_cards_and_analytics(selected_ids)

    def _on_topics_selection_changed(self, selected_ids: list):
        self._update_cards_and_analytics(selected_ids)

    def _get_card_status(self, card) -> str:
        """
        Определяет статус карточки.
        Если в твоей БД есть поля interval, status или next_review, замени логику здесь.
        """
        # Заглушка: если есть поле interval, используем его. Иначе считаем всё "Новым".
        interval = getattr(card, 'interval', 0)
        if interval > 0:
            return "Выучено"
        # Если бы было поле status: return card.status
        return "Новое"

    def _update_cards_and_analytics(self, topic_ids: list):
        if not topic_ids:
            self.card_list.clear()
            self.card_list.addItem("📭 Выберите хотя бы одну тему в дереве слева")
            self.card_display.clear()
            self.stat_total.setText("Всего: 0")
            self.stat_new.setText("Новые: 0")
            self.stat_review.setText("На повторении: 0")
            return

        cards = self._controller.get_cards_by_topics(topic_ids)

        # Сортировка
        sort_by = self.sort_combo.currentData()
        if sort_by == "topic":
            # Сортируем по имени темы (упрощенно)
            cards.sort(key=lambda c: self._get_topic_name(c.topic_id))
        elif sort_by == "status":
            cards.sort(key=lambda c: self._get_card_status(c))
        else:
            cards.sort(key=lambda c: c.created_at)

        total = len(cards)
        new_count = sum(1 for c in cards if self._get_card_status(c) == "Новое")
        review_count = total - new_count

        self.stat_total.setText(f"📚 Всего: {total}")
        self.stat_new.setText(f"🆕 Новые: {new_count}")
        self.stat_review.setText(f"🔄 На повторении: {review_count}")

        self.card_list.clear()
        if not cards:
            self.card_list.addItem("📭 В выбранных темах нет карточек")
            self.card_display.clear()
            return

        for card in cards:
            item = QListWidgetItem()
            topic_name = self._get_topic_name(card.topic_id)
            status = self._get_card_status(card)

            # Цветной бейдж статуса
            if status == "Новое":
                status_badge = "[🆕 Новое]"
            elif status == "Выучено":
                status_badge = "[✅ Выучено]"
            else:
                status_badge = "[🔄 В процессе]"

            if card.is_free:
                preview = card.content[:50] + "..." if len(card.content) > 50 else card.content
                item.setText(f"{status_badge} 📝 [{topic_name}] {preview}")
            else:
                preview = card.question[:50] + "..." if len(card.question) > 50 else card.question
                item.setText(f"{status_badge} ❓ [{topic_name}] {preview}")

            item.setData(Qt.UserRole, card.id)
            self.card_list.addItem(item)

    def _get_topic_name(self, topic_id: int) -> str:
        row = db.fetchone("SELECT name FROM topics WHERE id = ?", (topic_id,))
        return row['name'] if row else "Без темы"

    def _on_card_selected(self, item: QListWidgetItem):
        card_id = item.data(Qt.UserRole)
        card = self._controller.get_card(card_id)
        if not card:
            return

        self._current_card = card
        self.card_selected.emit(card_id)

        status = self._get_card_status(card)
        status_html = f"<span style='color: #4caf50; font-weight: bold;'>{status}</span>"

        if card.is_free:
            self.card_display.setHtml(
                f"<h3>📝 Свободная карточка <small>({status_html})</small></h3>"
                f"<hr><p style='font-size: 16px;'>{card.content}</p>"
            )
        else:
            self.card_display.setHtml(
                f"<h3>❓ Карточка Вопрос-Ответ <small>({status_html})</small></h3>"
                f"<p><b>Вопрос:</b><br>{card.question}</p>"
                f"<hr>"
                f"<p><b>Ответ:</b><br>{card.answer}</p>"
            )

    def _on_start_review_clicked(self):
        topic_ids = self.topic_tree.get_selected_topic_ids()
        if not topic_ids:
            QMessageBox.warning(self, "Внимание", "Выберите хотя бы одну тему в дереве слева.")
            return

        self.start_review_requested.emit(topic_ids, True, True, True)

    def refresh(self):
        self.topic_tree.reset_selection()
        self.topic_tree._load_topics()
        self._load_data()