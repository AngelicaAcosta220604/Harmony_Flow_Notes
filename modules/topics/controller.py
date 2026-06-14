# modules/topics/controller.py
from typing import List, Optional, Dict, Any
from datebase.repositories.topic_repo import TopicRepository
from models.topic import Topic


class TopicController:
    """
    Контроллер для управления темами и папками.
    Обеспечивает CRUD операции и работу с деревом.
    """

    def __init__(self, topic_repo: TopicRepository):
        self._repo = topic_repo

    def get_all_topics(self) -> List[Topic]:
        """Возвращает все темы в виде объектов Topic"""
        rows = self._repo.get_all()
        return [Topic.from_row(row) for row in rows]

    def get_topic(self, topic_id: int) -> Optional[Topic]:
        """Возвращает тему по ID"""
        row = self._repo.get_by_id(topic_id)
        return Topic.from_row(row) if row else None

    def get_children(self, parent_id: Optional[int] = None) -> List[Topic]:
        """Возвращает дочерние элементы"""
        rows = self._repo.get_children(parent_id)
        return [Topic.from_row(row) for row in rows]

    def get_tree_structure(self) -> List[Topic]:
        """
        Возвращает древовидную структуру тем.
        Строит иерархию, заполняя children каждого Topic.
        """
        all_topics = self.get_all_topics()

        # Создаём словарь для быстрого доступа
        topics_dict: Dict[int, Topic] = {t.id: t for t in all_topics}

        # Строим дерево
        roots = []
        for topic in all_topics:
            if topic.parent_id is None:
                roots.append(topic)
            else:
                parent = topics_dict.get(topic.parent_id)
                if parent:
                    parent.children.append(topic)

        return roots

    def create_folder(self, name: str, parent_id: Optional[int] = None, description: str = "") -> int:
        """Создаёт новую папку"""
        return self._repo.create(name, 'folder', parent_id, description)

    def create_topic(self, name: str, parent_id: Optional[int] = None, description: str = "") -> int:
        """Создаёт новую тему"""
        return self._repo.create(name, 'topic', parent_id, description)

    def update_topic(self, topic_id: int, **kwargs) -> bool:
        """Обновляет тему/папку"""
        rows_affected = self._repo.update(topic_id, **kwargs)
        return rows_affected > 0

    def rename(self, topic_id: int, new_name: str) -> bool:
        """Переименовывает тему/папку"""
        return self.update_topic(topic_id, name=new_name)

    def move(self, topic_id: int, new_parent_id: Optional[int]) -> bool:
        """
        Перемещает тему/папку в другое место.
        Проверяет, что не пытаемся переместить в самого себя или потомка.
        """
        # Проверка на циклическую ссылку
        if new_parent_id is not None:
            # Нельзя переместить в самого себя
            if topic_id == new_parent_id:
                return False

            # Нельзя переместить в потомка
            descendants = self._repo.get_descendants_ids(topic_id)
            if new_parent_id in descendants:
                return False

        return self.update_topic(topic_id, parent_id=new_parent_id)

    def delete(self, topic_id: int) -> bool:
        """
        Удаляет тему/папку и все связанные данные.
        Возвращает True если успешно.
        """
        # Проверяем, существует ли тема
        topic = self.get_topic(topic_id)
        if not topic:
            return False

        rows_affected = self._repo.delete(topic_id)
        return rows_affected > 0

    def get_topic_count(self) -> int:
        """Возвращает количество тем (не папок)"""
        all_topics = self.get_all_topics()
        return sum(1 for t in all_topics if t.is_topic)

    def get_folder_count(self) -> int:
        """Возвращает количество папок"""
        all_topics = self.get_all_topics()
        return sum(1 for t in all_topics if t.is_folder)

    def search(self, query: str) -> List[Topic]:
        """Поиск тем по названию"""
        rows = self._repo.search(query)
        return [Topic.from_row(row) for row in rows]

    def get_path(self, topic_id: int) -> List[Topic]:
        """
        Возвращает путь от корня до указанной темы.
        """
        path = []
        current = self.get_topic(topic_id)

        while current:
            path.insert(0, current)
            if current.parent_id:
                current = self.get_topic(current.parent_id)
            else:
                current = None

        return path

    def get_path_string(self, topic_id: int, separator: str = " / ") -> str:
        """Возвращает путь в виде строки"""
        path = self.get_path(topic_id)
        return separator.join([t.name for t in path])

    def get_all_descendants_ids(self, topic_id: int) -> List[int]:
        """Возвращает ID всех потомков темы"""
        return self._repo.get_descendants_ids(topic_id)