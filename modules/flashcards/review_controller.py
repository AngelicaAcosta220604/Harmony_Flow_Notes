# modules/flashcards/review_controller.py
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from datebase.repositories.review_repo import ReviewRepository
from datebase.repositories.flashcard_repo import FlashcardRepository
from models.review_session import ReviewSession
from models.review_answer import ReviewAnswer
from models.flashcard import Flashcard

# Настройка логирования
logger = logging.getLogger(__name__)


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
        logger.debug("ReviewController инициализирован")

    def start_review_session(self, topic_ids: list, mode: str = 'sequential',
                             include_free: bool = True, include_qa: bool = True,
                             skip_reviewed: bool = True,
                             card_ids: list = None) -> Optional[int]:
        """
        Начинает новую сессию повторения

        Args:
            topic_ids: Список ID тем
            mode: 'sequential' или 'random'
            include_free: Включать свободные карточки
            include_qa: Включать карточки вопрос-ответ
            skip_reviewed: Пропускать выученные
            card_ids: Если передан — использовать только эти карточки
        """
        try:
            # ✅ ИСПРАВЛЕНО: безопасное получение topic_id
            topic_id = topic_ids[0] if topic_ids else 0

            # 🆕 Если переданы конкретные card_ids — берём только их
            if card_ids:
                all_cards = []
                for cid in card_ids:
                    try:
                        card = self._flashcard_repo.get_by_id(cid)
                        if card:
                            all_cards.append(Flashcard.from_row(card))
                    except Exception as e:
                        logger.warning(f"Не удалось загрузить карточку {cid}: {e}")
            else:
                # Получаем карточки для всех выбранных тем
                all_cards = []
                for tid in topic_ids:
                    cards = self._get_cards_for_topic(tid)
                    all_cards.extend(cards)

            # Применяем фильтры (только если не переданы конкретные card_ids)
            if not card_ids:
                if include_free and not include_qa:
                    all_cards = [c for c in all_cards if c.is_free]
                elif include_qa and not include_free:
                    all_cards = [c for c in all_cards if c.is_qa]

                if skip_reviewed:
                    all_cards = [c for c in all_cards if getattr(c, 'interval', 0) == 0]

            if not all_cards:
                logger.info("Нет карточек для повторения")
                return None

            if mode == 'random':
                import random
                all_cards = random.sample(all_cards, len(all_cards))

            # Создаём сессию
            session_id = self._review_repo.create_review_session(
                topic_id=topic_id,
                mode=mode,
                total_cards=len(all_cards)
            )

            if not session_id:
                logger.error("Не удалось создать сессию повторения")
                return None

            self._current_session = ReviewSession(
                id=session_id,
                topic_id=topic_id,
                mode=mode,
                total_cards=len(all_cards)
            )
            self._current_cards = all_cards
            self._current_index = 0

            logger.info(f"Начата сессия повторения {session_id}: {len(all_cards)} карточек, режим {mode}")
            return session_id
        except Exception as e:
            logger.error(f"Ошибка запуска сессии повторения: {e}", exc_info=True)
            return None

    def _get_cards_for_topic(self, topic_id: int) -> List[Flashcard]:
        """Возвращает карточки для повторения"""
        try:
            rows = self._flashcard_repo.get_by_topic(topic_id)
            return [Flashcard.from_row(row) for row in rows]
        except Exception as e:
            logger.error(f"Ошибка получения карточек темы {topic_id}: {e}", exc_info=True)
            return []

    def get_current_card(self) -> Optional[Flashcard]:
        """Возвращает текущую карточку"""
        try:
            if 0 <= self._current_index < len(self._current_cards):
                return self._current_cards[self._current_index]
            return None
        except Exception as e:
            logger.error(f"Ошибка получения текущей карточки: {e}", exc_info=True)
            return None

    def answer_current_card(self, correct: bool) -> bool:
        """
        Сохраняет ответ на текущую карточку и переходит к следующей

        Returns:
            True если есть ещё карточки, False если сессия завершена
        """
        try:
            if not self._current_session:
                logger.warning("Нет активной сессии для ответа")
                return False

            current_card = self.get_current_card()
            if not current_card:
                logger.warning("Нет текущей карточки для ответа")
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
                logger.info(f"Сессия {self._current_session.id} завершена")
                return False  # Сессия завершена

            return True
        except Exception as e:
            logger.error(f"Ошибка обработки ответа на карточку: {e}", exc_info=True)
            return False

    def end_review_session(self):
        """Завершает сессию повторения"""
        try:
            if self._current_session:
                self._review_repo.complete_review_session(self._current_session.id)
                logger.info(f"Сессия повторения {self._current_session.id} завершена")
                self._current_session = None
                self._current_cards = []
                self._current_index = 0
        except Exception as e:
            logger.error(f"Ошибка завершения сессии повторения: {e}", exc_info=True)
            # Все равно очищаем состояние
            self._current_session = None
            self._current_cards = []
            self._current_index = 0

    def get_progress(self) -> Dict[str, Any]:
        """Возвращает прогресс текущей сессии"""
        try:
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
        except Exception as e:
            logger.error(f"Ошибка получения прогресса сессии: {e}", exc_info=True)
            return {
                'completed': 0,
                'total': 0,
                'percent': 0,
                'remaining': 0
            }

    def is_session_active(self) -> bool:
        """Возвращает, активна ли сессия"""
        return self._current_session is not None

    def get_session_stats(self, session_id: int) -> Dict[str, Any]:
        """Возвращает статистику по завершённой сессии"""
        try:
            return self._review_repo.get_statistics(session_id)
        except Exception as e:
            logger.error(f"Ошибка получения статистики сессии {session_id}: {e}", exc_info=True)
            return {
                'correct': 0,
                'total': 0,
                'percentage': 0
            }

    def get_session_history(self, topic_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Возвращает историю сессий повторения"""
        try:
            sessions = self._review_repo.get_review_sessions(topic_id)

            result = []
            for session in sessions[:limit]:
                try:
                    stats = self.get_session_stats(session['id'])
                    result.append({
                        'id': session['id'],
                        'date': session.get('started_at', '')[:10] if session.get('started_at') else "—",
                        'mode': session.get('mode', 'sequential'),
                        'total_cards': session.get('total_cards', 0),
                        'correct': stats.get('correct', 0),
                        'percentage': stats.get('percentage', 0)
                    })
                except Exception as e:
                    logger.warning(f"Не удалось загрузить статистику сессии {session.get('id')}: {e}")

            return result
        except Exception as e:
            logger.error(f"Ошибка получения истории сессий темы {topic_id}: {e}", exc_info=True)
            return []

    def record_answer(self, flashcard_id: int, correct: bool):
        """Записывает ответ и обновляет прогресс карточки"""
        try:
            from datebase.db_manager import db

            # Проверяем, есть ли запись о прогрессе
            progress = db.fetchone(
                "SELECT * FROM flashcard_progress WHERE flashcard_id = ?",
                (flashcard_id,)
            )

            if not progress:
                # Создаём новую запись
                db.execute(
                    """INSERT INTO flashcard_progress (flashcard_id, review_count, correct_count, status)
                       VALUES (?, ?, ?, ?)""",
                    (flashcard_id, 1, 1 if correct else 0, 'in_progress')
                )
                logger.debug(f"Создан прогресс для карточки {flashcard_id}")
            else:
                # Обновляем существующую
                new_review_count = progress['review_count'] + 1
                new_correct_count = progress['correct_count'] + (1 if correct else 0)

                # Определяем статус
                if new_correct_count >= 5:
                    new_status = 'mastered'
                else:
                    new_status = 'in_progress'

                db.execute(
                    """UPDATE flashcard_progress 
                       SET review_count = ?, correct_count = ?, status = ?, last_reviewed = CURRENT_TIMESTAMP
                       WHERE flashcard_id = ?""",
                    (new_review_count, new_correct_count, new_status, flashcard_id)
                )
                logger.debug(
                    f"Обновлен прогресс карточки {flashcard_id}: {new_review_count} повторов, {new_correct_count} правильных")
        except Exception as e:
            logger.error(f"Ошибка записи ответа для карточки {flashcard_id}: {e}", exc_info=True)