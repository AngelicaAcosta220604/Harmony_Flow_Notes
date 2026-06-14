# models/review_answer.py
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ReviewAnswer:
    """Модель ответа на карточку при повторении"""
    id: int
    review_session_id: int
    flashcard_id: int
    correct: bool
    answered_at: str = field(default_factory=lambda: datetime.now().isoformat())

    @classmethod
    def from_row(cls, row: dict) -> 'ReviewAnswer':
        """Создаёт объект из строки БД"""
        return cls(
            id=row['id'],
            review_session_id=row['review_session_id'],
            flashcard_id=row['flashcard_id'],
            correct=bool(row['correct']),
            answered_at=row.get('answered_at', datetime.now().isoformat())
        )

    def to_dict(self) -> dict:
        """Преобразует в словарь для БД"""
        return {
            'id': self.id,
            'review_session_id': self.review_session_id,
            'flashcard_id': self.flashcard_id,
            'correct': 1 if self.correct else 0,
            'answered_at': self.answered_at
        }

    @classmethod
    def create(cls, review_session_id: int, flashcard_id: int, correct: bool) -> 'ReviewAnswer':
        """Фабричный метод для создания ответа"""
        return cls(
            id=0,
            review_session_id=review_session_id,
            flashcard_id=flashcard_id,
            correct=correct
        )