# modules/sessions/history_view.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox
)
from PySide6.QtCore import Qt, Signal

from .controller import SessionController


class SessionsView(QWidget):
    """
    Экран истории сессий.
    """

    session_selected = Signal(int)  # session_id

    def __init__(self, controller: SessionController, parent=None):
        super().__init__(parent)
        self._controller = controller
        self._setup_ui()
        self._connect_signals()
        self._load_sessions()

    def _setup_ui(self):
        """Настраивает интерфейс"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Заголовок
        header_layout = QHBoxLayout()
        title_label = QLabel("⏱️ История сессий")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        header_layout.addWidget(title_label)

        header_layout.addStretch()

        self.refresh_btn = QPushButton("🔄 Обновить")
        header_layout.addWidget(self.refresh_btn)

        layout.addLayout(header_layout)

        # Таблица
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Дата", "Тема", "Длительность", "Статус", ""])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)

        layout.addWidget(self.table)

    def _connect_signals(self):
        """Подключает сигналы"""
        self.refresh_btn.clicked.connect(self._load_sessions)
        self.table.cellDoubleClicked.connect(self._on_cell_double_clicked)

    def _load_sessions(self):
        """Загружает сессии в таблицу"""
        sessions = self._controller.get_all_sessions()

        self.table.setRowCount(len(sessions))

        for row, session in enumerate(sessions):
            # Дата
            date_item = QTableWidgetItem(session['date'])
            self.table.setItem(row, 0, date_item)

            # Тема
            topic_item = QTableWidgetItem(session['topic_name'])
            self.table.setItem(row, 1, topic_item)

            # Длительность
            duration_item = QTableWidgetItem(session['duration_display'])
            self.table.setItem(row, 2, duration_item)

            # Статус
            status_text = "✅ Завершена" if session['status'] == 'completed' else "🔄 Авто-завершена"
            status_item = QTableWidgetItem(status_text)
            self.table.setItem(row, 3, status_item)

            # Кнопка "Аналитика"
            btn = QPushButton("📊 Аналитика")
            btn.clicked.connect(lambda checked, sid=session['id']: self.session_selected.emit(sid))
            self.table.setCellWidget(row, 4, btn)

    def _on_cell_double_clicked(self, row: int, column: int):
        """Обработчик двойного клика по строке"""
        sessions = self._controller.get_all_sessions()
        if row < len(sessions):
            self.session_selected.emit(sessions[row]['id'])

    def refresh(self):
        """Обновляет таблицу"""
        self._load_sessions()