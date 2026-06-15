from datetime import datetime


def now_local_iso() -> str:
    """Возвращает текущее время в формате ISO"""
    return datetime.now().isoformat()


def format_datetime(dt_str: str) -> str:
    """Форматирует datetime строку для отображения"""
    if not dt_str:
        return "—"
    try:
        dt = datetime.fromisoformat(dt_str)
        return dt.strftime("%d.%m.%Y %H:%M")
    except:
        return dt_str[:16] if len(dt_str) > 16 else dt_str