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
    """
    selection_changed = Signal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setHeaderHidden(True)
        self.setContextMenuPolicy(Qt.NoContextMenu)
        self.itemChanged.connect(self._on_item_changed)

        self._active_first_level_id = None
        self._items_by_id = {}
        self._sort_mode = 'name_asc'  # режим сортировки по умолчанию

        self._load_topics()

    def set_sort_mode(self, mode: str):
        """Устанавливает режим сортировки"""
        self._sort_mode = mode

    def reload(self):
        """Перезагружает дерево с текущей сортировкой"""
        self._load_topics()

    def _load_topics(self):
        """Загружает темы из БД с правильной сортировкой"""
        self.clear()
        self._items_by_id.clear()
        self._active_first_level_id = None

        # Получаем ВСЕ темы
        rows = db.fetchall("SELECT id, name, parent_id, created_at FROM topics")

        # Создаём элементы (пока не добавляем в дерево)
        for row in rows:
            item = QTreeWidgetItem()
            item.setData(0, Qt.UserRole, row['id'])
            item.setText(0, row['name'])
            item.setCheckState(0, Qt.Unchecked)
            item.setData(0, Qt.UserRole + 1, row.get('created_at', ''))
            self._items_by_id[row['id']] = item

        # Разделяем на корневые и дочерние
        root_items = []
        child_items = {}  # parent_id -> list of items

        for row in rows:
            item = self._items_by_id[row['id']]
            parent_id = row.get('parent_id')

            if not parent_id or parent_id == 0 or parent_id not in self._items_by_id:
                root_items.append(item)
            else:
                if parent_id not in child_items:
                    child_items[parent_id] = []
                child_items[parent_id].append(item)

        # Сортируем корневые элементы: папки (с детьми) выше тем
        def is_folder(item):
            return item.data(0, Qt.UserRole) in child_items

        def sort_key(item):
            if self._sort_mode == 'name_asc':
                return (0 if is_folder(item) else 1, item.text(0).lower())
            elif self._sort_mode == 'name_desc':
                return (0 if is_folder(item) else 1, item.text(0).lower(), True)  # True для reverse
            elif self._sort_mode == 'date_new':
                return (0 if is_folder(item) else 1, item.data(0, Qt.UserRole + 1) or '', True)
            elif self._sort_mode == 'date_old':
                return (0 if is_folder(item) else 1, item.data(0, Qt.UserRole + 1) or '')
            return (0 if is_folder(item) else 1, item.text(0).lower())

        # Сортируем
        reverse = self._sort_mode in ('name_desc', 'date_new')
        root_items.sort(key=lambda x: x.text(0).lower(), reverse=reverse)
        root_items.sort(key=is_folder)  # папки (False=0) перед темами (True=1)

        # Сортируем детей каждого родителя
        for parent_id, children in child_items.items():
            children.sort(key=lambda x: x.text(0).lower(), reverse=reverse)
            children.sort(key=lambda x: x.childCount() > 0)  # папки перед темами

        # Добавляем корневые элементы в дерево
        for item in root_items:
            self.addTopLevelItem(item)
            item_id = item.data(0, Qt.UserRole)

            # Добавляем детей если есть
            if item_id in child_items:
                for child in child_items[item_id]:
                    item.addChild(child)
                    # Рекурсивно добавляем внуков
                    child_id = child.data(0, Qt.UserRole)
                    if child_id in child_items:
                        for grandchild in child_items[child_id]:
                            child.addChild(grandchild)

        # Стилизация
        for item in self._items_by_id.values():
            if item.childCount() > 0:
                self._style_as_folder(item)
            else:
                self._style_as_topic(item)

        self.collapseAll()

    def _sort_tree_items(self):
        """Сортирует элементы дерева: папки выше тем"""

        def sort_children(parent_item: QTreeWidgetItem):
            if parent_item.childCount() == 0:
                return

            # Забираем детей (takeChild НЕ удаляет C++ объект, только открепляет)
            children = []
            while parent_item.childCount() > 0:
                children.append(parent_item.takeChild(0))

            folders = [c for c in children if c.childCount() > 0]
            topics = [c for c in children if c.childCount() == 0]

            folders.sort(key=lambda x: self._get_sort_key(x))
            topics.sort(key=lambda x: self._get_sort_key(x))

            for folder in folders:
                parent_item.addChild(folder)
                sort_children(folder)  # рекурсия для вложенных папок

            for topic in topics:
                parent_item.addChild(topic)

        # Сортируем корневые элементы
        root_items = []
        while self.topLevelItemCount() > 0:
            root_items.append(self.takeTopLevelItem(0))

        folders = [item for item in root_items if item.childCount() > 0]
        topics = [item for item in root_items if item.childCount() == 0]

        folders.sort(key=lambda x: self._get_sort_key(x))
        topics.sort(key=lambda x: self._get_sort_key(x))

        for folder in folders:
            self.addTopLevelItem(folder)
            sort_children(folder)

        for topic in topics:
            self.addTopLevelItem(topic)

    def _get_sort_key(self, item: QTreeWidgetItem):
        """Ключ сортировки для элемента"""
        if self._sort_mode in ('name_asc', 'name_desc'):
            return item.text(0).lower()
        elif self._sort_mode in ('date_new', 'date_old'):
            return item.data(0, Qt.UserRole + 1) or ''
        return item.text(0).lower()

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

    def _on_item_changed(self, item: QTreeWidgetItem, column: int):
        first_level_id = self._get_first_level_container_id(item)

        if item.checkState(0) == Qt.Checked:
            if self._active_first_level_id is not None and self._active_first_level_id != first_level_id:
                item.setCheckState(0, Qt.Unchecked)
                QMessageBox.warning(
                    self, "Ограничение выбора",
                    "Нельзя выбирать карточки из разных разделов первого уровня.\nСначала снимите галочки в текущем разделе."
                )
                return
            self._active_first_level_id = first_level_id
        else:
            if self._active_first_level_id is not None:
                if not self._has_checked_items_in_container(self._active_first_level_id):
                    self._active_first_level_id = None

        self._emit_selection()

    def _emit_selection(self):
        selected_ids = [item.data(0, Qt.UserRole) for item in self._items_by_id.values() if
                        item.checkState(0) == Qt.Checked]
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

        # --- ЛЕВАЯ ЧАСТЬ: Дерево тем + Сортировка ---
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(8)

        left_layout.addWidget(QLabel("Выберите темы:"))

        # 🆕 ПЛАШКА СОРТИРОВКИ ДЕРЕВА
        tree_sort_widget = QWidget()
        tree_sort_layout = QHBoxLayout(tree_sort_widget)
        tree_sort_layout.setContentsMargins(0, 0, 0, 0)

        sort_label = QLabel("Сортировка:")
        sort_label.setStyleSheet("font-size: 12px; color: #555;")

        self.tree_sort_combo = QComboBox()
        self.tree_sort_combo.addItem("🔤 По имени (А-Я)", "name_asc")
        self.tree_sort_combo.addItem("🔽 По имени (Я-А)", "name_desc")
        self.tree_sort_combo.addItem(" Новые сверху", "date_new")
        self.tree_sort_combo.addItem("📅 Старые сверху", "date_old")
        tree_sort_layout.addWidget(sort_label)
        tree_sort_layout.addWidget(self.tree_sort_combo, 1)

        left_layout.addWidget(tree_sort_widget)

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
        self.tree_sort_combo.currentIndexChanged.connect(self._on_tree_sort_changed)

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

    def _on_tree_sort_changed(self):
        """Обработчик смены сортировки дерева"""
        sort_mode = self.tree_sort_combo.currentData()
        if sort_mode:
            self.topic_tree.set_sort_mode(sort_mode)
            self.topic_tree.reload()  # перестроим дерево с новой сортировкой