from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QGraphicsDropShadowEffect, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QFont, QPixmap, QIcon, QColor

from .controller import DashboardController




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
        self.setMinimumHeight(150)
        self.setMinimumWidth(120)  # Минимальная ширина карточки
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
        layout.setSpacing(16)
        layout.setAlignment(Qt.AlignCenter)

        # Цветной круг с иконкой
        self.icon_container = QLabel()
        self.icon_container.setFixedSize(52, 52)
        self.icon_container.setAlignment(Qt.AlignCenter)

        self.icon_label = QLabel()
        self.icon_label.setAlignment(Qt.AlignCenter)

        icon_layout = QVBoxLayout(self.icon_container)
        icon_layout.setContentsMargins(0, 0, 0, 0)
        icon_layout.addWidget(self.icon_label)

        layout.addWidget(self.icon_container)

        # Название
        self.title_label = QLabel()
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet(
            "font-size: 13px; color: #6B7280; background-color: transparent; font-weight: 500; padding-top: 4px;")
        layout.addWidget(self.title_label)

        # Значение
        self.value_label = QLabel()
        self.value_label.setAlignment(Qt.AlignCenter)
        self.value_label.setStyleSheet(
            "font-size: 28px; font-weight: bold; color: #1F2937; background-color: transparent;")
        layout.addWidget(self.value_label)

        self.current_title = ""
        self.current_icon_path = ""

    def _update_icon_style(self):
        color = self.ICON_COLORS.get(self.current_title, "#3B82F6")
        r = int(color[1:3], 16)
        g = int(color[3:5], 16)
        b = int(color[5:7], 16)
        self.icon_container.setStyleSheet(f"""
            border-radius: 26px;
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
            pixmap = pixmap.scaled(30, 30, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.icon_label.setPixmap(pixmap)
            self.icon_label.setStyleSheet("background-color: transparent;")

        self._update_icon_style()


class KpiRow(QWidget):
    """
    Адаптивный ряд KPI-карточек.
    При узком окне карточки переносятся на следующую строку.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        # 🆕 Внешний layout — вертикальный, содержит несколько строк
        self._outer_layout = QVBoxLayout(self)
        self._outer_layout.setSpacing(16)
        self._outer_layout.setContentsMargins(0, 0, 0, 0)

        #  Первая строка карточек
        self._current_row_layout = QHBoxLayout()
        self._current_row_layout.setSpacing(16)
        self._current_row_layout.setContentsMargins(0, 0, 0, 0)
        self._outer_layout.addLayout(self._current_row_layout)

        self._outer_layout.addStretch()

        self.cards = []
        self._cards_per_row = 6  # По умолчанию 6 в ряд

    def _start_new_row(self):
        """Создаёт новую строку для карточек"""
        new_row_layout = QHBoxLayout()
        new_row_layout.setSpacing(16)
        new_row_layout.setContentsMargins(0, 0, 0, 0)
        # Вставляем перед stretch
        self._outer_layout.insertLayout(self._outer_layout.count() - 1, new_row_layout)
        self._current_row_layout = new_row_layout
        self._cards_in_current_row = 0

    def add_card(self, title: str, value: str, icon_path: str):
        for card in self.cards:
            if card.title_label.text() == "":
                # 🆕 Если в текущей строке уже максимум карточек — создаём новую строку
                if not hasattr(self, '_cards_in_current_row'):
                    self._cards_in_current_row = 0
                if self._cards_in_current_row >= self._cards_per_row:
                    self._start_new_row()

                card.set_data(title, value, icon_path)
                card.show()
                self._current_row_layout.addWidget(card, 1)
                self._cards_in_current_row += 1
                return

    def clear(self):
        for card in self.cards:
            card.hide()
            card.title_label.setText("")
            card.value_label.setText("")

        # 🆕 Сбрасываем счётчик строк
        self._cards_in_current_row = 0
