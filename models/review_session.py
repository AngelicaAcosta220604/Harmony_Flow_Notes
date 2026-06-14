# models/review_session.py
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List


@dataclass
class ReviewSession:
    """Модель сессии повторения карточек"""
    id: int
    topic_id: int
    mode: str = 'sequential'  # 'sequential', 'random'
    total_cards: int = 0
    completed_cards: int = 0
    started_at: Optional[str] = None
    ended_at: Optional[str] = None

    @classmethod
    def from_row(cls, row: dict) -> 'ReviewSession':
        """Создаёт объект из строки БД"""
        return cls(
            id=row['id'],
            topic_id=row['topic_id'],
            mode=row.get('mode', 'sequential'),
            total_cards=row.get('total_cards', 0),
            completed_cards=row.get('completed_cards', 0),
            started_at=row.get('started_at'),
            ended_at=row.get('ended_at')
        )

    def to_dict(self) -> dict:
        """Преобразует в словарь для БД"""
        return {
            'id': self.id,
            'topic_id': self.topic_id,
            'mode': self.mode,
            'total_cards': self.total_cards,
            'completed_cards': self.completed_cards,
            'started_at': self.started_at,
            'ended_at': self.ended_at
        }

    def start(self, total_cards: int):
        """Начинает сессию повторения"""
        self.total_cards = total_cards
        self.completed_cards = 0
        self.started_at = datetime.now().isoformat()
        self.ended_at = None

    def complete(self):
        """Завершает сессию повторения"""
        self.ended_at = datetime.now().isoformat()

    def increment_completed(self):
        """Увеличивает счётчик завершённых карточек"""
        self.completed_cards += 1

    @property
    def is_active(self) -> bool:
        """Активна ли сессия"""
        return self.started_at is not None and self.ended_at is None

    @property
    def progress_percent(self) -> float:
        """Процент завершения"""
        if self.total_cards == 0:
            return 0
        return (self.completed_cards / self.total_cards) * 100