# modules/flashcards/global_view.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QListWidget, QListWidgetItem, QTextEdit, QSplitter,
    QTreeWidget, QTreeWidgetItem, QFrame, QMessageBox, QComboBox, QCheckBox,
    QScrollArea, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QIcon, QPixmap, QFont, QColor
import logging

from utils.resource_paths import get_resource_path
from .controller import FlashcardController
from datebase.db_manager import db

# Настройка логирования
logger = logging.getLogger(__name__)


class TopicCheckboxTree(QTreeWidget):
    """
    Дерево тем с чекбоксами.
    """
    selection_changed = Signal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setHeaderHidden(True)
        self.setContextMenuPolicy(Qt.NoContextMenu)
        self.itemChanged.connect(self._on_item_changed)
        self.setStyleSheet("""
            QTreeWidget {
                background-color: transparent;
                border: none;
                outline: none;
            }
            QTreeWidget::item {
                padding: 6px;
                border-radius: 6px;
            }
            QTreeWidget::item:hover {
                background-color: #F9FAFB;
            }
        """)

        self._active_first_level_id = None
        self._items_by_id = {}
        self._sort_mode = 'name_asc'
        self._updating_children = 0

        self._load_topics()

    def _on_item_changed(self, item: QTreeWidgetItem, column: int):
        try:
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
        except Exception as e:
            logger.error(f"Ошибка обработки изменения элемента дерева: {e}", exc_info=True)

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
        try:
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
            logger.debug(f"Загружено {len(rows)} тем в дерево")
        except Exception as e:
            logger.error(f"Ошибка загрузки тем в дерево: {e}", exc_info=True)

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
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("background-color: transparent; border: none;")

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setSpacing(20)

        # ========== ЗАГОЛОВОК (белая плашка) ==========
        header_widget = QWidget()
        header_widget.setStyleSheet("""
            QWidget {
                background-color: #FFFFFF;
                border-radius: 16px;
                border: none;
            }
        """)
        header_widget.setFixedHeight(80)

        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(20, 0, 20, 0)
        header_layout.setSpacing(12)
        header_layout.setAlignment(Qt.AlignCenter)

        header_icon = QLabel()
        # ✅ ИСПРАВЛЕНО: используем get_resource_path
        header_pixmap = QPixmap(str(get_resource_path("resources/icons/flashcard1.png")))
        if not header_pixmap.isNull():
            header_pixmap = header_pixmap.scaled(32, 32, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            header_icon.setPixmap(header_pixmap)
        header_layout.addWidget(header_icon)

        header_title = QLabel("Глобальные карточки")
        header_title.setStyleSheet("font-size: 20px; font-weight: bold; color: #1F2937;")
        header_layout.addWidget(header_title)

        content_layout.addWidget(header_widget)

        # ========== ТРИ ПЛАШКИ В РЯД ==========
        three_cols_layout = QHBoxLayout()
        three_cols_layout.setSpacing(20)

        # ----- ПЛАШКА 1: Выбор тем (левая) -----
        left_widget = QFrame()
        left_widget.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border-radius: 16px;
                border: none;
            }
        """)
        left_widget.setMinimumHeight(350)
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(16, 16, 16, 16)
        left_layout.setSpacing(12)

        left_title = QLabel("Выберите темы")
        left_title.setStyleSheet("font-weight: 600; color: #1F2937; font-size: 14px;")
        left_layout.addWidget(left_title)

        # Сортировка дерева
        tree_sort_layout = QHBoxLayout()
        sort_label = QLabel("Сортировка тем:")
        sort_label.setStyleSheet("color: #6B7280; font-size: 12px;")
        self.tree_sort_combo = QComboBox()
        self.tree_sort_combo.addItem("По имени (А-Я)", "name_asc")
        self.tree_sort_combo.addItem("По имени (Я-А)", "name_desc")
        self.tree_sort_combo.addItem("Новые сверху", "date_new")
        self.tree_sort_combo.addItem("Старые сверху", "date_old")
        self.tree_sort_combo.setStyleSheet("""
            QComboBox {
                background-color: #F0F4F8;
                border: 1px solid #E6EEF6;
                border-radius: 8px;
                padding: 4px 8px;
                font-size: 12px;
                min-width: 130px;
            }
        """)
        tree_sort_layout.addWidget(sort_label)
        tree_sort_layout.addWidget(self.tree_sort_combo)
        tree_sort_layout.addStretch()
        left_layout.addLayout(tree_sort_layout)

        self.topic_tree = TopicCheckboxTree()
        left_layout.addWidget(self.topic_tree)

        three_cols_layout.addWidget(left_widget, 1)

        # ----- ПЛАШКА 2: Карточки (центральная) -----
        center_widget = QFrame()
        center_widget.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border-radius: 16px;
                border: none;
            }
        """)
        center_widget.setMinimumHeight(350)
        center_layout = QVBoxLayout(center_widget)
        center_layout.setContentsMargins(16, 16, 16, 16)
        center_layout.setSpacing(12)

        center_title = QLabel("Карточки в выбранных темах")
        center_title.setStyleSheet("font-weight: 600; color: #1F2937; font-size: 14px;")
        center_layout.addWidget(center_title)

        self.card_list = QListWidget()
        self.card_list.setStyleSheet("""
            QListWidget {
                background-color: #F9FAFB;
                border-radius: 12px;
                border: none;
                min-height: 250px;
            }
            QListWidget::item {
                padding: 6px;
                border-radius: 6px;
            }
            QListWidget::item:hover {
                background-color: #F0F4F8;
            }
        """)
        center_layout.addWidget(self.card_list)

        three_cols_layout.addWidget(center_widget, 1)

        # ----- ПЛАШКА 3: Сортировка и кнопка (правая) -----
        right_widget = QFrame()
        right_widget.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border-radius: 16px;
                border: none;
            }
        """)
        right_widget.setMinimumHeight(350)
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(16, 16, 16, 16)
        right_layout.setSpacing(16)

        # Сортировка карточек
        sort_section = QWidget()
        sort_section_layout = QVBoxLayout(sort_section)
        sort_section_layout.setSpacing(8)
        sort_section_title = QLabel("Сортировка карточек")
        sort_section_title.setStyleSheet("font-weight: 600; color: #1F2937; font-size: 14px;")
        sort_section_layout.addWidget(sort_section_title)

        self.sort_combo = QComboBox()
        self.sort_combo.addItem("По дате создания", "created_at")
        self.sort_combo.addItem("По названию темы", "topic")
        self.sort_combo.addItem("По статусу", "status")
        self.sort_combo.setStyleSheet("""
            QComboBox {
                background-color: #F0F4F8;
                border: 1px solid #E6EEF6;
                border-radius: 8px;
                padding: 6px 12px;
                font-size: 13px;
            }
        """)
        sort_section_layout.addWidget(self.sort_combo)
        right_layout.addWidget(sort_section)

        # Разделитель
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("background-color: #E6EEF6;")
        right_layout.addWidget(sep)

        # Статистика
        stats_section = QWidget()
        stats_layout = QVBoxLayout(stats_section)
        stats_layout.setSpacing(10)
        stats_title = QLabel("Статистика")
        stats_title.setStyleSheet("font-weight: 600; color: #1F2937; font-size: 14px;")
        stats_layout.addWidget(stats_title)

        self.stat_total = QLabel("📚 Всего: 0")
        self.stat_new = QLabel("🆕 Новые: 0")
        self.stat_in_progress = QLabel("🔄 В процессе: 0")
        self.stat_mastered = QLabel("✅ Выучено: 0")
        for lbl in (self.stat_total, self.stat_new, self.stat_in_progress, self.stat_mastered):
            lbl.setStyleSheet("font-size: 13px; color: #374151;")
            stats_layout.addWidget(lbl)
        right_layout.addWidget(stats_section)

        right_layout.addStretch()

        # Кнопка "Начать повторение"
        self.start_review_btn = QPushButton("Начать повторение")
        self.start_review_btn.setStyleSheet("""
            QPushButton {
                background-color: #3B82F6;
                color: white;
                border: none;
                border-radius: 12px;
                padding: 10px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #2563EB;
            }
        """)
        right_layout.addWidget(self.start_review_btn)

        three_cols_layout.addWidget(right_widget, 1)
        content_layout.addLayout(three_cols_layout)

        # ========== ДЕМОНСТРАЦИЯ КАРТОЧКИ (внизу на всю ширину) ==========
        preview_widget = QFrame()
        preview_widget.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border-radius: 16px;
                border: none;
            }
        """)
        preview_layout = QVBoxLayout(preview_widget)
        preview_layout.setContentsMargins(20, 16, 20, 16)
        preview_layout.setSpacing(8)

        preview_title = QLabel("Просмотр карточки")
        preview_title.setStyleSheet("font-weight: 600; color: #1F2937; font-size: 14px;")
        preview_layout.addWidget(preview_title)

        self.card_display = QTextEdit()
        self.card_display.setReadOnly(True)
        self.card_display.setStyleSheet("""
            QTextEdit {
                background-color: #F9FAFB;
                border-radius: 12px;
                border: none;
                padding: 16px;
                font-size: 14px;
                min-height: 120px;
            }
        """)
        preview_layout.addWidget(self.card_display)

        content_layout.addWidget(preview_widget)

        scroll.setWidget(content)
        layout.addWidget(scroll)

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
        try:
            selected_ids = self.topic_tree.get_selected_topic_ids()
            self._update_cards_and_analytics(selected_ids)
        except Exception as e:
            logger.error(f"Ошибка загрузки данных: {e}", exc_info=True)

    def _on_topics_selection_changed(self, selected_ids: list):
        self._update_cards_and_analytics(selected_ids)

    def _get_card_status(self, card) -> str:
        progress = self._controller.get_card_progress(card.id)
        return progress['status']

    def _update_cards_and_analytics(self, topic_ids: list):
        try:
            if not topic_ids:
                self.card_list.clear()
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
            self._selected_card_ids.clear()

            if not cards:
                empty_item = QListWidgetItem("📭 В выбранных темах нет карточек")
                empty_item.setForeground(Qt.gray)
                self.card_list.addItem(empty_item)
                self.card_display.clear()
                return

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

                if status == "new":
                    status_badge = "[🆕 Новое]"
                    status_color = "#3B82F6"
                elif status == "in_progress":
                    status_badge = "[🔄 В процессе]"
                    status_color = "#F59E0B"
                else:
                    status_badge = "[✅ Выучено]"
                    status_color = "#10B981"

                if card.is_free:
                    preview = card.content[:50] + "..." if len(card.content) > 50 else card.content
                    text = f"{status_badge} 📝 [{topic_name}] {preview}"
                else:
                    preview = card.question[:50] + "..." if len(card.question) > 50 else card.question
                    text = f"{status_badge} ❓ [{topic_name}] {preview}"

                label = QLabel(text)
                label.setStyleSheet(f"color: {status_color}; font-size: 13px; background-color: transparent;")
                label.setWordWrap(True)

                widget_layout.addWidget(checkbox)
                widget_layout.addWidget(label, 1)

                widget.setMinimumHeight(35)
                widget.setMaximumHeight(50)

                item.setSizeHint(widget.sizeHint())
                self.card_list.addItem(item)
                self.card_list.setItemWidget(item, widget)
                item.setData(Qt.UserRole, card.id)

            logger.debug(f"Загружено {len(cards)} карточек для {len(topic_ids)} тем")
        except Exception as e:
            logger.error(f"Ошибка обновления карточек и аналитики: {e}", exc_info=True)

    def _update_analytics_labels(self, total: int, new_count: int, in_progress_count: int, mastered_count: int):
        self.stat_total.setText(f"📚 Всего: {total}")
        self.stat_new.setText(f"🆕 Новые: {new_count}")
        self.stat_in_progress.setText(f"🔄 В процессе: {in_progress_count}")
        self.stat_mastered.setText(f"✅ Выучено: {mastered_count}")

    def _get_topic_name(self, topic_id: int) -> str:
        row = db.fetchone("SELECT name FROM topics WHERE id = ?", (topic_id,))
        return row['name'] if row else "Без темы"

    def _on_card_selected(self, item: QListWidgetItem):
        try:
            card_id = item.data(Qt.UserRole)
            if not card_id:
                return

            card = self._controller.get_card(card_id)
            if not card:
                return

            self._current_card = card
            status = self._get_card_status(card)
            status_color = {
                "new": "#3B82F6",
                "in_progress": "#F59E0B",
                "mastered": "#10B981"
            }.get(status, "#6B7280")

            if card.is_free:
                self.card_display.setHtml(f"""
                    <style>
                        h3 {{ color: #1F2937; margin-bottom: 8px; }}
                        small {{ color: {status_color}; }}
                        hr {{ border: 1px solid #E6EEF6; }}
                        p {{ color: #374151; line-height: 1.5; }}
                    </style>
                    <h3>📝 Свободная карточка <small>({status})</small></h3>
                    <hr>
                    <p>{card.content}</p>
                """)
            else:
                self.card_display.setHtml(f"""
                    <style>
                        h3 {{ color: #1F2937; margin-bottom: 8px; }}
                        small {{ color: {status_color}; }}
                        hr {{ border: 1px solid #E6EEF6; }}
                        p {{ color: #374151; line-height: 1.5; }}
                        b {{ color: #1F2937; }}
                    </style>
                    <h3>❓ Карточка Вопрос-Ответ <small>({status})</small></h3>
                    <p><b>Вопрос:</b><br>{card.question}</p>
                    <hr>
                    <p><b>Ответ:</b><br>{card.answer}</p>
                """)
        except Exception as e:
            logger.error(f"Ошибка выбора карточки: {e}", exc_info=True)

    def _on_card_checkbox_changed(self, card_id: int, state: int):
        if state == Qt.Checked:
            self._selected_card_ids.add(card_id)
        else:
            self._selected_card_ids.discard(card_id)

    def _on_start_review_clicked(self):
        try:
            topic_ids = self.topic_tree.get_selected_topic_ids()
            if not topic_ids:
                QMessageBox.warning(self, "Внимание", "Выберите хотя бы одну тему в дереве слева.")
                return

            card_ids = list(self._selected_card_ids) if self._selected_card_ids else None
            self.start_review_requested.emit(topic_ids, True, True, True, card_ids)
            logger.info(f"Запрошено начало повторения для {len(topic_ids)} тем")
        except Exception as e:
            logger.error(f"Ошибка начала повторения: {e}", exc_info=True)

    def refresh(self):
        try:
            self.topic_tree.reset_selection()
            self.topic_tree.reload()
            self.topic_tree.collapseAll()
            self._load_data()
        except Exception as e:
            logger.error(f"Ошибка обновления: {e}", exc_info=True)

    def _on_tree_sort_changed(self):
        try:
            sort_mode = self.tree_sort_combo.currentData()
            if sort_mode:
                self.topic_tree.set_sort_mode(sort_mode)
                self.topic_tree.reload()
        except Exception as e:
            logger.error(f"Ошибка изменения сортировки: {e}", exc_info=True)