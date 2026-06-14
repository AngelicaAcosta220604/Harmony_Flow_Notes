# onboarding/steps.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTextEdit, QComboBox, QFrame
)
from widgets import SilentMessageBox
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont


class WelcomeStep(QWidget):
    """
    Шаг 1: Экран приветствия.
    """

    next_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        """Настраивает интерфейс"""
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(20)

        # Логотип
        logo_label = QLabel("🎵 HFLOW")
        logo_label.setStyleSheet("font-size: 32px; font-weight: bold; color: #1976d2;")
        logo_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(logo_label)

        # Заголовок
        title_label = QLabel("Добро пожаловать!")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; margin-top: 20px;")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        # Описание
        desc_label = QLabel(
            "HFlow помогает планировать задачи,\n"
            "вести заметки и понимать свою продуктивность.\n\n"
            "Все данные хранятся локально — ваш приватность под защитой."
        )
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setStyleSheet("color: #666666; font-size: 14px;")
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)

        layout.addStretch()

        # Кнопка "Начать работу"
        start_btn = QPushButton("🚀 Начать работу")
        start_btn.setFixedHeight(50)
        start_btn.setFixedWidth(250)
        start_btn.setStyleSheet("font-size: 16px; font-weight: bold; background-color: #4caf50;")
        start_btn.clicked.connect(self.next_requested.emit)

        btn_layout = QHBoxLayout()
        btn_layout.setAlignment(Qt.AlignCenter)
        btn_layout.addWidget(start_btn)
        layout.addLayout(btn_layout)

        layout.addSpacing(50)


class NameStep(QWidget):
    """
    Шаг 2: Запрос имени пользователя (обязательный шаг).
    """

    next_requested = Signal(str)  # user_name

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        """Настраивает интерфейс"""
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(20)

        # Иконка
        icon_label = QLabel("👋")
        icon_label.setStyleSheet("font-size: 48px;")
        icon_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon_label)

        # Заголовок
        title_label = QLabel("Как к вам обращаться?")
        title_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        # Поле ввода имени
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Введите ваше имя...")
        self.name_edit.setFixedWidth(300)
        self.name_edit.setFixedHeight(40)
        self.name_edit.setStyleSheet("font-size: 14px; padding: 5px;")

        name_layout = QHBoxLayout()
        name_layout.setAlignment(Qt.AlignCenter)
        name_layout.addWidget(self.name_edit)
        layout.addLayout(name_layout)

        # Пояснение
        hint_label = QLabel("(можно изменить позже в настройках)")
        hint_label.setStyleSheet("color: #888888; font-size: 11px;")
        hint_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(hint_label)

        layout.addStretch()

        # Кнопка "Продолжить"
        self.next_btn = QPushButton("➡️ Продолжить")
        self.next_btn.setFixedHeight(45)
        self.next_btn.setFixedWidth(200)
        self.next_btn.setStyleSheet("font-size: 14px; font-weight: bold;")

        btn_layout = QHBoxLayout()
        btn_layout.setAlignment(Qt.AlignCenter)
        btn_layout.addWidget(self.next_btn)
        layout.addLayout(btn_layout)

        layout.addSpacing(50)

    def _connect_signals(self):
        """Подключает сигналы"""
        self.next_btn.clicked.connect(self._on_next)
        self.name_edit.returnPressed.connect(self._on_next)

    def _on_next(self):
        """Обработчик нажатия кнопки Продолжить"""
        user_name = self.name_edit.text().strip()

        if not user_name:
            user_name = "Пользователь"

        self.next_requested.emit(user_name)

    def set_focus(self):
        """Устанавливает фокус на поле ввода"""
        self.name_edit.setFocus()


class TopicStep(QWidget):
    """
    Шаг 3: Создание первой темы.
    """

    next_requested = Signal(int)  # topic_id
    skip_requested = Signal()  # пропустить

    def __init__(self, topic_controller, parent=None):
        super().__init__(parent)
        self._topic_controller = topic_controller
        self._created_topic_id = None
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        """Настраивает интерфейс"""
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(20)

        # Иконка
        icon_label = QLabel("📚")
        icon_label.setStyleSheet("font-size: 48px;")
        icon_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon_label)

        # Заголовок
        title_label = QLabel("Создайте первую тему")
        title_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        # Быстрые варианты
        quick_label = QLabel("Быстрый выбор:")
        quick_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(quick_label)

        quick_buttons_layout = QHBoxLayout()
        quick_buttons_layout.setAlignment(Qt.AlignCenter)
        quick_buttons_layout.setSpacing(15)

        self.study_btn = QPushButton("📖 Учёба")
        self.work_btn = QPushButton("💼 Работа")
        self.personal_btn = QPushButton("❤️ Личное")

        for btn in [self.study_btn, self.work_btn, self.personal_btn]:
            btn.setFixedSize(120, 50)
            btn.setStyleSheet("font-size: 14px;")
            quick_buttons_layout.addWidget(btn)

        layout.addLayout(quick_buttons_layout)

        # Или введите своё
        custom_label = QLabel("Или введите своё название:")
        custom_label.setAlignment(Qt.AlignCenter)
        custom_label.setStyleSheet("margin-top: 15px;")
        layout.addWidget(custom_label)

        self.custom_edit = QLineEdit()
        self.custom_edit.setPlaceholderText("Название темы...")
        self.custom_edit.setFixedWidth(300)
        self.custom_edit.setFixedHeight(35)

        custom_layout = QHBoxLayout()
        custom_layout.setAlignment(Qt.AlignCenter)
        custom_layout.addWidget(self.custom_edit)
        layout.addLayout(custom_layout)

        self.create_custom_btn = QPushButton("✨ Создать")
        self.create_custom_btn.setFixedWidth(150)

        create_layout = QHBoxLayout()
        create_layout.setAlignment(Qt.AlignCenter)
        create_layout.addWidget(self.create_custom_btn)
        layout.addLayout(create_layout)

        layout.addStretch()

        # Кнопки навигации
        nav_layout = QHBoxLayout()
        nav_layout.setSpacing(20)

        self.skip_btn = QPushButton("Пропустить")
        self.skip_btn.setFlat(True)
        self.skip_btn.setStyleSheet("color: #888888;")

        nav_layout.addWidget(self.skip_btn)
        nav_layout.addStretch()

        self.next_btn = QPushButton("➡️ Продолжить")
        self.next_btn.setFixedWidth(150)
        self.next_btn.setEnabled(False)

        nav_layout.addWidget(self.next_btn)

        layout.addLayout(nav_layout)
        layout.addSpacing(30)

    def _connect_signals(self):
        """Подключает сигналы"""
        self.study_btn.clicked.connect(lambda: self._create_topic("Учёба"))
        self.work_btn.clicked.connect(lambda: self._create_topic("Работа"))
        self.personal_btn.clicked.connect(lambda: self._create_topic("Личное"))
        self.create_custom_btn.clicked.connect(self._create_custom_topic)
        self.next_btn.clicked.connect(self._on_next)
        self.skip_btn.clicked.connect(self.skip_requested.emit)
        self.custom_edit.returnPressed.connect(self._create_custom_topic)

    def _create_topic(self, name: str):
        """Создаёт тему с заданным именем"""
        topic_id = self._topic_controller.create_topic(name)
        if topic_id:
            self._created_topic_id = topic_id
            self.next_btn.setEnabled(True)
            self._show_success(name)

    def _create_custom_topic(self):
        """Создаёт тему из пользовательского ввода"""
        name = self.custom_edit.text().strip()
        if not name:
            SilentMessageBox.warning(self, "Ошибка", "Введите название темы")
            return

        self._create_topic(name)

    def _show_success(self, name: str):
        """Показывает сообщение об успехе"""
        self.status_label = QLabel(f"✅ Тема «{name}» создана!")
        self.status_label.setStyleSheet("color: #4caf50;")
        self.status_label.setAlignment(Qt.AlignCenter)

        # Добавляем в layout если ещё нет
        parent_layout = self.layout()
        if hasattr(self, 'status_label') and self.status_label.parent() != self:
            # Находим место перед кнопками
            parent_layout.insertWidget(parent_layout.count() - 1, self.status_label)

    def _on_next(self):
        """Переход к следующему шагу"""
        if self._created_topic_id:
            self.next_requested.emit(self._created_topic_id)

    def reset(self):
        """Сбрасывает состояние шага"""
        self._created_topic_id = None
        self.next_btn.setEnabled(False)
        self.custom_edit.clear()
        if hasattr(self, 'status_label'):
            self.status_label.deleteLater()


class NoteStep(QWidget):
    """
    Шаг 4: Создание первой заметки (опционально).
    """

    next_requested = Signal(int)  # note_id (или -1 если пропущено)

    def __init__(self, note_controller, topic_controller, parent=None):
        super().__init__(parent)
        self._note_controller = note_controller
        self._topic_controller = topic_controller
        self._current_topic_id = None
        self._created_note_id = None
        self._setup_ui()
        self._connect_signals()

    def set_topic(self, topic_id: int):
        """Устанавливает тему для заметки"""
        self._current_topic_id = topic_id
        topic = self._topic_controller.get_topic(topic_id)
        if topic:
            self.topic_label.setText(f"Тема: {topic.name}")

    def _setup_ui(self):
        """Настраивает интерфейс"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # Иконка
        icon_label = QLabel("📝")
        icon_label.setStyleSheet("font-size: 48px;")
        icon_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon_label)

        # Заголовок
        title_label = QLabel("Создайте первую заметку")
        title_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        # Тема
        self.topic_label = QLabel("Тема: —")
        self.topic_label.setAlignment(Qt.AlignCenter)
        self.topic_label.setStyleSheet("color: #1976d2;")
        layout.addWidget(self.topic_label)

        # Заголовок заметки
        header_label = QLabel("Заголовок:")
        layout.addWidget(header_label)

        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("Заголовок заметки...")
        layout.addWidget(self.title_edit)

        # Содержимое заметки
        content_label = QLabel("Текст:")
        layout.addWidget(content_label)

        self.content_edit = QTextEdit()
        self.content_edit.setPlaceholderText("Введите текст заметки...")
        self.content_edit.setMaximumHeight(150)
        layout.addWidget(self.content_edit)

        layout.addStretch()

        # Кнопки
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(15)

        self.skip_btn = QPushButton("Пропустить")
        self.skip_btn.setFlat(True)
        self.skip_btn.setStyleSheet("color: #888888;")
        btn_layout.addWidget(self.skip_btn)

        btn_layout.addStretch()

        self.save_btn = QPushButton("💾 Сохранить заметку")
        self.save_btn.setFixedWidth(180)
        btn_layout.addWidget(self.save_btn)

        layout.addLayout(btn_layout)

        layout.addSpacing(20)

    def _connect_signals(self):
        """Подключает сигналы"""
        self.save_btn.clicked.connect(self._on_save)
        self.skip_btn.clicked.connect(lambda: self.next_requested.emit(-1))

    def _on_save(self):
        """Сохраняет заметку"""
        title = self.title_edit.text().strip()
        if not title:
            title = "Моя первая заметка"

        content = self.content_edit.toPlainText()

        if self._current_topic_id:
            note_id = self._note_controller.create_note(
                self._current_topic_id, title, content
            )
            if note_id:
                self._created_note_id = note_id
                self.next_requested.emit(note_id)
            else:
                SilentMessageBox.warning(self, "Ошибка", "Не удалось создать заметку")
        else:
            SilentMessageBox.warning(self, "Ошибка", "Не выбрана тема для заметки")

    def reset(self):
        """Сбрасывает состояние шага"""
        self.title_edit.clear()
        self.content_edit.clear()
        self._created_note_id = None