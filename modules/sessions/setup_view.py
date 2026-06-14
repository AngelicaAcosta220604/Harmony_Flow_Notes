# modules/sessions/setup_view.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QPushButton
)
from PySide6.QtCore import Signal
from PySide6.QtCore import Qt
from modules.topics.widgets import TopicTreeSelector
from modules.music.widgets import MusicWidget
from modules.music.controller import MusicController
from widgets import SilentMessageBox


class FocusSetupView(QWidget):
    """Экран подготовки к сессии"""

    start_session = Signal(int, int)  # (topic_id, activity_check_interval)

    def __init__(self, topic_controller, music_controller: MusicController, settings_controller, parent=None):
        super().__init__(parent)
        self._topic_controller = topic_controller
        self._music_controller = music_controller
        self._settings_controller = settings_controller
        self._setup_ui()
        self._load_settings()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        title_label = QLabel("⏱️ Подготовка к фокус-сессии")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        topic_label = QLabel("📚 Выберите тему для работы:")
        topic_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(topic_label)

        self.topic_selector = TopicTreeSelector(self._topic_controller)
        layout.addWidget(self.topic_selector)

        interval_label = QLabel("⏰ Интервал контроля активности:")
        interval_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(interval_label)

        self.interval_combo = QComboBox()
        self.interval_combo.addItem("5 минут", 5)
        self.interval_combo.addItem("10 минут", 10)
        self.interval_combo.addItem("15 минут", 15)
        self.interval_combo.addItem("20 минут", 20)
        self.interval_combo.addItem("30 минут", 30)
        layout.addWidget(self.interval_combo)

        music_label = QLabel("🎵 Фоновые звуки (опционально):")
        music_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(music_label)

        self.music_widget = MusicWidget(self._music_controller)
        layout.addWidget(self.music_widget)

        layout.addStretch()

        self.start_btn = QPushButton("🚀 Начать сессию")
        self.start_btn.setFixedHeight(50)
        self.start_btn.setStyleSheet("font-size: 16px; font-weight: bold; background-color: #4caf50;")
        self.start_btn.clicked.connect(self._on_start)
        layout.addWidget(self.start_btn)

    def _load_settings(self):
        default_interval = self._settings_controller.get_activity_check_interval()
        index = self.interval_combo.findData(default_interval)
        if index >= 0:
            self.interval_combo.setCurrentIndex(index)

        default_sound = self._settings_controller.get_default_sound()
        if default_sound != 'off':
            self.music_widget._controller.play(default_sound)

    def _on_start(self):
        topic_id = self.topic_selector.get_selected_topic_id()
        if not topic_id:
            SilentMessageBox.warning(self, "Ошибка", "Выберите тему для сессии")
            return

        interval = self.interval_combo.currentData()
        self.start_session.emit(topic_id, interval)

    def refresh_topics(self):
        self.topic_selector.refresh()