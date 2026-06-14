# database/repositories/note_repo.py
from typing import List, Optional, Dict, Any

from datebase.db_manager import db


class NoteRepository:
    """Репозиторий для работы с заметками"""

    def get_all(self) -> List[Dict[str, Any]]:
        """Возвращает все заметки"""
        return db.fetchall("SELECT * FROM notes ORDER BY updated_at DESC")

    def get_by_id(self, note_id: int) -> Optional[Dict[str, Any]]:
        """Возвращает заметку по ID"""
        return db.fetchone("SELECT * FROM notes WHERE id = ?", (note_id,))

    def get_by_topic(self, topic_id: int) -> List[Dict[str, Any]]:
        """Возвращает все заметки темы"""
        return db.fetchall(
            "SELECT * FROM notes WHERE topic_id = ? ORDER BY updated_at DESC",
            (topic_id,)
        )

    def get_by_topics(self, topic_ids: List[int]) -> List[Dict[str, Any]]:
        """Возвращает заметки для списка тем"""
        if not topic_ids:
            return []
        placeholders = ','.join('?' * len(topic_ids))
        return db.fetchall(
            f"SELECT * FROM notes WHERE topic_id IN ({placeholders}) ORDER BY updated_at DESC",
            tuple(topic_ids)
        )

    def create(self, topic_id: int, title: str, content: str = '') -> int:
        """Создаёт новую заметку"""
        return db.insert('notes', {
            'topic_id': topic_id,
            'title': title,
            'content': content
        })

    def update(self, note_id: int, **kwargs) -> int:
        """Обновляет заметку"""
        allowed_fields = ['title', 'content']
        data = {k: v for k, v in kwargs.items() if k in allowed_fields}
        if not data:
            return 0
        # Добавляем обновление updated_at
        data['updated_at'] = 'CURRENT_TIMESTAMP'
        return db.update('notes', data, 'id = ?', (note_id,))

    def delete(self, note_id: int) -> int:
        """Удаляет заметку"""
        return db.delete('notes', 'id = ?', (note_id,))

    def delete_by_topic(self, topic_id: int) -> int:
        """Удаляет все заметки темы"""
        return db.delete('notes', 'topic_id = ?', (topic_id,))

    def search(self, query: str) -> List[Dict[str, Any]]:
        """Поиск заметок по заголовку или содержимому"""
        return db.fetchall(
            "SELECT * FROM notes WHERE title LIKE ? OR content LIKE ? ORDER BY updated_at DESC",
            (f'%{query}%', f'%{query}%')
        )

    def get_recent(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Возвращает последние заметки"""
        return db.fetchall(
            "SELECT * FROM notes ORDER BY updated_at DESC LIMIT ?",
            (limit,)
        )