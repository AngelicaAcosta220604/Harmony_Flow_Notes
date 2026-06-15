from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTabWidget,
    QWidget, QTextEdit, QTableWidget, QTableWidgetItem, QHeaderView, QDialogButtonBox
)
from PySide6.QtCore import Qt

from .controller import SessionController
from .state_log_controller import SessionStateLogController
from services.time_service import TimeService


class SessionAnalyticsDialog(QDialog):
    """
    Диалог с аналитикой по конкретной сессии.
    """

    def __init__(
            self,
            session_id: int,
            session_controller: SessionController,
            state_log_controller: SessionStateLogController,
            parent=None
    ):
        super().__init__(parent)
        self._session_id = session_id
        self._session_controller = session_controller
        self._state_log_controller = state_log_controller
        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        """Настраивает интерфейс"""
        self.setWindowTitle(f"Аналитика сессии #{self._session_id}")
        self.setMinimumSize(600, 500)

        layout = QVBoxLayout(self)

        # Вкладки
        self.tab_widget = QTabWidget()

        # Вкладка "Обзор"
        self.overview_tab = QWidget()
        overview_layout = QVBoxLayout(self.overview_tab)
        self.overview_text = QTextEdit()
        self.overview_text.setReadOnly(True)
        overview_layout.addWidget(self.overview_text)
        self.tab_widget.addTab(self.overview_tab, "📊 Обзор")

        # Вкладка "Динамика состояния"
        self.timeline_tab = QWidget()
        timeline_layout = QVBoxLayout(self.timeline_tab)
        self.timeline_table = QTableWidget()
        self.timeline_table.setColumnCount(3)
        self.timeline_table.setHorizontalHeaderLabels(["Минута", "Показатель", "Значение"])
        self.timeline_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        timeline_layout.addWidget(self.timeline_table)
        self.tab_widget.addTab(self.timeline_tab, "📈 Динамика")

        # Вкладка "Быстрые записи"
        self.notes_tab = QWidget()
        notes_layout = QVBoxLayout(self.notes_tab)
        self.notes_text = QTextEdit()
        self.notes_text.setReadOnly(True)
        notes_layout.addWidget(self.notes_text)
        self.tab_widget.addTab(self.notes_tab, "✏️ Записи")

        layout.addWidget(self.tab_widget)

        # Кнопка закрытия
        button_box = QDialogButtonBox(QDialogButtonBox.Close)
        button_box.rejected.connect(self.accept)
        layout.addWidget(button_box)

    def _load_data(self):
        """Загружает данные для аналитики"""
        stats = self._session_controller.get_session_stats(self._session_id)

        # 🆕 Форматируем время
        from utils.local_time import format_datetime
        start_time_formatted = format_datetime(stats.get('start_time', '')) if stats.get('start_time') else '—'

        # Обзор
        overview = f"""
        <h2>📊 Обзор сессии</h2>

        <p><b>📅 Дата:</b> {start_time_formatted}</p>
        <p><b>⏱️ Длительность:</b> {stats.get('duration_display', '—')}</p>
        <p><b>✅ Статус:</b> {'Завершена' if stats.get('status') == 'completed' else 'Авто-завершена'}</p>

        <h3>📈 Средние показатели</h3>
        <ul>
            <li><b>🧠 Концентрация:</b> {stats.get('avg_focus', 0)}/100</li>
            <li><b>⚡ Энергия:</b> {stats.get('avg_energy', 0)}/100</li>
            <li><b>❤️ Интерес:</b> {stats.get('avg_interest', 0)}/100</li>
        </ul>

        <h3>📝 Активность</h3>
        <ul>
            <li><b>✏️ Быстрых записей:</b> {stats.get('quick_notes_count', 0)}</li>
            <li><b>📋 Интервалов работы:</b> {stats.get('intervals_count', 0)}</li>
            <li><b>⏱️ Активное время:</b> {TimeService.format_time(stats.get('total_active_seconds', 0))}</li>
        </ul>
        """
        self.overview_text.setHtml(overview)

        # Динамика состояния
        logs = self._state_log_controller.get_logs_for_session(self._session_id)
        self.timeline_table.setRowCount(len(logs))

        # 🆕 Используем 'focus' вместо 'concentration'
        metrics_names = {
            'focus': '🧠 Концентрация',
            'energy': '⚡ Энергия',
            'interest': '❤️ Интерес'
        }

        for row, log in enumerate(logs):
            minute_item = QTableWidgetItem(str(log['minute']))
            self.timeline_table.setItem(row, 0, minute_item)

            metric_item = QTableWidgetItem(metrics_names.get(log['metric'], log['metric']))
            self.timeline_table.setItem(row, 1, metric_item)

            value_item = QTableWidgetItem(str(log['value']))
            value_item.setTextAlignment(Qt.AlignCenter)
            self.timeline_table.setItem(row, 2, value_item)

        # Быстрые записи
        quick_notes = self._session_controller._quick_note_repo.get_by_session(self._session_id)

        notes_text = "<h3>✏️ Быстрые записи во время сессии</h3><ul>"
        for note in quick_notes:
            # 🆕 Форматируем время
            time = format_datetime(note.get('created_at', '')) if note.get('created_at') else '—'
            notes_text += f"<li><b>{time}</b><br>{note.get('content', '')}</li><br>"
        notes_text += "</ul>"

        if not quick_notes:
            notes_text += "<p>Нет быстрых записей</p>"

        self.notes_text.setHtml(notes_text)