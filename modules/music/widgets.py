# modules/music/widgets.py
from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QComboBox, QLabel, QSlider
from PySide6.QtCore import Qt, Signal
from typing import Optional

from .controller import MusicController


class MusicWidget(QWidget):
    """
    Виджет для управления музыкой.
    Компактный элемент управления для экрана сессии.
    """

    # Сигналы для внешнего использования
    sound_changed = Signal(str)  # когда изменился звук
    volume_changed = Signal(float)  # когда изменилась громкость

    def __init__(self, controller: MusicController, parent=None):
        super().__init__(parent)
        self._controller = controller
        self._setup_ui()
        self._load_sounds()
        self._connect_signals()

    def _setup_ui(self):
        """Настраивает интерфейс"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Иконка (текстовая для простоты)
        self.icon_label = QLabel("🎵")
        layout.addWidget(self.icon_label)

        # Выбор звука
        self.sound_combo = QComboBox()
        self.sound_combo.setFixedWidth(100)
        layout.addWidget(self.sound_combo)

        # Кнопка Play/Pause
        self.play_button = QPushButton("▶")
        self.play_button.setFixedSize(30, 30)
        self.play_button.setToolTip("Воспроизвести / Пауза")
        layout.addWidget(self.play_button)

        # Кнопка Stop
        self.stop_button = QPushButton("⏹")
        self.stop_button.setFixedSize(30, 30)
        self.stop_button.setToolTip("Остановить")
        layout.addWidget(self.stop_button)

        # Регулятор громкости
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setFixedWidth(80)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(int(self._controller.get_volume() * 100))
        self.volume_slider.setToolTip("Громкость")
        layout.addWidget(self.volume_slider)

        # Label громкости
        self.volume_label = QLabel(f"{self.volume_slider.value()}%")
        self.volume_label.setFixedWidth(35)
        layout.addWidget(self.volume_label)

        self.setLayout(layout)

    def _load_sounds(self):
        """Загружает доступные звуки в комбобокс"""
        sounds = self._controller.get_available_sounds()

        self.sound_combo.clear()
        for sound_key, sound_name in sounds.items():
            self.sound_combo.addItem(sound_name, sound_key)

        # Устанавливаем текущий звук
        current = self._controller.get_current_sound()
        index = self.sound_combo.findData(current)
        if index >= 0:
            self.sound_combo.setCurrentIndex(index)

    def _connect_signals(self):
        """Подключает сигналы"""
        self.sound_combo.currentIndexChanged.connect(self._on_sound_changed)
        self.play_button.clicked.connect(self._on_play_clicked)
        self.stop_button.clicked.connect(self._on_stop_clicked)
        self.volume_slider.valueChanged.connect(self._on_volume_changed)

    def _on_sound_changed(self, index: int):
        """Обработчик изменения выбранного звука"""
        sound_key = self.sound_combo.itemData(index)
        if sound_key:
            self._controller.play(sound_key)
            self.sound_changed.emit(sound_key)
            self._update_play_button()

    def _on_play_clicked(self):
        """Обработчик клика по кнопке Play/Pause"""
        if self._controller.is_playing():
            self._controller.pause()
        else:
            current_sound = self._controller.get_current_sound()
            if current_sound == 'off':
                # Если ничего не выбрано, выбираем первый доступный
                if self.sound_combo.count() > 0:
                    self.sound_combo.setCurrentIndex(0)
            else:
                self._controller.resume()

        self._update_play_button()

    def _on_stop_clicked(self):
        """Обработчик клика по кнопке Stop"""
        self._controller.stop()
        self._update_play_button()

    def _on_volume_changed(self, value: int):
        """Обработчик изменения громкости"""
        volume = value / 100.0
        self._controller.set_volume(volume)
        self.volume_label.setText(f"{value}%")
        self.volume_changed.emit(volume)

    def _update_play_button(self):
        """Обновляет текст кнопки Play/Pause"""
        if self._controller.is_playing():
            self.play_button.setText("⏸")
            self.play_button.setToolTip("Пауза")
        else:
            self.play_button.setText("▶")
            self.play_button.setToolTip("Воспроизвести")

        # Обновляем состояние кнопки Stop
        has_sound = self._controller.get_current_sound() != 'off'
        self.stop_button.setEnabled(has_sound)

    def refresh(self):
        """Обновляет состояние виджета"""
        self._load_sounds()
        self._update_play_button()

    def set_enabled(self, enabled: bool):
        """Включает/отключает виджет"""
        self.sound_combo.setEnabled(enabled)
        self.play_button.setEnabled(enabled)
        self.stop_button.setEnabled(enabled and self._controller.get_current_sound() != 'off')
        self.volume_slider.setEnabled(enabled)

    def reset(self):
        """Сбрасывает виджет в начальное состояние"""
        self._controller.stop()
        # Сбрасываем выбор на "off"
        off_index = self.sound_combo.findData('off')
        if off_index >= 0:
            self.sound_combo.setCurrentIndex(off_index)
        self._update_play_button()