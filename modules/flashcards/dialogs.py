# modules/flashcards/dialogs.py
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QTextEdit, QPushButton, QComboBox, QDialogButtonBox, QWidget
)
from PySide6.QtCore import Qt, Signal


class CardTypeDialog(QDialog):
    """Диалог выбора типа карточки и создания"""

    card_saved = Signal(dict)  # сигнал при сохранении

    def __init__(self, parent=None, selected_text: str = ""):
        super().__init__(parent)
        self.setModal(False)
        self.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.selected_text = selected_text
        self._setup_ui()
        self._validate()

    def _setup_ui(self):
        self.setWindowTitle("Создание карточки")
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)

        layout = QVBoxLayout(self)

        type_layout = QHBoxLayout()
        type_label = QLabel("Тип карточки:")
        self.type_combo = QComboBox()
        self.type_combo.addItem("📝 Свободная карточка", "free")
        self.type_combo.addItem("❓ Вопрос-Ответ", "qa")
        self.type_combo.currentIndexChanged.connect(self._update_fields)
        type_layout.addWidget(type_label)
        type_layout.addWidget(self.type_combo)
        type_layout.addStretch()
        layout.addLayout(type_layout)

        self.fields_widget = QWidget()
        self.fields_layout = QVBoxLayout(self.fields_widget)
        layout.addWidget(self.fields_widget)

        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.save_btn = QPushButton("✅ Сохранить")
        self.save_btn.setEnabled(False)
        button_layout.addWidget(self.save_btn)

        self.cancel_btn = QPushButton("❌ Отмена")
        button_layout.addWidget(self.cancel_btn)

        layout.addLayout(button_layout)

        self._update_fields()
        self.save_btn.clicked.connect(self._on_save)
        self.cancel_btn.clicked.connect(self.reject)

    def _update_fields(self):
        # Очищаем
        while self.fields_layout.count():
            child = self.fields_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        card_type = self.type_combo.currentData()

        if card_type == "free":
            content_label = QLabel("Содержимое *")
            content_label.setStyleSheet("color: #ff9800;")
            self.content_edit = QTextEdit()
            if self.selected_text:
                self.content_edit.setPlainText(self.selected_text)
            self.content_edit.setPlaceholderText("Введите текст карточки...")
            self.content_edit.textChanged.connect(self._validate)
            self.fields_layout.addWidget(content_label)
            self.fields_layout.addWidget(self.content_edit)
        else:
            question_label = QLabel("Вопрос *")
            question_label.setStyleSheet("color: #ff9800;")
            self.question_edit = QTextEdit()
            self.question_edit.setPlaceholderText("Введите вопрос...")
            if self.selected_text:
                self.question_edit.setPlainText(self.selected_text)
            self.question_edit.textChanged.connect(self._validate)

            answer_label = QLabel("Ответ *")
            answer_label.setStyleSheet("color: #ff9800;")
            self.answer_edit = QTextEdit()
            self.answer_edit.setPlaceholderText("Введите ответ...")
            self.answer_edit.textChanged.connect(self._validate)

            self.fields_layout.addWidget(question_label)
            self.fields_layout.addWidget(self.question_edit)
            self.fields_layout.addWidget(answer_label)
            self.fields_layout.addWidget(self.answer_edit)

    def _validate(self):
        """Проверяет, можно ли сохранить карточку"""
        card_type = self.type_combo.currentData()

        if card_type == "free":
            has_content = bool(self.content_edit.toPlainText().strip())
            self.save_btn.setEnabled(has_content)
        else:
            has_question = bool(self.question_edit.toPlainText().strip())
            has_answer = bool(self.answer_edit.toPlainText().strip())
            self.save_btn.setEnabled(has_question and has_answer)

    def _on_save(self):
        card_type = self.type_combo.currentData()

        if card_type == "free":
            content = self.content_edit.toPlainText().strip()
            if not content:
                return
            self.card_saved.emit({'type': 'free', 'content': content})
        else:
            question = self.question_edit.toPlainText().strip()
            answer = self.answer_edit.toPlainText().strip()
            if not question or not answer:
                return
            self.card_saved.emit({'type': 'question_answer', 'question': question, 'answer': answer})

        self.accept()

    def get_card_data(self) -> dict:
        """Для совместимости со старым кодом"""
        card_type = self.type_combo.currentData()
        if card_type == "free":
            return {
                'type': 'free',
                'content': self.content_edit.toPlainText()
            }
        else:
            return {
                'type': 'question_answer',
                'question': self.question_edit.toPlainText(),
                'answer': self.answer_edit.toPlainText()
            }


class QuickCardDialog(QDialog):
    """Быстрый диалог для создания карточки из выделенного текста."""

    def __init__(self, parent=None, selected_text: str = ""):
        super().__init__(parent)
        self.setModal(False)
        self.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.selected_text = selected_text
        self._setup_ui()

    def _setup_ui(self):
        self.setWindowTitle("Создать карточку")
        self.setMinimumWidth(400)

        layout = QVBoxLayout(self)

        label = QLabel("Выделенный текст:")
        layout.addWidget(label)

        self.text_display = QTextEdit()
        self.text_display.setPlainText(self.selected_text)
        self.text_display.setReadOnly(True)
        self.text_display.setMaximumHeight(100)
        layout.addWidget(self.text_display)

        action_label = QLabel("Что сделать?")
        layout.addWidget(action_label)

        self.free_btn = QPushButton("📝 Создать свободную карточку")
        self.qa_btn = QPushButton("❓ Создать карточку вопрос-ответ")
        cancel_btn = QPushButton("Отмена")

        layout.addWidget(self.free_btn)
        layout.addWidget(self.qa_btn)
        layout.addWidget(cancel_btn)

        self.free_btn.clicked.connect(lambda: self.done(1))
        self.qa_btn.clicked.connect(lambda: self.done(2))
        cancel_btn.clicked.connect(self.reject)

    def get_choice(self) -> str:
        result = self.exec()
        if result == 1:
            return 'free'
        elif result == 2:
            return 'qa'
        return 'cancel'