# utils/resource_paths.py
import sys
import logging
from pathlib import Path

# Настройка логирования
logger = logging.getLogger(__name__)


def get_resource_path(relative_path: str) -> Path:
    """
    Возвращает абсолютный путь к ресурсу.
    Работает и в EXE, и в скрипте.
    """
    try:
        if getattr(sys, 'frozen', False):
            # Запущено как EXE - ресурсы в папке _internal
            if hasattr(sys, '_MEIPASS'):
                base_path = Path(sys._MEIPASS)
            else:
                # Fallback: используем папку с EXE
                base_path = Path(sys.executable).parent
                logger.warning(f"sys._MEIPASS недоступен, используем {base_path}")
        else:
            # Запущено как скрипт - ресурсы в папке проекта
            base_path = Path(__file__).parent.parent

        result = base_path / relative_path
        logger.debug(f"get_resource_path('{relative_path}') -> {result}")
        return result
    except Exception as e:
        logger.error(f"Ошибка get_resource_path('{relative_path}'): {e}", exc_info=True)
        # Fallback: возвращаем относительный путь
        return Path(relative_path)


def get_db_path() -> Path:
    """
    Возвращает путь к базе данных.
    В EXE - рядом с EXE (для портативности).
    В скрипте - в папке проекта.
    """
    try:
        if getattr(sys, 'frozen', False):
            # Для EXE используем папку с EXE
            result = Path(sys.executable).parent / "hflow.db"
        else:
            result = Path(__file__).parent.parent / "hflow.db"

        logger.debug(f"get_db_path() -> {result}")
        return result
    except Exception as e:
        logger.error(f"Ошибка get_db_path(): {e}", exc_info=True)
        # Fallback
        return Path("hflow.db")