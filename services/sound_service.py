# services/sound_service.py
from pathlib import Path
from typing import Optional, Dict
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtCore import QUrl, QObject, Signal
import logging

from utils.resource_paths import get_resource_path

# Настройка логирования
logger = logging.getLogger(__name__)


class SoundService(QObject):
    """Сервис для воспроизведения звуков с надёжным зацикливанием"""

    # Сигнал для обновления позиции (для прогресс-бара)
    position_changed = Signal(int)

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
            self.sounds_dir = get_resource_path("resources/sounds")

        self._player: Optional[QMediaPlayer] = None
        self._audio_output: Optional[QAudioOutput] = None
        self._current_sound: str = 'off'
        self._volume: float = 0.5
        self._loop_enabled: bool = True

    def _init_player(self):
        """Инициализирует плеер"""
        try:
            if self._player is None:
                self._player = QMediaPlayer()
                self._audio_output = QAudioOutput()
                self._player.setAudioOutput(self._audio_output)
                self._audio_output.setVolume(self._volume)

                # Обработчик окончания трека
                self._player.mediaStatusChanged.connect(self._on_media_status_changed)
                # Сигнал позиции для прогресс-бара
                self._player.positionChanged.connect(self._on_position_changed)

                logger.debug("Плеер инициализирован")
        except Exception as e:
            logger.error(f"Ошибка инициализации плеера: {e}")

    def _on_position_changed(self, position: int):
        """Обработчик изменения позиции"""
        try:
            self.position_changed.emit(position)
        except Exception as e:
            logger.error(f"Ошибка в _on_position_changed: {e}")

    def _on_media_status_changed(self, status):
        """Обработчик изменения статуса медиа — зацикливаем трек"""
        try:
            # EndOfMedia = 6 в PySide6 (проверяем числовое значение для надёжности)
            if status == 6 and self._loop_enabled and self._current_sound != 'off':
                logger.debug("Трек закончился, запускаем зацикливание")
                self._player.setPosition(0)
                self._player.play()
        except Exception as e:
            logger.error(f"Ошибка в _on_media_status_changed: {e}")

    def set_loop_enabled(self, enabled: bool):
        """Включает/отключает зацикливание"""
        self._loop_enabled = enabled

    def is_loop_enabled(self) -> bool:
        """Возвращает, включено ли зацикливание"""
        return self._loop_enabled

    def set_volume(self, volume: float):
        """Устанавливает громкость"""
        try:
            self._volume = max(0.0, min(1.0, volume))
            if self._audio_output:
                self._audio_output.setVolume(self._volume)
        except Exception as e:
            logger.error(f"Ошибка установки громкости: {e}")

    def get_volume(self) -> float:
        """Возвращает текущую громкость"""
        return self._volume

    def play(self, sound_name: str):
        """Начинает воспроизведение"""
        try:
            # Останавливаем текущее
            if self._player and self._player.playbackState() == QMediaPlayer.PlayingState:
                self._player.stop()

            if sound_name == 'off' or sound_name not in self.SOUNDS:
                self._current_sound = 'off'
                return

            sound_file = self.SOUNDS.get(sound_name)
            if not sound_file:
                logger.warning(f"Файл для звука '{sound_name}' не указан")
                return

            sound_path = self.sounds_dir / sound_file
            if not sound_path.exists():
                logger.error(f"Файл не найден: {sound_path}")
                return

            self._init_player()

            # Устанавливаем источник
            self._player.setSource(QUrl.fromLocalFile(str(sound_path)))
            self._player.play()
            self._current_sound = sound_name

            logger.debug(f"Воспроизведение: {sound_name}")
        except Exception as e:
            logger.error(f"Ошибка воспроизведения: {e}")

    def stop(self):
        """Останавливает воспроизведение"""
        try:
            if self._player:
                self._player.stop()
            self._current_sound = 'off'
        except Exception as e:
            logger.error(f"Ошибка остановки: {e}")

    def pause(self):
        """Ставит на паузу"""
        try:
            if self._player and self._player.playbackState() == QMediaPlayer.PlayingState:
                self._player.pause()
        except Exception as e:
            logger.error(f"Ошибка паузы: {e}")

    def resume(self):
        """Возобновляет воспроизведение"""
        try:
            if not self._player or self._current_sound == 'off':
                return

            state = self._player.playbackState()
            if state == QMediaPlayer.PausedState:
                self._player.play()
            elif state == QMediaPlayer.StoppedState:
                # Если плеер остановлен — перезапускаем с начала
                sound_file = self.SOUNDS.get(self._current_sound)
                if sound_file:
                    sound_path = self.sounds_dir / sound_file
                    if sound_path.exists():
                        self._player.setSource(QUrl.fromLocalFile(str(sound_path)))
                        self._player.play()
        except Exception as e:
            logger.error(f"Ошибка возобновления: {e}")

    def toggle_play_pause(self):
        """Переключает play/pause"""
        try:
            if self._player and self._current_sound != 'off':
                if self._player.playbackState() == QMediaPlayer.PlayingState:
                    self.pause()
                else:
                    self.resume()
        except Exception as e:
            logger.error(f"Ошибка toggle_play_pause: {e}")

    def get_position(self) -> int:
        """Возвращает текущую позицию в мс"""
        try:
            return self._player.position() if self._player else 0
        except Exception as e:
            logger.error(f"Ошибка get_position: {e}")
            return 0

    def get_duration(self) -> int:
        """Возвращает длительность в мс"""
        try:
            return self._player.duration() if self._player else 0
        except Exception as e:
            logger.error(f"Ошибка get_duration: {e}")
            return 0

    def set_position(self, position_ms: int):
        """Устанавливает позицию в мс"""
        try:
            if self._player:
                self._player.setPosition(position_ms)
        except Exception as e:
            logger.error(f"Ошибка set_position: {e}")

    def get_current_sound(self) -> str:
        """Возвращает текущий звук"""
        return self._current_sound

    def get_current_sound_name(self) -> str:
        """Возвращает название текущего звука"""
        return self.SOUND_NAMES.get(self._current_sound, 'Отключено')

    def get_available_sounds(self) -> Dict[str, str]:
        """Возвращает список доступных звуков"""
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
        try:
            if self._player and self._current_sound != 'off':
                return self._player.playbackState() == QMediaPlayer.PlayingState
            return False
        except Exception as e:
            logger.error(f"Ошибка is_playing: {e}")
            return False

    def cleanup(self):
        """Освобождает ресурсы"""
        try:
            if self._player:
                self._player.stop()
                self._player.deleteLater()
                self._player = None
            if self._audio_output:
                self._audio_output.deleteLater()
                self._audio_output = None
            logger.debug("Ресурсы освобождены")
        except Exception as e:
            logger.error(f"Ошибка cleanup: {e}")