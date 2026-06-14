# modules/flashcards/dialogs.py
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QTextEdit, QPushButton, QComboBox, QDialogButtonBox, QWidget
)
from PySide6.QtCore import Qt, Signal


class CardTypeDialog(QDialog):
    """
    Диалог выбора типа карточки и создания.
    """

    def __init__(self, parent=None, selected_text: str = ""):
        super().__init__(parent)
        self.selected_text = selected_text
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        """Настраивает интерфейс"""
        self.setWindowTitle("Создание карточки")
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)

        layout = QVBoxLayout(self)

        # Выбор типа
        type_layout = QHBoxLayout()
        type_label = QLabel("Тип карточки:")
        self.type_combo = QComboBox()
        self.type_combo.addItem("📝 Свободная карточка", "free")
        self.type_combo.addItem("❓ Вопрос-Ответ", "qa")
        type_layout.addWidget(type_label)
        type_layout.addWidget(self.type_combo)
        type_layout.addStretch()
        layout.addLayout(type_layout)

        # Контейнер для полей (будет меняться)
        self.fields_widget = QWidget()
        self.fields_layout = QVBoxLayout(self.fields_widget)
        layout.addWidget(self.fields_widget)

        # Кнопки
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

        # Изначально показываем свободную карточку
        self._update_fields()

        # Подключаем сигнал изменения типа
        self.type_combo.currentIndexChanged.connect(self._update_fields)

    def _update_fields(self):
        """Обновляет поля в зависимости от выбранного типа"""
        # Очищаем
        while self.fields_layout.count():
            child = self.fields_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        card_type = self.type_combo.currentData()

        if card_type == "free":
            # Свободная карточка
            content_label = QLabel("Содержимое:")
            self.content_edit = QTextEdit()
            if self.selected_text:
                self.content_edit.setPlainText(self.selected_text)
            self.content_edit.setPlaceholderText("Введите текст карточки...")

            self.fields_layout.addWidget(content_label)
            self.fields_layout.addWidget(self.content_edit)

        else:  # qa
            # Карточка вопрос-ответ
            question_label = QLabel("Вопрос:")
            self.question_edit = QTextEdit()
            self.question_edit.setPlaceholderText("Введите вопрос...")

            answer_label = QLabel("Ответ:")
            self.answer_edit = QTextEdit()
            self.answer_edit.setPlaceholderText("Введите ответ...")

            # Если есть выделенный текст, помещаем его в вопрос
            if self.selected_text:
                self.question_edit.setPlainText(self.selected_text)

            self.fields_layout.addWidget(question_label)
            self.fields_layout.addWidget(self.question_edit)
            self.fields_layout.addWidget(answer_label)
            self.fields_layout.addWidget(self.answer_edit)

    def get_card_data(self) -> dict:
        """Возвращает данные карточки"""
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
    """
    Быстрый диалог для создания карточки из выделенного текста.
    """

    def __init__(self, parent=None, selected_text: str = ""):
        super().__init__(parent)
        self.selected_text = selected_text
        self._setup_ui()

    def _setup_ui(self):
        """Настраивает интерфейс"""
        self.setWindowTitle("Создать карточку")
        self.setMinimumWidth(400)

        layout = QVBoxLayout(self)

        # Отображаем выделенный текст
        label = QLabel("Выделенный текст:")
        layout.addWidget(label)

        self.text_display = QTextEdit()
        self.text_display.setPlainText(self.selected_text)
        self.text_display.setReadOnly(True)
        self.text_display.setMaximumHeight(100)
        layout.addWidget(self.text_display)

        # Выбор действия
        action_label = QLabel("Что сделать?")
        layout.addWidget(action_label)

        self.free_btn = QPushButton("📝 Создать свободную карточку")
        self.qa_btn = QPushButton("❓ Создать карточку вопрос-ответ")

        layout.addWidget(self.free_btn)
        layout.addWidget(self.qa_btn)

        # Кнопка отмены
        cancel_btn = QPushButton("Отмена")
        cancel_btn.clicked.connect(self.reject)
        layout.addWidget(cancel_btn)

        self.free_btn.clicked.connect(lambda: self.done(1))
        self.qa_btn.clicked.connect(lambda: self.done(2))

    def get_choice(self) -> str:
        """Возвращает выбор пользователя"""
        result = self.exec()
        if result == 1:
            return 'free'
        elif result == 2:
            return 'qa'
        return 'cancel'