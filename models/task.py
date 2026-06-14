# models/task.py
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Task:
    """Модель задачи"""
    id: int
    title: str
    description: str = ''
    topic_id: Optional[int] = None
    deadline: Optional[str] = None
    status: str = 'active'  # 'active', 'completed', 'overdue'
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: Optional[str] = None

    @classmethod
    def from_row(cls, row: dict) -> 'Task':
        """Создаёт объект из строки БД"""
        return cls(
            id=row['id'],
            title=row['title'],
            description=row.get('description', ''),
            topic_id=row.get('topic_id'),
            deadline=row.get('deadline'),
            status=row.get('status', 'active'),
            created_at=row.get('created_at', datetime.now().isoformat()),
            completed_at=row.get('completed_at')
        )

    def to_dict(self) -> dict:
        """Преобразует в словарь для БД"""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'topic_id': self.topic_id,
            'deadline': self.deadline,
            'status': self.status,
            'created_at': self.created_at,
            'completed_at': self.completed_at
        }

    def complete(self):
        """Отмечает задачу выполненной"""
        self.status = 'completed'
        self.completed_at = datetime.now().isoformat()

    def is_overdue(self) -> bool:
        """Проверяет, просрочена ли задача"""
        if self.status != 'active' or not self.deadline:
            return False
        deadline = datetime.fromisoformat(self.deadline)
        return datetime.now() > deadline

    @property
    def deadline_display(self) -> str:
        """Возвращает отформатированную дату дедлайна"""
        if not self.deadline:
            return "—"
        dt = datetime.fromisoformat(self.deadline)
        return dt.strftime("%d.%m.%Y %H:%M")

    @property
    def status_icon(self) -> str:
        """Возвращает иконку статуса"""
        if self.status == 'completed':
            return "✅"
        if self.is_overdue():
            return "⚠️"
        return "⏳"