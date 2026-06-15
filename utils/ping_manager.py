from PySide6.QtCore import QObject, QTimer, Signal, QEvent
from PySide6.QtWidgets import QApplication


class PingManager(QObject):
    """
    Следит за активностью пользователя.
    - pingNeeded: срабатывает, если нет активности N мс (пора спросить "ты тут?")
    - timeoutReached: срабатывает, если после pingNeeded прошла ещё одна пауза
    """
    pingNeeded = Signal()
    timeoutReached = Signal()

    # События, которые считаем "активностью"
    _ACTIVITY_EVENTS = {
        QEvent.MouseMove,
        QEvent.MouseButtonPress,
        QEvent.MouseButtonRelease,
        QEvent.KeyPress,
        QEvent.KeyRelease,
        QEvent.Wheel,
    }

    def __init__(self, idle_ms: int = 15 * 60 * 1000, timeout_ms: int = 90 * 60 * 1000, parent=None):
        super().__init__(parent)
        self.idle_ms = idle_ms
        self.timeout_ms = timeout_ms

        self._idle_timer = QTimer(self)
        self._idle_timer.setSingleShot(True)
        self._idle_timer.timeout.connect(self._on_idle)

        self._timeout_timer = QTimer(self)
        self._timeout_timer.setSingleShot(True)
        self._timeout_timer.timeout.connect(self._on_timeout)

        # Глобально перехватываем события
        app = QApplication.instance()
        if app:
            app.installEventFilter(self)

        self.reset_idle()

    def eventFilter(self, obj, event):
        """Безопасный перехват событий активности"""
        try:
            # Защита от None и невалидных объектов
            if event is None:
                return False

            # Проверяем, что это событие из нужного списка
            try:
                event_type = event.type()
            except (RuntimeError, AttributeError):
                # C++ объект уже удалён или event невалиден
                return False

            if event_type in self._ACTIVITY_EVENTS:
                self.reset_idle()
        except Exception:
            # Ловим ВСЁ, чтобы не ломать приложение
            pass

        return False

    def reset_idle(self):
        """Сбросить таймер простоя"""
        try:
            if self._idle_timer:
                self._idle_timer.start(self.idle_ms)
            if self._timeout_timer:
                self._timeout_timer.stop()
        except Exception:
            pass

    def user_confirmed(self):
        """Пользователь нажал "Да, я тут" — сбрасываем всё"""
        self.reset_idle()

    def _on_idle(self):
        """Прошло idle_ms без активности — спрашиваем"""
        try:
            self.pingNeeded.emit()
            if self._timeout_timer:
                self._timeout_timer.start(self.timeout_ms - self.idle_ms)
        except Exception:
            pass

    def _on_timeout(self):
        """Пользователь не ответил — авто-пауза"""
        try:
            self.timeoutReached.emit()
        except Exception:
            pass

    def cleanup(self):
        """Останавливает таймеры и снимает eventFilter"""
        try:
            if self._idle_timer:
                self._idle_timer.stop()
            if self._timeout_timer:
                self._timeout_timer.stop()
            app = QApplication.instance()
            if app:
                app.removeEventFilter(self)
        except Exception:
            pass