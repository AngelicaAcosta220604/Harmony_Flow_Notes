# modules/settings/controller.py
from typing import Optional, Dict, Any
from datebase.repositories.settings_repo import SettingsRepository
from models.settings import Settings


class SettingsController:
    """Контроллер для управления настройками приложения"""

    def __init__(self, settings_repo: SettingsRepository):
        self._repo = settings_repo
        self._settings: Optional[Settings] = None
        self._load_settings()

    def _load_settings(self):
        """Загружает настройки из БД"""
        settings_dict = self._repo.get_all()
        self._settings = Settings.from_dict(settings_dict)

    def get_all(self) -> Settings:
        """Возвращает все настройки"""
        if self._settings is None:
            self._load_settings()
        return self._settings

    def get(self, key: str, default: Any = None) -> Any:
        """Возвращает значение конкретной настройки"""
        settings = self.get_all()
        return getattr(settings, key, default)

    def set(self, key: str, value: Any) -> bool:
        """
        Устанавливает значение настройки

        Args:
            key: Имя настройки
            value: Новое значение
        """
        if not hasattr(self._settings, key):
            return False

        setattr(self._settings, key, value)

        # Сохраняем в БД
        if key == 'user_name':
            return self._repo.set_user_name(value)
        elif key == 'theme':
            return self._repo.set_theme(value)
        elif key == 'activity_check_interval_minutes':
            return self._repo.set_int(key, value)
        elif key == 'auto_pause_minutes':
            return self._repo.set_int(key, value)
        elif key == 'auto_save_interval_seconds':
            return self._repo.set_int(key, value)
        elif key == 'notifications_enabled':
            return self._repo.set_bool(key, value)
        elif key == 'default_sound':
            return self._repo.set(key, value)

        return False

    def get_user_name(self) -> str:
        """Возвращает имя пользователя"""
        return self._repo.get_user_name()

    def set_user_name(self, name: str) -> bool:
        """Устанавливает имя пользователя"""
        name = name.strip()
        if not name:
            name = "Пользователь"
        return self.set('user_name', name)

    def get_theme(self) -> str:
        """Возвращает тему оформления"""
        return self._repo.get_theme()

    def set_theme(self, theme: str) -> bool:
        """Устанавливает тему оформления"""
        if theme not in ('light', 'dark'):
            return False
        return self.set('theme', theme)

    def get_notifications_enabled(self) -> bool:
        """Возвращает, включены ли уведомления"""
        return self._repo.get_bool('notifications_enabled', True)

    def set_notifications_enabled(self, enabled: bool) -> bool:
        """Включает/выключает уведомления"""
        return self.set('notifications_enabled', enabled)

    def get_activity_check_interval(self) -> int:
        """Возвращает интервал проверки активности (минуты)"""
        return self._repo.get_int('activity_check_interval_minutes', 15)

    def get_auto_pause_minutes(self) -> int:
        """Возвращает длительность до авто-паузы (минуты)"""
        return self._repo.get_int('auto_pause_minutes', 10)

    def get_auto_save_interval(self) -> int:
        """Возвращает интервал автосохранения (секунды)"""
        return self._repo.get_int('auto_save_interval_seconds', 60)

    def get_default_sound(self) -> str:
        """Возвращает звук по умолчанию"""
        return self._repo.get('default_sound', 'off')

    def save_all(self) -> bool:
        """Сохраняет все текущие настройки в БД"""
        if not self._settings:
            return False

        success = True
        for key, value in self._settings.to_dict().items():
            if not self.set(key, value):
                success = False

        return success

    def reset_to_defaults(self) -> bool:
        """Сбрасывает настройки к значениям по умолчанию"""
        default_settings = Settings()
        self._settings = default_settings
        return self.save_all()

    def get_onboarding_completed(self) -> bool:
        """Возвращает True, если онбординг уже пройден"""
        return self._settings_repo.get_bool('onboarding_completed', False)

    def set_onboarding_completed(self, completed: bool) -> bool:
        """Устанавливает флаг прохождения онбординга"""
        return self._settings_repo.set_bool('onboarding_completed', completed)