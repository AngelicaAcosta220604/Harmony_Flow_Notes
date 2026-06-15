# modules/sessions/active_view.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame
)

from utils.ping_manager import PingManager
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
        self._setup_ui()
        self._connect_signals()
        self._setup_ping_manager()

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





    def _on_inactivity_timeout(self):
        """Обработчик бездействия - показываем пинг-диалог"""
        self._session_controller.pause_session()

        dialog = PingDialog(self)
        dialog.continue_session.connect(self._on_continue_from_ping)
        dialog.pause_session.connect(self._on_pause_from_ping)
        dialog.exec()

    def _on_continue_from_ping(self):
        """Продолжение сессии после пинга"""
        self.ping_manager.user_confirmed()  # ← Сбрасываем таймер PingManager
        self._session_controller.resume_session()

    def _on_pause_from_ping(self):
        """Пауза после пинга"""
        self.ping_manager.reset_idle()  # ← Сбрасываем, чтобы не донимало
        self.status_label.setText("Сессия на паузе")
        self.status_label.setStyleSheet("color: #ff9800;")
        self.pause_btn.setText("▶ Возобновить")

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
        self.ping_manager.reset_idle()  # ← Сбрасываем при возобновлении
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
        self.ping_manager.reset_idle()  # ← движение ползунка = активность

    def _setup_ping_manager(self):
        """Настраивает менеджер контроля активности"""
        # Спросит "ты тут?" через 15 мин, авто-пауза через 90 мин
        self.ping_manager = PingManager(
            idle_ms=self._activity_check_interval * 60 * 1000,
            timeout_ms=90 * 60 * 1000,
            parent=self
        )
        self.ping_manager.pingNeeded.connect(self._show_ping_dialog)
        self.ping_manager.timeoutReached.connect(self._auto_pause_from_ping)

    def _show_ping_dialog(self):
        """Показывает диалог 'Ты ещё тут?' и ставит сессию на паузу"""
        self._session_controller.pause_session()

        dialog = PingDialog(self)
        dialog.continue_session.connect(self._on_continue_from_ping)
        dialog.pause_session.connect(self._on_pause_from_ping)
        dialog.exec()

    def _auto_pause_from_ping(self):
        """Авто-пауза, если пользователь вообще не ответил 90 минут"""
        if not self._session_controller.is_session_paused():
            self._session_controller.pause_session()
        self.status_label.setText("⏸ Авто-пауза (нет активности)")
        self.status_label.setStyleSheet("color: #ff9800;")
        self.pause_btn.setText("▶ Возобновить")

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


        # Стартуем музыку
        default_sound = self._music_controller.get_current_sound()
        if default_sound and default_sound != 'off':
            self.music_widget._controller.resume()

    def cleanup(self):
        """Очищает ресурсы"""
        self.ping_manager._idle_timer.stop()
        self.ping_manager._timeout_timer.stop()

    def force_save_time(self):
        """Принудительно сохраняет текущее время сессии в БД"""
        session_id = self._session_controller.get_current_session_id()
        if session_id and self.timer:
            current_seconds = self._session_controller.get_elapsed_seconds()
            if current_seconds > 0:
                from datebase.db_manager import db
                db.execute(
                    "UPDATE sessions SET total_active_seconds = ? WHERE id = ?",
                    (current_seconds, session_id)
                )

    def force_save_state(self):
        """Принудительно сохраняет ползунки"""
        session_id = self._session_controller.get_current_session_id()
        if session_id:
            values = self.state_sliders.get_values()
            # Если в БД нет полей concentration/energy/interest,
            # можно сохранять их через state_log_repo как последнюю запись
            from datebase.db_manager import db
            db.execute(
                """UPDATE sessions SET concentration = ?, energy = ?, interest = ? 
                WHERE id = ?""",
                (values['concentration'], values['energy'], values['interest'], session_id)
            )

    def hideEvent(self, event):
        """Сохраняем состояние при переключении вкладок"""
        if self._session_controller.get_current_session_id():
            self.force_save_time()
            self.force_save_state()
        super().hideEvent(event)

    def resume_existing_session(self, session_id: int, topic_id: int, topic_name: str):
        """Загружает старую сессию из БД"""
        self.topic_label.setText(f"Работа над темой: {topic_name}")

        # Получаем данные сессии из БД
        from datebase.db_manager import db
        row = db.fetchone("SELECT * FROM sessions WHERE id = ?", (session_id,))
        if not row:
            return

        # Восстанавливаем время
        total_seconds = row.get('total_active_seconds', 0)
        self.timer.set_time(total_seconds)

        # Восстанавливаем ползунки
        self.state_sliders.conc_slider.setValue(row.get('concentration', 50))
        self.state_sliders.energy_slider.setValue(row.get('energy', 50))
        self.state_sliders.interest_slider.setValue(row.get('interest', 50))

        # Если сессия была активна — продолжаем таймер
        if row['status'] == 'active':
            self._session_controller.resume_session()  # Нужно добавить этот метод в контроллер
            self.timer.resume()
        else:
            self.timer.pause()