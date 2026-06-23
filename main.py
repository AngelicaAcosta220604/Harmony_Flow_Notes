# main.py
import sys
import os
import logging
from pathlib import Path


# ✅ Настройка логирования ДО всех импортов
# В EXE логи будут записываться в файл рядом с EXE
def setup_logging():
    """Настраивает логирование"""
    try:
        # Определяем путь для лог-файла
        if getattr(sys, 'frozen', False):
            # В EXE — логи рядом с EXE
            log_dir = Path(sys.executable).parent / "logs"
        else:
            # В скрипте — логи в папке проекта
            log_dir = Path(__file__).parent / "logs"

        log_dir.mkdir(exist_ok=True, parents=True)
        log_file = log_dir / "hflow.log"

        # Настраиваем логирование
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8', mode='a'),
                logging.StreamHandler(sys.stdout)  # Также выводим в консоль
            ]
        )

        logger = logging.getLogger(__name__)
        logger.info(f"Логирование инициализировано. Файл: {log_file}")
        return logger
    except Exception as e:
        # Если не удалось настроить логирование — используем базовое
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s [%(levelname)s] %(message)s',
            handlers=[logging.StreamHandler(sys.stdout)]
        )
        logger = logging.getLogger(__name__)
        logger.error(f"Не удалось настроить файловое логирование: {e}")
        return logger


# ✅ Инициализируем логирование сразу
logger = setup_logging()

# ✅ Безопасное определение project_root
try:
    if getattr(sys, 'frozen', False):
        # В EXE используем папку с исполняемым файлом
        project_root = os.path.dirname(sys.executable)
    else:
        # В скрипте используем папку с main.py
        project_root = os.path.dirname(os.path.abspath(__file__))

    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    logger.debug(f"Project root: {project_root}")
except Exception as e:
    logger.error(f"Ошибка определения project_root: {e}", exc_info=True)

# Теперь импорты должны работать
try:
    from PySide6.QtWidgets import QApplication
    from core.app import HFlowApp
    from core.main_window import MainWindow

    logger.debug("Все импорты успешно загружены")
except Exception as e:
    logger.critical(f"Критическая ошибка при импорте модулей: {e}", exc_info=True)
    raise


def main():
    """Главная функция приложения"""
    try:
        logger.info("=" * 60)
        logger.info("Запуск приложения HFlow")
        logger.info("=" * 60)

        # Создаем приложение
        logger.debug("Создание HFlowApp...")
        app = HFlowApp(sys.argv)
        logger.info("HFlowApp создан")

        # Создаем главное окно
        logger.debug("Создание MainWindow...")
        window = MainWindow()
        logger.info("MainWindow создано")

        # Показываем окно
        window.show()
        logger.info("Окно показано, запуск event loop")

        # Запускаем event loop
        exit_code = app.exec()

        logger.info(f"Приложение завершено с кодом {exit_code}")
        sys.exit(exit_code)

    except KeyboardInterrupt:
        logger.info("Приложение прервано пользователем (Ctrl+C)")
        sys.exit(0)
    except Exception as e:
        logger.critical(f"Критическая ошибка приложения: {e}", exc_info=True)

        # Пытаемся показать диалог с ошибкой
        try:
            from PySide6.QtWidgets import QMessageBox, QApplication
            app = QApplication.instance() or QApplication(sys.argv)
            QMessageBox.critical(
                None,
                "Критическая ошибка",
                f"Произошла критическая ошибка:\n\n{e}\n\n"
                f"Подробности в логе:\n{log_file if 'log_file' in locals() else 'неизвестно'}"
            )
        except Exception:
            pass

        sys.exit(1)


if __name__ == "__main__":
    main()