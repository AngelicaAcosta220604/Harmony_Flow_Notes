# models/note.py
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Note:
    """Модель заметки"""
    id: int
    topic_id: int
    title: str
    content: str = ''
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    @classmethod
    def from_row(cls, row: dict) -> 'Note':
        """Создаёт объект из строки БД"""
        return cls(
            id=row['id'],
            topic_id=row['topic_id'],
            title=row['title'],
            content=row.get('content', ''),
            created_at=row.get('created_at', datetime.now().isoformat()),
            updated_at=row.get('updated_at', datetime.now().isoformat())
        )

    def to_dict(self) -> dict:
        """Преобразует в словарь для БД"""
        return {
            'id': self.id,
            'topic_id': self.topic_id,
            'title': self.title,
            'content': self.content,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }

    def update_content(self, new_content: str):
        """Обновляет содержимое и время изменения"""
        self.content = new_content
        self.updated_at = datetime.now().isoformat()

    def get_preview(self, length: int = 100) -> str:
        """Возвращает превью содержимого"""
        if len(self.content) <= length:
            return self.content
        return self.content[:length] + '...'

    @property
    def word_count(self) -> int:
        """Возвращает количество слов в заметке"""
        return len(self.content.split()) if self.content else 0