# modules/flashcards/controller.py
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from datebase.repositories.flashcard_repo import FlashcardRepository
from models.flashcard import Flashcard
from core.event_bus import event_bus

# Настройка логирования
logger = logging.getLogger(__name__)


class FlashcardController:
    """
    Контроллер для управления карточками.
    Обеспечивает CRUD операции, создание из заметок.
    """

    def __init__(self, flashcard_repo: FlashcardRepository):
        self._repo = flashcard_repo
        logger.debug("FlashcardController инициализирован")

    def get_all_cards(self) -> List[Flashcard]:
        """Возвращает все карточки"""
        try:
            rows = self._repo.get_all()
            return [Flashcard.from_row(row) for row in rows]
        except Exception as e:
            logger.error(f"Ошибка получения всех карточек: {e}", exc_info=True)
            return []

    def get_card(self, card_id: int) -> Optional[Flashcard]:
        """Возвращает карточку по ID"""
        try:
            row = self._repo.get_by_id(card_id)
            return Flashcard.from_row(row) if row else None
        except Exception as e:
            logger.error(f"Ошибка получения карточки {card_id}: {e}", exc_info=True)
            return None

    def get_cards_by_topic(self, topic_id: int) -> List[Flashcard]:
        """Возвращает карточки темы"""
        try:
            rows = self._repo.get_by_topic(topic_id)
            return [Flashcard.from_row(row) for row in rows]
        except Exception as e:
            logger.error(f"Ошибка получения карточек темы {topic_id}: {e}", exc_info=True)
            return []

    def get_cards_by_topics(self, topic_ids: List[int]) -> List[Flashcard]:
        """Возвращает карточки для списка тем"""
        try:
            if not topic_ids:
                return []
            rows = self._repo.get_by_topics(topic_ids)
            return [Flashcard.from_row(row) for row in rows]
        except Exception as e:
            logger.error(f"Ошибка получения карточек для тем {topic_ids}: {e}", exc_info=True)
            return []

    def create_free_card(self, topic_id: int, content: str) -> int:
        """Создаёт свободную карточку"""
        try:
            card_id = self._repo.create_free(topic_id, content)
            if card_id > 0:
                event_bus.flashcard_created.emit(card_id)
                logger.info(f"Создана свободная карточка {card_id} в теме {topic_id}")
            else:
                logger.warning(f"Не удалось создать свободную карточку в теме {topic_id}")
            return card_id
        except Exception as e:
            logger.error(f"Ошибка создания свободной карточки в теме {topic_id}: {e}", exc_info=True)
            return 0

    def create_qa_card(self, topic_id: int, question: str, answer: str) -> int:
        """Создаёт карточку вопрос-ответ"""
        try:
            card_id = self._repo.create_qa(topic_id, question, answer)
            if card_id > 0:
                event_bus.flashcard_created.emit(card_id)
                logger.info(f"Создана Q&A карточка {card_id} в теме {topic_id}")
            else:
                logger.warning(f"Не удалось создать Q&A карточку в теме {topic_id}")
            return card_id
        except Exception as e:
            logger.error(f"Ошибка создания Q&A карточки в теме {topic_id}: {e}", exc_info=True)
            return 0

    def create_from_selection(self, topic_id: int, selected_text: str) -> int:
        """
        Создаёт карточку из выделенного текста.
        По умолчанию создаёт свободную карточку.
        Пользователь может потом преобразовать в Q&A.
        """
        try:
            return self.create_free_card(topic_id, selected_text)
        except Exception as e:
            logger.error(f"Ошибка создания карточки из выделения: {e}", exc_info=True)
            return 0

    def update_card(self, card_id: int, **kwargs) -> bool:
        """Обновляет карточку"""
        try:
            rows_affected = self._repo.update(card_id, **kwargs)
            success = rows_affected > 0
            if success:
                logger.debug(f"Карточка {card_id} обновлена: {list(kwargs.keys())}")
            else:
                logger.warning(f"Не удалось обновить карточку {card_id}")
            return success
        except Exception as e:
            logger.error(f"Ошибка обновления карточки {card_id}: {e}", exc_info=True)
            return False

    def convert_to_qa(self, card_id: int, question: str, answer: str) -> bool:
        """Преобразует свободную карточку в Q&A"""
        try:
            success = self.update_card(card_id, type='question_answer', question=question, answer=answer)
            if success:
                logger.info(f"Карточка {card_id} преобразована в Q&A")
            return success
        except Exception as e:
            logger.error(f"Ошибка преобразования карточки {card_id} в Q&A: {e}", exc_info=True)
            return False

    def delete_card(self, card_id: int) -> bool:
        """Удаляет карточку"""
        try:
            success = self._repo.delete(card_id)
            if success:
                event_bus.flashcard_deleted.emit(card_id)
                logger.info(f"Удалена карточка {card_id}")
            else:
                logger.warning(f"Не удалось удалить карточку {card_id}")
            return success
        except Exception as e:
            logger.error(f"Ошибка удаления карточки {card_id}: {e}", exc_info=True)
            return False

    def delete_cards_by_topic(self, topic_id: int) -> int:
        """Удаляет все карточки темы"""
        try:
            deleted_count = self._repo.delete_by_topic(topic_id)
            logger.info(f"Удалено {deleted_count} карточек из темы {topic_id}")
            return deleted_count
        except Exception as e:
            logger.error(f"Ошибка удаления карточек темы {topic_id}: {e}", exc_info=True)
            return 0

    def search_cards(self, query: str) -> List[Flashcard]:
        """Ищет карточки по содержимому"""
        try:
            rows = self._repo.search(query)
            return [Flashcard.from_row(row) for row in rows]
        except Exception as e:
            logger.error(f"Ошибка поиска карточек по запросу '{query}': {e}", exc_info=True)
            return []

    def get_card_count(self) -> int:
        """Возвращает количество карточек"""
        try:
            return len(self.get_all_cards())
        except Exception as e:
            logger.error(f"Ошибка подсчета карточек: {e}", exc_info=True)
            return 0

    def get_card_count_by_topic(self, topic_id: int) -> int:
        """Возвращает количество карточек в теме"""
        try:
            return len(self.get_cards_by_topic(topic_id))
        except Exception as e:
            logger.error(f"Ошибка подсчета карточек темы {topic_id}: {e}", exc_info=True)
            return 0

    def get_random_cards(self, topic_id: int, limit: int = 10) -> List[Flashcard]:
        """Возвращает случайные карточки темы"""
        try:
            rows = self._repo.get_random(topic_id, limit)
            return [Flashcard.from_row(row) for row in rows]
        except Exception as e:
            logger.error(f"Ошибка получения случайных карточек темы {topic_id}: {e}", exc_info=True)
            return []

    def get_cards_for_review(self, topic_id: int, mode: str = 'sequential') -> List[Flashcard]:
        """
        Возвращает карточки для повторения в указанном режиме.

        Args:
            topic_id: ID темы
            mode: 'sequential' или 'random'
        """
        try:
            cards = self.get_cards_by_topic(topic_id)

            if mode == 'random' and cards:
                import random
                cards = random.sample(cards, len(cards))

            return cards
        except Exception as e:
            logger.error(f"Ошибка получения карточек для повторения (тема {topic_id}, режим {mode}): {e}", exc_info=True)
            return []

    def get_stats(self, topic_id: int = None) -> Dict[str, Any]:
        """
        Возвращает статистику по карточкам

        Args:
            topic_id: Если указан, статистика только по теме, иначе по всем
        """
        try:
            if topic_id:
                cards = self.get_cards_by_topic(topic_id)
            else:
                cards = self.get_all_cards()

            free_cards = sum(1 for c in cards if c.is_free)
            qa_cards = sum(1 for c in cards if c.is_qa)
            total = len(cards)

            return {
                'total': total,
                'free': free_cards,
                'qa': qa_cards,
                'free_percent': round(free_cards / total * 100, 1) if total else 0,
                'qa_percent': round(qa_cards / total * 100, 1) if total else 0
            }
        except Exception as e:
            logger.error(f"Ошибка получения статистики карточек: {e}", exc_info=True)
            return {
                'total': 0,
                'free': 0,
                'qa': 0,
                'free_percent': 0,
                'qa_percent': 0
            }

    def get_card_progress(self, card_id: int) -> dict:
        """Возвращает прогресс карточки"""
        try:
            from datebase.db_manager import db

            progress = db.fetchone(
                "SELECT * FROM flashcard_progress WHERE flashcard_id = ?",
                (card_id,)
            )

            if not progress:
                return {
                    'review_count': 0,
                    'correct_count': 0,
                    'status': 'new'
                }

            return {
                'review_count': progress['review_count'],
                'correct_count': progress['correct_count'],
                'status': progress['status']
            }
        except Exception as e:
            logger.error(f"Ошибка получения прогресса карточки {card_id}: {e}", exc_info=True)
            return {
                'review_count': 0,
                'correct_count': 0,
                'status': 'new'
            }