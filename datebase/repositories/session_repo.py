# database/repositories/session_repo.py
from typing import List, Optional, Dict, Any
from datetime import datetime
from datebase.db_manager import db


class SessionRepository:
    """Репозиторий для работы с сессиями"""

    def get_all(self) -> List[Dict[str, Any]]:
        """Возвращает все сессии"""
        return db.fetchall("SELECT * FROM sessions ORDER BY start_time DESC")

    def get_by_id(self, session_id: int) -> Optional[Dict[str, Any]]:
        """Возвращает сессию по ID"""
        return db.fetchone("SELECT * FROM sessions WHERE id = ?", (session_id,))

    def get_by_topic(self, topic_id: int) -> List[Dict[str, Any]]:
        """Возвращает сессии темы"""
        return db.fetchall(
            "SELECT * FROM sessions WHERE topic_id = ? ORDER BY start_time DESC",
            (topic_id,)
        )

    def get_by_topics(self, topic_ids: List[int]) -> List[Dict[str, Any]]:
        """Возвращает сессии для списка тем"""
        if not topic_ids:
            return []
        placeholders = ','.join('?' * len(topic_ids))
        return db.fetchall(
            f"SELECT * FROM sessions WHERE topic_id IN ({placeholders}) ORDER BY start_time DESC",
            tuple(topic_ids)
        )

    def create(self, topic_id: int) -> int:
        now = datetime.now().isoformat()
        return db.insert('sessions', {
            'topic_id': topic_id,
            'start_time': now,
            'status': 'active'
        })

    def update(self, session_id: int, **kwargs) -> int:
        """Обновляет сессию"""
        allowed_fields = ['end_time', 'duration_minutes', 'status']
        data = {k: v for k, v in kwargs.items() if k in allowed_fields}
        if not data:
            return 0
        return db.update('sessions', data, 'id = ?', (session_id,))

    def end_session(self, session_id: int, duration_minutes: int, status: str = 'completed') -> int:
        now = datetime.now().isoformat()
        return self.update(session_id, end_time=now, duration_minutes=duration_minutes, status=status)

    def delete(self, session_id: int) -> int:
        """Удаляет сессию (каскадно удалятся все связанные данные)"""
        return db.delete('sessions', 'id = ?', (session_id,))

    def delete_by_topic(self, topic_id: int) -> int:
        """Удаляет все сессии темы"""
        return db.delete('sessions', 'topic_id = ?', (topic_id,))

    def get_active(self) -> Optional[Dict[str, Any]]:
        """Возвращает активную сессию (если есть)"""
        return db.fetchone("SELECT * FROM sessions WHERE status = 'active' LIMIT 1")

    def get_recent(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Возвращает последние сессии"""
        return db.fetchall(
            "SELECT * FROM sessions ORDER BY start_time DESC LIMIT ?",
            (limit,)
        )