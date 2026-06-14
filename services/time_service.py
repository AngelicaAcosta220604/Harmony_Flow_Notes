# services/time_service.py
from datetime import datetime, timedelta
from typing import Optional, Tuple


class TimeService:
    """Сервис для работы со временем"""

    @staticmethod
    def now() -> datetime:
        """Возвращает текущее время"""
        return datetime.now()

    @staticmethod
    def now_iso() -> str:
        """Возвращает текущее время в ISO формате"""
        return datetime.now().isoformat()

    @staticmethod
    def format_datetime(dt: datetime, format_str: str = "%d.%m.%Y %H:%M") -> str:
        """Форматирует дату и время"""
        return dt.strftime(format_str)

    @staticmethod
    def format_time(seconds: int) -> str:
        """Форматирует секунды в ЧЧ:ММ:СС."""
        if seconds is None:
            return "00:00"
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        return f"{minutes:02d}:{secs:02d}"

    @staticmethod
    def format_duration(minutes) -> str:
        if minutes is None:
            return "0м"
        try:
            minutes = int(minutes)
            hours = minutes // 60
            mins = minutes % 60
            return f"{hours}ч {mins}м" if hours > 0 else f"{mins}м"
        except:
            return "0м"

    @staticmethod
    def parse_iso(date_str: str) -> Optional[datetime]:
        """Парсит ISO строку в datetime"""
        try:
            return datetime.fromisoformat(date_str)
        except (ValueError, TypeError):
            return None

    @staticmethod
    def get_start_of_day(dt: datetime = None) -> datetime:
        """Возвращает начало дня"""
        if dt is None:
            dt = datetime.now()
        return dt.replace(hour=0, minute=0, second=0, microsecond=0)

    @staticmethod
    def get_end_of_day(dt: datetime = None) -> datetime:
        """Возвращает конец дня"""
        if dt is None:
            dt = datetime.now()
        return dt.replace(hour=23, minute=59, second=59, microsecond=999999)

    @staticmethod
    def get_week_range() -> Tuple[datetime, datetime]:
        """Возвращает начало и конец текущей недели (пн-вс)"""
        today = datetime.now().date()
        start = today - timedelta(days=today.weekday())
        end = start + timedelta(days=6)
        return (
            datetime.combine(start, datetime.min.time()),
            datetime.combine(end, datetime.max.time())
        )

    @staticmethod
    def get_month_range() -> Tuple[datetime, datetime]:
        """Возвращает начало и конец текущего месяца"""
        today = datetime.now().date()
        start = today.replace(day=1)
        if today.month == 12:
            end = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            end = today.replace(month=today.month + 1, day=1) - timedelta(days=1)
        return (
            datetime.combine(start, datetime.min.time()),
            datetime.combine(end, datetime.max.time())
        )

    @staticmethod
    def minutes_between(start: datetime, end: datetime) -> int:
        """Возвращает количество минут между двумя датами"""
        delta = end - start
        return int(delta.total_seconds() / 60)

    @staticmethod
    def is_overdue(deadline: str) -> bool:
        """Проверяет, просрочена ли дата"""
        dt = TimeService.parse_iso(deadline)
        if dt is None:
            return False
        return datetime.now() > dt

    @staticmethod
    def days_until(deadline: str) -> int:
        """Возвращает количество дней до дедлайна"""
        dt = TimeService.parse_iso(deadline)
        if dt is None:
            return 0
        delta = dt - datetime.now()
        return delta.days

    @staticmethod
    def format_datetime_from_iso(date_str: str, format_str: str = "%d.%m.%Y %H:%M") -> str:
        """Форматирует ISO строку в читаемую дату"""
        if not date_str:
            return "—"
        try:
            dt = datetime.fromisoformat(date_str)
            return dt.strftime(format_str)
        except (ValueError, TypeError):
            return date_str[:16] if date_str else "—"