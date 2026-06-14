# modules/tasks/filters.py
from typing import List, Optional
from datetime import datetime, date

from models.task import Task


class TaskFilters:
    """
    Класс для фильтрации задач по различным критериям.
    Использует паттерн Specification.
    """

    @staticmethod
    def filter_by_status(tasks: List[Task], status: Optional[str]) -> List[Task]:
        """Фильтрует задачи по статусу (active/completed/overdue)"""
        if not status or status == 'all':
            return tasks

        if status == 'overdue':
            return [t for t in tasks if t.is_overdue()]

        return [t for t in tasks if t.status == status]

    @staticmethod
    def filter_by_topic(tasks: List[Task], topic_id: Optional[int]) -> List[Task]:
        """Фильтрует задачи по теме"""
        if topic_id is None:
            return tasks

        if topic_id == -1:  # Общие задачи
            return [t for t in tasks if t.topic_id is None]

        return [t for t in tasks if t.topic_id == topic_id]

    @staticmethod
    def filter_by_deadline_range(
            tasks: List[Task],
            start_date: Optional[date] = None,
            end_date: Optional[date] = None
    ) -> List[Task]:
        """Фильтрует задачи по диапазону дедлайнов"""
        result = tasks

        if start_date:
            start_str = start_date.isoformat()
            result = [t for t in result if t.deadline and t.deadline[:10] >= start_str]

        if end_date:
            end_str = end_date.isoformat()
            result = [t for t in result if t.deadline and t.deadline[:10] <= end_str]

        return result

    @staticmethod
    def filter_by_search(tasks: List[Task], query: str) -> List[Task]:
        """Фильтрует задачи по поисковому запросу"""
        if not query:
            return tasks

        query_lower = query.lower()
        return [
            t for t in tasks
            if query_lower in t.title.lower() or
               query_lower in t.description.lower()
        ]

    @staticmethod
    def sort_by_deadline(tasks: List[Task], ascending: bool = True) -> List[Task]:
        """Сортирует задачи по дедлайну"""

        def get_key(task: Task):
            if not task.deadline:
                return '9999-12-31' if ascending else '0000-01-01'
            return task.deadline

        return sorted(tasks, key=get_key, reverse=not ascending)

    @staticmethod
    def sort_by_priority(tasks: List[Task]) -> List[Task]:
        """
        Сортирует задачи по приоритету:
        1. Просроченные
        2. Сегодня
        3. Завтра
        4. Остальные
        """
        today = date.today().isoformat()
        tomorrow = (date.today() + __import__('datetime').timedelta(days=1)).isoformat()

        def priority(task: Task) -> int:
            if task.status == 'completed':
                return 99
            if task.is_overdue():
                return 0
            if task.deadline and task.deadline[:10] == today:
                return 1
            if task.deadline and task.deadline[:10] == tomorrow:
                return 2
            return 3

        return sorted(tasks, key=priority)

    @staticmethod
    def get_statistics(tasks: List[Task]) -> dict:
        """Возвращает статистику по отфильтрованным задачам"""
        total = len(tasks)
        completed = sum(1 for t in tasks if t.status == 'completed')
        active = sum(1 for t in tasks if t.status == 'active')
        overdue = sum(1 for t in tasks if t.is_overdue())

        return {
            'total': total,
            'completed': completed,
            'active': active,
            'overdue': overdue,
            'completion_rate': round(completed / total * 100, 1) if total else 0
        }