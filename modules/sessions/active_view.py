# modules/sessions/active_view.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame
)
from widgets import SilentMessageBox
from PySide6.QtCore import Qt, QTimer, Signal

from .controller import SessionController
from .widgets import CustomTimer, StateSliders, PingDialog
from .quick_capture import QuickNoteDialog
from modules.music.widgets import MusicWidget


class FocusActiveView(QWidget):
    """
    Экран активной фокус-сессии.
    Отображает таймер, ползунки состояния, кнопки управления.
    """

    session_ended = Signal(int)  # duration_minutes
    back_to_dashboard = Signal()

    def __init__(
            self,
            session_controller: SessionController,
            music_controller,
            parent=None
    ):
        super().__init__(parent)
        self._session_controller = session_controller
        self._music_controller = music_controller
        self._activity_check_interval = 15  # минут
        self._inactivity_timer = QTimer()
        self._setup_ui()
        self._connect_signals()
        self._setup_inactivity_timer()

    def _setup_ui(self):
        """Настраивает интерфейс"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Верхняя панель с названием темы
        self.topic_label = QLabel()
        self.topic_label.setStyleSheet("font-size: 16px; color: #888888;")
        self.topic_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.topic_label)

        # Таймер (центр)
        timer_container = QFrame()
        timer_container.setFrameShape(QFrame.NoFrame)
        timer_layout = QVBoxLayout(timer_container)
        timer_layout.setAlignment(Qt.AlignCenter)

        self.timer = CustomTimer()
        timer_layout.addWidget(self.timer)

        layout.addWidget(timer_container, 1)

        # Ползунки состояния
        sliders_container = QFrame()
        sliders_container.setFrameShape(QFrame.StyledPanel)
        sliders_layout = QVBoxLayout(sliders_container)

        sliders_label = QLabel("Отслеживание состояния")
        sliders_label.setStyleSheet("font-weight: bold;")
        sliders_layout.addWidget(sliders_label)

        self.state_sliders = StateSliders()
        sliders_layout.addWidget(self.state_sliders)

        layout.addWidget(sliders_container)

        # Нижняя панель с кнопками
        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(10)

        # Музыка
        self.music_widget = MusicWidget(self._music_controller)
        bottom_layout.addWidget(self.music_widget)

        bottom_layout.addStretch()

        # Кнопки управления
        self.quick_note_btn = QPushButton("✏️ Быстрая запись")
        self.pause_btn = QPushButton("⏸ Пауза")
        self.end_btn = QPushButton("⏹ Завершить")

        self.quick_note_btn.setFixedHeight(40)
        self.pause_btn.setFixedHeight(40)
        self.end_btn.setFixedHeight(40)

        bottom_layout.addWidget(self.quick_note_btn)
        bottom_layout.addWidget(self.pause_btn)
        bottom_layout.addWidget(self.end_btn)

        layout.addLayout(bottom_layout)

        # Статус
        self.status_label = QLabel("Сессия активна")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: #4caf50;")
        layout.addWidget(self.status_label)

    def _connect_signals(self):
        """Подключает сигналы."""
        self._session_controller.timer_updated.connect(self.timer.set_time)
        self._session_controller.session_paused.connect(self._on_paused)
        self._session_controller.session_resumed.connect(self._on_resumed)

        self.quick_note_btn.clicked.connect(self._on_quick_note)
        self.pause_btn.clicked.connect(self._on_pause_clicked)
        self.end_btn.clicked.connect(self._on_end_clicked)

        # ПОДКЛЮЧАЕМ ПОЛЗУНКИ ПРАВИЛЬНО
        self.state_sliders.state_changed.connect(self._on_state_changed)

    def _setup_inactivity_timer(self):
        """Настраивает таймер контроля активности"""
        self._inactivity_timer.timeout.connect(self._on_inactivity_timeout)
        self._reset_inactivity_timer()

    def _reset_inactivity_timer(self):
        """Сбрасывает таймер бездействия"""
        self._inactivity_timer.start(self._activity_check_interval * 60 * 1000)

    def _on_inactivity_timeout(self):
        """Обработчик бездействия - показываем пинг-диалог"""
        self._session_controller.pause_session()

        dialog = PingDialog(self)
        dialog.continue_session.connect(self._on_continue_from_ping)
        dialog.pause_session.connect(self._on_pause_from_ping)
        dialog.exec()

    def _on_continue_from_ping(self):
        """Продолжение сессии после пинга"""
        self._session_controller.resume_session()
        self._reset_inactivity_timer()

    def _on_pause_from_ping(self):
        """Пауза после пинга"""
        # Уже на паузе
        self.status_label.setText("Сессия на паузе")
        self.status_label.setStyleSheet("color: #ff9800;")
        self.pause_btn.setText("▶ Возобновить")
        self._inactivity_timer.stop()

    def _on_paused(self):
        """Обработчик паузы"""
        self.status_label.setText("Сессия на паузе")
        self.status_label.setStyleSheet("color: #ff9800;")
        self.pause_btn.setText("▶ Возобновить")
        self._inactivity_timer.stop()
        self.music_widget._controller.pause()

    def _on_resumed(self):
        """Обработчик возобновления"""
        self.status_label.setText("Сессия активна")
        self.status_label.setStyleSheet("color: #4caf50;")
        self.pause_btn.setText("⏸ Пауза")
        self._reset_inactivity_timer()
        self.music_widget._controller.resume()

    def _on_pause_clicked(self):
        """Обработчик кнопки паузы"""
        if self._session_controller.is_session_active():
            self._session_controller.pause_session()
        else:
            self._session_controller.resume_session()

    def _on_end_clicked(self):
        """Обработчик кнопки завершения"""
        reply = SilentMessageBox.question(
            self, "Завершить сессию?",
            "Вы действительно хотите завершить сессию?",
            SilentMessageBox.Yes | SilentMessageBox.No, SilentMessageBox.No
        )

        if reply == SilentMessageBox.Yes:
            duration = self._session_controller.end_session()
            self.session_ended.emit(duration)

    def _on_quick_note(self):
        """Быстрая запись"""
        dialog = QuickNoteDialog(self)
        dialog.note_saved.connect(self._save_quick_note)
        dialog.exec()

    def _save_quick_note(self, content: str):
        """Сохраняет быструю запись"""
        self._session_controller.add_quick_note(content)
        self.status_label.setText("✅ Запись сохранена")
        QTimer.singleShot(2000, lambda: self.status_label.setText("Сессия активна"))

    def _on_state_changed(self, metric: str, value: int):
        """Обработчик изменения состояния"""
        self._session_controller.log_state(metric, value)
        self._reset_inactivity_timer()  # активность - сбрасываем таймер

    def start(self, topic_id: int, topic_name: str, activity_check_interval: int):
        """
        Запускает сессию

        Args:
            topic_id: ID темы
            topic_name: Название темы
            activity_check_interval: Интервал контроля активности (минуты)
        """
        self._activity_check_interval = activity_check_interval
        self.topic_label.setText(f"Работа над темой: {topic_name}")

        # Подготавливаем и запускаем сессию
        self._session_controller.prepare_session(topic_id)
        self._session_controller.start_session()

        # Сбрасываем ползунки
        self.state_sliders.reset()

        # Запускаем таймер бездействия
        self._reset_inactivity_timer()

        # Стартуем музыку
        default_sound = self._music_controller.get_current_sound()
        if default_sound and default_sound != 'off':
            self.music_widget._controller.resume()

    def cleanup(self):
        """Очищает ресурсы"""
        self._inactivity_timer.stop()