# services/sound_service.py
from pathlib import Path
from typing import Optional, Dict
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtCore import QUrl


class SoundService:
    """Сервис для воспроизведения звуков (упрощённая версия)"""

    # Доступные звуки
    SOUNDS = {
        'white_noise': 'white_noise.mp3',
        'rain': 'rain.mp3',
        'forest': 'forest.mp3',
        'cafe': 'cafe.mp3',
        'off': None
    }

    # Русские названия
    SOUND_NAMES = {
        'white_noise': 'Белый шум',
        'rain': 'Дождь',
        'forest': 'Лес',
        'cafe': 'Кафе',
        'off': 'Отключено'
    }

    def __init__(self, sounds_dir: Optional[str] = None):
        """
        Args:
            sounds_dir: Директория со звуковыми файлами.
        """
        if sounds_dir:
            self.sounds_dir = Path(sounds_dir)
        else:
            self.sounds_dir = Path(__file__).parent.parent / "resources" / "sounds"

        self._player: Optional[QMediaPlayer] = None
        self._audio_output: Optional[QAudioOutput] = None
        self._current_sound: str = 'off'
        self._volume: float = 0.5  # 0.0 - 1.0

    def _init_player(self):
        """Инициализирует плеер (ленивая инициализация)"""
        if self._player is None:
            self._player = QMediaPlayer()
            self._audio_output = QAudioOutput()
            self._player.setAudioOutput(self._audio_output)
            self._audio_output.setVolume(self._volume)

    def set_volume(self, volume: float):
        """
        Устанавливает громкость

        Args:
            volume: 0.0 - 1.0
        """
        self._volume = max(0.0, min(1.0, volume))
        if self._audio_output:
            self._audio_output.setVolume(self._volume)

    def get_volume(self) -> float:
        """Возвращает текущую громкость"""
        return self._volume

    def play(self, sound_name: str):
        self.stop()

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

        # Бесконечное повторение (для PySide6 6.11+)
        try:
            self._player.setLoops(QMediaPlayer.Infinite)
        except AttributeError:
            pass

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
        """Возобновляет воспроизведение"""
        if self._player and self._player.playbackState() == QMediaPlayer.PausedState:
            self._player.play()

    def get_current_sound(self) -> str:
        """Возвращает текущий звук"""
        return self._current_sound

    def get_current_sound_name(self) -> str:
        """Возвращает русское название текущего звука"""
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

    def cleanup(self):
        """Очищает ресурсы"""
        if self._player:
            self._player.stop()
            self._player.deleteLater()
            self._player = None

        if self._audio_output:
            self._audio_output.deleteLater()
            self._audio_output = None