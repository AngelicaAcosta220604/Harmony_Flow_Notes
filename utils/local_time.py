from datetime import datetime


def now_local_iso() -> str:
    """Возвращает текущее локальное время в формате ISO (без T)"""
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def format_datetime(dt_str: str) -> str:
    """Форматирует datetime строку для отображения"""
    if not dt_str:
        return "—"
    try:
        # Убираем "T" если есть
        dt_str = dt_str.replace('T', ' ')
        # Парсим разные форматы
        if '.' in dt_str:
            dt = datetime.strptime(dt_str.split('.')[0], '%Y-%m-%d %H:%M:%S')
        else:
            dt = datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S')
        return dt.strftime("%d.%m.%Y %H:%M")
    except:
        # Если не получилось парсить, просто обрезаем
        return dt_str[:16] if len(dt_str) > 16 else dt_str


def parse_datetime(dt_str: str) -> datetime:
    """Парсит строку в datetime объект"""
    if not dt_str:
        return None
    try:
        dt_str = dt_str.replace('T', ' ')
        if '.' in dt_str:
            return datetime.strptime(dt_str.split('.')[0], '%Y-%m-%d %H:%M:%S')
        else:
            return datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S')
    except:
        return None