# models/session_state_log.py
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class SessionStateLog:
    """Модель лога состояния сессии"""
    id: int
    session_id: int
    metric: str  # 'concentration', 'energy', 'interest'
    value: int  # 1-5
    minute: int
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    @classmethod
    def from_row(cls, row: dict) -> 'SessionStateLog':
        """Создаёт объект из строки БД"""
        return cls(
            id=row['id'],
            session_id=row['session_id'],
            metric=row['metric'],
            value=row['value'],
            minute=row['minute'],
            created_at=row.get('created_at', datetime.now().isoformat())
        )

    def to_dict(self) -> dict:
        """Преобразует в словарь для БД"""
        return {
            'id': self.id,
            'session_id': self.session_id,
            'metric': self.metric,
            'value': self.value,
            'minute': self.minute,
            'created_at': self.created_at
        }

    @classmethod
    def create(cls, session_id: int, metric: str, value: int, minute: int) -> 'SessionStateLog':
        """Фабричный метод для создания лога"""
        return cls(
            id=0,
            session_id=session_id,
            metric=metric,
            value=value,
            minute=minute
        )

    @property
    def metric_name(self) -> str:
        """Русское название метрики"""
        names = {
            'concentration': 'Концентрация',
            'energy': 'Энергия',
            'interest': 'Интерес'
        }
        return names.get(self.metric, self.metric)

    @property
    def emoji(self) -> str:
        """Эмодзи для метрики"""
        emojis = {
            'concentration': '🧠',
            'energy': '⚡',
            'interest': '❤️'
        }
        return emojis.get(self.metric, '📊')