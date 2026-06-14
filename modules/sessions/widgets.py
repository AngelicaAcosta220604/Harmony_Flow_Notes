# modules/sessions/widgets.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSlider,
    QPushButton, QDialog, QProgressBar
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont


class CustomTimer(QWidget):
    """Виджет таймера для отображения времени сессии."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._seconds = 0
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)

        self.time_label = QLabel("00:00")
        font = QFont("Courier New", 48, QFont.Bold)
        self.time_label.setFont(font)
        self.time_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.time_label)

    def set_time(self, seconds: int):
        self._seconds = seconds
        hours = self._seconds // 3600
        minutes = (self._seconds % 3600) // 60
        secs = self._seconds % 60

        if hours > 0:
            self.time_label.setText(f"{hours:02d}:{minutes:02d}:{secs:02d}")
        else:
            self.time_label.setText(f"{minutes:02d}:{secs:02d}")

    def reset(self):
        self._seconds = 0
        self.time_label.setText("00:00")


class StateSliders(QWidget):
    """Виджет ползунков для отслеживания состояния."""

    state_changed = Signal(str, int)  # (metric, value)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # Концентрация
        self.conc_layout = QHBoxLayout()
        self.conc_label = QLabel("🧠 Концентрация")
        self.conc_label.setFixedWidth(100)
        self.conc_slider = QSlider(Qt.Horizontal)
        self.conc_slider.setRange(1, 5)
        self.conc_slider.setValue(3)
        self.conc_slider.setTickPosition(QSlider.TicksBelow)
        self.conc_slider.setTickInterval(1)
        self.conc_value_label = QLabel("3")
        self.conc_value_label.setFixedWidth(30)

        self.conc_layout.addWidget(self.conc_label)
        self.conc_layout.addWidget(self.conc_slider, 1)
        self.conc_layout.addWidget(self.conc_value_label)
        layout.addLayout(self.conc_layout)

        # Энергия
        self.energy_layout = QHBoxLayout()
        self.energy_label = QLabel("⚡ Энергия")
        self.energy_label.setFixedWidth(100)
        self.energy_slider = QSlider(Qt.Horizontal)
        self.energy_slider.setRange(1, 5)
        self.energy_slider.setValue(3)
        self.energy_slider.setTickPosition(QSlider.TicksBelow)
        self.energy_slider.setTickInterval(1)
        self.energy_value_label = QLabel("3")
        self.energy_value_label.setFixedWidth(30)

        self.energy_layout.addWidget(self.energy_label)
        self.energy_layout.addWidget(self.energy_slider, 1)
        self.energy_layout.addWidget(self.energy_value_label)
        layout.addLayout(self.energy_layout)

        # Интерес
        self.interest_layout = QHBoxLayout()
        self.interest_label = QLabel("❤️ Интерес")
        self.interest_label.setFixedWidth(100)
        self.interest_slider = QSlider(Qt.Horizontal)
        self.interest_slider.setRange(1, 5)
        self.interest_slider.setValue(3)
        self.interest_slider.setTickPosition(QSlider.TicksBelow)
        self.interest_slider.setTickInterval(1)
        self.interest_value_label = QLabel("3")
        self.interest_value_label.setFixedWidth(30)

        self.interest_layout.addWidget(self.interest_label)
        self.interest_layout.addWidget(self.interest_slider, 1)
        self.interest_layout.addWidget(self.interest_value_label)
        layout.addLayout(self.interest_layout)

    def _connect_signals(self):
        self.conc_slider.valueChanged.connect(
            lambda v: self._on_value_changed("concentration", v)
        )
        self.energy_slider.valueChanged.connect(
            lambda v: self._on_value_changed("energy", v)
        )
        self.interest_slider.valueChanged.connect(
            lambda v: self._on_value_changed("interest", v)
        )

    def _on_value_changed(self, metric: str, value: int):
        if metric == "concentration":
            self.conc_value_label.setText(str(value))
        elif metric == "energy":
            self.energy_value_label.setText(str(value))
        elif metric == "interest":
            self.interest_value_label.setText(str(value))

        self.state_changed.emit(metric, value)

    def get_values(self) -> dict:
        return {
            'concentration': self.conc_slider.value(),
            'energy': self.energy_slider.value(),
            'interest': self.interest_slider.value()
        }

    def reset(self):
        self.conc_slider.setValue(3)
        self.energy_slider.setValue(3)
        self.interest_slider.setValue(3)


class PingDialog(QDialog):
    """Диалог контроля активности (система "Пинг")."""

    continue_session = Signal()
    pause_session = Signal()

    def __init__(self, parent=None, timeout_seconds: int = 30):
        super().__init__(parent)
        self._timeout_seconds = timeout_seconds
        self._remaining = timeout_seconds
        self._timer = None
        self._setup_ui()
        self._start_timer()

    def _setup_ui(self):
        self.setWindowTitle("Проверка активности")
        self.setModal(True)
        self.setFixedSize(350, 180)

        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        icon_label = QLabel("👋")
        icon_label.setStyleSheet("font-size: 48px;")
        icon_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon_label)

        message_label = QLabel("Вы всё ещё здесь?")
        message_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        message_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(message_label)

        self.countdown_label = QLabel(f"Сессия будет приостановлена через {self._remaining} секунд...")
        self.countdown_label.setAlignment(Qt.AlignCenter)
        self.countdown_label.setStyleSheet("color: #ff9800;")
        layout.addWidget(self.countdown_label)

        button_layout = QHBoxLayout()

        continue_btn = QPushButton("✅ Продолжить")
        continue_btn.clicked.connect(self._on_continue)
        continue_btn.setStyleSheet("background-color: #4caf50;")
        button_layout.addWidget(continue_btn)

        pause_btn = QPushButton("⏸ Приостановить")
        pause_btn.clicked.connect(self._on_pause)
        button_layout.addWidget(pause_btn)

        layout.addLayout(button_layout)

    def _start_timer(self):
        self._timer = QTimer()
        self._timer.timeout.connect(self._on_timer_tick)
        self._timer.start(1000)

    def _on_timer_tick(self):
        self._remaining -= 1
        self.countdown_label.setText(f"Сессия будет приостановлена через {self._remaining} секунд...")

        if self._remaining <= 0:
            self._timer.stop()
            self._on_pause()

    def _on_continue(self):
        if self._timer:
            self._timer.stop()
        self.continue_session.emit()
        self.accept()

    def _on_pause(self):
        if self._timer:
            self._timer.stop()
        self.pause_session.emit()
        self.reject()