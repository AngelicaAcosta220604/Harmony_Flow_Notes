# modules/notes/controller.py
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from database.repositories.note_repo import NoteRepository
from models.note import Note
from core.event_bus import event_bus

# Настройка логирования
logger = logging.getLogger(__name__)


class NoteController:
    """
    Контроллер для управления заметками.
    Обеспечивает CRUD операции, поиск, импорт.
    """

    def __init__(self, note_repo: NoteRepository):
        self._repo = note_repo
        logger.debug("NoteController инициализирован")

    def get_all_notes(self) -> List[Note]:
        """Возвращает все заметки"""
        try:
            rows = self._repo.get_all()
            return [Note.from_row(row) for row in rows]
        except Exception as e:
            logger.error(f"Ошибка получения всех заметок: {e}", exc_info=True)
            return []

    def get_note(self, note_id: int) -> Optional[Note]:
        """Возвращает заметку по ID"""
        try:
            row = self._repo.get_by_id(note_id)
            return Note.from_row(row) if row else None
        except Exception as e:
            logger.error(f"Ошибка получения заметки {note_id}: {e}", exc_info=True)
            return None

    def get_notes_by_topic(self, topic_id: int) -> List[Note]:
        """Возвращает все заметки темы"""
        try:
            rows = self._repo.get_by_topic(topic_id)
            return [Note.from_row(row) for row in rows]
        except Exception as e:
            logger.error(f"Ошибка получения заметок темы {topic_id}: {e}", exc_info=True)
            return []

    def get_notes_by_topics(self, topic_ids: List[int]) -> List[Note]:
        """Возвращает заметки для списка тем"""
        try:
            if not topic_ids:
                return []
            rows = self._repo.get_by_topics(topic_ids)
            return [Note.from_row(row) for row in rows]
        except Exception as e:
            logger.error(f"Ошибка получения заметок для тем {topic_ids}: {e}", exc_info=True)
            return []

    def create_note(self, topic_id: int, title: str, content: str = "") -> int:
        """Создаёт новую заметку"""
        try:
            if not title.strip():
                title = f"Заметка от {datetime.now().strftime('%d.%m.%Y %H:%M')}"
            note_id = self._repo.create(topic_id, title.strip(), content)
            if note_id:
                event_bus.note_created.emit(note_id)
                logger.info(f"Создана заметка '{title}' (id={note_id}, topic={topic_id})")
            else:
                logger.warning(f"Не удалось создать заметку '{title}'")
            return note_id
        except Exception as e:
            logger.error(f"Ошибка создания заметки '{title}': {e}", exc_info=True)
            return 0

    def update_note(self, note_id: int, title: str = None, content: str = None) -> bool:
        """Обновляет заметку"""
        try:
            updates = {}
            if title is not None:
                updates['title'] = title
            if content is not None:
                updates['content'] = content

            if not updates:
                return True

            rows_affected = self._repo.update(note_id, **updates)
            if rows_affected > 0:
                event_bus.note_updated.emit(note_id)
                logger.debug(f"Заметка {note_id} обновлена: {list(updates.keys())}")
            else:
                logger.warning(f"Не удалось обновить заметку {note_id}")
            return rows_affected > 0
        except Exception as e:
            logger.error(f"Ошибка обновления заметки {note_id}: {e}", exc_info=True)
            return False

    def update_content(self, note_id: int, new_content: str) -> bool:
        """Обновляет только содержимое заметки"""
        try:
            return self.update_note(note_id, content=new_content)
        except Exception as e:
            logger.error(f"Ошибка обновления содержимого заметки {note_id}: {e}", exc_info=True)
            return False

    def rename(self, note_id: int, new_title: str) -> bool:
        """Переименовывает заметку"""
        try:
            return self.update_note(note_id, title=new_title)
        except Exception as e:
            logger.error(f"Ошибка переименования заметки {note_id}: {e}", exc_info=True)
            return False

    def delete_note(self, note_id: int) -> bool:
        """Удаляет заметку"""
        try:
            rows_affected = self._repo.delete(note_id)
            if rows_affected > 0:
                event_bus.note_deleted.emit(note_id)
                logger.info(f"Удалена заметка {note_id}")
                return True
            else:
                logger.warning(f"Не удалось удалить заметку {note_id}")
            return False
        except Exception as e:
            logger.error(f"Ошибка удаления заметки {note_id}: {e}", exc_info=True)
            return False

    def delete_notes_by_topic(self, topic_id: int) -> int:
        """Удаляет все заметки темы"""
        try:
            deleted_count = self._repo.delete_by_topic(topic_id)
            logger.info(f"Удалено {deleted_count} заметок из темы {topic_id}")
            return deleted_count
        except Exception as e:
            logger.error(f"Ошибка удаления заметок темы {topic_id}: {e}", exc_info=True)
            return 0

    def search_notes(self, query: str) -> List[Note]:
        """Ищет заметки по заголовку или содержимому"""
        try:
            rows = self._repo.search(query)
            return [Note.from_row(row) for row in rows]
        except Exception as e:
            logger.error(f"Ошибка поиска заметок по запросу '{query}': {e}", exc_info=True)
            return []

    def get_recent_notes(self, limit: int = 10) -> List[Note]:
        """Возвращает последние заметки"""
        try:
            rows = self._repo.get_recent(limit)
            return [Note.from_row(row) for row in rows]
        except Exception as e:
            logger.error(f"Ошибка получения последних заметок: {e}", exc_info=True)
            return []

    def get_note_count(self) -> int:
        """Возвращает количество заметок"""
        try:
            return len(self.get_all_notes())
        except Exception as e:
            logger.error(f"Ошибка подсчета заметок: {e}", exc_info=True)
            return 0

    def get_note_count_by_topic(self, topic_id: int) -> int:
        """Возвращает количество заметок в теме"""
        try:
            return len(self.get_notes_by_topic(topic_id))
        except Exception as e:
            logger.error(f"Ошибка подсчета заметок темы {topic_id}: {e}", exc_info=True)
            return 0

    def import_from_text(self, topic_id: int, file_path: str) -> Optional[int]:
        """
        Импортирует текст из файла .txt в новую заметку

        Returns:
            ID созданной заметки или None
        """
        try:
            from services.import_service import ImportService

            success, content = ImportService.import_text_file(file_path)
            if not success:
                logger.warning(f"Не удалось импортировать файл {file_path}")
                return None

            # Извлекаем имя файла как заголовок
            from pathlib import Path
            title = Path(file_path).stem

            note_id = self.create_note(topic_id, title, content)
            if note_id:
                logger.info(f"Импортирована заметка {note_id} из {file_path}")
            return note_id
        except FileNotFoundError:
            logger.error(f"Файл не найден: {file_path}")
            return None
        except PermissionError:
            logger.error(f"Нет прав доступа к файлу: {file_path}")
            return None
        except Exception as e:
            logger.error(f"Ошибка импорта из файла {file_path}: {e}", exc_info=True)
            return None

    def create_from_quick_note(self, quick_note_content: str, topic_id: int) -> int:
        """
        Создаёт заметку из быстрой записи
        """
        try:
            title = f"Быстрая запись от {datetime.now().strftime('%d.%m.%Y %H:%M')}"
            note_id = self.create_note(topic_id, title, quick_note_content)
            if note_id:
                logger.info(f"Создана быстрая заметка {note_id} в теме {topic_id}")
            return note_id
        except Exception as e:
            logger.error(f"Ошибка создания быстрой заметки: {e}", exc_info=True)
            return 0

    def get_notes_with_preview(self, topic_id: int, preview_length: int = 100) -> List[Dict[str, Any]]:
        """
        Возвращает заметки с превью для отображения в списке
        """
        try:
            notes = self.get_notes_by_topic(topic_id)

            result = []
            for note in notes:
                # ✅ ИСПРАВЛЕНО: безопасное получение preview и word_count
                try:
                    preview = note.get_preview(preview_length) if hasattr(note, 'get_preview') else ""
                except Exception as e:
                    logger.warning(f"Не удалось получить превью для заметки {note.id}: {e}")
                    preview = ""

                try:
                    word_count = note.word_count if hasattr(note, 'word_count') else 0
                except Exception as e:
                    logger.warning(f"Не удалось получить word_count для заметки {note.id}: {e}")
                    word_count = 0

                result.append({
                    'id': note.id,
                    'title': note.title,
                    'preview': preview,
                    'updated_at': note.updated_at,
                    'word_count': word_count
                })

            return result
        except Exception as e:
            logger.error(f"Ошибка получения заметок с превью для темы {topic_id}: {e}", exc_info=True)
            return []