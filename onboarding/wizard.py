# onboarding/wizard.py
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QStackedWidget,
    QPushButton, QWidget, QLabel, QProgressBar
)
from widgets import SilentMessageBox
from PySide6.QtCore import Qt, QTimer
import logging

from .steps import WelcomeStep, NameStep, TopicStep, NoteStep

# Настройка логирования
logger = logging.getLogger(__name__)


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
        logger.info("Онбординг мастер инициализирован")

    def _setup_ui(self):
        """Настраивает интерфейс мастера"""
        try:
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
        except Exception as e:
            logger.error(f"Ошибка настройки UI онбординга: {e}", exc_info=True)

    def _setup_steps(self):
        """Создаёт и добавляет все шаги"""
        try:
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

            logger.debug(f"Создано {self.stack.count()} шагов онбординга")
        except Exception as e:
            logger.error(f"Ошибка создания шагов онбординга: {e}", exc_info=True)

    def _next_step(self):
        """Переход к следующему шагу"""
        try:
            if self._current_step < self.stack.count() - 1:
                self._current_step += 1
                self._update_step()
                logger.debug(f"Переход к шагу {self._current_step}")
        except Exception as e:
            logger.error(f"Ошибка перехода к следующему шагу: {e}", exc_info=True)

    def _go_back(self):
        """Возврат к предыдущему шагу"""
        try:
            if self._current_step > 0:
                self._current_step -= 1
                self._update_step()
                logger.debug(f"Возврат к шагу {self._current_step}")
        except Exception as e:
            logger.error(f"Ошибка возврата к предыдущему шагу: {e}", exc_info=True)

    def _update_step(self):
        """Обновляет отображение текущего шага"""
        try:
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
        except Exception as e:
            logger.error(f"Ошибка обновления шага: {e}", exc_info=True)

    def _on_name_entered(self, user_name: str):
        """Обработчик ввода имени"""
        try:
            self._user_name = user_name
            self._settings_controller.set_user_name(user_name)
            self._next_step()
            logger.info(f"Пользователь ввел имя: {user_name}")
        except Exception as e:
            logger.error(f"Ошибка сохранения имени пользователя: {e}", exc_info=True)
            SilentMessageBox.warning(self, "Ошибка", f"Не удалось сохранить имя: {e}")

    def _on_topic_created(self, topic_id: int):
        """Обработчик создания темы"""
        try:
            self._topic_id = topic_id
            self._next_step()
            logger.info(f"Создана тема в онбординге: {topic_id}")
        except Exception as e:
            logger.error(f"Ошибка обработки создания темы: {e}", exc_info=True)

    def _on_topic_skipped(self):
        """Обработчик пропуска создания темы"""
        try:
            # Создаём тему по умолчанию
            self._topic_id = self._topic_controller.create_topic("Мои заметки")
            if self._topic_id:
                self._next_step()
                logger.info(f"Создана тема по умолчанию: {self._topic_id}")
            else:
                logger.warning("Не удалось создать тему по умолчанию")
                SilentMessageBox.warning(self, "Ошибка", "Не удалось создать тему по умолчанию")
        except Exception as e:
            logger.error(f"Ошибка создания темы по умолчанию: {e}", exc_info=True)
            SilentMessageBox.warning(self, "Ошибка", f"Не удалось создать тему: {e}")

    def _on_note_created(self, note_id: int):
        """Обработчик создания заметки или пропуска"""
        try:
            self._note_id = note_id if note_id != -1 else None
            self._complete_onboarding()
            if self._note_id:
                logger.info(f"Создана заметка в онбординге: {self._note_id}")
            else:
                logger.info("Пользователь пропустил создание заметки")
        except Exception as e:
            logger.error(f"Ошибка обработки создания заметки: {e}", exc_info=True)

    def _complete_onboarding(self):
        """Завершает онбординг"""
        try:
            # 🆕 Сохраняем флаг, что онбординг пройден
            self._settings_controller.set_onboarding_completed(True)
            logger.info("Флаг онбординга установлен в True")

            # Сохраняем имя пользователя (если ввели)
            if self._user_name:
                self._settings_controller.set_user_name(self._user_name)

            # Показываем финальное сообщение
            message = f"✨ Добро пожаловать, {self._user_name}!\n\n"
            message += "HFlow готов к работе.\n"
            message += "Вы можете:\n"
            message += "• Создавать заметки и карточки\n"
            message += "• Ставить задачи и дедлайны\n"
            message += "• Проводить фокус-сессии\n"
            message += "• Отслеживать свою продуктивность"

            SilentMessageBox.information(self, "Готово!", message)

            logger.info(f"Онбординг завершен для пользователя: {self._user_name}")
            self.accept()
        except Exception as e:
            logger.error(f"Ошибка завершения онбординга: {e}", exc_info=True)
            SilentMessageBox.warning(self, "Ошибка", f"Не удалось завершить онбординг: {e}")
            # Все равно закрываем, чтобы пользователь не застрял
            self.accept()