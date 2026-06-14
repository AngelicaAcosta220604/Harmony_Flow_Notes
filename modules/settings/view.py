# modules/settings/view.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QComboBox, QSlider, QCheckBox, QPushButton, QFrame,
    QScrollArea, QGroupBox, QFormLayout
)
from PySide6.QtCore import Qt, Signal
from typing import Optional

from .controller import SettingsController


class SettingsView(QWidget):
    """Экран настроек приложения"""

    # Сигналы
    settings_changed = Signal()  # когда изменились настройки
    theme_changed = Signal(str)  # когда изменилась тема (light/dark)

    def __init__(self, controller: SettingsController, parent=None):
        super().__init__(parent)
        self._controller = controller
        self._setup_ui()
        self._load_settings()
        self._connect_signals()

    def _setup_ui(self):
        """Настраивает интерфейс"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # Заголовок
        title = QLabel("⚙️ Настройки")
        title.setStyleSheet("font-size: 24px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title)

        # Скролл-область
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(15)

        # === Блок: Пользователь ===
        user_group = QGroupBox("👤 Пользователь")
        user_layout = QFormLayout(user_group)

        self.user_name_edit = QLineEdit()
        self.user_name_edit.setPlaceholderText("Введите имя")
        user_layout.addRow("Имя пользователя:", self.user_name_edit)

        content_layout.addWidget(user_group)

        # === Блок: Внешний вид ===
        appearance_group = QGroupBox("🎨 Внешний вид")
        appearance_layout = QFormLayout(appearance_group)

        self.theme_combo = QComboBox()
        self.theme_combo.addItem("Светлая", "light")
        self.theme_combo.addItem("Тёмная", "dark")
        appearance_layout.addRow("Тема оформления:", self.theme_combo)

        content_layout.addWidget(appearance_group)

        # === Блок: Поведение сессии ===
        session_group = QGroupBox("⏱️ Поведение сессии")
        session_layout = QFormLayout(session_group)

        self.activity_check_combo = QComboBox()
        self.activity_check_combo.addItem("5 минут", 5)
        self.activity_check_combo.addItem("10 минут", 10)
        self.activity_check_combo.addItem("15 минут", 15)
        self.activity_check_combo.addItem("20 минут", 20)
        self.activity_check_combo.addItem("30 минут", 30)
        session_layout.addRow("Интервал проверки активности:", self.activity_check_combo)

        self.auto_pause_combo = QComboBox()
        self.auto_pause_combo.addItem("5 минут", 5)
        self.auto_pause_combo.addItem("10 минут", 10)
        self.auto_pause_combo.addItem("15 минут", 15)
        session_layout.addRow("Длительность до авто-паузы:", self.auto_pause_combo)

        content_layout.addWidget(session_group)

        # === Блок: Редактор ===
        editor_group = QGroupBox("📝 Редактор")
        editor_layout = QFormLayout(editor_group)

        self.auto_save_combo = QComboBox()
        self.auto_save_combo.addItem("30 секунд", 30)
        self.auto_save_combo.addItem("60 секунд", 60)
        self.auto_save_combo.addItem("120 секунд", 120)
        editor_layout.addRow("Интервал автосохранения:", self.auto_save_combo)

        content_layout.addWidget(editor_group)

        # === Блок: Напоминания ===
        notifications_group = QGroupBox("🔔 Напоминания")
        notifications_layout = QFormLayout(notifications_group)

        self.notifications_checkbox = QCheckBox("Включить напоминания о задачах")
        notifications_layout.addRow(self.notifications_checkbox)

        content_layout.addWidget(notifications_group)

        # === Блок: Звук ===
        sound_group = QGroupBox("🎵 Звук по умолчанию")
        sound_layout = QFormLayout(sound_group)

        self.default_sound_combo = QComboBox()
        self.default_sound_combo.addItem("Белый шум", "white_noise")
        self.default_sound_combo.addItem("Дождь", "rain")
        self.default_sound_combo.addItem("Лес", "forest")
        self.default_sound_combo.addItem("Кафе", "cafe")
        self.default_sound_combo.addItem("Отключено", "off")
        sound_layout.addRow("Звук:", self.default_sound_combo)

        content_layout.addWidget(sound_group)

        # Кнопки
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.save_button = QPushButton("💾 Сохранить настройки")
        self.save_button.setFixedWidth(200)
        button_layout.addWidget(self.save_button)

        self.reset_button = QPushButton("🔄 Сбросить")
        self.reset_button.setFixedWidth(120)
        button_layout.addWidget(self.reset_button)

        content_layout.addLayout(button_layout)

        scroll.setWidget(content_widget)
        layout.addWidget(scroll)

    def _load_settings(self):
        """Загружает настройки в UI"""
        settings = self._controller.get_all()

        # Пользователь
        self.user_name_edit.setText(settings.user_name)

        # Тема
        index = self.theme_combo.findData(settings.theme)
        if index >= 0:
            self.theme_combo.setCurrentIndex(index)

        # Интервалы
        index = self.activity_check_combo.findData(settings.activity_check_interval_minutes)
        if index >= 0:
            self.activity_check_combo.setCurrentIndex(index)

        index = self.auto_pause_combo.findData(settings.auto_pause_minutes)
        if index >= 0:
            self.auto_pause_combo.setCurrentIndex(index)

        index = self.auto_save_combo.findData(settings.auto_save_interval_seconds)
        if index >= 0:
            self.auto_save_combo.setCurrentIndex(index)

        # Напоминания
        self.notifications_checkbox.setChecked(settings.notifications_enabled)

        # Звук
        index = self.default_sound_combo.findData(settings.default_sound)
        if index >= 0:
            self.default_sound_combo.setCurrentIndex(index)

    def _connect_signals(self):
        """Подключает сигналы"""
        self.save_button.clicked.connect(self._on_save)
        self.reset_button.clicked.connect(self._on_reset)
        self.theme_combo.currentIndexChanged.connect(self._on_theme_changed)

    def _on_save(self):
        """Обработчик сохранения настроек"""
        # Сохраняем имя
        self._controller.set_user_name(self.user_name_edit.text())

        # Сохраняем тему
        theme = self.theme_combo.currentData()
        self._controller.set_theme(theme)

        # Сохраняем интервалы
        self._controller.set('activity_check_interval_minutes',
                             self.activity_check_combo.currentData())
        self._controller.set('auto_pause_minutes',
                             self.auto_pause_combo.currentData())
        self._controller.set('auto_save_interval_seconds',
                             self.auto_save_combo.currentData())

        # Сохраняем напоминания
        self._controller.set_notifications_enabled(self.notifications_checkbox.isChecked())

        # Сохраняем звук
        self._controller.set('default_sound', self.default_sound_combo.currentData())

        # Сохраняем все
        self._controller.save_all()

        self.settings_changed.emit()

        # Визуальный фидбек
        self.save_button.setText("✅ Сохранено!")
        from PySide6.QtCore import QTimer
        QTimer.singleShot(1500, lambda: self.save_button.setText("💾 Сохранить настройки"))

    def _on_reset(self):
        """Обработчик сброса настроек"""
        self._controller.reset_to_defaults()
        self._load_settings()
        self.settings_changed.emit()

    def _on_theme_changed(self):
        """Обработчик изменения темы"""
        theme = self.theme_combo.currentData()
        self.theme_changed.emit(theme)

    def refresh(self):
        """Обновляет вьюху"""
        self._load_settings()