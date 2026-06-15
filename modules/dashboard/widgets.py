from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QFrame, QGraphicsDropShadowEffect,
    QSizePolicy
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QPixmap, QFont, QColor


class KpiCard(QFrame):
    """Карточка KPI с иконкой, названием и значением"""

    def __init__(self, title: str = "", value: str = "", icon_path: str = None, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.StyledPanel)
        self.setProperty("class", "kpi-card")

        # Убираем фиксированную высоту и ширину — делаем адаптивными
        self.setMinimumHeight(100)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.setStyleSheet("""
            KpiCard {
                background-color: #ffffff;
                border-radius: 16px;
                border: none;
            }
        """)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setOffset(2, 2)
        shadow.setColor(QColor(0, 0, 0, 30))
        self.setGraphicsEffect(shadow)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(10)

        self.icon_label = QLabel()
        self.icon_path = icon_path
        self.icon_label.setStyleSheet("background-color: transparent;")
        self._update_icon()

        text_widget = QWidget()
        text_widget.setStyleSheet("background-color: transparent;")
        text_layout = QVBoxLayout(text_widget)
        text_layout.setSpacing(4)

        self.title_label = QLabel(title)
        self.title_label.setStyleSheet("font-size: 12px; color: #1E2A3E; background-color: transparent;")

        self.value_label = QLabel(value)
        self.value_label.setStyleSheet(
            "font-size: 24px; font-weight: bold; color: #1E2A3E; background-color: transparent;")

        text_layout.addWidget(self.title_label)
        text_layout.addWidget(self.value_label)
        text_layout.addStretch()

        layout.addWidget(self.icon_label)
        layout.addWidget(text_widget)
        layout.addStretch()

    def _update_icon(self):
        if self.icon_path:
            pixmap = QPixmap(self.icon_path)
            if not pixmap.isNull():
                pixmap = pixmap.scaled(32, 32, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.icon_label.setPixmap(pixmap)
                return
        self.icon_label.setText("📊")
        self.icon_label.setStyleSheet("font-size: 32px; background-color: transparent; color: #1E2A3E;")

    def set_value(self, value: str):
        self.value_label.setText(value)

    def set_title(self, title: str):
        self.title_label.setText(title)

    def set_icon(self, icon_path: str):
        self.icon_path = icon_path
        self._update_icon()


class KpiRow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(0, 0, 0, 0)

        self._cards = []

        # Создаём 6 карточек с одинаковым коэффициентом растяжения
        for i in range(6):
            card = KpiCard()
            self._cards.append(card)
            layout.addWidget(card, 1)  # stretch factor = 1 — одинаковый для всех

    def add_card(self, title: str, value: str, icon_path: str = None):
        for card in self._cards:
            if card.title_label.text() == "" or card.title_label.text() == title:
                card.set_title(title)
                card.set_value(value)
                if icon_path:
                    card.set_icon(icon_path)
                card.show()
                return

    def clear(self):
        for card in self._cards:
            card.hide()
            card.set_title("")
            card.set_value("")