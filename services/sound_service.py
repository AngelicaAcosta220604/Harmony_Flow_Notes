# services/sound_service.py

from pathlib import Path
from typing import Optional, Dict
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtCore import QUrl, QObject, Signal


class SoundService(QObject):
    """Сервис для воспроизведения звуков с надёжным зацикливанием"""

    # Сигнал для обновления позиции (для прогресс-бара)
    position_changed = Signal(int)  # позиция в мс

    # Доступные звуки
    SOUNDS = {
        'white_noise': 'white_noise.mp3',
        'rain': 'rain.mp3',
        'forest': 'forest.mp3',
        'cafe': 'cafe.mp3',
        'off': None
    }

    SOUND_NAMES = {
        'white_noise': 'Белый шум',
        'rain': 'Дождь',
        'forest': 'Лес',
        'cafe': 'Кафе',
        'off': 'Отключено'
    }

    def __init__(self, sounds_dir: Optional[str] = None):
        super().__init__()
        if sounds_dir:
            self.sounds_dir = Path(sounds_dir)
        else:
            self.sounds_dir = Path(__file__).parent.parent / "resources" / "sounds"
        self._player: Optional[QMediaPlayer] = None
        self._audio_output: Optional[QAudioOutput] = None
        self._current_sound: str = 'off'
        self._volume: float = 0.5
        self._loop_enabled: bool = True  # 🆕 Флаг цикла

    def _init_player(self):
        """Инициализирует плеер"""
        if self._player is None:
            self._player = QMediaPlayer()
            self._audio_output = QAudioOutput()
            self._player.setAudioOutput(self._audio_output)
            self._audio_output.setVolume(self._volume)

            # 🆕 Обработчик окончания трека — для надёжного зацикливания
            self._player.mediaStatusChanged.connect(self._on_media_status_changed)
            # 🆕 Сигнал позиции для прогресс-бара
            self._player.positionChanged.connect(self.position_changed.emit)

    def _on_media_status_changed(self, status):
        """Обработчик изменения статуса медиа — зацикливаем трек"""
        # EndOfMedia = 6 в PySide6
        if status == QMediaPlayer.EndOfMedia and self._loop_enabled and self._current_sound != 'off':
            self._player.setPosition(0)
            self._player.play()

    def set_loop_enabled(self, enabled: bool):
        """Включает/отключает зацикливание"""
        self._loop_enabled = enabled

    def is_loop_enabled(self) -> bool:
        """Возвращает, включено ли зацикливание"""
        return self._loop_enabled

    def set_volume(self, volume: float):
        self._volume = max(0.0, min(1.0, volume))
        if self._audio_output:
            self._audio_output.setVolume(self._volume)

    def get_volume(self) -> float:
        return self._volume

    def play(self, sound_name: str):
        """Начинает воспроизведение"""
        # Останавливаем текущее, но не сбрасываем состояние плеера
        if self._player and self._player.playbackState() == QMediaPlayer.PlayingState:
            self._player.stop()

        if sound_name == 'off' or sound_name not in self.SOUNDS:
            self._current_sound = 'off'
            return

        sound_file = self.SOUNDS.get(sound_name)
        if not sound_file:
            return

        sound_path = self.sounds_dir / sound_file
        if not sound_path.exists():
            print(f"[SoundService] Файл не найден: {sound_path}")
            return

        self._init_player()
        self._player.setSource(QUrl.fromLocalFile(str(sound_path)))
        self._player.play()
        self._current_sound = sound_name

    def stop(self):
        """Останавливает воспроизведение"""
        if self._player:
            self._player.stop()
        self._current_sound = 'off'

    def pause(self):
        """Ставит на паузу"""
        if self._player and self._player.playbackState() == QMediaPlayer.PlayingState:
            self._player.pause()

    def resume(self):
        """Возобновляет воспроизведение — работает из любого состояния"""
        if not self._player or self._current_sound == 'off':
            return

        state = self._player.playbackState()
        if state == QMediaPlayer.PausedState:
            self._player.play()
        elif state == QMediaPlayer.StoppedState:
            # 🆕 Если плеер остановлен — запускаем заново
            self._player.play()

    def toggle_play_pause(self):
        """Переключает play/pause"""
        if self._player and self._current_sound != 'off':
            if self._player.playbackState() == QMediaPlayer.PlayingState:
                self.pause()
            else:
                self.resume()

    def get_position(self) -> int:
        """Возвращает текущую позицию в мс"""
        return self._player.position() if self._player else 0

    def get_duration(self) -> int:
        """Возвращает длительность в мс"""
        return self._player.duration() if self._player else 0

    def set_position(self, position_ms: int):
        """Устанавливает позицию в мс"""
        if self._player:
            self._player.setPosition(position_ms)

    def get_current_sound(self) -> str:
        return self._current_sound

    def get_current_sound_name(self) -> str:
        return self.SOUND_NAMES.get(self._current_sound, 'Отключено')

    def get_available_sounds(self) -> Dict[str, str]:
        available = {}
        for key, filename in self.SOUNDS.items():
            if key == 'off':
                available[key] = self.SOUND_NAMES[key]
            else:
                sound_path = self.sounds_dir / filename
                if sound_path.exists():
                    available[key] = self.SOUND_NAMES[key]
        return available

    def is_playing(self) -> bool:
        """Проверяет, играет ли сейчас"""
        if self._player and self._current_sound != 'off':
            return self._player.playbackState() == QMediaPlayer.PlayingState
        return False

    def cleanup(self):
        if self._player:
            self._player.stop()
            self._player.deleteLater()
            self._player = None
        if self._audio_output:
            self._audio_output.deleteLater()
            self._audio_output = None