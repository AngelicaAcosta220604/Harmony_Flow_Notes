# models/session.py
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List


@dataclass
class Session:
    """Модель фокус-сессии"""
    id: int
    topic_id: int
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    duration_minutes: Optional[int] = None
    status: str = 'active'  # 'active', 'paused', 'completed', 'auto_completed'
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    # Связанные данные (не из БД, для удобства)
    state_logs: List['SessionStateLog'] = field(default_factory=list, repr=False)
    quick_notes: List['QuickNote'] = field(default_factory=list, repr=False)

    @classmethod
    def from_row(cls, row: dict) -> 'Session':
        """Создаёт объект из строки БД"""
        return cls(
            id=row['id'],
            topic_id=row['topic_id'],
            start_time=row.get('start_time'),
            end_time=row.get('end_time'),
            duration_minutes=row.get('duration_minutes'),
            status=row.get('status', 'active'),
            created_at=row.get('created_at', datetime.now().isoformat())
        )

    def to_dict(self) -> dict:
        """Преобразует в словарь для БД"""
        return {
            'id': self.id,
            'topic_id': self.topic_id,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'duration_minutes': self.duration_minutes,
            'status': self.status,
            'created_at': self.created_at
        }

    def start(self):
        """Начинает сессию"""
        self.start_time = datetime.now().isoformat()
        self.status = 'active'

    def pause(self):
        """Ставит сессию на паузу"""
        self.status = 'paused'

    def resume(self):
        """Возобновляет сессию"""
        self.status = 'active'

    def complete(self, auto: bool = False):
        """Завершает сессию"""
        if self.start_time:
            start = datetime.fromisoformat(self.start_time)
            end = datetime.now()
            self.duration_minutes = int((end - start).total_seconds() / 60)
            self.end_time = end.isoformat()
        self.status = 'auto_completed' if auto else 'completed'

    @property
    def is_active(self) -> bool:
        """Активна ли сессия"""
        return self.status == 'active'

    @property
    def is_completed(self) -> bool:
        """Завершена ли сессия"""
        return self.status in ('completed', 'auto_completed')

    @property
    def duration_display(self) -> str:
        """Возвращает отформатированную длительность"""
        if not self.duration_minutes:
            return "—"
        hours = self.duration_minutes // 60
        minutes = self.duration_minutes % 60
        if hours > 0:
            return f"{hours}ч {minutes}м"
        return f"{minutes}м"