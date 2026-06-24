# database/repositories/topic_repo.py
from typing import List, Optional, Dict, Any
from database.db_manager import db


class TopicRepository:
    """Репозиторий для работы с темами и папками"""

    def get_all(self) -> List[Dict[str, Any]]:
        """Возвращает все темы"""
        return db.fetchall("SELECT * FROM topics ORDER BY created_at")

    def get_by_id(self, topic_id: int) -> Optional[Dict[str, Any]]:
        """Возвращает тему по ID"""
        return db.fetchone("SELECT * FROM topics WHERE id = ?", (topic_id,))

    def get_children(self, parent_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Возвращает дочерние элементы для указанного parent_id"""
        if parent_id is None:
            return db.fetchall("SELECT * FROM topics WHERE parent_id IS NULL")
        return db.fetchall("SELECT * FROM topics WHERE parent_id = ?", (parent_id,))

    def get_tree(self) -> List[Dict[str, Any]]:
        """Возвращает все темы, отсортированные для отображения дерева"""
        return db.fetchall("SELECT * FROM topics ORDER BY parent_id NULLS FIRST, created_at")

    def create(self, name: str, topic_type: str = 'topic', parent_id: Optional[int] = None,
               description: str = '') -> int:
        """Создаёт новую тему/папку"""
        return db.insert('topics', {
            'name': name,
            'description': description,
            'parent_id': parent_id,
            'type': topic_type
        })

    def update(self, topic_id: int, **kwargs) -> int:
        """Обновляет тему"""
        allowed_fields = ['name', 'description', 'parent_id', 'type']
        data = {k: v for k, v in kwargs.items() if k in allowed_fields}
        if not data:
            return 0
        return db.update('topics', data, 'id = ?', (topic_id,))

    def delete(self, topic_id: int) -> int:
        """Удаляет тему (каскадно удалятся все связанные данные)"""
        return db.delete('topics', 'id = ?', (topic_id,))

    def get_descendants_ids(self, topic_id: int) -> List[int]:
        """Возвращает ID всех потомков темы (рекурсивно)"""
        # SQLite с рекурсивным CTE
        query = """
            WITH RECURSIVE descendants AS (
                SELECT id FROM topics WHERE id = ?
                UNION ALL
                SELECT t.id FROM topics t
                INNER JOIN descendants d ON t.parent_id = d.id
            )
            SELECT id FROM descendants WHERE id != ?
        """
        rows = db.fetchall(query, (topic_id, topic_id))
        return [row['id'] for row in rows]

    def search(self, query: str) -> List[Dict[str, Any]]:
        """Поиск тем по названию"""
        return db.fetchall(
            "SELECT * FROM topics WHERE name LIKE ? ORDER BY name",
            (f'%{query}%',)
        )