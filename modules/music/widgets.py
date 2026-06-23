# modules/music/widgets.py
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QComboBox,
    QLabel, QSlider, QFrame, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QTimer
from typing import Optional
import logging

from .controller import MusicController

# Настройка логирования
logger = logging.getLogger(__name__)


class MusicWidget(QWidget):
    """
    Полноценный виджет-плеер для управления музыкой.
    Включает: выбор звука, play/pause, stop, цикл, громкость, прогресс-бар.
    """

    sound_changed = Signal(str)
    volume_changed = Signal(float)

    def __init__(self, controller: MusicController, parent=None):
        super().__init__(parent)
        self._controller = controller
        self._setup_ui()
        self._load_sounds()
        self._connect_signals()
        self._update_play_button()

        # Таймер обновления прогресс-бара (10 раз в секунду)
        self._progress_timer = QTimer(self)
        self._progress_timer.setInterval(100)
        self._progress_timer.timeout.connect(self._update_progress)
        self._progress_timer.start()
        logger.debug("MusicWidget инициализирован")

    def _setup_ui(self):
        """Настраивает интерфейс"""
        try:
            main_layout = QVBoxLayout(self)
            main_layout.setContentsMargins(12, 10, 12, 10)
            main_layout.setSpacing(8)

            # === ВЕРХНЯЯ СТРОКА: выбор звука + кнопки управления ===
            top_row = QHBoxLayout()
            top_row.setSpacing(8)

            # Иконка
            self.icon_label = QLabel("🎵")
            self.icon_label.setStyleSheet("font-size: 16px;")
            top_row.addWidget(self.icon_label)

            # Выбор звука
            self.sound_combo = QComboBox()
            self.sound_combo.setFixedWidth(120)
            self.sound_combo.setStyleSheet("""
                QComboBox {
                    background-color: #F9FAFB;
                    border: 1px solid #E5E7EB;
                    border-radius: 6px;
                    padding: 4px 8px;
                    font-size: 12px;
                    color: #1F2937;
                }
                QComboBox:hover {
                    border: 1px solid #3B82F6;
                }
            """)
            top_row.addWidget(self.sound_combo)

            top_row.addSpacing(8)

            # Кнопка Play/Pause (большая, круглая)
            self.play_button = QPushButton("⏸")  # По умолчанию пауза (когда играет)
            self.play_button.setFixedSize(44, 44)
            self.play_button.setCursor(Qt.PointingHandCursor)
            self.play_button.setToolTip("Воспроизвести / Пауза")
            self.play_button.setStyleSheet("""
                        QPushButton {
                            background-color: #3B82F6;
                            color: white;
                            border: none;
                            border-radius: 22px;
                            font-size: 18px;
                            font-weight: bold;
                            padding: 0;
                        }
                        QPushButton:hover {
                            background-color: #2563EB;
                        }
                        QPushButton:pressed {
                            background-color: #1D4ED8;
                        }
                    """)
            top_row.addWidget(self.play_button)

            # Кнопка Stop
            self.stop_button = QPushButton("⏹")
            self.stop_button.setFixedSize(36, 36)
            self.stop_button.setCursor(Qt.PointingHandCursor)
            self.stop_button.setToolTip("Остановить")
            self.stop_button.setStyleSheet("""
                        QPushButton {
                            background-color: #FFFFFF;
                            color: #EF4444;
                            border: 2px solid #EF4444;
                            border-radius: 18px;
                            font-size: 16px;
                            font-weight: bold;
                            padding: 0;
                        }
                        QPushButton:hover {
                            background-color: #FEF2F2;
                        }
                        QPushButton:disabled {
                            color: #D1D5DB;
                            border-color: #D1D5DB;
                        }
                    """)
            top_row.addWidget(self.stop_button)

            # Кнопка Loop (цикл)
            self.loop_button = QPushButton("🔁")
            self.loop_button.setFixedSize(36, 36)
            self.loop_button.setCursor(Qt.PointingHandCursor)
            self.loop_button.setCheckable(True)
            self.loop_button.setChecked(True)  # По умолчанию цикл включён
            self.loop_button.setToolTip("Зациклить трек")
            self.loop_button.setStyleSheet("""
                        QPushButton {
                            background-color: #FFFFFF;
                            color: #6B7280;
                            border: 2px solid #E5E7EB;
                            border-radius: 18px;
                            font-size: 16px;
                            padding: 0;
                        }
                        QPushButton:checked {
                            background-color: #DBEAFE;
                            color: #3B82F6;
                            border: 2px solid #3B82F6;
                        }
                        QPushButton:hover {
                            background-color: #F3F4F6;
                        }
                    """)
            top_row.addWidget(self.loop_button)

            # Громкость
            self.volume_icon = QLabel("🔊")
            self.volume_icon.setStyleSheet("font-size: 14px;")
            top_row.addWidget(self.volume_icon)

            self.volume_slider = QSlider(Qt.Horizontal)
            self.volume_slider.setFixedWidth(100)
            self.volume_slider.setRange(0, 100)
            try:
                self.volume_slider.setValue(int(self._controller.get_volume() * 100))
            except Exception as e:
                logger.warning(f"Не удалось получить громкость: {e}")
                self.volume_slider.setValue(50)
            self.volume_slider.setToolTip("Громкость")
            self.volume_slider.setStyleSheet("""
                QSlider::groove:horizontal {
                    background: #E5E7EB;
                    height: 4px;
                    border-radius: 2px;
                }
                QSlider::handle:horizontal {
                    background: #3B82F6;
                    width: 12px;
                    height: 12px;
                    margin: -4px 0;
                    border-radius: 6px;
                }
                QSlider::sub-page:horizontal {
                    background: #3B82F6;
                    border-radius: 2px;
                }
            """)
            top_row.addWidget(self.volume_slider)

            self.volume_label = QLabel(f"{self.volume_slider.value()}%")
            self.volume_label.setFixedWidth(35)
            self.volume_label.setStyleSheet("color: #6B7280; font-size: 11px;")
            top_row.addWidget(self.volume_label)

            main_layout.addLayout(top_row)

            # === НИЖНЯЯ СТРОКА: прогресс-бар ===
            progress_row = QHBoxLayout()
            progress_row.setSpacing(8)

            self.time_current = QLabel("0:00")
            self.time_current.setStyleSheet("color: #6B7280; font-size: 11px; min-width: 35px;")
            progress_row.addWidget(self.time_current)

            # Прогресс-бар (слайдер)
            self.progress_slider = QSlider(Qt.Horizontal)
            self.progress_slider.setRange(0, 1000)  # 0-1000 для точности
            self.progress_slider.setValue(0)
            self.progress_slider.setToolTip("Перемотка")
            self.progress_slider.setCursor(Qt.PointingHandCursor)
            self.progress_slider.setStyleSheet("""
                QSlider::groove:horizontal {
                    background: #E5E7EB;
                    height: 6px;
                    border-radius: 3px;
                }
                QSlider::handle:horizontal {
                    background: #3B82F6;
                    width: 10px;
                    height: 10px;
                    margin: -2px 0;
                    border-radius: 5px;
                }
                QSlider::sub-page:horizontal {
                    background: #3B82F6;
                    border-radius: 3px;
                }
            """)
            progress_row.addWidget(self.progress_slider, 1)

            self.time_total = QLabel("0:00")
            self.time_total.setStyleSheet("color: #6B7280; font-size: 11px; min-width: 35px;")
            progress_row.addWidget(self.time_total)

            main_layout.addLayout(progress_row)

            # Флаг, чтобы не было конфликта при перемотке пользователем
            self._is_seeking = False
        except Exception as e:
            logger.error(f"Ошибка настройки UI MusicWidget: {e}", exc_info=True)

    def _load_sounds(self):
        """Загружает доступные звуки"""
        try:
            sounds = self._controller.get_available_sounds()
            if sounds is None:
                sounds = {}
                logger.warning("get_available_sounds() вернул None")

            self.sound_combo.blockSignals(True)
            self.sound_combo.clear()
            for sound_key, sound_name in sounds.items():
                self.sound_combo.addItem(sound_name, sound_key)

            current = self._controller.get_current_sound()
            index = self.sound_combo.findData(current)
            if index >= 0:
                self.sound_combo.setCurrentIndex(index)
            self.sound_combo.blockSignals(False)
            logger.debug(f"Загружено {len(sounds)} звуков")
        except Exception as e:
            logger.error(f"Ошибка загрузки звуков: {e}", exc_info=True)

    def _connect_signals(self):
        """Подключает сигналы"""
        self.sound_combo.currentIndexChanged.connect(self._on_sound_changed)
        self.play_button.clicked.connect(self._on_play_clicked)
        self.stop_button.clicked.connect(self._on_stop_clicked)
        self.loop_button.clicked.connect(self._on_loop_clicked)
        self.volume_slider.valueChanged.connect(self._on_volume_changed)

        # Прогресс-бар: начало и конец перемотки
        self.progress_slider.sliderPressed.connect(self._on_seek_start)
        self.progress_slider.sliderReleased.connect(self._on_seek_end)

    def _on_sound_changed(self, index: int):
        """Обработчик выбора звука"""
        try:
            sound_key = self.sound_combo.itemData(index)
            if sound_key and sound_key != 'off':
                self._controller.play(sound_key)
                self.sound_changed.emit(sound_key)
                self._update_play_button()
                self._update_progress()
                logger.debug(f"Выбран звук: {sound_key}")
            elif sound_key == 'off':
                self._controller.stop()
                self._update_play_button()
                logger.debug("Звук отключен")
        except Exception as e:
            logger.error(f"Ошибка изменения звука: {e}", exc_info=True)

    def _on_play_clicked(self):
        """Play/Pause"""
        try:
            if self._controller.is_playing():
                self._controller.pause()
                logger.debug("Пауза")
            else:
                current_sound = self._controller.get_current_sound()
                if current_sound == 'off':
                    # Если ничего не выбрано — запускаем первый доступный
                    if self.sound_combo.count() > 1:
                        # Пропускаем "off" если он первый
                        first_sound = self.sound_combo.itemData(1)
                        if first_sound and first_sound != 'off':
                            self.sound_combo.setCurrentIndex(1)
                            logger.debug(f"Автоматически выбран звук: {first_sound}")
                            return
                        else:
                            self.sound_combo.setCurrentIndex(0)
                            return
                else:
                    self._controller.resume()
                    logger.debug("Возобновление воспроизведения")
            self._update_play_button()
        except Exception as e:
            logger.error(f"Ошибка play/pause: {e}", exc_info=True)

    def _on_stop_clicked(self):
        """Stop"""
        try:
            self._controller.stop()
            self._update_play_button()
            self.progress_slider.setValue(0)
            self.time_current.setText("0:00")
            logger.debug("Остановлено")
        except Exception as e:
            logger.error(f"Ошибка остановки: {e}", exc_info=True)

    def _on_loop_clicked(self):
        """Переключение цикла"""
        try:
            new_state = self._controller.toggle_loop()
            self.loop_button.setChecked(new_state)
            logger.debug(f"Цикл {'включен' if new_state else 'выключен'}")
        except Exception as e:
            logger.error(f"Ошибка переключения цикла: {e}", exc_info=True)

    def _on_volume_changed(self, value: int):
        """Изменение громкости"""
        try:
            volume = value / 100.0
            self._controller.set_volume(volume)
            self.volume_label.setText(f"{value}%")

            # Меняем иконку в зависимости от громкости
            if value == 0:
                self.volume_icon.setText("🔇")
            elif value < 30:
                self.volume_icon.setText("🔈")
            elif value < 70:
                self.volume_icon.setText("🔉")
            else:
                self.volume_icon.setText("🔊")

            self.volume_changed.emit(volume)
            logger.debug(f"Громкость: {value}%")
        except Exception as e:
            logger.error(f"Ошибка изменения громкости: {e}", exc_info=True)

    def _on_seek_start(self):
        """Начало перемотки — останавливаем автообновление"""
        self._is_seeking = True

    def _on_seek_end(self):
        """Конец перемотки — устанавливаем позицию"""
        try:
            self._is_seeking = False
            duration = self._controller.get_duration()
            if duration > 0:
                position = int((self.progress_slider.value() / 1000.0) * duration)
                self._controller.set_position(position)
                logger.debug(f"Перемотка на позицию: {position} мс")
        except Exception as e:
            logger.error(f"Ошибка перемотки: {e}", exc_info=True)

    def _update_play_button(self):
        """Обновляет кнопку Play/Pause"""
        try:
            if self._controller.is_playing():
                self.play_button.setText("⏸")
                self.play_button.setToolTip("Пауза")
            else:
                self.play_button.setText("▶")
                self.play_button.setToolTip("Воспроизвести")

            has_sound = self._controller.get_current_sound() != 'off'
            self.stop_button.setEnabled(has_sound)
        except Exception as e:
            logger.error(f"Ошибка обновления кнопки play: {e}", exc_info=True)

    def _update_progress(self):
        """Обновляет прогресс-бар и время"""
        try:
            if self._is_seeking:
                return

            duration = self._controller.get_duration()
            position = self._controller.get_position()

            if duration > 0:
                progress = int((position / duration) * 1000)
                self.progress_slider.setValue(progress)
                self.time_total.setText(self._format_time(duration))
                self.time_current.setText(self._format_time(position))
            else:
                self.time_total.setText("0:00")
                self.time_current.setText("0:00")

            # Обновляем кнопку play/pause на всякий случай
            self._update_play_button()
        except Exception as e:
            logger.error(f"Ошибка обновления прогресса: {e}", exc_info=True)

    def _format_time(self, ms: int) -> str:
        """Форматирует миллисекунды в M:SS"""
        try:
            seconds = ms // 1000
            minutes = seconds // 60
            secs = seconds % 60
            return f"{minutes}:{secs:02d}"
        except Exception as e:
            logger.error(f"Ошибка форматирования времени: {e}", exc_info=True)
            return "0:00"

    def refresh(self):
        """Обновляет состояние"""
        try:
            self._load_sounds()
            self._update_play_button()
            logger.debug("MusicWidget обновлен")
        except Exception as e:
            logger.error(f"Ошибка обновления MusicWidget: {e}", exc_info=True)

    def set_enabled(self, enabled: bool):
        """Включает/отключает виджет"""
        try:
            self.sound_combo.setEnabled(enabled)
            self.play_button.setEnabled(enabled)
            self.stop_button.setEnabled(enabled)
            self.loop_button.setEnabled(enabled)
            self.volume_slider.setEnabled(enabled)
            self.progress_slider.setEnabled(enabled)
        except Exception as e:
            logger.error(f"Ошибка set_enabled: {e}", exc_info=True)

    def reset(self):
        """Сбрасывает"""
        try:
            self._controller.stop()
            off_index = self.sound_combo.findData('off')
            if off_index >= 0:
                self.sound_combo.setCurrentIndex(off_index)
            self._update_play_button()
            self.progress_slider.setValue(0)
            self.time_current.setText("0:00")
            logger.debug("MusicWidget сброшен")
        except Exception as e:
            logger.error(f"Ошибка сброса MusicWidget: {e}", exc_info=True)