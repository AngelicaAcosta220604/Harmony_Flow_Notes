# database/repositories/quick_note_repo.py
from typing import List, Optional, Dict, Any

from database.db_manager import db


class QuickNoteRepository:
    """Репозиторий для работы с быстрыми записями"""

    def get_by_session(self, session_id: int) -> List[Dict[str, Any]]:
        """Возвращает быстрые записи для сессии"""
        return db.fetchall(
            "SELECT * FROM quick_notes WHERE session_id = ? ORDER BY created_at ASC",
            (session_id,)
        )

    def get_by_topic(self, topic_id: int) -> List[Dict[str, Any]]:
        """Возвращает быстрые записи для темы"""
        return db.fetchall(
            "SELECT * FROM quick_notes WHERE topic_id = ? ORDER BY created_at DESC",
            (topic_id,)
        )

    def create(self, session_id: int, topic_id: int, content: str) -> int:
        """Создаёт быструю запись"""
        return db.insert('quick_notes', {
            'session_id': session_id,
            'topic_id': topic_id,
            'content': content
        })

    def delete(self, note_id: int) -> int:
        """Удаляет быструю запись"""
        return db.delete('quick_notes', 'id = ?', (note_id,))

    def delete_by_session(self, session_id: int) -> int:
        """Удаляет все быстрые записи сессии"""
        return db.delete('quick_notes', 'session_id = ?', (session_id,))