# modules/music/controller.py
from typing import Optional, Dict
from services.sound_service import SoundService


class MusicController:
    """
    Контроллер для управления музыкой/звуками во время сессий.
    Упрощённая версия для v1.0.
    """

    def __init__(self, sound_service: SoundService):
        """
        Args:
            sound_service: Сервис для воспроизведения звуков
        """
        self._sound_service = sound_service
        self._is_playing = False
        self._current_sound = 'off'

    def get_available_sounds(self) -> Dict[str, str]:
        """
        Возвращает доступные звуки

        Returns:
            Словарь {ключ: отображаемое_название}
        """
        return self._sound_service.get_available_sounds()

    def play(self, sound_key: str):
        """
        Начинает воспроизведение выбранного звука

        Args:
            sound_key: 'white_noise', 'rain', 'forest', 'cafe', 'off'
        """
        self._sound_service.play(sound_key)
        self._current_sound = sound_key
        self._is_playing = sound_key != 'off'

    def stop(self):
        """Останавливает воспроизведение"""
        self._sound_service.stop()
        self._is_playing = False
        self._current_sound = 'off'

    def pause(self):
        """Ставит на паузу"""
        if self._is_playing and self._current_sound != 'off':
            self._sound_service.pause()
            self._is_playing = False

    def resume(self):
        """Возобновляет воспроизведение"""
        if not self._is_playing and self._current_sound != 'off':
            self._sound_service.resume()
            self._is_playing = True

    def set_volume(self, volume: float):
        """
        Устанавливает громкость

        Args:
            volume: 0.0 - 1.0
        """
        self._sound_service.set_volume(volume)

    def get_volume(self) -> float:
        """Возвращает текущую громкость"""
        return self._sound_service.get_volume()

    def get_current_sound(self) -> str:
        """Возвращает текущий звук"""
        return self._current_sound

    def get_current_sound_name(self) -> str:
        """Возвращает название текущего звука"""
        return self._sound_service.get_current_sound_name()

    def is_playing(self) -> bool:
        """Возвращает, воспроизводится ли звук"""
        return self._is_playing and self._current_sound != 'off'

    def cleanup(self):
        """Очищает ресурсы"""
        self.stop()
        self._sound_service.cleanup()