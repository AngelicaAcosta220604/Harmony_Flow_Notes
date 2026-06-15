# modules/settings/view.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QComboBox, QSlider, QCheckBox, QPushButton, QFrame,
    QScrollArea, QGroupBox, QFormLayout, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QIcon, QPixmap
from typing import Optional

from .controller import SettingsController


class SettingsView(QWidget):
    """Экран настроек приложения"""

    # Сигналы
    settings_changed = Signal()
    theme_changed = Signal(str)

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

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("background-color: transparent; border: none;")

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setSpacing(20)

        # ========== ЗАГОЛОВОК (белая плашка) ==========
        header_widget = QWidget()
        header_widget.setStyleSheet("""
            QWidget {
                background-color: #FFFFFF;
                border-radius: 16px;
                border: none;
            }
        """)
        header_widget.setFixedHeight(80)

        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(20, 0, 20, 0)
        header_layout.setSpacing(12)
        header_layout.setAlignment(Qt.AlignCenter)

        header_icon = QLabel()
        header_pixmap = QPixmap("resources/icons/setting1.png")
        if not header_pixmap.isNull():
            header_pixmap = header_pixmap.scaled(32, 32, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            header_icon.setPixmap(header_pixmap)
        header_layout.addWidget(header_icon)

        header_title = QLabel("Настройки")
        header_title.setStyleSheet("font-size: 20px; font-weight: bold; color: #1F2937;")
        header_layout.addWidget(header_title)

        content_layout.addWidget(header_widget)

        # ========== ПЛАШКА 1: Пользователь ==========
        # ПЛАШКА 1: Пользователь (зелёный круг)
        user_widget = self._create_setting_card("resources/icons/user1.png", "Пользователь", "#10B981")
        user_content = QVBoxLayout()
        user_content.setContentsMargins(20, 0, 20, 20)
        user_content.setSpacing(12)

        self.user_name_edit = QLineEdit()
        self.user_name_edit.setPlaceholderText("Введите имя")
        self.user_name_edit.setStyleSheet("""
            QLineEdit {
                background-color: #F0F4F8;
                border: 1px solid #E6EEF6;
                border-radius: 8px;
                padding: 10px 12px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border: 1px solid #3B82F6;
                background-color: #FFFFFF;
            }
        """)
        user_content.addWidget(self.user_name_edit)

        user_widget.layout().addLayout(user_content)
        content_layout.addWidget(user_widget)

        # ПЛАШКА 2: Внешний вид (синий круг)
        appearance_widget = self._create_setting_card("resources/icons/view1.png", "Внешний вид", "#3B82F6")
        appearance_content = QVBoxLayout()
        appearance_content.setContentsMargins(20, 0, 20, 20)
        appearance_content.setSpacing(12)

        self.theme_combo = QComboBox()
        self.theme_combo.addItem("Светлая", "light")
        self.theme_combo.addItem("Тёмная", "dark")
        self.theme_combo.setStyleSheet("""
            QComboBox {
                background-color: #F0F4F8;
                border: 1px solid #E6EEF6;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 13px;
                color: #1F2937;
            }
            QComboBox:hover {
                border: 1px solid #3B82F6;
            }
        """)
        appearance_content.addWidget(self.theme_combo)

        appearance_widget.layout().addLayout(appearance_content)
        content_layout.addWidget(appearance_widget)

        # ПЛАШКА 3: Поведение сессии (оранжевый круг)
        session_widget = self._create_setting_card("resources/icons/session1.png", "Поведение сессии", "#F59E0B")

        session_content = QVBoxLayout()
        session_content.setContentsMargins(20, 0, 20, 20)
        session_content.setSpacing(12)

        interval_label = QLabel("Интервал проверки активности:")
        interval_label.setStyleSheet("color: #374151; font-size: 13px; font-weight: 500;")
        session_content.addWidget(interval_label)

        self.activity_check_combo = QComboBox()
        self.activity_check_combo.addItem("5 минут", 5)
        self.activity_check_combo.addItem("10 минут", 10)
        self.activity_check_combo.addItem("15 минут", 15)
        self.activity_check_combo.addItem("20 минут", 20)
        self.activity_check_combo.addItem("30 минут", 30)
        self.activity_check_combo.setStyleSheet("""
            QComboBox {
                background-color: #F0F4F8;
                border: 1px solid #E6EEF6;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 13px;
                color: #1F2937;
            }
            QComboBox:hover {
                border: 1px solid #3B82F6;
            }
        """)
        session_content.addWidget(self.activity_check_combo)

        pause_label = QLabel("Длительность до авто-паузы:")
        pause_label.setStyleSheet("color: #374151; font-size: 13px; font-weight: 500; margin-top: 8px;")
        session_content.addWidget(pause_label)

        self.auto_pause_combo = QComboBox()
        self.auto_pause_combo.addItem("5 минут", 5)
        self.auto_pause_combo.addItem("10 минут", 10)
        self.auto_pause_combo.addItem("15 минут", 15)
        self.auto_pause_combo.setStyleSheet("""
            QComboBox {
                background-color: #F0F4F8;
                border: 1px solid #E6EEF6;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 13px;
                color: #1F2937;
            }
            QComboBox:hover {
                border: 1px solid #3B82F6;
            }
        """)
        session_content.addWidget(self.auto_pause_combo)

        session_widget.layout().addLayout(session_content)
        content_layout.addWidget(session_widget)

        # ПЛАШКА 4: Редактор (фиолетовый круг)
        editor_widget = self._create_setting_card("resources/icons/time1.png", "Редактор", "#8B5CF6")
        editor_content = QVBoxLayout()
        editor_content.setContentsMargins(20, 0, 20, 20)
        editor_content.setSpacing(12)

        save_label = QLabel("Интервал автосохранения:")
        save_label.setStyleSheet("color: #374151; font-size: 13px; font-weight: 500;")
        editor_content.addWidget(save_label)

        self.auto_save_combo = QComboBox()
        self.auto_save_combo.addItem("30 секунд", 30)
        self.auto_save_combo.addItem("60 секунд", 60)
        self.auto_save_combo.addItem("120 секунд", 120)
        self.auto_save_combo.setStyleSheet("""
            QComboBox {
                background-color: #F0F4F8;
                border: 1px solid #E6EEF6;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 13px;
                color: #1F2937;
            }
            QComboBox:hover {
                border: 1px solid #3B82F6;
            }
        """)
        editor_content.addWidget(self.auto_save_combo)

        editor_widget.layout().addLayout(editor_content)
        content_layout.addWidget(editor_widget)

        # ПЛАШКА 5: Напоминания (розовый круг)
        notify_widget = self._create_setting_card("resources/icons/N.png", "Напоминания", "#EC4899")
        notify_content = QVBoxLayout()
        notify_content.setContentsMargins(20, 0, 20, 20)
        notify_content.setSpacing(12)

        self.notifications_checkbox = QCheckBox("Включить напоминания о задачах")
        self.notifications_checkbox.setStyleSheet("""
            QCheckBox {
                spacing: 10px;
                color: #1F2937;
                font-size: 13px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 4px;
                border: 1px solid #E6EEF6;
                background-color: #F0F4F8;
            }
            QCheckBox::indicator:checked {
                background-color: #3B82F6;
                border-color: #3B82F6;
            }
        """)
        notify_content.addWidget(self.notifications_checkbox)

        notify_widget.layout().addLayout(notify_content)
        content_layout.addWidget(notify_widget)

        # ПЛАШКА 6: Звук по умолчанию (жёлтый круг)
        sound_widget = self._create_setting_card("resources/icons/music1.png", "Звук по умолчанию", "#F59E0B")
        sound_content = QVBoxLayout()
        sound_content.setContentsMargins(20, 0, 20, 20)
        sound_content.setSpacing(12)

        self.default_sound_combo = QComboBox()
        self.default_sound_combo.addItem("Белый шум", "white_noise")
        self.default_sound_combo.addItem("Дождь", "rain")
        self.default_sound_combo.addItem("Лес", "forest")
        self.default_sound_combo.addItem("Кафе", "cafe")
        self.default_sound_combo.addItem("Отключено", "off")
        self.default_sound_combo.setStyleSheet("""
            QComboBox {
                background-color: #F0F4F8;
                border: 1px solid #E6EEF6;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 13px;
                color: #1F2937;
            }
            QComboBox:hover {
                border: 1px solid #3B82F6;
            }
        """)
        sound_content.addWidget(self.default_sound_combo)

        sound_widget.layout().addLayout(sound_content)
        content_layout.addWidget(sound_widget)

        # ========== КНОПКИ (отдельно, без плашки) ==========
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(16)
        buttons_layout.addStretch()

        # Кнопка "Сохранить настройки" (зелёная контурная)
        self.save_button = QPushButton("Сохранить настройки")
        self.save_button.setIcon(QIcon("resources/icons/save.png"))
        self.save_button.setIconSize(QSize(18, 18))
        self.save_button.setFixedWidth(200)
        self.save_button.setFixedHeight(42)
        self.save_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(16, 185, 129, 0.15);
                color: #059669;
                border: 1px solid #10B981;
                border-radius: 12px;
                padding: 10px 20px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: rgba(16, 185, 129, 0.25);
                border: 1px solid #059669;
                color: #047857;
            }
        """)
        buttons_layout.addWidget(self.save_button)

        # Кнопка "Сбросить" (красная контурная)
        self.reset_button = QPushButton("Сбросить")
        self.reset_button.setIcon(QIcon("resources/icons/reset.png"))
        self.reset_button.setIconSize(QSize(18, 18))
        self.reset_button.setFixedWidth(120)
        self.reset_button.setFixedHeight(42)
        self.reset_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(239, 68, 68, 0.15);
                color: #EF4444;
                border: 1px solid #EF4444;
                border-radius: 12px;
                padding: 10px 20px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: rgba(239, 68, 68, 0.25);
                border: 1px solid #DC2626;
                color: #DC2626;
            }
        """)
        buttons_layout.addWidget(self.reset_button)

        buttons_layout.addStretch()
        content_layout.addLayout(buttons_layout)

        content_layout.addStretch()

        scroll.setWidget(content)
        layout.addWidget(scroll)

    def _create_setting_card(self, icon_path: str, title: str, color: str = "#3B82F6") -> QFrame:
        """Создаёт карточку настройки с иконкой в цветном круге и заголовком"""
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border-radius: 16px;
                border: none;
            }
        """)
        card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        # Тень
        from PySide6.QtWidgets import QGraphicsDropShadowEffect
        from PySide6.QtGui import QColor
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(12)
        shadow.setOffset(0, 2)
        shadow.setColor(QColor(0, 0, 0, 20))
        card.setGraphicsEffect(shadow)

        # Основной layout карточки
        main_layout = QVBoxLayout(card)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Заголовок с иконкой в цветном круге
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(20, 16, 20, 0)
        header_layout.setSpacing(12)

        # Цветной круг для иконки
        r = int(color[1:3], 16)
        g = int(color[3:5], 16)
        b = int(color[5:7], 16)

        icon_container = QLabel()
        icon_container.setFixedSize(32, 32)
        icon_container.setAlignment(Qt.AlignCenter)
        icon_container.setStyleSheet(f"""
            background-color: rgba({r}, {g}, {b}, 0.15);
            border-radius: 16px;
            border: none;
        """)

        icon_label = QLabel()
        icon_label.setAlignment(Qt.AlignCenter)
        pixmap = QPixmap(icon_path)
        if not pixmap.isNull():
            pixmap = pixmap.scaled(18, 18, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            icon_label.setPixmap(pixmap)
        else:
            icon_label.setText("🔧")
            icon_label.setStyleSheet("font-size: 14px;")

        container_layout = QVBoxLayout(icon_container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.addWidget(icon_label)

        title_label = QLabel(title)
        title_label.setStyleSheet("font-weight: 600; color: #1F2937; font-size: 14px;")

        header_layout.addWidget(icon_container)
        header_layout.addWidget(title_label)
        header_layout.addStretch()

        main_layout.addLayout(header_layout)
        main_layout.addSpacing(8)  # отступ между заголовком и содержимым

        return card

    def _load_settings(self):
        """Загружает настройки в UI"""
        settings = self._controller.get_all()

        self.user_name_edit.setText(settings.user_name)

        index = self.theme_combo.findData(settings.theme)
        if index >= 0:
            self.theme_combo.setCurrentIndex(index)

        index = self.activity_check_combo.findData(settings.activity_check_interval_minutes)
        if index >= 0:
            self.activity_check_combo.setCurrentIndex(index)

        index = self.auto_pause_combo.findData(settings.auto_pause_minutes)
        if index >= 0:
            self.auto_pause_combo.setCurrentIndex(index)

        index = self.auto_save_combo.findData(settings.auto_save_interval_seconds)
        if index >= 0:
            self.auto_save_combo.setCurrentIndex(index)

        self.notifications_checkbox.setChecked(settings.notifications_enabled)

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
        self._controller.set_user_name(self.user_name_edit.text())

        theme = self.theme_combo.currentData()
        self._controller.set_theme(theme)

        self._controller.set('activity_check_interval_minutes',
                             self.activity_check_combo.currentData())
        self._controller.set('auto_pause_minutes',
                             self.auto_pause_combo.currentData())
        self._controller.set('auto_save_interval_seconds',
                             self.auto_save_combo.currentData())

        self._controller.set_notifications_enabled(self.notifications_checkbox.isChecked())

        self._controller.set('default_sound', self.default_sound_combo.currentData())

        self._controller.save_all()

        self.settings_changed.emit()

        self.save_button.setText("✅ Сохранено!")
        from PySide6.QtCore import QTimer
        QTimer.singleShot(1500, lambda: self.save_button.setText("Сохранить настройки"))

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