# modules/topics/controller.py
from typing import List, Optional, Dict, Any
import logging

from datebase.repositories.topic_repo import TopicRepository
from datebase.repositories.note_repo import NoteRepository
from datebase.repositories.task_repo import TaskRepository
from datebase.repositories.flashcard_repo import FlashcardRepository
from datebase.repositories.session_repo import SessionRepository
from models.topic import Topic
from models.note import Note
from models.task import Task
from models.flashcard import Flashcard
from models.session import Session
from core.event_bus import event_bus

# Настройка логирования
logger = logging.getLogger(__name__)


class TopicController:
    """
    Контроллер для управления темами и папками.
    Обеспечечивает CRUD операции и работу с деревом.
    """

    def __init__(
        self,
        topic_repo: TopicRepository,
        note_repo: NoteRepository = None,
        task_repo: TaskRepository = None,
        flashcard_repo: FlashcardRepository = None,
        session_repo: SessionRepository = None
    ):
        self._repo = topic_repo
        self._note_repo = note_repo
        self._task_repo = task_repo
        self._flashcard_repo = flashcard_repo
        self._session_repo = session_repo
        logger.debug("TopicController инициализирован")

    def get_all_topics(self) -> List[Topic]:
        """Возвращает все темы в виде объектов Topic"""
        try:
            rows = self._repo.get_all()
            return [Topic.from_row(row) for row in rows]
        except Exception as e:
            logger.error(f"Ошибка получения всех тем: {e}", exc_info=True)
            return []

    def get_topic(self, topic_id: int) -> Optional[Topic]:
        """Возвращает тему по ID"""
        try:
            row = self._repo.get_by_id(topic_id)
            return Topic.from_row(row) if row else None
        except Exception as e:
            logger.error(f"Ошибка получения темы {topic_id}: {e}", exc_info=True)
            return None

    def get_children(self, parent_id: Optional[int] = None) -> List[Topic]:
        """Возвращает дочерние элементы"""
        try:
            rows = self._repo.get_children(parent_id)
            return [Topic.from_row(row) for row in rows]
        except Exception as e:
            logger.error(f"Ошибка получения дочерних элементов для {parent_id}: {e}", exc_info=True)
            return []

    def get_tree_structure(self) -> List[Topic]:
        """
        Возвращает древовидную структуру тем.
        Строит иерархию, заполняя children каждого Topic.
        """
        try:
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

            logger.debug(f"Построена структура дерева: {len(roots)} корневых элементов")
            return roots
        except Exception as e:
            logger.error(f"Ошибка построения дерева тем: {e}", exc_info=True)
            return []

    def create_folder(self, name: str, parent_id: Optional[int] = None, description: str = "") -> int:
        """Создаёт новую папку"""
        try:
            folder_id = self._repo.create(name, 'folder', parent_id, description)
            if folder_id:
                event_bus.topic_created.emit(folder_id)
                logger.info(f"Создана папка '{name}' (id={folder_id}, parent={parent_id})")
            else:
                logger.warning(f"Не удалось создать папку '{name}'")
            return folder_id
        except Exception as e:
            logger.error(f"Ошибка создания папки '{name}': {e}", exc_info=True)
            return 0

    def create_topic(self, name: str, parent_id: Optional[int] = None, description: str = "") -> int:
        """Создаёт новую тему"""
        try:
            topic_id = self._repo.create(name, 'topic', parent_id, description)
            if topic_id:
                event_bus.topic_created.emit(topic_id)
                logger.info(f"Создана тема '{name}' (id={topic_id}, parent={parent_id})")
            else:
                logger.warning(f"Не удалось создать тему '{name}'")
            return topic_id
        except Exception as e:
            logger.error(f"Ошибка создания темы '{name}': {e}", exc_info=True)
            return 0

    def update_topic(self, topic_id: int, **kwargs) -> bool:
        """Обновляет тему/папку"""
        try:
            rows_affected = self._repo.update(topic_id, **kwargs)
            success = rows_affected > 0
            if success:
                logger.debug(f"Тема {topic_id} обновлена: {kwargs}")
            else:
                logger.warning(f"Не удалось обновить тему {topic_id}")
            return success
        except Exception as e:
            logger.error(f"Ошибка обновления темы {topic_id}: {e}", exc_info=True)
            return False

    def rename(self, topic_id: int, new_name: str) -> bool:
        """Переименовывает тему/папку"""
        try:
            success = self.update_topic(topic_id, name=new_name)
            if success:
                # ✅ ИСПРАВЛЕНО: используем topic_updated вместо topic_created
                event_bus.topic_updated.emit(topic_id)
                logger.info(f"Тема {topic_id} переименована в '{new_name}'")
            return success
        except Exception as e:
            logger.error(f"Ошибка переименования темы {topic_id}: {e}", exc_info=True)
            return False

    def move(self, topic_id: int, new_parent_id: Optional[int]) -> bool:
        """
        Перемещает тему/папку в другое место.
        Проверяет, что не пытаемся переместить в самого себя или потомка.
        """
        try:
            # Проверка на циклическую ссылку
            if new_parent_id is not None:
                # Нельзя переместить в самого себя
                if topic_id == new_parent_id:
                    logger.warning(f"Попытка переместить тему {topic_id} в саму себя")
                    return False

                # Нельзя переместить в потомка
                descendants = self._repo.get_descendants_ids(topic_id)
                if new_parent_id in descendants:
                    logger.warning(f"Попытка переместить тему {topic_id} в потомка {new_parent_id}")
                    return False

            success = self.update_topic(topic_id, parent_id=new_parent_id)
            if success:
                # ✅ ИСПРАВЛЕНО: используем topic_updated вместо topic_created
                event_bus.topic_updated.emit(topic_id)
                logger.info(f"Тема {topic_id} перемещена в parent={new_parent_id}")
            return success
        except Exception as e:
            logger.error(f"Ошибка перемещения темы {topic_id}: {e}", exc_info=True)
            return False

    def delete(self, topic_id: int) -> bool:
        """
        Удаляет тему/папку и все связанные данные.
        Возвращает True если успешно.
        """
        try:
            topic = self.get_topic(topic_id)
            if not topic:
                logger.warning(f"Тема {topic_id} не найдена для удаления")
                return False

            rows_affected = self._repo.delete(topic_id)
            if rows_affected > 0:
                event_bus.topic_deleted.emit(topic_id)
                logger.info(f"Удалена тема {topic_id} ('{topic.name}')")
                return True
            else:
                logger.warning(f"Не удалось удалить тему {topic_id}")
            return False
        except Exception as e:
            logger.error(f"Ошибка удаления темы {topic_id}: {e}", exc_info=True)
            return False

    def get_topic_count(self) -> int:
        """Возвращает количество тем (не папок)"""
        try:
            all_topics = self.get_all_topics()
            return sum(1 for t in all_topics if t.is_topic)
        except Exception as e:
            logger.error(f"Ошибка подсчета тем: {e}", exc_info=True)
            return 0

    def get_folder_count(self) -> int:
        """Возвращает количество папок"""
        try:
            all_topics = self.get_all_topics()
            return sum(1 for t in all_topics if t.is_folder)
        except Exception as e:
            logger.error(f"Ошибка подсчета папок: {e}", exc_info=True)
            return 0

    def search(self, query: str) -> List[Topic]:
        """Поиск тем по названию"""
        try:
            rows = self._repo.search(query)
            return [Topic.from_row(row) for row in rows]
        except Exception as e:
            logger.error(f"Ошибка поиска тем по запросу '{query}': {e}", exc_info=True)
            return []

    def get_path(self, topic_id: int) -> List[Topic]:
        """
        Возвращает путь от корня до указанной темы.
        """
        try:
            path = []
            current = self.get_topic(topic_id)

            while current:
                path.insert(0, current)
                if current.parent_id:
                    current = self.get_topic(current.parent_id)
                else:
                    current = None

            return path
        except Exception as e:
            logger.error(f"Ошибка получения пути для темы {topic_id}: {e}", exc_info=True)
            return []

    def get_path_string(self, topic_id: int, separator: str = " / ") -> str:
        """Возвращает путь в виде строки"""
        try:
            path = self.get_path(topic_id)
            return separator.join([t.name for t in path])
        except Exception as e:
            logger.error(f"Ошибка получения строки пути для темы {topic_id}: {e}", exc_info=True)
            return ""

    def get_all_descendants_ids(self, topic_id: int) -> List[int]:
        """Возвращает ID всех потомков темы"""
        try:
            return self._repo.get_descendants_ids(topic_id)
        except Exception as e:
            logger.error(f"Ошибка получения потомков темы {topic_id}: {e}", exc_info=True)
            return []

    def get_notes_by_topic(self, topic_id: int) -> List[Note]:
        """Возвращает заметки темы"""
        try:
            if not self._note_repo:
                return []
            rows = self._note_repo.get_by_topic(topic_id)
            return [Note.from_row(row) for row in rows]
        except Exception as e:
            logger.error(f"Ошибка получения заметок темы {topic_id}: {e}", exc_info=True)
            return []

    def get_tasks_by_topic(self, topic_id: int) -> List[Task]:
        """Возвращает задачи темы"""
        try:
            if not self._task_repo:
                return []
            rows = self._task_repo.get_by_topic(topic_id)
            return [Task.from_row(row) for row in rows]
        except Exception as e:
            logger.error(f"Ошибка получения задач темы {topic_id}: {e}", exc_info=True)
            return []

    def get_cards_by_topic(self, topic_id: int) -> List[Flashcard]:
        """Возвращает карточки темы"""
        try:
            if not self._flashcard_repo:
                return []
            rows = self._flashcard_repo.get_by_topic(topic_id)
            return [Flashcard.from_row(row) for row in rows]
        except Exception as e:
            logger.error(f"Ошибка получения карточек темы {topic_id}: {e}", exc_info=True)
            return []

    def get_sessions_by_topic(self, topic_id: int) -> List[Session]:
        """Возвращает сессии темы"""
        try:
            if not self._session_repo:
                return []
            rows = self._session_repo.get_by_topic(topic_id)
            return [Session.from_row(row) for row in rows]
        except Exception as e:
            logger.error(f"Ошибка получения сессий темы {topic_id}: {e}", exc_info=True)
            return []

    def get_note_by_id(self, note_id: int) -> Optional[Note]:
        """Возвращает заметку по ID"""
        try:
            if not self._note_repo:
                return None
            row = self._note_repo.get_by_id(note_id)
            return Note.from_row(row) if row else None
        except Exception as e:
            logger.error(f"Ошибка получения заметки {note_id}: {e}", exc_info=True)
            return None