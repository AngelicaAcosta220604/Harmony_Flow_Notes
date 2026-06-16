# modules/notes/controller.py
from typing import List, Optional, Dict, Any
from datetime import datetime
from datebase.repositories.note_repo import NoteRepository
from models.note import Note
from core.event_bus import event_bus

class NoteController:
    """
    Контроллер для управления заметками.
    Обеспечивает CRUD операции, поиск, импорт.
    """

    def __init__(self, note_repo: NoteRepository):
        self._repo = note_repo

    def get_all_notes(self) -> List[Note]:
        """Возвращает все заметки"""
        rows = self._repo.get_all()
        return [Note.from_row(row) for row in rows]

    def get_note(self, note_id: int) -> Optional[Note]:
        """Возвращает заметку по ID"""
        row = self._repo.get_by_id(note_id)
        return Note.from_row(row) if row else None

    def get_notes_by_topic(self, topic_id: int) -> List[Note]:
        """Возвращает все заметки темы"""
        rows = self._repo.get_by_topic(topic_id)
        return [Note.from_row(row) for row in rows]

    def get_notes_by_topics(self, topic_ids: List[int]) -> List[Note]:
        """Возвращает заметки для списка тем"""
        if not topic_ids:
            return []
        rows = self._repo.get_by_topics(topic_ids)
        return [Note.from_row(row) for row in rows]

    def create_note(self, topic_id: int, title: str, content: str = "") -> int:
        """Создаёт новую заметку"""
        if not title.strip():
            title = f"Заметка от {datetime.now().strftime('%d.%m.%Y %H:%M')}"
        note_id = self._repo.create(topic_id, title.strip(), content)
        if note_id:
            event_bus.note_created.emit(note_id)  # 🆕 ДОБАВИТЬ
        return note_id

    def update_note(self, note_id: int, title: str = None, content: str = None) -> bool:
        """Обновляет заметку"""
        updates = {}
        if title is not None:
            updates['title'] = title
        if content is not None:
            updates['content'] = content

        if not updates:
            return True

        rows_affected = self._repo.update(note_id, **updates)
        if rows_affected > 0:
            event_bus.note_updated.emit(note_id)  # 🆕 ДОБАВИТЬ
        return rows_affected > 0

    def update_content(self, note_id: int, new_content: str) -> bool:
        """Обновляет только содержимое заметки"""
        return self.update_note(note_id, content=new_content)

    def rename(self, note_id: int, new_title: str) -> bool:
        """Переименовывает заметку"""
        return self.update_note(note_id, title=new_title)

    def delete_note(self, note_id: int) -> bool:
        """Удаляет заметку"""
        rows_affected = self._repo.delete(note_id)
        if rows_affected > 0:
            event_bus.note_deleted.emit(note_id)  # 🆕 ДОБАВИТЬ
        return rows_affected > 0

    def delete_notes_by_topic(self, topic_id: int) -> int:
        """Удаляет все заметки темы"""
        return self._repo.delete_by_topic(topic_id)

    def search_notes(self, query: str) -> List[Note]:
        """Ищет заметки по заголовку или содержимому"""
        rows = self._repo.search(query)
        return [Note.from_row(row) for row in rows]

    def get_recent_notes(self, limit: int = 10) -> List[Note]:
        """Возвращает последние заметки"""
        rows = self._repo.get_recent(limit)
        return [Note.from_row(row) for row in rows]

    def get_note_count(self) -> int:
        """Возвращает количество заметок"""
        return len(self.get_all_notes())

    def get_note_count_by_topic(self, topic_id: int) -> int:
        """Возвращает количество заметок в теме"""
        return len(self.get_notes_by_topic(topic_id))

    def import_from_text(self, topic_id: int, file_path: str) -> Optional[int]:
        """
        Импортирует текст из файла .txt в новую заметку

        Returns:
            ID созданной заметки или None
        """
        from services.import_service import ImportService

        success, content = ImportService.import_text_file(file_path)
        if not success:
            return None

        # Извлекаем имя файла как заголовок
        from pathlib import Path
        title = Path(file_path).stem

        return self.create_note(topic_id, title, content)

    def create_from_quick_note(self, quick_note_content: str, topic_id: int) -> int:
        """
        Создаёт заметку из быстрой записи
        """
        title = f"Быстрая запись от {datetime.now().strftime('%d.%m.%Y %H:%M')}"
        return self.create_note(topic_id, title, quick_note_content)

    def get_notes_with_preview(self, topic_id: int, preview_length: int = 100) -> List[Dict[str, Any]]:
        """
        Возвращает заметки с превью для отображения в списке
        """
        notes = self.get_notes_by_topic(topic_id)

        result = []
        for note in notes:
            result.append({
                'id': note.id,
                'title': note.title,
                'preview': note.get_preview(preview_length),
                'updated_at': note.updated_at,
                'word_count': note.word_count
            })

        return result