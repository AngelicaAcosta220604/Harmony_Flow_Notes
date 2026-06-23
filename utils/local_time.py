# utils/local_time.py
from datetime import datetime
import logging

# Настройка логирования
logger = logging.getLogger(__name__)


def now_local_iso() -> str:
    """Возвращает текущее локальное время в формате ISO (без T)"""
    try:
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    except Exception as e:
        logger.error(f"Ошибка получения текущего времени: {e}", exc_info=True)
        return ""


def format_datetime(dt_str: str) -> str:
    """Форматирует datetime строку для отображения"""
    try:
        if not dt_str:
            return "—"

        # ✅ ИСПРАВЛЕНО: проверка типа
        if not isinstance(dt_str, str):
            logger.warning(f"format_datetime получил не-строку: {type(dt_str)}")
            return str(dt_str)

        # Убираем "T" если есть
        dt_str = dt_str.replace('T', ' ')

        # Парсим разные форматы
        if '.' in dt_str:
            dt = datetime.strptime(dt_str.split('.')[0], '%Y-%m-%d %H:%M:%S')
        else:
            dt = datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S')

        return dt.strftime("%d.%m.%Y %H:%M")
    except (ValueError, TypeError) as e:
        # ✅ ИСПРАВЛЕНО: логируем ошибку парсинга
        logger.debug(f"Не удалось отформатировать дату '{dt_str}': {e}")
        # Если не получилось парсить, просто обрезаем
        try:
            return dt_str[:16] if len(dt_str) > 16 else dt_str
        except Exception:
            return "—"
    except Exception as e:
        logger.error(f"Неожиданная ошибка форматирования даты '{dt_str}': {e}", exc_info=True)
        return "—"


def parse_datetime(dt_str: str) -> datetime:
    """Парсит строку в datetime объект"""
    try:
        if not dt_str:
            return None

        # ✅ ИСПРАВЛЕНО: проверка типа
        if not isinstance(dt_str, str):
            logger.warning(f"parse_datetime получил не-строку: {type(dt_str)}")
            return None

        dt_str = dt_str.replace('T', ' ')

        if '.' in dt_str:
            return datetime.strptime(dt_str.split('.')[0], '%Y-%m-%d %H:%M:%S')
        else:
            return datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S')
    except (ValueError, TypeError) as e:
        # ✅ ИСПРАВЛЕНО: логируем ошибку парсинга
        logger.debug(f"Не удалось распарсить дату '{dt_str}': {e}")
        return None
    except Exception as e:
        logger.error(f"Неожиданная ошибка парсинга даты '{dt_str}': {e}", exc_info=True)
        return None