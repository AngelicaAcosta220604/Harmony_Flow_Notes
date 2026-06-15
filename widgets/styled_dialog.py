# widgets/styled_dialog.py
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QColor


class StyledInputDialog(QDialog):
    def __init__(self, title: str, label: str, parent=None, default_text: str = ""):
        super().__init__(parent)
        self._result_text = ""
        self._dragging = False
        self._drag_position = QPoint()

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setModal(True)
        self.setFixedSize(400, 260)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self.content = QWidget()
        self.content.setObjectName("Content")
        main_layout.addWidget(self.content)

        content_layout = QVBoxLayout(self.content)
        content_layout.setContentsMargins(24, 20, 24, 24)
        content_layout.setSpacing(16)

        header_layout = QHBoxLayout()
        self.title_label = QLabel(title)
        self.title_label.setObjectName("Title")
        header_layout.addWidget(self.title_label)
        header_layout.addStretch()

        self.close_btn = QPushButton("✕")
        self.close_btn.setObjectName("CloseBtn")
        self.close_btn.setFixedSize(30, 30)
        self.close_btn.clicked.connect(self.reject)
        header_layout.addWidget(self.close_btn)
        content_layout.addLayout(header_layout)

        self.label = QLabel(label)
        self.label.setObjectName("Label")
        content_layout.addWidget(self.label)

        self.input = QLineEdit()
        self.input.setObjectName("Input")
        self.input.setFixedHeight(40)
        if default_text:
            self.input.setText(default_text)
            self.input.selectAll()
        content_layout.addWidget(self.input)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        btn_layout.addStretch()

        self.cancel_btn = QPushButton("Отмена")
        self.cancel_btn.setObjectName("CancelBtn")
        self.cancel_btn.setFixedSize(100, 36)
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)

        self.ok_btn = QPushButton("ОК")
        self.ok_btn.setObjectName("OkBtn")
        self.ok_btn.setFixedSize(100, 36)
        self.ok_btn.clicked.connect(self._on_ok)
        btn_layout.addWidget(self.ok_btn)

        content_layout.addLayout(btn_layout)

        self.setStyleSheet("""
            #Content {
                background-color: #FFFFFF;
                border-radius: 16px;
            }
            #Title {
                font-size: 14px;
                font-weight: 600;
                color: #1F2937;
            }
            #CloseBtn {
                background-color: transparent;
                color: #6B7280;
                border: none;
                border-radius: 6px;
                font-size: 14px;
            }
            #CloseBtn:hover {
                background-color: #FEE2E2;
                color: #EF4444;
            }
            #Label {
                font-size: 14px;
                font-weight: 600;
                color: #1F2937;
            }
            #Input {
                background-color: #F0F4F8;
                border: 1px solid #E6EEF6;
                border-radius: 8px;
                padding: 0 12px;
                font-size: 14px;
                color: #1F2937;
            }
            #Input:focus {
                background-color: #FFFFFF;
                border: 1.5px solid #3B82F6;
            }
            #CancelBtn {
                background-color: #F0F4F8;
                color: #1F2937;
                border: none;
                border-radius: 8px;
                font-size: 13px;
                font-weight: 500;
            }
            #CancelBtn:hover {
                background-color: #E2E8F0;
            }
            #OkBtn {
                background-color: #3B82F6;
                color: #FFFFFF;
                border: none;
                border-radius: 8px;
                font-size: 13px;
                font-weight: 600;
            }
            #OkBtn:hover {
                background-color: #2563EB;
            }
        """)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(25)
        shadow.setOffset(0, 6)
        shadow.setColor(QColor(0, 0, 0, 40))
        self.content.setGraphicsEffect(shadow)

        self.input.setFocus()
        self.input.returnPressed.connect(self._on_ok)

    def _on_ok(self):
        self._result_text = self.input.text().strip()
        if self._result_text:
            self.accept()
        else:
            self.input.setStyleSheet(
                "background-color: #FEF2F2; border: 1.5px solid #EF4444; border-radius: 8px; padding: 0 12px;")
            from PySide6.QtCore import QTimer
            QTimer.singleShot(500, self._reset_style)

    def _reset_style(self):
        self.input.setStyleSheet(
            "#Input { background-color: #F0F4F8; border: 1px solid #E6EEF6; border-radius: 8px; padding: 0 12px; font-size: 14px; color: #1F2937; } #Input:focus { background-color: #FFFFFF; border: 1.5px solid #3B82F6; }")

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and event.pos().y() <= 60:
            self._dragging = True
            self._drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self._dragging:
            self.move(event.globalPosition().toPoint() - self._drag_position)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._dragging = False
        event.accept()

    def get_text(self) -> str:
        return self._result_text

    @staticmethod
    def getText(parent, title: str, label: str, text: str = "") -> tuple:
        dialog = StyledInputDialog(title, label, parent, text)
        result = dialog.exec()
        if result == QDialog.Accepted:
            return dialog.get_text(), True
        return "", False