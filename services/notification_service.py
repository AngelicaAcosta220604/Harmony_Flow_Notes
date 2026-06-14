# services/notification_service.py
from typing import Optional, Callable
from PySide6.QtWidgets import QSystemTrayIcon, QMenu
from PySide6.QtGui import QIcon
from PySide6.QtCore import QTimer, QObject, Signal
import os


class NotificationService(QObject):
    """Сервис для уведомлений (внутри приложения)"""

    notification_clicked = Signal(str)  # сигнал при клике на уведомление

    def __init__(self, parent=None):
        super().__init__(parent)
        self._tray_icon: Optional[QSystemTrayIcon] = None
        self._notifications_enabled = True
        self._pending_notifications = []

    def init_tray_icon(self, parent_widget=None):
        """Инициализирует иконку в трее (опционально)"""
        if QSystemTrayIcon.isSystemTrayAvailable():
            self._tray_icon = QSystemTrayIcon(parent_widget)
            # Устанавливаем иконку (нужен реальный файл)
            # self._tray_icon.setIcon(QIcon(":/icons/app.png"))
            self._tray_icon.show()

    def set_enabled(self, enabled: bool):
        """Включает/выключает уведомления"""
        self._notifications_enabled = enabled

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
        if not self._notifications_enabled:
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
        else:
            # Заглушка для консоли (при разработке)
            print(f"[NOTIFICATION] {title}: {message}")

    def _cleanup_notification(self, title: str, message: str):
        """Удаляет уведомление из списка ожидания"""
        self._pending_notifications = [
            n for n in self._pending_notifications
            if not (n['title'] == title and n['message'] == message)
        ]

    def show_task_reminder(self, task_title: str, deadline: str = None):
        """Показывает напоминание о задаче"""
        if deadline:
            message = f"Дедлайн: {deadline}"
        else:
            message = "Не забудьте выполнить задачу"
        self.show("📋 Напоминание о задаче", f"{task_title}\n{message}",
                  notification_id=f"task_{task_title}")

    def show_session_reminder(self, topic_name: str):
        """Показывает напоминание о сессии"""
        self.show("⏱️ Фокус-сессия",
                  f"Вы не начинали сессию по теме '{topic_name}'. Хотите начать?",
                  notification_id="session_reminder")

    def show_ping(self):
        """Показывает уведомление-пинг (Вы ещё здесь?)"""
        self.show("👋 Проверка активности",
                  "Вы всё ещё здесь? Продолжайте работу или сделайте перерыв.",
                  notification_id="ping")

    def show_auto_pause(self):
        """Показывает уведомление об автоматической паузе"""
        self.show("⏸️ Автоматическая пауза",
                  "Сессия поставлена на паузу из-за отсутствия активности.",
                  notification_id="auto_pause")

    def show_backup_complete(self, backup_path: str):
        """Показывает уведомление о завершении бэкапа"""
        self.show("💾 Резервное копирование",
                  f"Данные сохранены в:\n{backup_path}",
                  notification_id="backup_complete")

    def handle_notification_click(self, title: str, message: str):
        """Обрабатывает клик по уведомлению"""
        for notification in self._pending_notifications:
            if notification['title'] == title and notification['message'] == message:
                if notification['callback']:
                    notification['callback']()
                else:
                    self.notification_clicked.emit(notification.get('id', ''))
                break