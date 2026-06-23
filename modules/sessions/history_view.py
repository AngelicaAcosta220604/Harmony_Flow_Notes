# modules/sessions/history_view.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QFrame, QScrollArea, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QIcon, QPixmap
import logging

from utils.resource_paths import get_resource_path
from widgets import SilentMessageBox
from .controller import SessionController

# Настройка логирования
logger = logging.getLogger(__name__)


class SessionCard(QFrame):
    """Карточка одной сессии"""

    resume_clicked = Signal(int)
    delete_clicked = Signal(int)
    analytics_clicked = Signal(int)

    def __init__(self, session_data: dict, parent=None):
        super().__init__(parent)
        self.session_id = session_data['id']
        self.session_data = session_data
        self._is_expanded = False
        self._setup_ui()

    def _setup_ui(self):
        try:
            self.setStyleSheet("""
                QFrame {
                    background-color: #FFFFFF;
                    border-radius: 12px;
                    border: 1px solid #E6EEF6;
                }
            """)

            layout = QVBoxLayout(self)
            layout.setContentsMargins(16, 12, 16, 12)
            layout.setSpacing(8)

            # Верхняя строка: статус + тема + длительность
            top_layout = QHBoxLayout()
            top_layout.setSpacing(12)

            status = self.session_data.get('status', 'completed')
            if status == 'active':
                status_text = " Активна"
                status_color = "#10B981"
            elif status == 'paused':
                status_text = " Пауза"
                status_color = "#F59E0B"
            elif status == 'completed':
                status_text = "✅ Завершена"
                status_color = "#3B82F6"
            else:
                status_text = "⚪ Авто"
                status_color = "#6B7280"

            status_label = QLabel(status_text)
            status_label.setStyleSheet(f"color: {status_color}; font-weight: 600; font-size: 13px;")
            top_layout.addWidget(status_label)

            topic_label = QLabel(self.session_data.get('topic_name', '—'))
            topic_label.setStyleSheet("font-weight: 600; color: #1F2937; font-size: 14px;")
            top_layout.addWidget(topic_label, 1)

            duration_label = QLabel(self.session_data.get('duration_display', '—'))
            duration_label.setStyleSheet("color: #6B7280; font-size: 13px;")
            top_layout.addWidget(duration_label)

            layout.addLayout(top_layout)

            # Вторая строка: время начала/конца + статистика
            middle_layout = QHBoxLayout()
            middle_layout.setSpacing(16)

            start_time = self.session_data.get('start_time', '')[:16] if self.session_data.get('start_time') else '—'
            end_time = self.session_data.get('end_time', '')[:16] if self.session_data.get('end_time') else '—'
            time_label = QLabel(f"🕐 {start_time} → {end_time}")
            time_label.setStyleSheet("color: #6B7280; font-size: 12px;")
            middle_layout.addWidget(time_label)

            avg_focus = self.session_data.get('avg_focus', 0)
            avg_energy = self.session_data.get('avg_energy', 0)
            avg_interest = self.session_data.get('avg_interest', 0)

            if avg_focus or avg_energy or avg_interest:
                stats_label = QLabel(f"🧠 {avg_focus} | ⚡ {avg_energy} | ❤️ {avg_interest}")
                stats_label.setStyleSheet("color: #6B7280; font-size: 12px;")
                middle_layout.addWidget(stats_label)

            middle_layout.addStretch()
            layout.addLayout(middle_layout)

            # Кнопки
            buttons_layout = QHBoxLayout()
            buttons_layout.setSpacing(8)

            intervals_count = self.session_data.get('intervals_count', 0)
            if intervals_count > 0:
                self.intervals_btn = QPushButton(f"📋 Интервалы ({intervals_count})")
                self.intervals_btn.setIconSize(QSize(14, 14))
                self.intervals_btn.setFixedHeight(32)
                self.intervals_btn.setStyleSheet("""
                    QPushButton {
                        background-color: rgba(107, 114, 128, 0.1);
                        color: #6B7280;
                        border: 1px solid #E6EEF6;
                        border-radius: 8px;
                        padding: 4px 12px;
                        font-size: 12px;
                    }
                    QPushButton:hover {
                        background-color: rgba(107, 114, 128, 0.2);
                    }
                """)
                self.intervals_btn.clicked.connect(self._toggle_intervals)
                buttons_layout.addWidget(self.intervals_btn)

            if status in ('active', 'paused'):
                resume_btn = QPushButton("▶ Продолжить")
                resume_btn.setIconSize(QSize(14, 14))
                resume_btn.setFixedHeight(32)
                resume_btn.setStyleSheet("""
                    QPushButton {
                        background-color: rgba(16, 185, 129, 0.15);
                        color: #059669;
                        border: 1px solid #10B981;
                        border-radius: 8px;
                        padding: 4px 12px;
                        font-size: 12px;
                        font-weight: 500;
                    }
                    QPushButton:hover {
                        background-color: rgba(16, 185, 129, 0.25);
                    }
                """)
                resume_btn.clicked.connect(lambda: self.resume_clicked.emit(self.session_id))
                buttons_layout.addWidget(resume_btn)

            analytics_btn = QPushButton("📊 Аналитика")
            analytics_btn.setIconSize(QSize(14, 14))
            analytics_btn.setFixedHeight(32)
            analytics_btn.setStyleSheet("""
                QPushButton {
                    background-color: rgba(59, 130, 246, 0.15);
                    color: #3B82F6;
                    border: 1px solid #3B82F6;
                    border-radius: 8px;
                    padding: 4px 12px;
                    font-size: 12px;
                    font-weight: 500;
                }
                QPushButton:hover {
                    background-color: rgba(59, 130, 246, 0.25);
                }
            """)
            analytics_btn.clicked.connect(lambda: self.analytics_clicked.emit(self.session_id))
            buttons_layout.addWidget(analytics_btn)

            buttons_layout.addStretch()

            delete_btn = QPushButton("")
            delete_btn.setIconSize(QSize(14, 14))
            delete_btn.setFixedSize(32, 32)
            delete_btn.setToolTip("Удалить сессию")
            delete_btn.setStyleSheet("""
                QPushButton {
                    background-color: rgba(239, 68, 68, 0.15);
                    color: #EF4444;
                    border: 1px solid #EF4444;
                    border-radius: 8px;
                    padding: 4px;
                }
                QPushButton:hover {
                    background-color: rgba(239, 68, 68, 0.25);
                }
            """)
            delete_btn.clicked.connect(self._on_delete_clicked)
            buttons_layout.addWidget(delete_btn)

            layout.addLayout(buttons_layout)

            # Контейнер для интервалов (скрыт по умолчанию)
            self.intervals_container = QFrame()
            self.intervals_container.setVisible(False)
            self.intervals_container.setStyleSheet("""
                QFrame {
                    background-color: #F9FAFB;
                    border-radius: 8px;
                    border: 1px solid #E6EEF6;
                }
            """)
            intervals_layout = QVBoxLayout(self.intervals_container)
            intervals_layout.setContentsMargins(12, 8, 12, 8)
            intervals_layout.setSpacing(4)

            intervals = self.session_data.get('intervals', [])
            if intervals:
                for i, interval in enumerate(intervals):
                    start = interval.get('start_time', '')[:16] if interval.get('start_time') else '—'
                    end = interval.get('end_time', '')[:16] if interval.get('end_time') else '—'
                    duration = interval.get('duration_seconds', 0)
                    duration_min = duration // 60
                    duration_sec = duration % 60

                    interval_label = QLabel(f"  #{i + 1}: {start} → {end} ({duration_min}м {duration_sec}с)")
                    interval_label.setStyleSheet("color: #4B5563; font-size: 12px;")
                    intervals_layout.addWidget(interval_label)
            else:
                no_intervals_label = QLabel("  Нет данных об интервалах")
                no_intervals_label.setStyleSheet("color: #9CA3AF; font-size: 12px; font-style: italic;")
                intervals_layout.addWidget(no_intervals_label)

            layout.addWidget(self.intervals_container)
        except Exception as e:
            logger.error(f"Ошибка настройки SessionCard для сессии {self.session_id}: {e}", exc_info=True)

    def _toggle_intervals(self):
        """Переключает видимость интервалов"""
        self._is_expanded = not self._is_expanded
        self.intervals_container.setVisible(self._is_expanded)

    def _on_delete_clicked(self):
        """Удаление сессии"""
        try:
            reply = SilentMessageBox.question(
                self, "Удалить сессию?",
                "Вы действительно хотите удалить эту сессию?\nЭто действие нельзя отменить."
            )
            if reply == SilentMessageBox.Yes:
                self.delete_clicked.emit(self.session_id)
        except Exception as e:
            logger.error(f"Ошибка удаления сессии {self.session_id}: {e}", exc_info=True)


class SessionsView(QWidget):
    """Экран истории сессий"""

    session_selected = Signal(int)
    session_resumed = Signal(int)
    session_deleted = Signal()

    def __init__(self, controller: SessionController, parent=None):
        super().__init__(parent)
        self._controller = controller
        self._setup_ui()
        self._connect_signals()
        self._load_sessions()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

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
        # ✅ ИСПРАВЛЕНО: используем get_resource_path
        header_pixmap = QPixmap(str(get_resource_path("resources/icons/session.png")))
        if not header_pixmap.isNull():
            header_pixmap = header_pixmap.scaled(32, 32, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            header_icon.setPixmap(header_pixmap)
        header_layout.addWidget(header_icon)

        header_title = QLabel("История сессий")
        header_title.setStyleSheet("font-size: 20px; font-weight: bold; color: #1F2937;")
        header_layout.addWidget(header_title)

        header_layout.addStretch()

        self.refresh_btn = QPushButton("🔄 Обновить")
        self.refresh_btn.setFixedWidth(120)
        self.refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(59, 130, 246, 0.15);
                color: #3B82F6;
                border: 1px solid #3B82F6;
                border-radius: 12px;
                padding: 8px 14px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: rgba(59, 130, 246, 0.25);
            }
        """)
        header_layout.addWidget(self.refresh_btn)

        layout.addWidget(header_widget)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("background-color: transparent; border: none;")

        self.cards_container = QWidget()
        self.cards_layout = QVBoxLayout(self.cards_container)
        self.cards_layout.setContentsMargins(0, 0, 0, 0)
        self.cards_layout.setSpacing(12)
        self.cards_layout.addStretch()

        scroll.setWidget(self.cards_container)
        layout.addWidget(scroll)

    def _connect_signals(self):
        self.refresh_btn.clicked.connect(self._load_sessions)

    def _load_sessions(self):
        try:
            while self.cards_layout.count() > 1:
                item = self.cards_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()

            all_sessions = self._controller.get_all_sessions()

            if not all_sessions:
                no_sessions_label = QLabel("📭 Нет сессий. Начните первую сессию!")
                no_sessions_label.setAlignment(Qt.AlignCenter)
                no_sessions_label.setStyleSheet("color: #6B7280; font-size: 14px; padding: 40px;")
                self.cards_layout.insertWidget(0, no_sessions_label)
                return

            def sort_key(s):
                if s['status'] in ('active', 'paused'):
                    return (0, s['date'])
                return (1, s['date'])

            all_sessions.sort(key=sort_key, reverse=True)

            for session_data in all_sessions:
                stats = self._controller.get_session_stats(session_data['id'])
                session_data.update(stats)

                intervals = self._controller.get_session_intervals(session_data['id'])
                session_data['intervals'] = intervals

                card = SessionCard(session_data)
                card.resume_clicked.connect(self._on_resume_clicked)
                card.delete_clicked.connect(self._on_delete_clicked)
                card.analytics_clicked.connect(self._on_analytics_clicked)

                self.cards_layout.insertWidget(self.cards_layout.count() - 1, card)

            logger.debug(f"Загружено {len(all_sessions)} сессий")
        except Exception as e:
            logger.error(f"Ошибка загрузки сессий: {e}", exc_info=True)
            SilentMessageBox.warning(self, "Ошибка", f"Не удалось загрузить историю сессий: {e}")

    def _on_resume_clicked(self, session_id: int):
        self.session_resumed.emit(session_id)

    def _on_delete_clicked(self, session_id: int):
        try:
            self._controller.delete_session(session_id)
            self._load_sessions()
            self.session_deleted.emit()
            logger.info(f"Сессия {session_id} удалена")
        except Exception as e:
            logger.error(f"Ошибка удаления сессии {session_id}: {e}", exc_info=True)
            SilentMessageBox.warning(self, "Ошибка", f"Не удалось удалить сессию: {e}")

    def _on_analytics_clicked(self, session_id: int):
        self.session_selected.emit(session_id)

    def refresh(self):
        self._load_sessions()