# modules/analytics/insights.py
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QScrollArea, QFrame
from PySide6.QtCore import Qt
from typing import List


class AnalyticsInsights(QWidget):
    """
    Виджет для отображения текстовых выводов (инсайтов) аналитики.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        """Настраивает интерфейс"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        # Заголовок
        title_label = QLabel("💡 Аналитические выводы")
        title_label.setStyleSheet("font-size: 14px; font-weight: bold; margin-bottom: 5px;")
        layout.addWidget(title_label)

        # Скролл-область для списка инсайтов
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        self.container = QWidget()
        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setAlignment(Qt.AlignTop)
        self.container_layout.setSpacing(8)

        scroll.setWidget(self.container)
        layout.addWidget(scroll)

    def set_insights(self, insights: List[str]):
        """
        Устанавливает список инсайтов

        Args:
            insights: Список строк с выводами
        """
        # Очищаем
        while self.container_layout.count():
            child = self.container_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        if not insights:
            empty_label = QLabel("📭 Нет данных для анализа")
            empty_label.setAlignment(Qt.AlignCenter)
            empty_label.setStyleSheet("color: #888888; padding: 20px;")
            self.container_layout.addWidget(empty_label)
            return

        for insight in insights:
            insight_widget = self._create_insight_widget(insight)
            self.container_layout.addWidget(insight_widget)

    def _create_insight_widget(self, insight: str) -> QFrame:
        """Создаёт виджет для одного инсайта"""
        widget = QFrame()
        widget.setFrameShape(QFrame.StyledPanel)

        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 8, 10, 8)

        label = QLabel(insight)
        label.setWordWrap(True)
        label.setStyleSheet("font-size: 12px;")

        layout.addWidget(label)

        return widget

    def clear(self):
        """Очищает все инсайты"""
        self.set_insights([])