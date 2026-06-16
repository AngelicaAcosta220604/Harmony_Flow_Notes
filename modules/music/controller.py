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

    def toggle_loop(self) -> bool:
        """Переключает зацикливание. Возвращает новое состояние."""
        current = self._sound_service.is_loop_enabled()
        self._sound_service.set_loop_enabled(not current)
        return not current

    def is_loop_enabled(self) -> bool:
        """Возвращает, включено ли зацикливание"""
        return self._sound_service.is_loop_enabled()

    def get_position(self) -> int:
        """Текущая позиция в мс"""
        return self._sound_service.get_position()

    def get_duration(self) -> int:
        """Длительность в мс"""
        return self._sound_service.get_duration()

    def set_position(self, position_ms: int):
        """Устанавливает позицию"""
        self._sound_service.set_position(position_ms)

    def toggle_play_pause(self):
        """Переключает play/pause"""
        self._sound_service.toggle_play_pause()
        self._is_playing = self._sound_service.is_playing()

    @property
    def position_changed(self):
        """Прокси для сигнала позиции"""
        return self._sound_service.position_changed