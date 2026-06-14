# database/repositories/review_repo.py
from typing import List, Optional, Dict, Any
from datebase.db_manager import db

class ReviewRepository:
    """Репозиторий для работы с сессиями повторения карточек"""

    # ========== Review Sessions ==========

    def get_review_sessions(self, topic_id: int) -> List[Dict[str, Any]]:
        """Возвращает все сессии повторения для темы"""
        return db.fetchall(
            "SELECT * FROM review_sessions WHERE topic_id = ? ORDER BY started_at DESC",
            (topic_id,)
        )

    def create_review_session(self, topic_id: int, mode: str = 'sequential', total_cards: int = 0) -> int:
        """Создаёт сессию повторения"""
        from datetime import datetime
        return db.insert('review_sessions', {
            'topic_id': topic_id,
            'mode': mode,
            'total_cards': total_cards,
            'started_at': datetime.now().isoformat()
        })

    def update_review_session(self, session_id: int, **kwargs) -> int:
        """Обновляет сессию повторения"""
        allowed_fields = ['completed_cards', 'ended_at']
        data = {k: v for k, v in kwargs.items() if k in allowed_fields}
        if not data:
            return 0
        return db.update('review_sessions', data, 'id = ?', (session_id,))

    def complete_review_session(self, session_id: int) -> int:
        """Завершает сессию повторения"""
        from datetime import datetime
        return self.update_review_session(session_id, ended_at=datetime.now().isoformat())

    # ========== Review Answers ==========

    def save_answer(self, review_session_id: int, flashcard_id: int, correct: bool) -> int:
        """Сохраняет ответ на карточку"""
        return db.insert('review_answers', {
            'review_session_id': review_session_id,
            'flashcard_id': flashcard_id,
            'correct': 1 if correct else 0
        })

    def get_answers_for_session(self, review_session_id: int) -> List[Dict[str, Any]]:
        """Возвращает все ответы для сессии повторения"""
        return db.fetchall(
            "SELECT * FROM review_answers WHERE review_session_id = ?",
            (review_session_id,)
        )

    def get_statistics(self, review_session_id: int) -> Dict[str, Any]:
        """Возвращает статистику по сессии повторения"""
        answers = self.get_answers_for_session(review_session_id)

        total = len(answers)
        correct = sum(1 for a in answers if a['correct'])

        return {
            'total': total,
            'correct': correct,
            'incorrect': total - correct,
            'percentage': round(correct / total * 100, 1) if total > 0 else 0
        }