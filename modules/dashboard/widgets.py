from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QFrame, QGraphicsDropShadowEffect,
    QSizePolicy
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QColor


class KpiCard(QFrame):
    # Цвета для подложки иконки
    ICON_COLORS = {
        "Темы": "#3B82F6",
        "Заметки": "#8B5CF6",
        "Карточки": "#EC4899",
        "Задачи": "#10B981",
        "Сессии": "#F59E0B",
        "Время": "#EF4444",
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(110)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.setStyleSheet("""
            KpiCard {
                background-color: #FFFFFF;
                border-radius: 20px;
                border: none;
            }
        """)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(12)
        shadow.setOffset(0, 2)
        shadow.setColor(QColor(0, 0, 0, 15))
        self.setGraphicsEffect(shadow)

        # Основной вертикальный layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignTop)

        # Цветной круг с иконкой
        self.icon_container = QLabel()
        self.icon_container.setFixedSize(44, 44)
        self.icon_container.setAlignment(Qt.AlignCenter)

        self.icon_label = QLabel()
        self.icon_label.setAlignment(Qt.AlignCenter)

        icon_layout = QVBoxLayout(self.icon_container)
        icon_layout.setContentsMargins(0, 0, 0, 0)
        icon_layout.addWidget(self.icon_label)

        layout.addWidget(self.icon_container)

        # Название
        self.title_label = QLabel()
        self.title_label.setStyleSheet(
            "font-size: 12px; color: #6B7280; background-color: transparent; font-weight: 500;")
        layout.addWidget(self.title_label)

        # Значение
        self.value_label = QLabel()
        self.value_label.setStyleSheet(
            "font-size: 26px; font-weight: bold; color: #1F2937; background-color: transparent;")
        layout.addWidget(self.value_label)

        layout.addStretch()

        self.current_title = ""
        self.current_icon_path = ""

    def _update_icon_style(self):
        color = self.ICON_COLORS.get(self.current_title, "#3B82F6")
        r = int(color[1:3], 16)
        g = int(color[3:5], 16)
        b = int(color[5:7], 16)
        self.icon_container.setStyleSheet(f"""
            border-radius: 22px;
            background-color: rgba({r}, {g}, {b}, 0.15);
        """)

    def set_data(self, title: str, value: str, icon_path: str):
        self.current_title = title
        self.current_icon_path = icon_path
        self.title_label.setText(title)
        self.value_label.setText(value)

        # Загружаем иконку
        pixmap = QPixmap(icon_path)
        if not pixmap.isNull():
            pixmap = pixmap.scaled(24, 24, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.icon_label.setPixmap(pixmap)
            self.icon_label.setStyleSheet("background-color: transparent;")

        self._update_icon_style()


class KpiRow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(0, 0, 0, 0)

        self.cards = []
        for i in range(6):
            card = KpiCard()
            self.cards.append(card)
            layout.addWidget(card, 1)

    def add_card(self, title: str, value: str, icon_path: str):
        for card in self.cards:
            if card.title_label.text() == "":
                card.set_data(title, value, icon_path)
                card.show()
                return

    def clear(self):
        for card in self.cards:
            card.hide()
            card.title_label.setText("")
            card.value_label.setText("")