# database/repositories/settings_repo.py
from typing import Optional, Dict, Any
from database.db_manager import db


class SettingsRepository:
    """Репозиторий для работы с настройками"""

    def get(self, key: str, default: str = '') -> str:
        """Возвращает значение настройки"""
        row = db.fetchone("SELECT setting_value FROM app_settings WHERE setting_key = ?", (key,))
        return row['setting_value'] if row else default

    def get_int(self, key: str, default: int = 0) -> int:
        """Возвращает целочисленное значение настройки"""
        value = self.get(key, str(default))
        try:
            return int(value)
        except ValueError:
            return default

    def get_bool(self, key: str, default: bool = False) -> bool:
        """Возвращает булево значение настройки"""
        value = self.get(key, str(default).lower())
        return value.lower() in ('true', '1', 'yes')

    def set(self, key: str, value: str) -> bool:
        """Устанавливает значение настройки"""
        existing = db.fetchone("SELECT id FROM app_settings WHERE setting_key = ?", (key,))

        if existing:
            db.update('app_settings', {'setting_value': value}, 'setting_key = ?', (key,))
        else:
            db.insert('app_settings', {'setting_key': key, 'setting_value': value})

        return True

    def set_int(self, key: str, value: int) -> bool:
        """Устанавливает целочисленное значение настройки"""
        return self.set(key, str(value))

    def set_bool(self, key: str, value: bool) -> bool:
        """Устанавливает булево значение настройки"""
        return self.set(key, 'true' if value else 'false')

    def get_all(self) -> Dict[str, str]:
        """Возвращает все настройки"""
        rows = db.fetchall("SELECT setting_key, setting_value FROM app_settings")
        return {row['setting_key']: row['setting_value'] for row in rows}

    def get_user_name(self) -> str:
        """Возвращает имя пользователя"""
        return self.get('user_name', 'Пользователь')

    def set_user_name(self, name: str) -> bool:
        """Устанавливает имя пользователя"""
        return self.set('user_name', name.strip() or 'Пользователь')

    def get_theme(self) -> str:
        """Возвращает тему оформления"""
        return self.get('theme', 'light')

    def set_theme(self, theme: str) -> bool:
        """Устанавливает тему оформления"""
        if theme in ('light', 'dark'):
            return self.set('theme', theme)
        return False