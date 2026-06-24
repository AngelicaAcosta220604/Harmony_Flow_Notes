# database/repositories/flashcard_repo.py
from typing import List, Optional, Dict, Any

from database.db_manager import db


class FlashcardRepository:
    """Репозиторий для работы с карточками"""

    def get_all(self) -> List[Dict[str, Any]]:
        """Возвращает все карточки"""
        return db.fetchall("SELECT * FROM flashcards ORDER BY created_at DESC")

    def get_by_id(self, card_id: int) -> Optional[Dict[str, Any]]:
        """Возвращает карточку по ID"""
        return db.fetchone("SELECT * FROM flashcards WHERE id = ?", (card_id,))

    def get_by_topic(self, topic_id: int) -> List[Dict[str, Any]]:
        """Возвращает карточки темы"""
        return db.fetchall(
            "SELECT * FROM flashcards WHERE topic_id = ? ORDER BY created_at DESC",
            (topic_id,)
        )

    def get_by_topics(self, topic_ids: List[int]) -> List[Dict[str, Any]]:
        """Возвращает карточки для списка тем"""
        if not topic_ids:
            return []
        placeholders = ','.join('?' * len(topic_ids))
        return db.fetchall(
            f"SELECT * FROM flashcards WHERE topic_id IN ({placeholders}) ORDER BY created_at DESC",
            tuple(topic_ids)
        )

    def create_free(self, topic_id: int, content: str) -> int:
        """Создаёт свободную карточку"""
        return db.insert('flashcards', {
            'topic_id': topic_id,
            'type': 'free',
            'content': content
        })

    def create_qa(self, topic_id: int, question: str, answer: str) -> int:
        """Создаёт карточку вопрос-ответ"""
        return db.insert('flashcards', {
            'topic_id': topic_id,
            'type': 'question_answer',
            'question': question,
            'answer': answer
        })

    def update(self, card_id: int, **kwargs) -> int:
        """Обновляет карточку"""
        allowed_fields = ['type', 'question', 'answer', 'content']
        data = {k: v for k, v in kwargs.items() if k in allowed_fields}
        if not data:
            return 0
        return db.update('flashcards', data, 'id = ?', (card_id,))

    def delete(self, card_id: int) -> int:
        """Удаляет карточку"""
        return db.delete('flashcards', 'id = ?', (card_id,))

    def delete_by_topic(self, topic_id: int) -> int:
        """Удаляет все карточки темы"""
        return db.delete('flashcards', 'topic_id = ?', (topic_id,))

    def search(self, query: str) -> List[Dict[str, Any]]:
        """Поиск карточек по содержимому"""
        return db.fetchall(
            """SELECT * FROM flashcards 
               WHERE content LIKE ? OR question LIKE ? OR answer LIKE ? 
               ORDER BY created_at DESC""",
            (f'%{query}%', f'%{query}%', f'%{query}%')
        )

    def get_random(self, topic_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Возвращает случайные карточки темы"""
        return db.fetchall(
            "SELECT * FROM flashcards WHERE topic_id = ? ORDER BY RANDOM() LIMIT ?",
            (topic_id, limit)
        )