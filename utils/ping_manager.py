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

    def __init__(self, idle_ms: int = 15 * 60 * 1000, timeout_ms: int = 90 * 60 * 1000, parent=None):
        super().__init__(parent)
        self.idle_ms = idle_ms          # Через сколько спросить "ты тут?"
        self.timeout_ms = timeout_ms    # Через сколько авто-пауза
        self._idle_timer = QTimer(self)
        self._idle_timer.setSingleShot(True)
        self._idle_timer.timeout.connect(self._on_idle)

        self._timeout_timer = QTimer(self)
        self._timeout_timer.setSingleShot(True)
        self._timeout_timer.timeout.connect(self._on_timeout)

        # Глобально перехватываем события мыши и клавиатуры
        app = QApplication.instance()
        if app:
            app.installEventFilter(self)

        self.reset_idle()

    def eventFilter(self, obj, event):
        """Любое движение мыши/клавиши — сбрасываем таймер"""
        if event.type() in (
            QEvent.MouseMove, QEvent.MouseButtonPress,
            QEvent.KeyPress, QEvent.KeyRelease
        ):
            self.reset_idle()
        return False

    def reset_idle(self):
        """Сбросить таймер простоя (вызывать при любой активности)"""
        self._idle_timer.start(self.idle_ms)
        self._timeout_timer.stop()

    def user_confirmed(self):
        """Пользователь нажал "Да, я тут" — сбрасываем всё"""
        self.reset_idle()

    def _on_idle(self):
        """Прошло idle_ms без активности — спрашиваем"""
        self.pingNeeded.emit()
        self._timeout_timer.start(self.timeout_ms - self.idle_ms)

    def _on_timeout(self):
        """Пользователь не ответил — авто-пауза"""
        self.timeoutReached.emit()