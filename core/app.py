# core/app.py
import sys
import os
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QIcon

from .di.container import container
from .event_bus import event_bus
from .navigation import Navigation
from services.notification_service import NotificationService


class HFlowApp(QApplication):
    """
    Главный класс приложения HFlow.
    Инициализирует все зависимости и управляет жизненным циклом.
    """

    def __init__(self, argv: list):
        super().__init__(argv)

        # Устанавливаем атрибуты приложения
        self.setApplicationName("HFlow")
        self.setApplicationVersion("1.0")
        self.setOrganizationName("HarmonyFlow")

        # Инициализируем контейнер зависимостей
        container.init()

        container.session_controller.check_and_pause_active_session()

        # Создаём навигацию
        self.navigation = Navigation()

        # Загружаем настройки и применяем тему
        self._apply_theme()

        # Инициализируем уведомления
        self._init_notifications()

        # Устанавливаем глобальные горячие клавиши
        self._setup_global_hotkeys()

        # Запускаем автосохранение
        self._setup_autosave()

    def _apply_theme(self):
        """Применяет тему оформления из настроек"""
        from modules.settings.themes import ThemeManager

        theme = container.settings_controller.get_theme()
        theme_manager = ThemeManager()
        style = theme_manager.get_style(theme)
        self.setStyleSheet(style)

    def _init_notifications(self):
        """Инициализирует сервис уведомлений"""
        self.notification_service = container.notification_service

        # Включаем/отключаем уведомления согласно настройкам
        enabled = container.settings_controller.get_notifications_enabled()
        self.notification_service.set_enabled(enabled)

    def _setup_global_hotkeys(self):
        """Настраивает глобальные горячие клавиши"""
        # Глобальные хоткеи будут установлены в главном окне
        # так как им нужен родительский виджет
        pass

    def _setup_autosave(self):
        """Настраивает автосохранение"""
        interval = container.settings_controller.get_auto_save_interval()
        # Автосохранение будет настроено в редакторе заметок

    def shutdown(self):
        container.settings_controller.save_all()
        container.music_controller.stop()
        try:
            from database.db_manager import db
            db.close()
        except ImportError:
            pass

    def get_container(self):
        """Возвращает контейнер зависимостей"""
        return container

    def get_navigation(self):
        """Возвращает менеджер навигации"""
        return self.navigation