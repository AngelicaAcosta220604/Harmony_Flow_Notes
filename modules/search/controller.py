# modules/search/controller.py
from typing import List, Dict, Any, Optional
from datetime import datetime


from datebase.db_manager import db
from datebase.repositories.topic_repo import TopicRepository
from datebase.repositories.note_repo import NoteRepository
from datebase.repositories.flashcard_repo import FlashcardRepository
from datebase.repositories.task_repo import TaskRepository

class SearchController:
    """
    Контроллер для поиска по всем данным приложения.
    Поддерживает поиск по:
    - темам
    - заметкам (заголовок + содержимое)
    - задачам (название)
    - карточкам (содержимое, вопрос, ответ)
    """

    def __init__(
            self,
            topic_repo: TopicRepository,
            note_repo: NoteRepository,
            task_repo: TaskRepository,
            flashcard_repo: FlashcardRepository
    ):
        self._topic_repo = topic_repo
        self._note_repo = note_repo
        self._task_repo = task_repo
        self._flashcard_repo = flashcard_repo

    def search_all(self, query: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Выполняет поиск по всем типам данных

        Args:
            query: Поисковый запрос

        Returns:
            Словарь с результатами по категориям:
            {
                'topics': [...],
                'notes': [...],
                'tasks': [...],
                'flashcards': [...]
            }
        """
        if not query or len(query.strip()) < 2:
            return {
                'topics': [],
                'notes': [],
                'tasks': [],
                'flashcards': []
            }

        query_lower = query.strip().lower()

        return {
            'topics': self._search_topics(query_lower),
            'notes': self._search_notes(query_lower),
            'tasks': self._search_tasks(query_lower),
            'flashcards': self._search_flashcards(query_lower)
        }

    def _search_topics(self, query: str) -> List[Dict[str, Any]]:
        """Поиск по темам"""
        rows = self._topic_repo.search(query)

        results = []
        for row in rows:
            # Получаем путь к теме
            path = self._get_topic_path(row['id'])

            results.append({
                'id': row['id'],
                'title': row['name'],
                'type': 'topic',
                'icon': '📁' if row['type'] == 'folder' else '📚',
                'description': row.get('description', ''),
                'path': path,
                'created_at': row.get('created_at', '')
            })

        return results

    def _search_notes(self, query: str) -> List[Dict[str, Any]]:
        """Поиск по заметкам"""
        rows = self._note_repo.search(query)

        results = []
        for row in rows:
            # Находим тему
            topic = self._topic_repo.get_by_id(row['topic_id'])
            topic_name = topic['name'] if topic else "—"

            # Выделяем фрагмент с совпадением
            snippet = self._get_snippet(row.get('content', ''), query)

            results.append({
                'id': row['id'],
                'title': row['title'],
                'type': 'note',
                'icon': '📝',
                'topic_id': row['topic_id'],
                'topic_name': topic_name,
                'snippet': snippet,
                'updated_at': row.get('updated_at', '')
            })

        return results

    def _search_tasks(self, query: str) -> List[Dict[str, Any]]:
        """Поиск по задачам"""
        rows = self._task_repo.search(query)

        results = []
        for row in rows:
            # Находим тему
            topic_name = "Общие задачи"
            if row.get('topic_id'):
                topic = self._topic_repo.get_by_id(row['topic_id'])
                if topic:
                    topic_name = topic['name']

            # Статус и иконка
            status = row.get('status', 'active')
            if status == 'completed':
                icon = '✅'
                status_text = 'Выполнена'
            elif row.get('deadline') and self._is_overdue(row['deadline']):
                icon = '⚠️'
                status_text = 'Просрочена'
            else:
                icon = '⏳'
                status_text = 'Активна'

            results.append({
                'id': row['id'],
                'title': row['title'],
                'type': 'task',
                'icon': icon,
                'topic_id': row.get('topic_id'),
                'topic_name': topic_name,
                'status': status,
                'status_text': status_text,
                'deadline': row.get('deadline', ''),
                'created_at': row.get('created_at', '')
            })

        return results

    def _search_flashcards(self, query: str) -> List[Dict[str, Any]]:
        """Поиск по карточкам"""
        rows = self._flashcard_repo.search(query)

        results = []
        for row in rows:
            # Находим тему
            topic = self._topic_repo.get_by_id(row['topic_id'])
            topic_name = topic['name'] if topic else "—"

            card_type = row.get('type', 'free')
            if card_type == 'free':
                icon = '🃏'
                content = row.get('content', '')
                preview = content[:100] + '...' if len(content) > 100 else content
            else:
                icon = '❓'
                question = row.get('question', '')
                preview = question[:100] + '...' if len(question) > 100 else question

            results.append({
                'id': row['id'],
                'title': preview,
                'type': 'flashcard',
                'icon': icon,
                'card_type': card_type,
                'topic_id': row['topic_id'],
                'topic_name': topic_name,
                'question': row.get('question', ''),
                'answer': row.get('answer', ''),
                'content': row.get('content', ''),
                'created_at': row.get('created_at', '')
            })

        return results

    def _get_topic_path(self, topic_id: int) -> str:
        """Возвращает путь к теме"""
        path_parts = []
        current_id = topic_id

        while current_id:
            topic = self._topic_repo.get_by_id(current_id)
            if not topic:
                break
            path_parts.insert(0, topic['name'])
            current_id = topic.get('parent_id')

        return ' / '.join(path_parts) if path_parts else ''

    def _get_snippet(self, text: str, query: str, context_chars: int = 50) -> str:
        """Выделяет фрагмент текста с совпадением"""
        if not text:
            return ""

        text_lower = text.lower()
        query_lower = query.lower()

        pos = text_lower.find(query_lower)
        if pos == -1:
            return text[:100] + '...' if len(text) > 100 else text

        start = max(0, pos - context_chars)
        end = min(len(text), pos + len(query) + context_chars)

        snippet = text[start:end]

        if start > 0:
            snippet = "..." + snippet
        if end < len(text):
            snippet = snippet + "..."

        return snippet

    def _is_overdue(self, deadline: str) -> bool:
        """Проверяет, просрочен ли дедлайн"""
        from datetime import datetime
        try:
            deadline_date = datetime.fromisoformat(deadline)
            return datetime.now() > deadline_date
        except (ValueError, TypeError):
            return False

    def save_search_query(self, query: str):
        """Сохраняет поисковый запрос в историю"""
        if not query or len(query.strip()) < 2:
            return

        db.insert('search_history', {
            'query': query.strip()
        })

        # Оставляем только последние 50 записей
        db.execute(
            "DELETE FROM search_history WHERE id NOT IN (SELECT id FROM search_history ORDER BY created_at DESC LIMIT 50)")

    def get_search_history(self, limit: int = 10) -> List[str]:
        """Возвращает историю поисковых запросов"""
        rows = db.fetchall(
            "SELECT DISTINCT query FROM search_history ORDER BY created_at DESC LIMIT ?",
            (limit,)
        )
        return [row['query'] for row in rows]

    def clear_search_history(self):
        """Очищает историю поиска"""
        db.execute("DELETE FROM search_history")

    def get_result_count(self, results: Dict[str, List]) -> int:
        """Возвращает общее количество результатов"""
        return sum(len(results.get(category, [])) for category in ['topics', 'notes', 'tasks', 'flashcards'])