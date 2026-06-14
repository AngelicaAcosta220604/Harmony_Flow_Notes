# onboarding/wizard.py
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QStackedWidget,
    QPushButton, QWidget, QLabel, QProgressBar
)
from widgets import SilentMessageBox
from PySide6.QtCore import Qt, QTimer

from .steps import WelcomeStep, NameStep, TopicStep, NoteStep


class OnboardingWizard(QDialog):
    """
    Мастер первого запуска приложения.
    Проводит пользователя через:
    1. Приветствие
    2. Ввод имени
    3. Создание первой темы
    4. Создание первой заметки (опционально)
    """

    def __init__(self, topic_controller, note_controller, settings_controller, parent=None):
        super().__init__(parent)
        self._topic_controller = topic_controller
        self._note_controller = note_controller
        self._settings_controller = settings_controller

        self._current_step = 0
        self._user_name = None
        self._topic_id = None
        self._note_id = None

        self._setup_ui()
        self._setup_steps()
        self._update_step()

    def _setup_ui(self):
        """Настраивает интерфейс мастера"""
        self.setWindowTitle("Добро пожаловать в HFlow")
        self.setMinimumSize(550, 500)
        self.setModal(True)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)

        layout = QVBoxLayout(self)
        layout.setSpacing(0)

        # Заголовок с прогрессом
        header = QWidget()
        header.setFixedHeight(5)
        header.setStyleSheet("background-color: #1976d2;")
        layout.addWidget(header)

        # Контент
        self.stack = QStackedWidget()
        layout.addWidget(self.stack, 1)

        # Нижняя панель
        footer = QWidget()
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(20, 10, 20, 10)

        self.back_btn = QPushButton("◀ Назад")
        self.back_btn.setVisible(False)
        self.back_btn.clicked.connect(self._go_back)
        footer_layout.addWidget(self.back_btn)

        footer_layout.addStretch()

        self.close_btn = QPushButton("✖")
        self.close_btn.setFlat(True)
        self.close_btn.setFixedSize(30, 30)
        self.close_btn.setStyleSheet("color: #888888;")
        self.close_btn.clicked.connect(self.reject)
        footer_layout.addWidget(self.close_btn)

        layout.addWidget(footer)

    def _setup_steps(self):
        """Создаёт и добавляет все шаги"""
        # Шаг 1: Приветствие
        self.welcome_step = WelcomeStep()
        self.welcome_step.next_requested.connect(self._next_step)
        self.stack.addWidget(self.welcome_step)

        # Шаг 2: Имя пользователя
        self.name_step = NameStep()
        self.name_step.next_requested.connect(self._on_name_entered)
        self.stack.addWidget(self.name_step)

        # Шаг 3: Создание темы
        self.topic_step = TopicStep(self._topic_controller)
        self.topic_step.next_requested.connect(self._on_topic_created)
        self.topic_step.skip_requested.connect(self._on_topic_skipped)
        self.stack.addWidget(self.topic_step)

        # Шаг 4: Создание заметки
        self.note_step = NoteStep(self._note_controller, self._topic_controller)
        self.note_step.next_requested.connect(self._on_note_created)
        self.stack.addWidget(self.note_step)

    def _next_step(self):
        """Переход к следующему шагу"""
        if self._current_step < self.stack.count() - 1:
            self._current_step += 1
            self._update_step()

    def _go_back(self):
        """Возврат к предыдущему шагу"""
        if self._current_step > 0:
            self._current_step -= 1
            self._update_step()

    def _update_step(self):
        """Обновляет отображение текущего шага"""
        self.stack.setCurrentIndex(self._current_step)

        # Показываем кнопку "Назад" только после первого шага
        self.back_btn.setVisible(self._current_step > 0)

        # Устанавливаем фокус для шага с именем
        if self._current_step == 1:
            self.name_step.set_focus()

        # Сбрасываем состояние шага с темой при возврате
        if self._current_step == 2:
            self.topic_step.reset()

        # Устанавливаем тему для шага с заметкой
        if self._current_step == 3 and self._topic_id:
            self.note_step.set_topic(self._topic_id)
            self.note_step.reset()

    def _on_name_entered(self, user_name: str):
        """Обработчик ввода имени"""
        self._user_name = user_name
        self._settings_controller.set_user_name(user_name)
        self._next_step()

    def _on_topic_created(self, topic_id: int):
        """Обработчик создания темы"""
        self._topic_id = topic_id
        self._next_step()

    def _on_topic_skipped(self):
        """Обработчик пропуска создания темы"""
        # Создаём тему по умолчанию
        self._topic_id = self._topic_controller.create_topic("Мои заметки")
        self._next_step()

    def _on_note_created(self, note_id: int):
        """Обработчик создания заметки или пропуска"""
        self._note_id = note_id if note_id != -1 else None
        self._complete_onboarding()

    def _complete_onboarding(self):
        """Завершает онбординг"""
        # Сохраняем настройку, что онбординг пройден
        self._settings_controller.set('onboarding_completed', 'true')

        # Показываем финальное сообщение


        message = f"✨ Добро пожаловать, {self._user_name}!\n\n"
        message += "HFlow готов к работе.\n"
        message += "Вы можете:\n"
        message += "• Создавать заметки и карточки\n"
        message += "• Ставить задачи и дедлайны\n"
        message += "• Проводить фокус-сессии\n"
        message += "• Отслеживать свою продуктивность"

        SilentMessageBox.information(self, "Готово!", message)

        self.accept()