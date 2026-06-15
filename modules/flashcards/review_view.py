# modules/flashcards/review_view.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTextEdit, QProgressBar
)
from widgets import SilentMessageBox
from PySide6.QtCore import Qt, Signal, QTimer

from .review_controller import ReviewController
from models.flashcard import Flashcard


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
        layout.setSpacing(15)

        # Заголовок
        self.title_label = QLabel("Повторение карточек")
        self.title_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        self.title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.title_label)

        # Прогресс
        self.progress_label = QLabel("Карточка 0 из 0")
        self.progress_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.progress_label)

        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)

        # Карточка
        self.card_display = QTextEdit()
        self.card_display.setReadOnly(True)
        self.card_display.setMinimumHeight(300)
        self.card_display.setStyleSheet("""
                    QTextEdit {
                        font-size: 14px;
                        padding: 30px;
                        background-color: #ffffff;
                        border: 2px solid #e0e0e0;
                        border-radius: 12px;
                    }
                """)
        self.card_display.setAlignment(Qt.AlignCenter)  # Центрируем текст!
        layout.addWidget(self.card_display)

        # Кнопки
        button_layout = QHBoxLayout()

        self.cancel_btn = QPushButton("❌ Завершить досрочно")
        self.show_btn = QPushButton("👁️ Показать ответ")
        self.knew_btn = QPushButton("✅ Знал(а)")
        self.doubt_btn = QPushButton("🤔 Сомневался/лась")
        self.didnt_know_btn = QPushButton("❌ Не знал(а)")

        self.knew_btn.setStyleSheet("background-color: #4caf50;")
        self.doubt_btn.setStyleSheet("background-color: #ff9800;")
        self.didnt_know_btn.setStyleSheet("background-color: #f44336;")

        button_layout.addWidget(self.cancel_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.show_btn)
        button_layout.addWidget(self.knew_btn)
        button_layout.addWidget(self.doubt_btn)
        button_layout.addWidget(self.didnt_know_btn)

        layout.addLayout(button_layout)

        # Статус
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: #888888;")
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
                      skip_reviewed: bool = True):
        """
        Начинает сессию повторения для нескольких тем
        """
        session_id = self._controller.start_review_session(
            topic_ids, mode, include_free, include_qa, skip_reviewed
        )

        if not session_id:
            SilentMessageBox.warning(self, "Ошибка", "Нет карточек для повторения в выбранных темах")
            self.session_cancelled.emit()
            return

        self._load_current_card()

    def _load_current_card(self):
        """Загружает текущую карточку"""
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

    def _on_show_answer(self):
        """Показывает ответ"""
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

    def _on_answer(self, correct: bool):
        """Обработчик ответа пользователя"""
        if not self._current_card:
            return

        # 🆕 Записываем ответ и обновляем прогресс
        self._controller.record_answer(self._current_card.id, correct)

        # Сохраняем ответ и переходим к следующей карточке
        has_more = self._controller.answer_current_card(correct)

        if has_more:
            self._load_current_card()
        else:
            self._end_session()

    def _end_session(self):
        """Завершает сессию"""
        progress = self._controller.get_progress()

        # Очищаем контроллер ПЕРЕД показом сообщения
        self._controller.end_review_session()

        # Эмитим сигнал
        self.session_completed.emit(
            progress['completed'],
            progress['total']
        )

        # Показываем сообщение
        SilentMessageBox.information(
            self, "Сессия завершена",
            f"Повторение завершено!\n\n"
            f"Повторено карточек: {progress['completed']} из {progress['total']}"
        )

    def _on_cancel(self):
        """Отмена сессии"""
        reply = SilentMessageBox.question(
            self, "Завершить сессию?",
            "Вы действительно хотите завершить сессию повторения досрочно?",
            SilentMessageBox.Yes | SilentMessageBox.No, SilentMessageBox.No
        )

        if reply == SilentMessageBox.Yes:
            self._controller.end_review_session()
            self.session_cancelled.emit()