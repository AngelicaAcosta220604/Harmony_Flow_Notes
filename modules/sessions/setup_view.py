# modules/sessions/setup_view.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QPushButton, QFrame, QScrollArea, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QIcon, QPixmap
import logging

from utils.resource_paths import get_resource_path
from modules.topics.widgets import TopicTreeSelector
from widgets import SilentMessageBox

# Настройка логирования
logger = logging.getLogger(__name__)


class FocusSetupView(QWidget):
    """Экран подготовки к сессии"""

    start_session = Signal(int, int)
    resume_session = Signal(int, int, str)  # session_id, topic_id, topic_name

    def __init__(self, topic_controller, music_controller=None, settings_controller=None, parent=None):
        super().__init__(parent)
        self._topic_controller = topic_controller
        self._music_controller = music_controller
        self._settings_controller = settings_controller
        self._setup_ui()
        self._load_settings()

    def _setup_ui(self):
        try:
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

            # ========== ЗАГОЛОВОК ==========
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
            header_pixmap = QPixmap(str(get_resource_path("resources/icons/session1.png")))
            if not header_pixmap.isNull():
                header_pixmap = header_pixmap.scaled(32, 32, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                header_icon.setPixmap(header_pixmap)
            header_layout.addWidget(header_icon)

            header_title = QLabel("Подготовка к фокус-сессии")
            header_title.setStyleSheet("font-size: 20px; font-weight: bold; color: #1F2937;")
            header_layout.addWidget(header_title)

            content_layout.addWidget(header_widget)

            # ========== РЯД: ЛЕВАЯ КОЛОНКА + ПРАВАЯ КОЛОНКА ==========
            main_row_layout = QHBoxLayout()
            main_row_layout.setSpacing(20)

            # ----- ЛЕВАЯ КОЛОНКА -----
            left_col = QWidget()
            left_col_layout = QVBoxLayout(left_col)
            left_col_layout.setContentsMargins(0, 0, 0, 0)

            topic_widget = QFrame()
            topic_widget.setStyleSheet("""
                QFrame {
                    background-color: #FFFFFF;
                    border-radius: 16px;
                    border: none;
                }
            """)
            topic_widget.setMinimumHeight(120)

            topic_layout = QVBoxLayout(topic_widget)
            topic_layout.setContentsMargins(20, 16, 20, 16)
            topic_layout.setSpacing(12)

            topic_title_layout = QHBoxLayout()
            topic_icon = QLabel()
            topic_icon_pixmap = QPixmap(str(get_resource_path("resources/icons/new_notes1.png")))
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

            left_col_layout.addWidget(topic_widget)
            main_row_layout.addWidget(left_col, 1)

            # ----- ПРАВАЯ КОЛОНКА -----
            right_col = QWidget()
            right_col_layout = QVBoxLayout(right_col)
            right_col_layout.setContentsMargins(0, 0, 0, 0)

            interval_widget = QFrame()
            interval_widget.setStyleSheet("""
                QFrame {
                    background-color: #FFFFFF;
                    border-radius: 16px;
                    border: none;
                }
            """)
            interval_widget.setMinimumHeight(120)

            interval_layout = QVBoxLayout(interval_widget)
            interval_layout.setContentsMargins(20, 16, 20, 16)
            interval_layout.setSpacing(12)

            interval_title_layout = QHBoxLayout()
            interval_icon = QLabel()
            interval_icon_pixmap = QPixmap(str(get_resource_path("resources/icons/time1.png")))
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
            """)
            interval_layout.addWidget(self.interval_combo)

            right_col_layout.addWidget(interval_widget)
            main_row_layout.addWidget(right_col, 1)

            content_layout.addLayout(main_row_layout)

            # ========== КНОПКИ ==========
            # ✅ ИСПРАВЛЕНО: создаём ВСЕ кнопки ПЕРЕД добавлением layout в content
            button_layout = QHBoxLayout()
            button_layout.addStretch()

            # Кнопка "Начать сессию"
            self.start_btn = QPushButton("Начать сессию")
            self.start_btn.setIcon(QIcon(str(get_resource_path("resources/icons/play1.png"))))
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

            # ✅ ИСПРАВЛЕНО: кнопка возобновления добавляется СРАЗУ после start_btn
            self.resume_btn = QPushButton("▶ Возобновить")
            self.resume_btn.setIcon(QIcon(str(get_resource_path("resources/icons/play1.png"))))
            self.resume_btn.setIconSize(QSize(20, 20))
            self.resume_btn.setFixedWidth(200)
            self.resume_btn.setFixedHeight(48)
            self.resume_btn.setVisible(False)
            self.resume_btn.setStyleSheet("""
                QPushButton {
                    background-color: rgba(245, 158, 11, 0.15);
                    color: #D97706;
                    border: 1px solid #F59E0B;
                    border-radius: 12px;
                    padding: 10px 20px;
                    font-weight: 600;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background-color: rgba(245, 158, 11, 0.25);
                    border: 1px solid #D97706;
                    color: #B45309;
                }
            """)
            button_layout.addWidget(self.resume_btn)

            button_layout.addStretch()

            # ✅ ТЕПЕРЬ добавляем layout в content (после всех кнопок)
            content_layout.addLayout(button_layout)
            content_layout.addStretch()

            scroll.setWidget(content)
            layout.addWidget(scroll)

            # Подключаем сигналы
            self.start_btn.clicked.connect(self._on_start)
            self.resume_btn.clicked.connect(self._on_resume_clicked)

            logger.debug("FocusSetupView инициализирован")
        except Exception as e:
            logger.error(f"Ошибка настройки FocusSetupView: {e}", exc_info=True)

    def _on_resume_clicked(self):
        """Возобновление существующей сессии"""
        try:
            from core.di.container import container
            has_session, session_id, status, topic_id = container.session_controller.has_active_or_paused_session()

            if has_session and session_id:
                topic = container.topic_controller.get_topic(topic_id)
                if topic:
                    self.resume_session.emit(session_id, topic_id, topic.name)
                    logger.info(f"Запрошено возобновление сессии {session_id}")
            else:
                logger.warning("Нет активной сессии для возобновления")
                SilentMessageBox.information(self, "Информация", "Нет активной сессии для возобновления")
        except Exception as e:
            logger.error(f"Ошибка возобновления сессии: {e}", exc_info=True)
            SilentMessageBox.warning(self, "Ошибка", f"Не удалось возобновить сессию: {e}")

    def _load_settings(self):
        """Загружает настройки и проверяет активные сессии"""
        try:
            if self._settings_controller:
                default_interval = self._settings_controller.get_activity_check_interval()
                index = self.interval_combo.findData(default_interval)
                if index >= 0:
                    self.interval_combo.setCurrentIndex(index)

            # Проверяем наличие активных сессий
            from core.di.container import container
            has_session, session_id, status, topic_id = container.session_controller.has_active_or_paused_session()

            if has_session:
                self.resume_btn.setVisible(True)
                status_text = {
                    'active': 'активна',
                    'paused': 'на паузе'
                }.get(status, status)
                self.resume_btn.setText(f"▶ Возобновить ({status_text})")
                logger.debug(f"Найдена сессия для возобновления: {session_id} ({status})")
            else:
                self.resume_btn.setVisible(False)
        except Exception as e:
            logger.error(f"Ошибка загрузки настроек: {e}", exc_info=True)

    def _on_start(self):
        """Запуск сессии"""
        try:
            topic_id = self.topic_selector.get_selected_topic_id()
            if not topic_id:
                SilentMessageBox.warning(self, "Ошибка", "Выберите тему для сессии")
                logger.warning("Попытка начать сессию без выбранной темы")
                return

            interval = self.interval_combo.currentData()
            self.start_session.emit(topic_id, interval)
            logger.info(f"Запрошен запуск сессии для темы {topic_id}, интервал {interval} мин")
        except Exception as e:
            logger.error(f"Ошибка запуска сессии: {e}", exc_info=True)
            SilentMessageBox.warning(self, "Ошибка", f"Не удалось начать сессию: {e}")

    def refresh_topics(self):
        """Обновляет список тем"""
        try:
            self.topic_selector.refresh()
            logger.debug("Список тем обновлен")
        except Exception as e:
            logger.error(f"Ошибка обновления списка тем: {e}", exc_info=True)