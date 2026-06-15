from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QListWidget, QListWidgetItem, QTextEdit, QSplitter,
    QTreeWidget, QTreeWidgetItem, QFrame, QMessageBox, QComboBox, QCheckBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from .controller import FlashcardController
from datebase.db_manager import db


class TopicCheckboxTree(QTreeWidget):
    """
    Дерево тем с чекбоксами.
    Правило: можно выбирать только внутри ОДНОГО контейнера первого уровня.
    """
    selection_changed = Signal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setHeaderHidden(True)
        self.setContextMenuPolicy(Qt.NoContextMenu)
        self.itemChanged.connect(self._on_item_changed)

        self._active_first_level_id = None
        self._items_by_id = {}
        self._sort_mode = 'name_asc'
        self._updating_children = 0

        self._load_topics()

    def _on_item_changed(self, item: QTreeWidgetItem, column: int):
        if self._updating_children > 0:
            return

        first_level_id = self._get_first_level_container_id(item)

        if item.checkState(0) == Qt.Checked:
            if self._active_first_level_id is not None and self._active_first_level_id != first_level_id:
                self._updating_children += 1
                item.setCheckState(0, Qt.Unchecked)
                self._updating_children -= 1
                QMessageBox.warning(
                    self, "Ограничение выбора",
                    "Нельзя выбирать карточки из разных разделов первого уровня.\nСначала снимите галочки в текущем разделе."
                )
                return

            self._active_first_level_id = first_level_id

            if item.childCount() > 0:
                self._check_all_children(item, Qt.Checked)
        else:
            if item.childCount() > 0:
                self._check_all_children(item, Qt.Unchecked)

            if self._active_first_level_id is not None:
                if not self._has_checked_items_in_container(self._active_first_level_id):
                    self._active_first_level_id = None

        self._emit_selection()

    def _check_all_children(self, item: QTreeWidgetItem, state):
        self._updating_children += 1
        try:
            for i in range(item.childCount()):
                child = item.child(i)
                child.setCheckState(0, state)
                if child.childCount() > 0:
                    self._check_all_children(child, state)
        finally:
            self._updating_children -= 1

    def set_sort_mode(self, mode: str):
        self._sort_mode = mode

    def reload(self):
        self._load_topics()

    def _load_topics(self):
        self.clear()
        self._items_by_id.clear()
        self._active_first_level_id = None

        rows = db.fetchall("SELECT id, name, parent_id, created_at FROM topics")

        for row in rows:
            item = QTreeWidgetItem()
            item.setData(0, Qt.UserRole, row['id'])
            item.setText(0, row['name'])
            item.setCheckState(0, Qt.Unchecked)
            item.setData(0, Qt.UserRole + 1, row.get('created_at', ''))
            self._items_by_id[row['id']] = item

        root_items = []
        child_items = {}

        for row in rows:
            item = self._items_by_id[row['id']]
            parent_id = row.get('parent_id')

            if not parent_id or parent_id == 0 or parent_id not in self._items_by_id:
                root_items.append(item)
            else:
                if parent_id not in child_items:
                    child_items[parent_id] = []
                child_items[parent_id].append(item)

        def is_folder(item):
            return item.data(0, Qt.UserRole) in child_items

        reverse = self._sort_mode in ('name_desc', 'date_new')
        root_items.sort(key=lambda x: x.text(0).lower(), reverse=reverse)
        root_items.sort(key=is_folder)

        for parent_id, children in child_items.items():
            children.sort(key=lambda x: x.text(0).lower(), reverse=reverse)
            children.sort(key=lambda x: x.childCount() > 0)

        for item in root_items:
            self.addTopLevelItem(item)
            item_id = item.data(0, Qt.UserRole)

            if item_id in child_items:
                for child in child_items[item_id]:
                    item.addChild(child)
                    child_id = child.data(0, Qt.UserRole)
                    if child_id in child_items:
                        for grandchild in child_items[child_id]:
                            child.addChild(grandchild)

        for item in self._items_by_id.values():
            if item.childCount() > 0:
                self._style_as_folder(item)
            else:
                self._style_as_topic(item)

        self.collapseAll()

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
        text = item.text(0).replace(' ', '').replace('📝 ', '')
        item.setText(0, f"📝 {text}")

    def _get_first_level_container_id(self, item: QTreeWidgetItem) -> int:
        current = item
        while current.parent() is not None:
            current = current.parent()
        return current.data(0, Qt.UserRole)

    def _has_checked_items_in_container(self, container_id: int) -> bool:
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

    def _emit_selection(self):
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
    start_review_requested = Signal(list, bool, bool, bool, object)

    def __init__(self, controller: FlashcardController, parent=None):
        super().__init__(parent)
        self._controller = controller
        self._current_card = None
        self._selected_card_ids = set()
        self._setup_ui()
        self._connect_signals()
        self._subscribe_to_events()
        self._load_data()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        header_layout = QHBoxLayout()
        title_label = QLabel("🃏 Глобальные карточки")
        title_label.setFont(QFont("Arial", 16, QFont.Bold))
        header_layout.addWidget(title_label)

        header_layout.addStretch()

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

        main_splitter = QSplitter(Qt.Horizontal)

        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(8)

        left_layout.addWidget(QLabel("Выберите темы:"))

        tree_sort_widget = QWidget()
        tree_sort_layout = QHBoxLayout(tree_sort_widget)
        tree_sort_layout.setContentsMargins(0, 0, 0, 0)

        sort_label = QLabel("Сортировка:")
        sort_label.setStyleSheet("font-size: 12px; color: #555;")

        self.tree_sort_combo = QComboBox()
        self.tree_sort_combo.addItem("🔤 По имени (А-Я)", "name_asc")
        self.tree_sort_combo.addItem(" По имени (Я-А)", "name_desc")
        self.tree_sort_combo.addItem(" Новые сверху", "date_new")
        self.tree_sort_combo.addItem("📅 Старые сверху", "date_old")
        tree_sort_layout.addWidget(sort_label)
        tree_sort_layout.addWidget(self.tree_sort_combo, 1)

        left_layout.addWidget(tree_sort_widget)

        self.topic_tree = TopicCheckboxTree()
        left_layout.addWidget(self.topic_tree)

        main_splitter.addWidget(left_panel)

        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(10)

        self.analytics_frame = QFrame()
        self.analytics_frame.setFrameShape(QFrame.StyledPanel)
        self.analytics_frame.setStyleSheet("background-color: #f0f4f8; border-radius: 8px;")
        analytics_layout = QHBoxLayout(self.analytics_frame)

        self.stat_total = QLabel("Всего: 0")
        self.stat_new = QLabel("Новые: 0")
        self.stat_in_progress = QLabel("В процессе: 0")
        self.stat_mastered = QLabel("Выучено: 0")

        for lbl in (self.stat_total, self.stat_new, self.stat_in_progress, self.stat_mastered):
            lbl.setFont(QFont("Arial", 11, QFont.Bold))
            analytics_layout.addWidget(lbl)
        right_layout.addWidget(self.analytics_frame)

        self.card_list = QListWidget()
        self.card_list.setFixedHeight(250)
        self.card_list.setStyleSheet("""
            QListWidget {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 4px;
            }
            QListWidget::item {
                padding: 5px;
            }
            QListWidget::item:hover {
                background-color: #f0f8ff;
            }
            QListWidget::item:selected {
                background-color: #e3f2fd;
            }
        """)

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
        self.card_list.itemPressed.connect(self._on_card_selected)
        self.start_review_btn.clicked.connect(self._on_start_review_clicked)
        self.sort_combo.currentIndexChanged.connect(self._load_data)
        self.tree_sort_combo.currentIndexChanged.connect(self._on_tree_sort_changed)

    def _subscribe_to_events(self):
        from core.event_bus import event_bus

        event_bus.topic_created.connect(lambda tid: self.refresh())
        event_bus.topic_deleted.connect(lambda tid: self.refresh())
        event_bus.topic_updated.connect(lambda tid: self.refresh())

        event_bus.flashcard_created.connect(lambda cid: self._load_data())
        event_bus.flashcard_deleted.connect(lambda cid: self._load_data())

    def _load_data(self):
        selected_ids = self.topic_tree.get_selected_topic_ids()
        self._update_cards_and_analytics(selected_ids)

    def _on_topics_selection_changed(self, selected_ids: list):
        self._update_cards_and_analytics(selected_ids)

    def _get_card_status(self, card) -> str:
        progress = self._controller.get_card_progress(card.id)
        return progress['status']

    def _update_cards_and_analytics(self, topic_ids: list):
        if not topic_ids:
            self.card_list.clear()
            self.card_list.addItem(" Выберите хотя бы одну тему в дереве слева")
            self.card_display.clear()
            self._update_analytics_labels(0, 0, 0, 0)
            return

        cards = self._controller.get_cards_by_topics(topic_ids)

        sort_by = self.sort_combo.currentData()
        if sort_by == "topic":
            cards.sort(key=lambda c: self._get_topic_name(c.topic_id))
        elif sort_by == "status":
            cards.sort(key=lambda c: self._get_card_status(c))
        else:
            cards.sort(key=lambda c: c.created_at)

        total = len(cards)
        new_count = sum(1 for c in cards if self._get_card_status(c) == "new")
        in_progress_count = sum(1 for c in cards if self._get_card_status(c) == "in_progress")
        mastered_count = sum(1 for c in cards if self._get_card_status(c) == "mastered")

        self._update_analytics_labels(total, new_count, in_progress_count, mastered_count)

        self.card_list.clear()
        if not cards:
            self.card_list.addItem("📭 В выбранных темах нет карточек")
            self.card_display.clear()
            return

        self._selected_card_ids.clear()

        for card in cards:
            item = QListWidgetItem()
            topic_name = self._get_topic_name(card.topic_id)
            status = self._get_card_status(card)

            widget = QWidget()
            widget_layout = QHBoxLayout(widget)
            widget_layout.setContentsMargins(8, 5, 8, 5)
            widget_layout.setSpacing(10)

            checkbox = QCheckBox()
            checkbox.setChecked(True)
            checkbox.setStyleSheet("QCheckBox { spacing: 5px; }")
            self._selected_card_ids.add(card.id)
            checkbox.stateChanged.connect(
                lambda state, cid=card.id: self._on_card_checkbox_changed(cid, state)
            )
            checkbox.stateChanged.connect(lambda state, cid=card.id: self._on_card_checkbox_changed(cid, state))

            if status == "new":
                status_badge = "[ Новое]"
                status_color = "#2196f3"
            elif status == "in_progress":
                status_badge = "[🔄 В процессе]"
                status_color = "#ff9800"
            else:
                status_badge = "[✅ Выучено]"
                status_color = "#4caf50"

            if card.is_free:
                preview = card.content[:50] + "..." if len(card.content) > 50 else card.content
                text = f"{status_badge} 📝 [{topic_name}] {preview}"
            else:
                preview = card.question[:50] + "..." if len(card.question) > 50 else card.question
                text = f"{status_badge} ❓ [{topic_name}] {preview}"

            label = QLabel(text)
            label.setStyleSheet(f"color: {status_color}; font-size: 13px;")
            label.setWordWrap(True)

            widget_layout.addWidget(checkbox)
            widget_layout.addWidget(label, 1)

            widget.setMinimumHeight(35)
            widget.setMaximumHeight(50)

            item.setSizeHint(widget.sizeHint())
            self.card_list.addItem(item)
            self.card_list.setItemWidget(item, widget)

            item.setData(Qt.UserRole, card.id)

    def _update_analytics_labels(self, total: int, new_count: int, in_progress_count: int, mastered_count: int):
        self.stat_total.setText(f"📚 Всего: {total}")
        self.stat_new.setText(f"🆕 Новые: {new_count}")
        self.stat_in_progress.setText(f"🔄 В процессе: {in_progress_count}")
        self.stat_mastered.setText(f"✅ Выучено: {mastered_count}")

    def _get_topic_name(self, topic_id: int) -> str:
        row = db.fetchone("SELECT name FROM topics WHERE id = ?", (topic_id,))
        return row['name'] if row else "Без темы"

    def _on_card_selected(self, item: QListWidgetItem):
        """Показывает содержимое карточки без сброса списка и галочек"""
        card_id = item.data(Qt.UserRole)
        if not card_id:
            return

        card = self._controller.get_card(card_id)
        if not card:
            return

        self._current_card = card

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

    def _on_card_checkbox_changed(self, card_id: int, state: int):
        """Обработчик изменения чекбокса карточки"""
        if state == Qt.Checked:
            self._selected_card_ids.add(card_id)
        else:
            self._selected_card_ids.discard(card_id)

    def _on_start_review_clicked(self):
        topic_ids = self.topic_tree.get_selected_topic_ids()
        if not topic_ids:
            QMessageBox.warning(self, "Внимание", "Выберите хотя бы одну тему в дереве слева.")
            return

        card_ids = list(self._selected_card_ids) if self._selected_card_ids else None

        self.start_review_requested.emit(topic_ids, True, True, True, card_ids)

    def refresh(self):
        self.topic_tree.reset_selection()
        self.topic_tree.reload()
        self.topic_tree.collapseAll()
        self._load_data()

    def _on_tree_sort_changed(self):
        sort_mode = self.tree_sort_combo.currentData()
        if sort_mode:
            self.topic_tree.set_sort_mode(sort_mode)
            self.topic_tree.reload()