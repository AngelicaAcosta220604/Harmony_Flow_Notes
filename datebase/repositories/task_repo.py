# database/repositories/task_repo.py
from typing import List, Optional, Dict, Any
from datetime import datetime
from datebase.db_manager import db

class TaskRepository:
    """Репозиторий для работы с задачами"""

    def get_all(self) -> List[Dict[str, Any]]:
        """Возвращает все задачи"""
        return db.fetchall("SELECT * FROM tasks ORDER BY deadline ASC, created_at DESC")

    def get_by_id(self, task_id: int) -> Optional[Dict[str, Any]]:
        """Возвращает задачу по ID"""
        return db.fetchone("SELECT * FROM tasks WHERE id = ?", (task_id,))

    def get_by_topic(self, topic_id: int) -> List[Dict[str, Any]]:
        """Возвращает задачи темы"""
        return db.fetchall(
            "SELECT * FROM tasks WHERE topic_id = ? ORDER BY deadline ASC, created_at DESC",
            (topic_id,)
        )

    def get_by_topics(self, topic_ids: List[int], include_general: bool = False) -> List[Dict[str, Any]]:
        """Возвращает задачи для списка тем"""
        tasks = []

        if topic_ids:
            placeholders = ','.join('?' * len(topic_ids))
            tasks.extend(db.fetchall(
                f"SELECT * FROM tasks WHERE topic_id IN ({placeholders}) ORDER BY deadline ASC",
                tuple(topic_ids)
            ))

        if include_general:
            tasks.extend(db.fetchall(
                "SELECT * FROM tasks WHERE topic_id IS NULL ORDER BY deadline ASC"
            ))

        return tasks

    def get_general(self) -> List[Dict[str, Any]]:
        """Возвращает общие задачи (без привязки к теме)"""
        return db.fetchall("SELECT * FROM tasks WHERE topic_id IS NULL ORDER BY deadline ASC")

    def create(self, title: str, description: str = '', topic_id: Optional[int] = None,
               deadline: Optional[str] = None) -> int:
        """Создаёт новую задачу"""
        return db.insert('tasks', {
            'title': title,
            'description': description,
            'topic_id': topic_id,
            'deadline': deadline,
            'status': 'active'
        })

    def update(self, task_id: int, **kwargs) -> int:
        """Обновляет задачу"""
        allowed_fields = ['title', 'description', 'deadline', 'status', 'topic_id', 'completed_at']
        data = {k: v for k, v in kwargs.items() if k in allowed_fields}
        if not data:
            return 0
        return db.update('tasks', data, 'id = ?', (task_id,))

    def delete(self, task_id: int) -> int:
        """Удаляет задачу"""
        return db.delete('tasks', 'id = ?', (task_id,))

    def delete_by_topic(self, topic_id: int) -> int:
        """Удаляет все задачи темы"""
        return db.delete('tasks', 'topic_id = ?', (topic_id,))

    def complete(self, task_id: int, completed_at: Optional[str] = None) -> int:
        """Отмечает задачу выполненной"""
        if completed_at is None:
            completed_at = datetime.now().isoformat()
        return self.update(task_id, status='completed', completed_at=completed_at)

    def get_overdue(self) -> List[Dict[str, Any]]:
        """Возвращает просроченные активные задачи"""
        now = datetime.now().isoformat()
        return db.fetchall(
            "SELECT * FROM tasks WHERE status = 'active' AND deadline IS NOT NULL AND deadline < ? ORDER BY deadline ASC",
            (now,)
        )

    def get_for_today(self) -> List[Dict[str, Any]]:
        """Возвращает задачи с дедлайном на сегодня"""
        today = datetime.now().date().isoformat()
        tomorrow = datetime.now().replace(day=datetime.now().day + 1).date().isoformat()
        return db.fetchall(
            "SELECT * FROM tasks WHERE deadline >= ? AND deadline < ? ORDER BY deadline ASC",
            (today, tomorrow)
        )

    def search(self, query: str) -> List[Dict[str, Any]]:
        """Поиск задач по названию"""
        return db.fetchall(
            "SELECT * FROM tasks WHERE title LIKE ? ORDER BY deadline ASC",
            (f'%{query}%',)
        )