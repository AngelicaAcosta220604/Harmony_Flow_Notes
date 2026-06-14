# models/flashcard.py
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Flashcard:
    """Модель карточки"""
    id: int
    topic_id: int
    type: str  # 'free' or 'question_answer'
    question: str = ''
    answer: str = ''
    content: str = ''  # для free типа
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    @classmethod
    def from_row(cls, row: dict) -> 'Flashcard':
        """Создаёт объект из строки БД"""
        return cls(
            id=row['id'],
            topic_id=row['topic_id'],
            type=row['type'],
            question=row.get('question', ''),
            answer=row.get('answer', ''),
            content=row.get('content', ''),
            created_at=row.get('created_at', datetime.now().isoformat())
        )

    def to_dict(self) -> dict:
        """Преобразует в словарь для БД"""
        return {
            'id': self.id,
            'topic_id': self.topic_id,
            'type': self.type,
            'question': self.question,
            'answer': self.answer,
            'content': self.content,
            'created_at': self.created_at
        }

    @property
    def is_free(self) -> bool:
        """Является ли свободной карточкой"""
        return self.type == 'free'

    @property
    def is_qa(self) -> bool:
        """Является ли карточкой вопрос-ответ"""
        return self.type == 'question_answer'

    @property
    def display_front(self) -> str:
        """Возвращает лицевую сторону карточки"""
        if self.is_free:
            return self.content
        return self.question

    @property
    def display_back(self) -> str:
        """Возвращает оборотную сторону карточки"""
        if self.is_free:
            return self.content
        return self.answer

    @classmethod
    def create_free(cls, topic_id: int, content: str) -> 'Flashcard':
        """Фабричный метод для создания свободной карточки"""
        return cls(
            id=0,  # временный ID
            topic_id=topic_id,
            type='free',
            content=content
        )

    @classmethod
    def create_qa(cls, topic_id: int, question: str, answer: str) -> 'Flashcard':
        """Фабричный метод для создания карточки вопрос-ответ"""
        return cls(
            id=0,  # временный ID
            topic_id=topic_id,
            type='question_answer',
            question=question,
            answer=answer
        )