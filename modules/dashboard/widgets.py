# modules/dashboard/widgets.py
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont


class KpiCard(QFrame):
    """
    Карточка с ключевым показателем (KPI)
    """

    def __init__(self, title: str, value: str, icon: str = "", parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShadow(QFrame.Raised)
        self.setProperty("class", "kpi-card")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 10, 15, 10)

        # Верхняя строка с иконкой и заголовком
        top_layout = QHBoxLayout()

        if icon:
            icon_label = QLabel(icon)
            icon_label.setStyleSheet("font-size: 24px;")
            top_layout.addWidget(icon_label)

        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 12px; color: #888888;")
        top_layout.addWidget(title_label)
        top_layout.addStretch()

        layout.addLayout(top_layout)

        # Значение
        value_label = QLabel(str(value))
        value_label.setStyleSheet("font-size: 28px; font-weight: bold;")
        value_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(value_label)

        self.setMinimumWidth(120)

    def set_value(self, value: str):
        """Обновляет значение"""
        value_label = self.findChild(QLabel, "value")
        if value_label:
            value_label.setText(str(value))


class KpiRow(QWidget):
    """
    Строка с несколькими KPI карточками
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QHBoxLayout(self)
        self.layout.setSpacing(15)
        self.layout.setContentsMargins(0, 0, 0, 0)

    def add_card(self, title: str, value: str, icon: str = "") -> KpiCard:
        """Добавляет карточку и возвращает её для обновления"""
        card = KpiCard(title, value, icon)
        self.layout.addWidget(card)
        return card

    def clear(self):
        """Очищает все карточки"""
        while self.layout.count():
            child = self.layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()