# modules/settings/__init__.py
from .controller import SettingsController
from .view import SettingsView
from .themes import ThemeManager

__all__ = [
    'SettingsController',
    'SettingsView',
    'ThemeManager',
]