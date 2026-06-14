# models/settings.py
from dataclasses import dataclass, field
from typing import Dict, Any


@dataclass
class Settings:
    """Модель настроек приложения"""
    user_name: str = "Пользователь"
    theme: str = "light"  # 'light' or 'dark'
    activity_check_interval_minutes: int = 15
    auto_pause_minutes: int = 10
    auto_save_interval_seconds: int = 60
    notifications_enabled: bool = True
    default_sound: str = "off"  # 'white_noise', 'rain', 'forest', 'cafe', 'off'

    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> 'Settings':
        """Создаёт объект из словаря настроек"""
        return cls(
            user_name=data.get('user_name', 'Пользователь'),
            theme=data.get('theme', 'light'),
            activity_check_interval_minutes=int(data.get('activity_check_interval_minutes', '15')),
            auto_pause_minutes=int(data.get('auto_pause_minutes', '10')),
            auto_save_interval_seconds=int(data.get('auto_save_interval_seconds', '60')),
            notifications_enabled=data.get('notifications_enabled', 'true').lower() == 'true',
            default_sound=data.get('default_sound', 'off')
        )

    def to_dict(self) -> Dict[str, str]:
        """Преобразует в словарь для БД"""
        return {
            'user_name': self.user_name,
            'theme': self.theme,
            'activity_check_interval_minutes': str(self.activity_check_interval_minutes),
            'auto_pause_minutes': str(self.auto_pause_minutes),
            'auto_save_interval_seconds': str(self.auto_save_interval_seconds),
            'notifications_enabled': 'true' if self.notifications_enabled else 'false',
            'default_sound': self.default_sound
        }

    @property
    def theme_display(self) -> str:
        """Отображаемое название темы"""
        return "Светлая" if self.theme == 'light' else "Тёмная"

    @property
    def sound_display(self) -> str:
        """Отображаемое название звука"""
        sounds = {
            'white_noise': 'Белый шум',
            'rain': 'Дождь',
            'forest': 'Лес',
            'cafe': 'Кафе',
            'off': 'Отключено'
        }
        return sounds.get(self.default_sound, 'Отключено')