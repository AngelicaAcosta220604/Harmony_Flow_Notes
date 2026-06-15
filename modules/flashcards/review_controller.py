# modules/flashcards/review_controller.py
from typing import List, Optional, Dict, Any
from datetime import datetime

from datebase.repositories.review_repo import ReviewRepository
from datebase.repositories.flashcard_repo import FlashcardRepository
from models.review_session import ReviewSession
from models.review_answer import ReviewAnswer
from models.flashcard import Flashcard


class ReviewController:
    """
    Контроллер для сессий повторения карточек.
    """

    def __init__(self, review_repo: ReviewRepository, flashcard_repo: FlashcardRepository):
        self._review_repo = review_repo
        self._flashcard_repo = flashcard_repo
        self._current_session: Optional[ReviewSession] = None
        self._current_cards: List[Flashcard] = []
        self._current_index: int = 0

    def start_review_session(self, topic_ids: list, mode: str = 'sequential',
                             include_free: bool = True, include_qa: bool = True,
                             skip_reviewed: bool = True) -> Optional[int]:
        """
        Начинает новую сессию повторения для нескольких тем

        Args:
            topic_ids: Список ID тем
            mode: 'sequential' или 'random'
            include_free: Включать свободные карточки
            include_qa: Включать карточки вопрос-ответ
            skip_reviewed: Пропускать выученные (с интервалом > 0)

        Returns:
            ID сессии
        """
        # Получаем карточки для всех выбранных тем
        all_cards = []
        for topic_id in topic_ids:
            cards = self._get_cards_for_topic(topic_id)
            all_cards.extend(cards)

        # Применяем фильтры
        if include_free and not include_qa:
            all_cards = [c for c in all_cards if c.is_free]
        elif include_qa and not include_free:
            all_cards = [c for c in all_cards if c.is_qa]

        # Пропускаем выученные (если есть поле interval)
        if skip_reviewed:
            all_cards = [c for c in all_cards if getattr(c, 'interval', 0) == 0]

        if not all_cards:
            return None

        if mode == 'random':
            import random
            all_cards = random.sample(all_cards, len(all_cards))

        # Создаём сессию (используем первый topic_id для записи в БД)
        session_id = self._review_repo.create_review_session(
            topic_id=topic_ids[0] if topic_ids else 0,
            mode=mode,
            total_cards=len(all_cards)
        )

        # Сохраняем состояние
        self._current_session = ReviewSession(
            id=session_id,
            topic_id=topic_ids[0] if topic_ids else 0,
            mode=mode,
            total_cards=len(all_cards)
        )
        self._current_cards = all_cards
        self._current_index = 0

        return session_id

    def _get_cards_for_topic(self, topic_id: int) -> List[Flashcard]:
        """Возвращает карточки для повторения"""
        rows = self._flashcard_repo.get_by_topic(topic_id)
        return [Flashcard.from_row(row) for row in rows]

    def get_current_card(self) -> Optional[Flashcard]:
        """Возвращает текущую карточку"""
        if 0 <= self._current_index < len(self._current_cards):
            return self._current_cards[self._current_index]
        return None

    def answer_current_card(self, correct: bool) -> bool:
        """
        Сохраняет ответ на текущую карточку и переходит к следующей

        Returns:
            True если есть ещё карточки, False если сессия завершена
        """
        if not self._current_session:
            return False

        current_card = self.get_current_card()
        if not current_card:
            return False

        # Сохраняем ответ
        self._review_repo.save_answer(
            review_session_id=self._current_session.id,
            flashcard_id=current_card.id,
            correct=correct
        )

        # Обновляем счётчик
        self._current_session.completed_cards += 1
        self._review_repo.update_review_session(
            self._current_session.id,
            completed_cards=self._current_session.completed_cards
        )

        # Переходим к следующей карточке
        self._current_index += 1

        # Проверяем, завершена ли сессия
        if self._current_index >= len(self._current_cards):
            self.end_review_session()
            return False

        return True

    def end_review_session(self):
        """Завершает сессию повторения"""
        if self._current_session:
            self._review_repo.complete_review_session(self._current_session.id)
            self._current_session = None
            self._current_cards = []
            self._current_index = 0

    def get_progress(self) -> Dict[str, Any]:
        """Возвращает прогресс текущей сессии"""
        if not self._current_session:
            return {
                'completed': 0,
                'total': 0,
                'percent': 0,
                'remaining': 0
            }

        completed = self._current_session.completed_cards
        total = self._current_session.total_cards
        percent = (completed / total * 100) if total > 0 else 0

        return {
            'completed': completed,
            'total': total,
            'percent': round(percent, 1),
            'remaining': total - completed
        }

    def is_session_active(self) -> bool:
        """Возвращает, активна ли сессия"""
        return self._current_session is not None

    def get_session_stats(self, session_id: int) -> Dict[str, Any]:
        """Возвращает статистику по завершённой сессии"""
        return self._review_repo.get_statistics(session_id)

    def get_session_history(self, topic_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Возвращает историю сессий повторения"""
        sessions = self._review_repo.get_review_sessions(topic_id)

        result = []
        for session in sessions[:limit]:
            stats = self.get_session_stats(session['id'])
            result.append({
                'id': session['id'],
                'date': session.get('started_at', '')[:10] if session.get('started_at') else "—",
                'mode': session.get('mode', 'sequential'),
                'total_cards': session.get('total_cards', 0),
                'correct': stats.get('correct', 0),
                'percentage': stats.get('percentage', 0)
            })

        return result