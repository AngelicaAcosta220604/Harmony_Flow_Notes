# models/quick_note.py
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class QuickNote:
    """Модель быстрой записи"""
    id: int
    session_id: int
    topic_id: int
    content: str
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    @classmethod
    def from_row(cls, row: dict) -> 'QuickNote':
        """Создаёт объект из строки БД"""
        return cls(
            id=row['id'],
            session_id=row['session_id'],
            topic_id=row['topic_id'],
            content=row['content'],
            created_at=row.get('created_at', datetime.now().isoformat())
        )

    def to_dict(self) -> dict:
        """Преобразует в словарь для БД"""
        return {
            'id': self.id,
            'session_id': self.session_id,
            'topic_id': self.topic_id,
            'content': self.content,
            'created_at': self.created_at
        }

    @classmethod
    def create(cls, session_id: int, topic_id: int, content: str) -> 'QuickNote':
        """Фабричный метод для создания быстрой записи"""
        return cls(
            id=0,
            session_id=session_id,
            topic_id=topic_id,
            content=content
        )

    @property
    def preview(self, length: int = 50) -> str:
        """Возвращает превью содержимого"""
        if len(self.content) <= length:
            return self.content
        return self.content[:length] + '...'

    @property
    def time_display(self) -> str:
        """Возвращает отформатированное время создания"""
        dt = datetime.fromisoformat(self.created_at)
        return dt.strftime("%H:%M:%S")