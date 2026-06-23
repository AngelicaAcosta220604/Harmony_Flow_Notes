# services/notification_service.py
from typing import Optional, Callable
from PySide6.QtWidgets import QSystemTrayIcon, QMenu
from PySide6.QtGui import QIcon
from PySide6.QtCore import QTimer, QObject, Signal
import os
import logging

# Настройка логирования
logger = logging.getLogger(__name__)


class NotificationService(QObject):
    """Сервис для уведомлений (внутри приложения)"""

    notification_clicked = Signal(str)  # сигнал при клике на уведомление

    def __init__(self, parent=None):
        super().__init__(parent)
        self._tray_icon: Optional[QSystemTrayIcon] = None
        self._notifications_enabled = True
        self._pending_notifications = []
        logger.debug("NotificationService инициализирован")

    def init_tray_icon(self, parent_widget=None):
        """Инициализирует иконку в трее (опционально)"""
        try:
            if QSystemTrayIcon.isSystemTrayAvailable():
                self._tray_icon = QSystemTrayIcon(parent_widget)
                # Устанавливаем иконку (нужен реальный файл)
                # self._tray_icon.setIcon(QIcon(":/icons/app.png"))
                self._tray_icon.show()
                logger.info("Иконка в трее инициализирована")
            else:
                logger.warning("Системный трей недоступен")
        except Exception as e:
            logger.error(f"Ошибка инициализации иконки в трее: {e}", exc_info=True)

    def set_enabled(self, enabled: bool):
        """Включает/выключает уведомления"""
        self._notifications_enabled = enabled
        logger.debug(f"Уведомления {'включены' if enabled else 'отключены'}")

    def is_enabled(self) -> bool:
        """Возвращает, включены ли уведомления"""
        return self._notifications_enabled

    def show(self, title: str, message: str, duration: int = 3000,
             notification_id: str = None, callback: Optional[Callable] = None):
        """
        Показывает уведомление

        Args:
            title: Заголовок
            message: Текст сообщения
            duration: Длительность показа в мс
            notification_id: ID для отслеживания клика
            callback: Функция при клике (если нет сигнала)
        """
        try:
            if not self._notifications_enabled:
                logger.debug(f"Уведомление пропущено (отключено): {title}")
                return

            if self._tray_icon and self._tray_icon.isVisible():
                # Используем системный трей
                self._tray_icon.showMessage(title, message, QSystemTrayIcon.Information, duration)

                # Сохраняем callback для обработки клика
                if notification_id or callback:
                    self._pending_notifications.append({
                        'title': title,
                        'message': message,
                        'callback': callback,
                        'id': notification_id
                    })
                    # Через duration убираем из pending
                    QTimer.singleShot(duration, lambda: self._cleanup_notification(title, message))

                logger.info(f"Показано уведомление: {title}")
            else:
                # ✅ ИСПРАВЛЕНО: используем logger вместо print
                logger.debug(f"[NOTIFICATION] {title}: {message}")
        except Exception as e:
            logger.error(f"Ошибка показа уведомления '{title}': {e}", exc_info=True)

    def _cleanup_notification(self, title: str, message: str):
        """Удаляет уведомление из списка ожидания"""
        try:
            self._pending_notifications = [
                n for n in self._pending_notifications
                if not (n['title'] == title and n['message'] == message)
            ]
        except Exception as e:
            logger.error(f"Ошибка очистки уведомления: {e}", exc_info=True)

    def show_task_reminder(self, task_title: str, deadline: str = None):
        """Показывает напоминание о задаче"""
        try:
            if deadline:
                message = f"Дедлайн: {deadline}"
            else:
                message = "Не забудьте выполнить задачу"
            self.show("📋 Напоминание о задаче", f"{task_title}\n{message}",
                      notification_id=f"task_{task_title}")
        except Exception as e:
            logger.error(f"Ошибка показа напоминания о задаче: {e}", exc_info=True)

    def show_session_reminder(self, topic_name: str):
        """Показывает напоминание о сессии"""
        try:
            self.show("⏱️ Фокус-сессия",
                      f"Вы не начинали сессию по теме '{topic_name}'. Хотите начать?",
                      notification_id="session_reminder")
        except Exception as e:
            logger.error(f"Ошибка показа напоминания о сессии: {e}", exc_info=True)

    def show_ping(self):
        """Показывает уведомление-пинг (Вы ещё здесь?)"""
        try:
            self.show("👋 Проверка активности",
                      "Вы всё ещё здесь? Продолжайте работу или сделайте перерыв.",
                      notification_id="ping")
        except Exception as e:
            logger.error(f"Ошибка показа пинга: {e}", exc_info=True)

    def show_auto_pause(self):
        """Показывает уведомление об автоматической паузе"""
        try:
            self.show("⏸️ Автоматическая пауза",
                      "Сессия поставлена на паузу из-за отсутствия активности.",
                      notification_id="auto_pause")
        except Exception as e:
            logger.error(f"Ошибка показа уведомления об авто-паузе: {e}", exc_info=True)

    def show_backup_complete(self, backup_path: str):
        """Показывает уведомление о завершении бэкапа"""
        try:
            self.show("💾 Резервное копирование",
                      f"Данные сохранены в:\n{backup_path}",
                      notification_id="backup_complete")
        except Exception as e:
            logger.error(f"Ошибка показа уведомления о бэкапе: {e}", exc_info=True)

    def handle_notification_click(self, title: str, message: str):
        """Обрабатывает клик по уведомлению"""
        try:
            for notification in self._pending_notifications:
                if notification['title'] == title and notification['message'] == message:
                    if notification['callback']:
                        try:
                            notification['callback']()
                        except Exception as e:
                            logger.error(f"Ошибка вызова callback уведомления: {e}", exc_info=True)
                    else:
                        self.notification_clicked.emit(notification.get('id', ''))

                    logger.info(f"Обработан клик по уведомлению: {title}")
                    break
        except Exception as e:
            logger.error(f"Ошибка обработки клика по уведомлению: {e}", exc_info=True)