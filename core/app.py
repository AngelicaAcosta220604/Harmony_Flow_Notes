# core/app.py
import sys
import os
import logging
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QIcon

from .di.container import container
from .event_bus import event_bus
from .navigation import Navigation
from services.notification_service import NotificationService

# Настройка логирования
logger = logging.getLogger(__name__)


class HFlowApp(QApplication):
    """
    Главный класс приложения HFlow.
    Инициализирует все зависимости и управляет жизненным циклом.
    """

    def __init__(self, argv: list):
        super().__init__(argv)

        try:
            logger.info("Инициализация HFlowApp...")

            # ВАЖНО: Инициализируем контейнер ПОСЛЕ создания QApplication
            logger.debug("Инициализация контейнера зависимостей...")
            container.init()
            logger.info("Контейнер инициализирован")

            # Устанавливаем атрибуты приложения
            self.setApplicationName("HFlow")
            self.setApplicationVersion("1.0")
            self.setOrganizationName("HarmonyFlow")

            # Создаём навигацию
            logger.debug("Создание навигации...")
            self.navigation = Navigation()
            logger.info("Навигация создана")

            # Загружаем настройки и применяем тему
            logger.debug("Применение темы...")
            self._apply_theme()
            logger.info("Тема применена")

            # Инициализируем уведомления
            logger.debug("Инициализация уведомлений...")
            self._init_notifications()
            logger.info("Уведомления инициализированы")

            # Устанавливаем глобальные горячие клавиши
            logger.debug("Настройка горячих клавиш...")
            self._setup_global_hotkeys()
            logger.info("Горячие клавиши настроены")

            # Запускаем автосохранение
            logger.debug("Настройка автосохранения...")
            self._setup_autosave()
            logger.info("Автосохранение настроено")

            # Проверяем активную сессию (после полной инициализации)
            logger.debug("Проверка активной сессии...")
            self._check_active_session()
            logger.info("Проверка сессии завершена")

            logger.info("HFlowApp успешно инициализирован")

        except Exception as e:
            logger.critical(f"Критическая ошибка при инициализации HFlowApp: {e}", exc_info=True)
            raise RuntimeError(f"Невозможно инициализировать приложение: {e}") from e

    def _check_active_session(self):
        """Безопасно проверяет и приостанавливает активную сессию"""
        try:
            container.session_controller.check_and_pause_active_session()
        except AttributeError as e:
            logger.warning(f"session_controller не готов к проверке сессии: {e}")
        except Exception as e:
            logger.error(f"Ошибка при проверке активной сессии: {e}", exc_info=True)

    def _apply_theme(self):
        """Применяет тему оформления из настроек"""
        try:
            from modules.settings.themes import ThemeManager

            theme = container.settings_controller.get_theme()
            logger.debug(f"Загружена тема: {theme}")

            theme_manager = ThemeManager()
            style = theme_manager.get_style(theme)
            self.setStyleSheet(style)
            logger.debug("Стиль применен к приложению")

        except Exception as e:
            logger.error(f"Ошибка применения темы: {e}", exc_info=True)
            # Применяем базовый стиль при ошибке
            self.setStyleSheet("")

    def _init_notifications(self):
        """Инициализирует сервис уведомлений"""
        try:
            self.notification_service = container.notification_service

            # Включаем/отключаем уведомления согласно настройкам
            enabled = container.settings_controller.get_notifications_enabled()
            self.notification_service.set_enabled(enabled)
            logger.debug(f"Уведомления {'включены' if enabled else 'отключены'}")

        except Exception as e:
            logger.error(f"Ошибка инициализации уведомлений: {e}", exc_info=True)

    def _setup_global_hotkeys(self):
        """Настраивает глобальные горячие клавиши"""
        # Глобальные хоткеи будут установлены в главном окне
        # так как им нужен родительский виджет
        logger.debug("Глобальные хоткеи будут настроены в главном окне")

    def _setup_autosave(self):
        """Настраивает автосохранение"""
        try:
            interval = container.settings_controller.get_auto_save_interval()
            logger.debug(f"Интервал автосохранения: {interval} сек")
            # Автосохранение будет настроено в редакторе заметок
        except Exception as e:
            logger.error(f"Ошибка настройки автосохранения: {e}", exc_info=True)

    def shutdown(self):
        """Завершает работу приложения и освобождает ресурсы"""
        try:
            logger.info("Завершение работы приложения...")

            # Сохраняем настройки
            try:
                container.settings_controller.save_all()
                logger.debug("Настройки сохранены")
            except Exception as e:
                logger.error(f"Ошибка сохранения настроек: {e}")

            # Останавливаем музыку
            try:
                container.music_controller.stop()
                logger.debug("Музыка остановлена")
            except Exception as e:
                logger.error(f"Ошибка остановки музыки: {e}")

            # Закрываем БД
            try:
                from database.db_manager import db
                if db is not None:
                    db.close()
                    logger.debug("База данных закрыта")
            except ImportError as e:
                logger.warning(f"Не удалось импортировать db_manager: {e}")
            except Exception as e:
                logger.error(f"Ошибка закрытия БД: {e}")

            logger.info("Приложение завершено")

        except Exception as e:
            logger.critical(f"Критическая ошибка при завершении работы: {e}", exc_info=True)

    def get_container(self):
        """Возвращает контейнер зависимостей"""
        return container

    def get_navigation(self):
        """Возвращает менеджер навигации"""
        return self.navigation