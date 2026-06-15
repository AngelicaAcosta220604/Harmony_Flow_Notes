# modules/sessions/setup_view.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QPushButton, QFrame, QScrollArea, QSlider, QCheckBox, QSizePolicy
)
from PySide6.QtCore import Signal, Qt, QSize
from PySide6.QtGui import QIcon, QPixmap

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

        # Иконка
        header_icon = QLabel()
        header_pixmap = QPixmap("resources/icons/session.png")
        if not header_pixmap.isNull():
            header_pixmap = header_pixmap.scaled(32, 32, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            header_icon.setPixmap(header_pixmap)
        header_layout.addWidget(header_icon)

        # Заголовок
        header_title = QLabel("Подготовка к фокус-сессии")
        header_title.setStyleSheet("font-size: 20px; font-weight: bold; color: #1F2937;")
        header_layout.addWidget(header_title)

        content_layout.addWidget(header_widget)

        # ========== ПЛАШКА ВЫБОРА ТЕМЫ ==========
        topic_widget = QFrame()
        topic_widget.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border-radius: 16px;
                border: none;
            }
        """)
        topic_widget.setMinimumHeight(100)

        topic_layout = QVBoxLayout(topic_widget)
        topic_layout.setContentsMargins(20, 16, 20, 16)
        topic_layout.setSpacing(12)

        # Заголовок с иконкой
        topic_title_layout = QHBoxLayout()
        topic_icon = QLabel()
        topic_icon_pixmap = QPixmap("resources/icons/topic.png")
        if not topic_icon_pixmap.isNull():
            topic_icon_pixmap = topic_icon_pixmap.scaled(20, 20, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            topic_icon.setPixmap(topic_icon_pixmap)
        topic_title = QLabel("Выберите тему для работы:")
        topic_title.setStyleSheet("font-weight: 600; color: #1F2937; font-size: 14px;")
        topic_title_layout.addWidget(topic_icon)
        topic_title_layout.addWidget(topic_title)
        topic_title_layout.addStretch()
        topic_layout.addLayout(topic_title_layout)

        self.topic_selector = TopicTreeSelector(self._topic_controller)
        topic_layout.addWidget(self.topic_selector)

        content_layout.addWidget(topic_widget)

        # ========== РЯД 2: Интервал активности и Фоновые звуки ==========
        row2_layout = QHBoxLayout()
        row2_layout.setSpacing(16)

        # Плашка "Интервал контроля активности"
        interval_widget = QFrame()
        interval_widget.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border-radius: 16px;
                border: none;
            }
        """)
        interval_widget.setMinimumHeight(140)
        interval_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        interval_layout = QVBoxLayout(interval_widget)
        interval_layout.setContentsMargins(20, 16, 20, 16)
        interval_layout.setSpacing(12)

        interval_title_layout = QHBoxLayout()
        interval_icon = QLabel()
        interval_icon_pixmap = QPixmap("resources/icons/time.png")
        if not interval_icon_pixmap.isNull():
            interval_icon_pixmap = interval_icon_pixmap.scaled(20, 20, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            interval_icon.setPixmap(interval_icon_pixmap)
        interval_title = QLabel("Интервал контроля активности:")
        interval_title.setStyleSheet("font-weight: 600; color: #1F2937; font-size: 14px;")
        interval_title_layout.addWidget(interval_icon)
        interval_title_layout.addWidget(interval_title)
        interval_title_layout.addStretch()
        interval_layout.addLayout(interval_title_layout)

        self.interval_combo = QComboBox()
        self.interval_combo.addItem("5 минут", 5)
        self.interval_combo.addItem("10 минут", 10)
        self.interval_combo.addItem("15 минут", 15)
        self.interval_combo.addItem("20 минут", 20)
        self.interval_combo.addItem("30 минут", 30)
        self.interval_combo.setStyleSheet("""
            QComboBox {
                background-color: #F0F4F8;
                border: 1px solid #E6EEF6;
                border-radius: 8px;
                padding: 8px 12px;
                min-height: 36px;
                font-size: 13px;
                color: #1F2937;
            }
            QComboBox:hover {
                border: 1px solid #3B82F6;
            }
            QComboBox::drop-down {
                border: none;
            }
        """)
        interval_layout.addWidget(self.interval_combo)
        row2_layout.addWidget(interval_widget, 1)

        # Плашка "Фоновые звуки"
        sound_widget = QFrame()
        sound_widget.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border-radius: 16px;
                border: none;
            }
        """)
        sound_widget.setMinimumHeight(140)
        sound_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        sound_layout = QVBoxLayout(sound_widget)
        sound_layout.setContentsMargins(20, 16, 20, 16)
        sound_layout.setSpacing(12)

        sound_title_layout = QHBoxLayout()
        sound_icon = QLabel()
        sound_icon_pixmap = QPixmap("resources/icons/music.png")
        if not sound_icon_pixmap.isNull():
            sound_icon_pixmap = sound_icon_pixmap.scaled(20, 20, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            sound_icon.setPixmap(sound_icon_pixmap)
        else:
            sound_icon.setText("🎵")
        sound_title = QLabel("Фоновые звуки (опционально):")
        sound_title.setStyleSheet("font-weight: 600; color: #1F2937; font-size: 14px;")
        sound_title_layout.addWidget(sound_icon)
        sound_title_layout.addWidget(sound_title)
        sound_title_layout.addStretch()
        sound_layout.addLayout(sound_title_layout)

        self.music_widget = MusicWidget(self._music_controller)
        sound_layout.addWidget(self.music_widget)

        row2_layout.addWidget(sound_widget, 1)
        content_layout.addLayout(row2_layout)

        # ========== КНОПКА НАЧАТЬ СЕССИЮ ==========
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        # 🆕 Кнопка "Продолжить сессию" (скрыта по умолчанию)
        self.resume_btn = QPushButton("Продолжить сессию")
        self.resume_btn.setIcon(QIcon("resources/icons/play.png"))
        self.resume_btn.setIconSize(QSize(20, 20))
        self.resume_btn.setFixedWidth(200)
        self.resume_btn.setFixedHeight(48)
        self.resume_btn.setStyleSheet("""
                   QPushButton {
                       background-color: rgba(59, 130, 246, 0.15);
                       color: #3B82F6;
                       border: 1px solid #3B82F6;
                       border-radius: 12px;
                       padding: 10px 20px;
                       font-weight: 600;
                       font-size: 14px;
                   }
                   QPushButton:hover {
                       background-color: rgba(59, 130, 246, 0.25);
                       border: 1px solid #2563EB;
                       color: #2563EB;
                   }
               """)
        self.resume_btn.setVisible(False)  # Скрыта по умолчанию
        button_layout.addWidget(self.resume_btn)

        self.start_btn = QPushButton("Начать сессию")
        self.start_btn.setIcon(QIcon("resources/icons/rocket.png"))
        self.start_btn.setIconSize(QSize(20, 20))
        self.start_btn.setFixedWidth(200)
        self.start_btn.setFixedHeight(48)
        self.start_btn.setStyleSheet("""
                   QPushButton {
                       background-color: rgba(16, 185, 129, 0.15);
                       color: #059669;
                       border: 1px solid #10B981;
                       border-radius: 12px;
                       padding: 10px 20px;
                       font-weight: 600;
                       font-size: 14px;
                   }
                   QPushButton:hover {
                       background-color: rgba(16, 185, 129, 0.25);
                       border: 1px solid #059669;
                       color: #047857;
                   }
               """)
        button_layout.addWidget(self.start_btn)
        button_layout.addStretch()

        content_layout.addLayout(button_layout)
        content_layout.addStretch()

        scroll.setWidget(content)
        layout.addWidget(scroll)

        self.start_btn.clicked.connect(self._on_start)
        self.resume_btn.clicked.connect(self._on_resume)

        # Проверяем активные сессии при изменении темы
        self.topic_selector.topic_changed.connect(self._check_active_session)

        def _check_active_session(self, topic_id: int):
            """Проверяет, есть ли активная/пауза сессия для выбранной темы"""
            if not topic_id:
                self.resume_btn.setVisible(False)
                return

            from core.di.container import container
            has_session, session_id, status, existing_topic_id = container.session_controller.has_active_or_paused_session(
                topic_id)

            if has_session:
                self.resume_btn.setVisible(True)
                self.resume_btn.setText(f"Продолжить сессию ({status})")
            else:
                self.resume_btn.setVisible(False)

        def _on_resume(self):
            """Возобновляет существующую сессию"""
            topic_id = self.topic_selector.get_selected_topic_id()
            if not topic_id:
                return

            from core.di.container import container
            has_session, session_id, status, existing_topic_id = container.session_controller.has_active_or_paused_session(
                topic_id)

            if has_session:
                from core.main_window import MainWindow
                main_window = self.window()
                if isinstance(main_window, MainWindow):
                    topic = self._topic_controller.get_topic(topic_id)
                    if topic:
                        main_window.focus_active_view.resume_existing_session(
                            session_id, topic_id, topic.name
                        )
                        main_window.content_stack.setCurrentWidget(main_window.focus_active_view)

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

        # Проверяем, есть ли активная/пауза сессия для этой темы
        from core.di.container import container
        has_session, session_id, status, existing_topic_id = container.session_controller.has_active_or_paused_session(topic_id)

        if has_session:
            # Показываем диалог: продолжить или начать новую
            reply = SilentMessageBox.question(
                self,
                "Незавершённая сессия",
                f"У вас есть {status} сессия для этой темы.\n\n"
                "• Нажмите «Да» — чтобы завершить её и начать новую\n"
                "• Нажмите «Нет» — чтобы продолжить существующую сессию",
                SilentMessageBox.Yes | SilentMessageBox.No,
                SilentMessageBox.No
            )

            if reply == SilentMessageBox.Yes:
                # Завершаем старую сессию
                container.session_controller.end_session(session_id)
                # Начинаем новую
                interval = self.interval_combo.currentData()
                self.start_session.emit(topic_id, interval)
            else:
                # Возобновляем старую сессию
                from core.main_window import MainWindow
                main_window = self.window()
                if isinstance(main_window, MainWindow):
                    topic = self._topic_controller.get_topic(topic_id)
                    if topic:
                        main_window.focus_active_view.resume_existing_session(
                            session_id, topic_id, topic.name
                        )
                        main_window.content_stack.setCurrentWidget(main_window.focus_active_view)
        else:
            # Начинаем новую сессию
            interval = self.interval_combo.currentData()
            self.start_session.emit(topic_id, interval)

    def refresh_topics(self):
        self.topic_selector.refresh()