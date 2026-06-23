# modules/flashcards/review_view.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTextEdit, QProgressBar
)
from widgets import SilentMessageBox
from PySide6.QtCore import Qt, Signal, QTimer, QSize
from PySide6.QtGui import QIcon, QPixmap, QColor
import logging

from utils.resource_paths import get_resource_path
from .review_controller import ReviewController
from models.flashcard import Flashcard

# Настройка логирования
logger = logging.getLogger(__name__)


class ReviewSessionView(QWidget):
    """
    Экран для сессии повторения карточек.
    """

    # Сигналы
    session_completed = Signal(int, int)  # (correct_count, total_count)
    session_cancelled = Signal()

    def __init__(self, controller: ReviewController, parent=None):
        super().__init__(parent)
        self._controller = controller
        self._current_card: Flashcard = None
        self._show_answer = False
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        """Настраивает интерфейс"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

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

        header_title = QLabel("Повторение карточек")
        header_title.setStyleSheet("font-size: 20px; font-weight: bold; color: #1F2937;")
        header_layout.addWidget(header_title)

        layout.addWidget(header_widget)

        # Прогресс
        self.progress_label = QLabel("Карточка 0 из 0")
        self.progress_label.setAlignment(Qt.AlignCenter)
        self.progress_label.setStyleSheet("font-size: 14px; color: #6B7280;")
        layout.addWidget(self.progress_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: #F0F4F8;
                border-radius: 8px;
                height: 8px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #3B82F6;
                border-radius: 8px;
            }
        """)
        self.progress_bar.setTextVisible(False)
        layout.addWidget(self.progress_bar)

        # Карточка
        self.card_display = QTextEdit()
        self.card_display.setReadOnly(True)
        self.card_display.setMinimumHeight(300)
        self.card_display.setStyleSheet("""
            QTextEdit {
                font-size: 16px;
                padding: 30px;
                background-color: #FFFFFF;
                border: 1px solid #E6EEF6;
                border-radius: 16px;
                color: #1F2937;
            }
            QTextEdit:focus {
                outline: none;
            }
        """)
        self.card_display.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.card_display)

        # Кнопки
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)

        self.cancel_btn = QPushButton("Завершить досрочно")
        self.cancel_btn.setIconSize(QSize(18, 18))
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(239, 68, 68, 0.15);
                color: #EF4444;
                border: 1px solid #EF4444;
                border-radius: 12px;
                padding: 8px 16px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: rgba(239, 68, 68, 0.25);
                border: 1px solid #DC2626;
                color: #DC2626;
            }
        """)
        button_layout.addWidget(self.cancel_btn)

        button_layout.addStretch()

        self.show_btn = QPushButton("Показать ответ")
        # ✅ ИСПРАВЛЕНО: используем get_resource_path
        self.show_btn.setIcon(QIcon(str(get_resource_path("resources/icons/eye.png"))))
        self.show_btn.setIconSize(QSize(18, 18))
        self.show_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(59, 130, 246, 0.15);
                color: #3B82F6;
                border: 1px solid #3B82F6;
                border-radius: 12px;
                padding: 8px 20px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: rgba(59, 130, 246, 0.25);
                border: 1px solid #2563EB;
                color: #2563EB;
            }
        """)
        button_layout.addWidget(self.show_btn)

        # Кнопка "Знал(а)" (зелёная контурная)
        self.knew_btn = QPushButton("Знал(а)")
        # ✅ ИСПРАВЛЕНО: используем get_resource_path
        self.knew_btn.setIcon(QIcon(str(get_resource_path("resources/icons/check.png"))))
        self.knew_btn.setIconSize(QSize(18, 18))
        self.knew_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(16, 185, 129, 0.15);
                color: #059669;
                border: 1px solid #10B981;
                border-radius: 12px;
                padding: 8px 20px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: rgba(16, 185, 129, 0.25);
                border: 1px solid #059669;
                color: #047857;
            }
        """)
        button_layout.addWidget(self.knew_btn)

        # Кнопка "Сомневался/лась" (оранжевая контурная)
        self.doubt_btn = QPushButton("Сомневался/лась")
        # ✅ ИСПРАВЛЕНО: используем get_resource_path
        self.doubt_btn.setIcon(QIcon(str(get_resource_path("resources/icons/doubt.png"))))
        self.doubt_btn.setIconSize(QSize(18, 18))
        self.doubt_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(245, 158, 11, 0.15);
                color: #D97706;
                border: 1px solid #F59E0B;
                border-radius: 12px;
                padding: 8px 20px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: rgba(245, 158, 11, 0.25);
                border: 1px solid #D97706;
                color: #B45309;
            }
        """)
        button_layout.addWidget(self.doubt_btn)

        # Кнопка "Не знал(а)" (красная контурная)
        self.didnt_know_btn = QPushButton("Не знал(а)")
        # ✅ ИСПРАВЛЕНО: используем get_resource_path
        self.didnt_know_btn.setIcon(QIcon(str(get_resource_path("resources/icons/close.png"))))
        self.didnt_know_btn.setIconSize(QSize(18, 18))
        self.didnt_know_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(239, 68, 68, 0.15);
                color: #EF4444;
                border: 1px solid #EF4444;
                border-radius: 12px;
                padding: 8px 20px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: rgba(239, 68, 68, 0.25);
                border: 1px solid #DC2626;
                color: #DC2626;
            }
        """)
        button_layout.addWidget(self.didnt_know_btn)

        layout.addLayout(button_layout)

        # Статус
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: #6B7280; font-size: 12px;")
        layout.addWidget(self.status_label)

        # Изначально скрываем кнопки ответа
        self._set_answer_buttons_visible(False)

    def _connect_signals(self):
        """Подключает сигналы"""
        self.cancel_btn.clicked.connect(self._on_cancel)
        self.show_btn.clicked.connect(self._on_show_answer)
        self.knew_btn.clicked.connect(lambda: self._on_answer(True))
        self.doubt_btn.clicked.connect(lambda: self._on_answer(True))
        self.didnt_know_btn.clicked.connect(lambda: self._on_answer(False))

    def _set_answer_buttons_visible(self, visible: bool):
        """Показывает/скрывает кнопки ответа"""
        self.show_btn.setVisible(not visible)
        self.knew_btn.setVisible(visible)
        self.doubt_btn.setVisible(visible)
        self.didnt_know_btn.setVisible(visible)

    def start_session(self, topic_ids: list, mode: str = 'sequential',
                      include_free: bool = True, include_qa: bool = True,
                      skip_reviewed: bool = True, card_ids: list = None):
        """
        Начинает сессию повторения
        """
        try:
            session_id = self._controller.start_review_session(
                topic_ids, mode, include_free, include_qa, skip_reviewed, card_ids
            )

            if not session_id:
                SilentMessageBox.warning(self, "Ошибка", "Нет карточек для повторения в выбранных темах")
                self.session_cancelled.emit()
                return

            self._load_current_card()
            logger.info(f"Сессия повторения начата: {len(topic_ids)} тем, режим: {mode}")
        except Exception as e:
            logger.error(f"Ошибка начала сессии повторения: {e}", exc_info=True)
            SilentMessageBox.warning(self, "Ошибка", f"Не удалось начать сессию: {e}")
            self.session_cancelled.emit()

    def _load_current_card(self):
        """Загружает текущую карточку"""
        try:
            self._current_card = self._controller.get_current_card()

            if not self._current_card:
                self._end_session()
                return

            self._show_answer = False
            self._set_answer_buttons_visible(False)

            # Отображаем карточку
            if self._current_card.is_free:
                self.card_display.setPlainText(self._current_card.content)
            else:
                self.card_display.setPlainText(f"❓ {self._current_card.question}\n\n[Нажмите «Показать ответ»]")

            # Обновляем прогресс
            progress = self._controller.get_progress()
            self.progress_label.setText(f"Карточка {progress['completed'] + 1} из {progress['total']}")
            self.progress_bar.setMaximum(progress['total'])
            self.progress_bar.setValue(progress['completed'])

            self.status_label.setText("Подумайте над ответом, затем нажмите «Показать ответ»")
        except Exception as e:
            logger.error(f"Ошибка загрузки карточки: {e}", exc_info=True)
            SilentMessageBox.warning(self, "Ошибка", f"Не удалось загрузить карточку: {e}")

    def _on_show_answer(self):
        """Показывает ответ"""
        try:
            if not self._current_card:
                return

            self._show_answer = True

            # Отображаем ответ
            if self._current_card.is_free:
                self.card_display.setPlainText(
                    f"{self._current_card.content}\n\n"
                    f"{'=' * 50}\n"
                    f"Оцените, насколько хорошо вы запомнили этот материал:"
                )
            else:
                self.card_display.setPlainText(
                    f"❓ {self._current_card.question}\n\n"
                    f"📝 Ответ:\n{self._current_card.answer}\n\n"
                    f"{'=' * 50}\n"
                    f"Оцените свой ответ:"
                )

            self._set_answer_buttons_visible(True)
            self.status_label.setText("Оцените, насколько хорошо вы знали ответ")
        except Exception as e:
            logger.error(f"Ошибка показа ответа: {e}", exc_info=True)

    def _on_answer(self, correct: bool):
        """Обработчик ответа пользователя"""
        try:
            if not self._current_card:
                return

            self._controller.record_answer(self._current_card.id, correct)
            has_more = self._controller.answer_current_card(correct)

            if has_more:
                self._load_current_card()
            else:
                self._end_session()
        except Exception as e:
            logger.error(f"Ошибка обработки ответа: {e}", exc_info=True)
            SilentMessageBox.warning(self, "Ошибка", f"Не удалось обработать ответ: {e}")

    def _end_session(self):
        """Завершает сессию"""
        try:
            progress = self._controller.get_progress()

            self._controller.end_review_session()

            self.session_completed.emit(
                progress['completed'],
                progress['total']
            )

            SilentMessageBox.information(
                self, "Сессия завершена",
                f"Повторение завершено!\n\n"
                f"Повторено карточек: {progress['completed']} из {progress['total']}"
            )
            logger.info(f"Сессия повторения завершена: {progress['completed']}/{progress['total']}")
        except Exception as e:
            logger.error(f"Ошибка завершения сессии: {e}", exc_info=True)
            SilentMessageBox.warning(self, "Ошибка", f"Не удалось завершить сессию: {e}")

    def _on_cancel(self):
        """Отмена сессии"""
        try:
            reply = SilentMessageBox.question(
                self, "Завершить сессию?",
                "Вы действительно хотите завершить сессию повторения досрочно?",
                SilentMessageBox.Yes | SilentMessageBox.No, SilentMessageBox.No
            )

            if reply == SilentMessageBox.Yes:
                self._controller.end_review_session()
                self.session_cancelled.emit()
                logger.info("Сессия повторения отменена пользователем")
        except Exception as e:
            logger.error(f"Ошибка отмены сессии: {e}", exc_info=True)