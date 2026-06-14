# widgets/silent_dialog.py
from PySide6.QtWidgets import QMessageBox, QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QLineEdit
from PySide6.QtCore import Qt


class SilentMessageBox(QDialog):
    """Модальное окно без звука, совместимое с QMessageBox API"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setModal(True)
        self.setMinimumWidth(400)
        self.setMinimumHeight(180)

        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(25, 20, 25, 20)

        self.icon_label = QLabel()
        self.icon_label.setAlignment(Qt.AlignCenter)
        self.icon_label.setStyleSheet("font-size: 32px;")
        layout.addWidget(self.icon_label)

        self.text_label = QLabel()
        self.text_label.setWordWrap(True)
        self.text_label.setAlignment(Qt.AlignCenter)
        self.text_label.setStyleSheet("font-size: 13px;")
        layout.addWidget(self.text_label)

        self.button_layout = QHBoxLayout()
        self.button_layout.addStretch()
        layout.addLayout(self.button_layout)

        self.setStyleSheet("""
            QDialog {
                background-color: white;
                border: 1px solid #CCC;
                border-radius: 10px;
            }
            QPushButton {
                padding: 6px 16px;
                border: 1px solid #CCC;
                border-radius: 5px;
                background-color: #F0F0F0;
                min-width: 80px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #E0E0E0;
            }
        """)

    @staticmethod
    def information(parent, title, text):
        dialog = SilentMessageBox(parent)
        dialog.setWindowTitle(title)
        dialog.icon_label.setText("ℹ️")
        dialog.text_label.setText(text)

        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(dialog.accept)
        dialog.button_layout.addWidget(ok_btn)
        dialog.button_layout.addStretch()

        return dialog.exec()

    @staticmethod
    def warning(parent, title, text):
        dialog = SilentMessageBox(parent)
        dialog.setWindowTitle(title)
        dialog.icon_label.setText("⚠️")
        dialog.text_label.setText(text)

        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(dialog.accept)
        dialog.button_layout.addWidget(ok_btn)
        dialog.button_layout.addStretch()

        return dialog.exec()

    @staticmethod
    def question(parent, title, text, buttons=QMessageBox.Yes | QMessageBox.No, defaultButton=QMessageBox.No):
        """Бесшумный аналог QMessageBox.question. Возвращает QMessageBox.Yes или QMessageBox.No."""
        dialog = SilentMessageBox(parent)
        dialog.setWindowTitle(title)
        dialog.icon_label.setText("❓")
        dialog.text_label.setText(text)

        result = QMessageBox.No

        def set_yes():
            nonlocal result
            result = QMessageBox.Yes
            dialog.accept()

        def set_no():
            nonlocal result
            result = QMessageBox.No
            dialog.accept()

        yes_btn = QPushButton("Да")
        no_btn = QPushButton("Нет")

        yes_btn.clicked.connect(set_yes)
        no_btn.clicked.connect(set_no)

        dialog.button_layout.addWidget(yes_btn)
        dialog.button_layout.addWidget(no_btn)
        dialog.button_layout.addStretch()

        dialog.exec()
        return result

    # Добавляем Yes/No как константы для совместимости
    Yes = QMessageBox.Yes
    No = QMessageBox.No


class SilentDialog(QDialog):
    """Базовый бесшумный диалог"""
    def __init__(self, parent=None, f=Qt.WindowFlags()):
        super().__init__(parent, f)
        self.setModal(True)
        self.setStyleSheet("""
            QDialog {
                background-color: white;
                border: 1px solid #CCC;
                border-radius: 10px;
            }
        """)


class SilentInputDialog(SilentDialog):
    """Бесшумный аналог QInputDialog"""

    @staticmethod
    def getText(parent, title, label, text=""):
        dialog = SilentDialog(parent)
        dialog.setWindowTitle(title)
        dialog.setMinimumWidth(400)

        layout = QVBoxLayout(dialog)
        layout.addWidget(QLabel(label))

        line_edit = QLineEdit(text)
        layout.addWidget(line_edit)

        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("OK")
        cancel_btn = QPushButton("Отмена")

        ok_btn.clicked.connect(dialog.accept)
        cancel_btn.clicked.connect(dialog.reject)

        btn_layout.addStretch()
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

        if dialog.exec() == QDialog.Accepted:
            return line_edit.text(), True
        return "", False


__all__ = [
    'SilentMessageBox',
    'SilentDialog',
    'SilentInputDialog',
]