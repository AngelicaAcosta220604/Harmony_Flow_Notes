# modules/sessions/active_view.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QSizePolicy
)

from utils.ping_manager import PingManager
from utils.resource_paths import get_resource_path
from widgets import SilentMessageBox
from PySide6.QtCore import Qt, QTimer, Signal, QSize
from PySide6.QtGui import QIcon, QPixmap, QFont
import logging

from .controller import SessionController
from .widgets import CustomTimer, StateSliders, PingDialog
from .quick_capture import QuickNoteDialog
from modules.music.widgets import MusicWidget

# Настройка логирования
logger = logging.getLogger(__name__)


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
        # ✅ ИСПРАВЛЕНО: используем get_resource_path
        state_icon_pixmap = QPixmap(str(get_resource_path("resources/icons/brain1.png")))
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
        # ✅ ИСПРАВЛЕНО: используем get_resource_path
        music_icon_pixmap = QPixmap(str(get_resource_path("resources/icons/music1.png")))
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
        # ✅ ИСПРАВЛЕНО: используем get_resource_path
        self.quick_note_btn.setIcon(QIcon(str(get_resource_path("resources/icons/new_notes1.png"))))
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
        # ✅ ИСПРАВЛЕНО: используем get_resource_path
        self.pause_btn.setIcon(QIcon(str(get_resource_path("resources/icons/play1.png"))))
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

    def _setup_ping_manager(self):
        """Настраивает менеджер контроля активности"""
        try:
            self.ping_manager = PingManager(
                idle_ms=self._activity_check_interval * 60 * 1000,
                timeout_ms=90 * 60 * 1000,
                parent=self
            )
            self.ping_manager.pingNeeded.connect(self._show_ping_dialog)
            self.ping_manager.timeoutReached.connect(self._auto_pause_from_ping)
            logger.debug(f"PingManager настроен: idle={self._activity_check_interval} мин")
        except Exception as e:
            logger.error(f"Ошибка настройки PingManager: {e}", exc_info=True)

    def _show_ping_dialog(self):
        """Показывает диалог 'Ты ещё тут?' и ставит сессию на паузу"""
        try:
            self._session_controller.pause_session()

            dialog = PingDialog(self)
            dialog.continue_session.connect(self._on_continue_from_ping)
            dialog.pause_session.connect(self._on_pause_from_ping)
            dialog.exec()
        except Exception as e:
            logger.error(f"Ошибка показа PingDialog: {e}", exc_info=True)

    def _on_continue_from_ping(self):
        """Продолжение сессии после пинга"""
        try:
            self.ping_manager.user_confirmed()
            self._session_controller.resume_session()
            logger.debug("Сессия продолжена после пинга")
        except Exception as e:
            logger.error(f"Ошибка продолжения сессии: {e}", exc_info=True)

    def _on_pause_from_ping(self):
        """Пауза после пинга"""
        try:
            self.ping_manager.reset_idle()
            self.status_label.setText("Сессия на паузе")
            self.status_label.setStyleSheet("color: #F59E0B; font-weight: 500;")
            self.pause_btn.setText("Возобновить")
            # ✅ ИСПРАВЛЕНО: используем get_resource_path
            self.pause_btn.setIcon(QIcon(str(get_resource_path("resources/icons/play1.png"))))
        except Exception as e:
            logger.error(f"Ошибка паузы после пинга: {e}", exc_info=True)

    def _auto_pause_from_ping(self):
        """Авто-пауза, если пользователь вообще не ответил"""
        try:
            if not self._session_controller.is_session_paused():
                self._session_controller.pause_session()
            self.status_label.setText("Авто-пауза (нет активности)")
            self.status_label.setStyleSheet("color: #F59E0B; font-weight: 500;")
            self.pause_btn.setText("Возобновить")
            # ✅ ИСПРАВЛЕНО: используем get_resource_path
            self.pause_btn.setIcon(QIcon(str(get_resource_path("resources/icons/play1.png"))))
            logger.info("Авто-пауза сессии из-за отсутствия активности")
        except Exception as e:
            logger.error(f"Ошибка авто-паузы: {e}", exc_info=True)

    def _on_paused(self):
        """Обработчик паузы"""
        try:
            self.status_label.setText("Сессия на паузе")
            self.status_label.setStyleSheet("color: #F59E0B; font-weight: 500;")
            self.pause_btn.setText("Возобновить")
            # ✅ ИСПРАВЛЕНО: используем get_resource_path
            self.pause_btn.setIcon(QIcon(str(get_resource_path("resources/icons/play1.png"))))
            self.music_widget._controller.pause()
            logger.debug("Сессия на паузе")
        except Exception as e:
            logger.error(f"Ошибка обработки паузы: {e}", exc_info=True)

    def _on_resumed(self):
        """Обработчик возобновления"""
        try:
            self.status_label.setText("Сессия активна")
            self.status_label.setStyleSheet("color: #10B981; font-weight: 500;")
            self.pause_btn.setText("Пауза")
            # ✅ ИСПРАВЛЕНО: используем get_resource_path
            self.pause_btn.setIcon(QIcon(str(get_resource_path("resources/icons/pause1.png"))))
            self.ping_manager.reset_idle()
            self.music_widget._controller.resume()
            logger.debug("Сессия возобновлена")
        except Exception as e:
            logger.error(f"Ошибка возобновления сессии: {e}", exc_info=True)

    def _on_pause_clicked(self):
        """Обработчик кнопки паузы"""
        try:
            if self._session_controller.is_session_active():
                self._session_controller.pause_session()
            else:
                self._session_controller.resume_session()
        except Exception as e:
            logger.error(f"Ошибка переключения паузы: {e}", exc_info=True)
            SilentMessageBox.warning(self, "Ошибка", f"Не удалось изменить состояние сессии: {e}")

    def _on_end_clicked(self):
        """Обработчик кнопки завершения"""
        try:
            reply = SilentMessageBox.question(
                self, "Завершить сессию?",
                "Вы действительно хотите завершить сессию?",
                SilentMessageBox.Yes | SilentMessageBox.No, SilentMessageBox.No
            )

            if reply == SilentMessageBox.Yes:
                duration = self._session_controller.end_session()
                self.session_ended.emit(duration)
                logger.info(f"Сессия завершена, длительность: {duration} мин")
        except Exception as e:
            logger.error(f"Ошибка завершения сессии: {e}", exc_info=True)
            SilentMessageBox.warning(self, "Ошибка", f"Не удалось завершить сессию: {e}")

    def _on_quick_note(self):
        """Быстрая запись"""
        try:
            dialog = QuickNoteDialog(self)
            dialog.note_saved.connect(self._save_quick_note)
            dialog.exec()
        except Exception as e:
            logger.error(f"Ошибка открытия QuickNoteDialog: {e}", exc_info=True)

    def _save_quick_note(self, content: str):
        """Сохраняет быструю запись"""
        try:
            self._session_controller.add_quick_note(content)
            self.status_label.setText("✅ Запись сохранена")
            QTimer.singleShot(2000, lambda: self.status_label.setText("Сессия активна"))
            logger.debug("Быстрая запись сохранена")
        except Exception as e:
            logger.error(f"Ошибка сохранения быстрой записи: {e}", exc_info=True)
            self.status_label.setText("❌ Ошибка сохранения записи")

    def _on_state_changed(self, metric: str, value: int):
        """Обработчик изменения состояния"""
        try:
            self._session_controller.log_state(metric, value)
            self.ping_manager.reset_idle()
        except Exception as e:
            logger.error(f"Ошибка логирования состояния {metric}: {e}", exc_info=True)

    def start(self, topic_id: int, topic_name: str, activity_check_interval: int):
        """Запускает НОВУЮ сессию"""
        try:
            self._activity_check_interval = activity_check_interval
            self.topic_label.setText(f"Работа над темой: {topic_name}")

            # 🆕 Используем новый метод, который создаёт новую сессию
            session_id = self._session_controller.start_new_session(topic_id)

            if not session_id:
                SilentMessageBox.warning(self, "Ошибка", "Не удалось создать сессию")
                logger.warning(f"Не удалось создать сессию для темы {topic_id}")
                return

            # Сбрасываем UI
            # self.timer.reset()
            self.state_sliders.reset()

            # Обновляем UI
            self.status_label.setText("Сессия активна")
            self.status_label.setStyleSheet("color: #10B981; font-weight: 500;")
            self.pause_btn.setText("Пауза")
            # ✅ ИСПРАВЛЕНО: используем get_resource_path
            self.pause_btn.setIcon(QIcon(str(get_resource_path("resources/icons/pause1.png"))))

            # Запускаем PingManager
            self.ping_manager = PingManager(
                idle_ms=self._activity_check_interval * 60 * 1000,
                timeout_ms=90 * 60 * 1000,
                parent=self
            )
            self.ping_manager.pingNeeded.connect(self._show_ping_dialog)
            self.ping_manager.timeoutReached.connect(self._auto_pause_from_ping)

            # 🎵 Запускаем музыку, если выбран звук
            default_sound = self._music_controller.get_current_sound()
            if default_sound and default_sound != 'off':
                # Обновляем виджет и запускаем
                self.music_widget.refresh()
                self._music_controller.play(default_sound)
                self.music_widget._update_play_button()

            logger.info(f"Начата новая сессия {session_id} для темы '{topic_name}'")
        except Exception as e:
            logger.error(f"Ошибка запуска сессии: {e}", exc_info=True)
            SilentMessageBox.warning(self, "Ошибка", f"Не удалось запустить сессию: {e}")

    def cleanup(self):
        """Очищает ресурсы"""
        try:
            if hasattr(self, 'ping_manager'):
                self.ping_manager._idle_timer.stop()
                self.ping_manager._timeout_timer.stop()
                logger.debug("Ресурсы PingManager очищены")
        except Exception as e:
            logger.error(f"Ошибка очистки ресурсов: {e}", exc_info=True)

    def force_save_time(self):
        """Принудительно сохраняет текущее время сессии в БД"""
        try:
            session_id = self._session_controller.get_current_session_id()
            if session_id and self.timer:
                current_seconds = self._session_controller.get_elapsed_seconds()
                if current_seconds > 0:
                    from datebase.db_manager import db
                    db.execute(
                        "UPDATE sessions SET duration_minutes = ? WHERE id = ?",
                        (current_seconds // 60, session_id)
                    )
                    logger.debug(f"Принудительно сохранено время сессии {session_id}: {current_seconds} сек")
        except Exception as e:
            logger.error(f"Ошибка принудительного сохранения времени: {e}", exc_info=True)

    def force_save_state(self):
        """Принудительно сохраняет ползунки"""
        try:
            session_id = self._session_controller.get_current_session_id()
            if session_id:
                values = self.state_sliders.get_values()
                # Маппинг: concentration -> focus (в БД колонка focus)
                self._session_controller.save_slider_values(
                    values.get('concentration', 50),  # conc_slider -> focus
                    values.get('energy', 50),
                    values.get('interest', 50)
                )
                logger.debug(f"Принудительно сохранены ползунки сессии {session_id}")
        except Exception as e:
            logger.error(f"Ошибка принудительного сохранения состояния: {e}", exc_info=True)

    def hideEvent(self, event):
        """Сохраняем состояние при переключении вкладок"""
        try:
            if self._session_controller.get_current_session_id():
                self.force_save_time()
                self.force_save_state()
        except Exception as e:
            logger.error(f"Ошибка сохранения состояния при скрытии: {e}", exc_info=True)
        super().hideEvent(event)

    def resume_existing_session(self, session_id: int, topic_id: int, topic_name: str):
        """Загружает СТАРУЮ сессию из БД"""
        try:
            self.topic_label.setText(f"Работа над темой: {topic_name}")

            success = self._session_controller.load_and_resume_session(session_id)
            if not success:
                SilentMessageBox.warning(self, "Ошибка", "Не удалось загрузить сессию")
                logger.warning(f"Не удалось загрузить сессию {session_id}")
                return

            # 🆕 Восстанавливаем время из контроллера (оно уже загружено из БД)
            total_seconds = self._session_controller.get_elapsed_seconds()
            self.timer.set_time(total_seconds)

            slider_values = self._session_controller.get_slider_values(session_id)
            self.state_sliders.conc_slider.setValue(slider_values.get('focus', 50))
            self.state_sliders.energy_slider.setValue(slider_values.get('energy', 50))
            self.state_sliders.interest_slider.setValue(slider_values.get('interest', 50))

            if self._session_controller.is_session_active():
                self.status_label.setText("Сессия активна")
                self.status_label.setStyleSheet("color: #10B981; font-weight: 500;")
                self.pause_btn.setText("Пауза")
                # ✅ ИСПРАВЛЕНО: используем get_resource_path
                self.pause_btn.setIcon(QIcon(str(get_resource_path("resources/icons/pause1.png"))))
            else:
                self.status_label.setText("Сессия на паузе")
                self.status_label.setStyleSheet("color: #F59E0B; font-weight: 500;")
                self.pause_btn.setText("Возобновить")
                # ✅ ИСПРАВЛЕНО: используем get_resource_path
                self.pause_btn.setIcon(QIcon(str(get_resource_path("resources/icons/play1.png"))))

            self.ping_manager = PingManager(
                idle_ms=self._activity_check_interval * 60 * 1000,
                timeout_ms=90 * 60 * 1000,
                parent=self
            )
            self.ping_manager.pingNeeded.connect(self._show_ping_dialog)
            self.ping_manager.timeoutReached.connect(self._auto_pause_from_ping)

            # 🎵 Возобновляем музыку, если она была включена
            current_sound = self._music_controller.get_current_sound()
            if current_sound and current_sound != 'off':
                self.music_widget.refresh()
                self._music_controller.resume()
                self.music_widget._update_play_button()

            logger.info(f"Возобновлена существующая сессия {session_id}")
        except Exception as e:
            logger.error(f"Ошибка возобновления сессии {session_id}: {e}", exc_info=True)
            SilentMessageBox.warning(self, "Ошибка", f"Не удалось возобновить сессию: {e}")