# models/topic.py
from typing import Optional, List
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Topic:
    """Модель темы/папки"""
    id: int
    name: str
    description: str = ''
    parent_id: Optional[int] = None
    type: str = 'topic'  # 'topic' or 'folder'
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    # Дочерние элементы (не из БД, для удобства)
    children: List['Topic'] = field(default_factory=list, repr=False)

    @classmethod
    def from_row(cls, row: dict) -> 'Topic':
        """Создаёт объект из строки БД"""
        return cls(
            id=row['id'],
            name=row['name'],
            description=row.get('description', ''),
            parent_id=row.get('parent_id'),
            type=row.get('type', 'topic'),
            created_at=row.get('created_at', datetime.now().isoformat())
        )

    def to_dict(self) -> dict:
        """Преобразует в словарь для БД"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'parent_id': self.parent_id,
            'type': self.type,
            'created_at': self.created_at
        }

    @property
    def is_folder(self) -> bool:
        """Является ли папкой"""
        return self.type == 'folder'

    @property
    def is_topic(self) -> bool:
        """Является ли темой"""
        return self.type == 'topic'

    @property
    def display_name(self) -> str:
        """Отображаемое имя с эмодзи"""
        if self.is_folder:
            return f"📁 {self.name}"
        return f"📚 {self.name}"