# modules/flashcards/controller.py
from typing import List, Optional, Dict, Any
from datetime import datetime

from datebase.repositories.flashcard_repo import FlashcardRepository
from models.flashcard import Flashcard


class FlashcardController:
    """
    Контроллер для управления карточками.
    Обеспечивает CRUD операции, создание из заметок.
    """

    def __init__(self, flashcard_repo: FlashcardRepository):
        self._repo = flashcard_repo

    def get_all_cards(self) -> List[Flashcard]:
        """Возвращает все карточки"""
        rows = self._repo.get_all()
        return [Flashcard.from_row(row) for row in rows]

    def get_card(self, card_id: int) -> Optional[Flashcard]:
        """Возвращает карточку по ID"""
        row = self._repo.get_by_id(card_id)
        return Flashcard.from_row(row) if row else None

    def get_cards_by_topic(self, topic_id: int) -> List[Flashcard]:
        """Возвращает карточки темы"""
        rows = self._repo.get_by_topic(topic_id)
        return [Flashcard.from_row(row) for row in rows]

    def get_cards_by_topics(self, topic_ids: List[int]) -> List[Flashcard]:
        """Возвращает карточки для списка тем"""
        if not topic_ids:
            return []
        rows = self._repo.get_by_topics(topic_ids)
        return [Flashcard.from_row(row) for row in rows]

    def create_free_card(self, topic_id: int, content: str) -> int:
        """Создаёт свободную карточку"""
        card_id = self._repo.create_free(topic_id, content)
        if card_id > 0:
            from core.event_bus import event_bus
            event_bus.flashcard_created.emit(card_id)
        return card_id

    def create_qa_card(self, topic_id: int, question: str, answer: str) -> int:
        """Создаёт карточку вопрос-ответ"""
        card_id = self._repo.create_qa(topic_id, question, answer)
        if card_id > 0:
            from core.event_bus import event_bus
            event_bus.flashcard_created.emit(card_id)
        return card_id

    def create_from_selection(self, topic_id: int, selected_text: str) -> int:
        """
        Создаёт карточку из выделенного текста.
        По умолчанию создаёт свободную карточку.
        Пользователь может потом преобразовать в Q&A.
        """
        return self.create_free_card(topic_id, selected_text)

    def update_card(self, card_id: int, **kwargs) -> bool:
        """Обновляет карточку"""
        rows_affected = self._repo.update(card_id, **kwargs)
        return rows_affected > 0

    def convert_to_qa(self, card_id: int, question: str, answer: str) -> bool:
        """Преобразует свободную карточку в Q&A"""
        return self.update_card(card_id, type='question_answer', question=question, answer=answer)

    def delete_card(self, card_id: int) -> bool:
        """Удаляет карточку"""
        success = self._repo.delete(card_id)
        if success:
            from core.event_bus import event_bus
            event_bus.flashcard_deleted.emit(card_id)
        return success

    def delete_cards_by_topic(self, topic_id: int) -> int:
        """Удаляет все карточки темы"""
        return self._repo.delete_by_topic(topic_id)

    def search_cards(self, query: str) -> List[Flashcard]:
        """Ищет карточки по содержимому"""
        rows = self._repo.search(query)
        return [Flashcard.from_row(row) for row in rows]

    def get_card_count(self) -> int:
        """Возвращает количество карточек"""
        return len(self.get_all_cards())

    def get_card_count_by_topic(self, topic_id: int) -> int:
        """Возвращает количество карточек в теме"""
        return len(self.get_cards_by_topic(topic_id))

    def get_random_cards(self, topic_id: int, limit: int = 10) -> List[Flashcard]:
        """Возвращает случайные карточки темы"""
        rows = self._repo.get_random(topic_id, limit)
        return [Flashcard.from_row(row) for row in rows]

    def get_cards_for_review(self, topic_id: int, mode: str = 'sequential') -> List[Flashcard]:
        """
        Возвращает карточки для повторения в указанном режиме.

        Args:
            topic_id: ID темы
            mode: 'sequential' или 'random'
        """
        cards = self.get_cards_by_topic(topic_id)

        if mode == 'random':
            import random
            cards = random.sample(cards, len(cards))

        return cards

    def get_stats(self, topic_id: int = None) -> Dict[str, Any]:
        """
        Возвращает статистику по карточкам

        Args:
            topic_id: Если указан, статистика только по теме, иначе по всем
        """
        if topic_id:
            cards = self.get_cards_by_topic(topic_id)
        else:
            cards = self.get_all_cards()

        free_cards = sum(1 for c in cards if c.is_free)
        qa_cards = sum(1 for c in cards if c.is_qa)

        return {
            'total': len(cards),
            'free': free_cards,
            'qa': qa_cards,
            'free_percent': round(free_cards / len(cards) * 100, 1) if cards else 0,
            'qa_percent': round(qa_cards / len(cards) * 100, 1) if cards else 0
        }