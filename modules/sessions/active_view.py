# modules/sessions/active_view.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QSizePolicy
)
from widgets import SilentMessageBox
from PySide6.QtCore import Qt, QTimer, Signal, QSize
from PySide6.QtGui import QIcon, QPixmap, QFont

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
        layout.setSpacing(20)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("background-color: transparent; border: none;")

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setSpacing(20)

        # ========== НАЗВАНИЕ ТЕМЫ ==========
        self.topic_label = QLabel()
        self.topic_label.setStyleSheet("font-size: 16px; color: #6B7280;")
        self.topic_label.setAlignment(Qt.AlignCenter)
        content_layout.addWidget(self.topic_label)

        # ========== ПЛАШКА ТАЙМЕРА ==========
        timer_widget = QFrame()
        timer_widget.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border-radius: 24px;
                border: none;
            }
        """)
        timer_widget.setMinimumHeight(220)
        timer_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        timer_layout = QVBoxLayout(timer_widget)
        timer_layout.setContentsMargins(20, 20, 20, 20)
        timer_layout.setAlignment(Qt.AlignCenter)

        self.timer = CustomTimer()
        timer_layout.addWidget(self.timer)

        content_layout.addWidget(timer_widget)

        # ========== ПЛАШКА ОТСЛЕЖИВАНИЯ СОСТОЯНИЯ ==========
        state_widget = QFrame()
        state_widget.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border-radius: 16px;
                border: none;
            }
        """)
        state_widget.setMinimumHeight(180)

        state_layout = QVBoxLayout(state_widget)
        state_layout.setContentsMargins(20, 16, 20, 16)
        state_layout.setSpacing(12)

        # Заголовок с иконкой
        state_title_layout = QHBoxLayout()
        state_icon = QLabel()
        state_icon_pixmap = QPixmap("resources/icons/brain.png")
        if not state_icon_pixmap.isNull():
            state_icon_pixmap = state_icon_pixmap.scaled(20, 20, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            state_icon.setPixmap(state_icon_pixmap)
        state_title = QLabel("Отслеживание состояния")
        state_title.setStyleSheet("font-weight: 600; color: #1F2937; font-size: 14px;")
        state_title_layout.addWidget(state_icon)
        state_title_layout.addWidget(state_title)
        state_title_layout.addStretch()
        state_layout.addLayout(state_title_layout)

        self.state_sliders = StateSliders()
        state_layout.addWidget(self.state_sliders)

        content_layout.addWidget(state_widget)

        # ========== ПЛАШКА МУЗЫКИ ==========
        music_widget_frame = QFrame()
        music_widget_frame.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border-radius: 16px;
                border: none;
            }
        """)

        music_layout = QVBoxLayout(music_widget_frame)
        music_layout.setContentsMargins(20, 16, 20, 16)
        music_layout.setSpacing(12)

        # Заголовок с иконкой
        music_title_layout = QHBoxLayout()
        music_icon = QLabel()
        music_icon_pixmap = QPixmap("resources/icons/music.png")
        if not music_icon_pixmap.isNull():
            music_icon_pixmap = music_icon_pixmap.scaled(20, 20, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            music_icon.setPixmap(music_icon_pixmap)
        else:
            music_icon.setText("🎵")
            music_icon.setStyleSheet("font-size: 16px;")
        music_title = QLabel("Фоновые звуки")
        music_title.setStyleSheet("font-weight: 600; color: #1F2937; font-size: 14px;")
        music_title_layout.addWidget(music_icon)
        music_title_layout.addWidget(music_title)
        music_title_layout.addStretch()
        music_layout.addLayout(music_title_layout)

        self.music_widget = MusicWidget(self._music_controller)
        music_layout.addWidget(self.music_widget)

        content_layout.addWidget(music_widget_frame)

        # ========== КНОПКИ УПРАВЛЕНИЯ ==========
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(12)

        # Быстрая запись (жёлтая)
        self.quick_note_btn = QPushButton("Быстрая запись")
        self.quick_note_btn.setIcon(QIcon("resources/icons/notes.png"))
        self.quick_note_btn.setIconSize(QSize(18, 18))
        self.quick_note_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(245, 158, 11, 0.15);
                color: #D97706;
                border: 1px solid #F59E0B;
                border-radius: 12px;
                padding: 10px 20px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: rgba(245, 158, 11, 0.25);
                border: 1px solid #D97706;
                color: #B45309;
            }
        """)
        buttons_layout.addWidget(self.quick_note_btn)

        # Возобновить/Пауза (зелёная)
        self.pause_btn = QPushButton("Пауза")
        self.pause_btn.setIcon(QIcon("resources/icons/play.png"))
        self.pause_btn.setIconSize(QSize(18, 18))
        self.pause_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(16, 185, 129, 0.15);
                color: #059669;
                border: 1px solid #10B981;
                border-radius: 12px;
                padding: 10px 20px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: rgba(16, 185, 129, 0.25);
                border: 1px solid #059669;
                color: #047857;
            }
        """)
        buttons_layout.addWidget(self.pause_btn)

        # Завершить (красная)
        self.end_btn = QPushButton("Завершить")
        self.end_btn.setIcon(QIcon("resources/icons/urna.png"))
        self.end_btn.setIconSize(QSize(18, 18))
        self.end_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(239, 68, 68, 0.15);
                color: #EF4444;
                border: 1px solid #EF4444;
                border-radius: 12px;
                padding: 10px 20px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: rgba(239, 68, 68, 0.25);
                border: 1px solid #DC2626;
                color: #DC2626;
            }
        """)
        buttons_layout.addWidget(self.end_btn)

        buttons_layout.addStretch()
        content_layout.addLayout(buttons_layout)

        # ========== СТАТУС ==========
        self.status_label = QLabel("Сессия активна")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: #10B981; font-weight: 500;")
        content_layout.addWidget(self.status_label)

        content_layout.addStretch()

        scroll.setWidget(content)
        layout.addWidget(scroll)

    def _connect_signals(self):
        """Подключает сигналы."""
        self._session_controller.timer_updated.connect(self.timer.set_time)
        self._session_controller.session_paused.connect(self._on_paused)
        self._session_controller.session_resumed.connect(self._on_resumed)

        self.quick_note_btn.clicked.connect(self._on_quick_note)
        self.pause_btn.clicked.connect(self._on_pause_clicked)
        self.end_btn.clicked.connect(self._on_end_clicked)

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
        self.status_label.setText("Сессия на паузе")
        self.status_label.setStyleSheet("color: #F59E0B; font-weight: 500;")
        self.pause_btn.setText("Возобновить")
        self.pause_btn.setIcon(QIcon("resources/icons/play.png"))
        self._inactivity_timer.stop()

    def _on_paused(self):
        """Обработчик паузы"""
        self.status_label.setText("Сессия на паузе")
        self.status_label.setStyleSheet("color: #F59E0B; font-weight: 500;")
        self.pause_btn.setText("Возобновить")
        self.pause_btn.setIcon(QIcon("resources/icons/play.png"))
        self._inactivity_timer.stop()
        self.music_widget._controller.pause()

    def _on_resumed(self):
        """Обработчик возобновления"""
        self.status_label.setText("Сессия активна")
        self.status_label.setStyleSheet("color: #10B981; font-weight: 500;")
        self.pause_btn.setText("Пауза")
        self.pause_btn.setIcon(QIcon("resources/icons/pause.png"))
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
        self._reset_inactivity_timer()

    def start(self, topic_id: int, topic_name: str, activity_check_interval: int):
        """
        Запускает сессию
        """
        self._activity_check_interval = activity_check_interval
        self.topic_label.setText(f"Работа над темой: {topic_name}")

        self._session_controller.prepare_session(topic_id)
        self._session_controller.start_session()

        self.state_sliders.reset()

        self._reset_inactivity_timer()

        default_sound = self._music_controller.get_current_sound()
        if default_sound and default_sound != 'off':
            self.music_widget._controller.resume()

    def cleanup(self):
        """Очищает ресурсы"""
        self._inactivity_timer.stop()