# modules/tasks/controller.py
from typing import List, Optional, Dict, Any
from datetime import datetime, date

from datebase.repositories.task_repo import TaskRepository
from datebase.repositories.topic_repo import TopicRepository
from models.task import Task
from services.notification_service import NotificationService
from services.time_service import TimeService


class TaskController:
    """
    Контроллер для управления задачами.
    Обеспечивает CRUD операции, фильтрацию, работу с дедлайнами.
    Написан по SOLID принципам.
    """

    def __init__(
            self,
            task_repo: TaskRepository,
            topic_repo: TopicRepository,
            notification_service: NotificationService = None
    ):
        self._task_repo = task_repo
        self._topic_repo = topic_repo
        self._notification_service = notification_service

    # ==================== Базовые CRUD операции ====================

    def get_all_tasks(self) -> List[Task]:
        """Возвращает все задачи"""
        rows = self._task_repo.get_all()
        return [Task.from_row(row) for row in rows]

    def get_task(self, task_id: int) -> Optional[Task]:
        """Возвращает задачу по ID"""
        row = self._task_repo.get_by_id(task_id)
        return Task.from_row(row) if row else None

    def get_tasks_by_topic(self, topic_id: int) -> List[Task]:
        """Возвращает задачи темы"""
        rows = self._task_repo.get_by_topic(topic_id)
        return [Task.from_row(row) for row in rows]

    def get_general_tasks(self) -> List[Task]:
        """Возвращает общие задачи (без привязки к теме)"""
        rows = self._task_repo.get_general()
        return [Task.from_row(row) for row in rows]

    def create_task(
            self,
            title: str,
            description: str = "",
            topic_id: Optional[int] = None,
            deadline: Optional[str] = None
    ) -> int:
        """
        Создаёт новую задачу и эмитит сигнал
        """
        if not title.strip():
            raise ValueError("Название задачи не может быть пустым")

        task_id = self._task_repo.create(title.strip(), description, topic_id, deadline)

        # 🆕 Эмитим сигнал создания задачи
        if task_id:
            from core.event_bus import event_bus
            event_bus.task_created.emit(task_id)

        return task_id

    def update_task(self, task_id: int, **kwargs) -> bool:
        """Обновляет задачу"""
        allowed_fields = ['title', 'description', 'deadline', 'topic_id']
        updates = {k: v for k, v in kwargs.items() if k in allowed_fields and v is not None}

        if not updates:
            return True

        rows_affected = self._task_repo.update(task_id, **updates)
        return rows_affected > 0

    def delete_task(self, task_id: int) -> bool:
        """Удаляет задачу"""
        success = self._task_repo.delete(task_id)
        if success:
            from core.event_bus import event_bus
            event_bus.task_deleted.emit(task_id)
        return success

    def delete_tasks_by_topic(self, topic_id: int) -> int:
        """Удаляет все задачи темы"""
        return self._task_repo.delete_by_topic(topic_id)

    # ==================== Статусы задачи ====================

    def complete_task(self, task_id: int) -> bool:
        """Отмечает задачу выполненной"""
        task = self.get_task(task_id)
        if not task:
            return False

        return self._task_repo.complete(task_id)

    def reopen_task(self, task_id: int) -> bool:
        """Возвращает задачу в активный статус"""
        return self._task_repo.update(task_id, status='active', completed_at=None)

    def get_overdue_tasks(self) -> List[Task]:
        """Возвращает просроченные задачи"""
        rows = self._task_repo.get_overdue()
        tasks = [Task.from_row(row) for row in rows]

        # Отправляем уведомления о просроченных задачах
        if self._notification_service:
            for task in tasks:
                self._notification_service.show_task_reminder(
                    task.title,
                    task.deadline_display
                )

        return tasks

    def get_tasks_for_today(self) -> List[Task]:
        """Возвращает задачи с дедлайном на сегодня"""
        rows = self._task_repo.get_for_today()
        return [Task.from_row(row) for row in rows]

    def get_urgent_tasks(self, limit: int = 10) -> List[Task]:
        """
        Возвращает срочные задачи (просроченные + сегодня + завтра)
        Отсортированы по срочности
        """
        today = date.today()
        tomorrow = today.replace(day=today.day + 1)

        all_tasks = self.get_all_tasks()
        urgent = []

        for task in all_tasks:
            if task.status == 'completed':
                continue

            if not task.deadline:
                continue

            try:
                deadline_date = datetime.fromisoformat(task.deadline).date()
            except (ValueError, TypeError):
                continue

            is_overdue = deadline_date < today
            is_today = deadline_date == today
            is_tomorrow = deadline_date == tomorrow

            if is_overdue or is_today or is_tomorrow:
                task._is_overdue_flag = is_overdue
                urgent.append(task)

        # Сортировка: сначала просроченные, потом сегодня, потом завтра
        urgent.sort(key=lambda x: (
            0 if getattr(x, '_is_overdue_flag', False) else
            (1 if x.deadline and x.deadline[:10] == today.isoformat() else 2),
            x.deadline or ''
        ))

        return urgent[:limit]

    # ==================== Статистика ====================

    def get_task_stats(self, topic_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Возвращает статистику по задачам

        Args:
            topic_id: Если указан, статистика только по теме, иначе по всем
        """
        if topic_id:
            tasks = self.get_tasks_by_topic(topic_id)
        else:
            tasks = self.get_all_tasks()

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

    def get_completion_timeline(self, weeks: int = 12) -> Dict[str, List[int]]:
        """Возвращает динамику создания и выполнения задач по неделям"""
        tasks = self.get_all_tasks()
        return self._task_repo.get_task_timeline(tasks, weeks)

    # ==================== Поиск ====================

    def search_tasks(self, query: str) -> List[Task]:
        """Ищет задачи по названию"""
        rows = self._task_repo.search(query)
        return [Task.from_row(row) for row in rows]

    # ==================== Вспомогательные методы ====================

    def get_topic_name(self, task: Task) -> str:
        """Возвращает название темы задачи (или 'Общие')"""
        if not task.topic_id:
            return "Общие задачи"

        topic_row = self._topic_repo.get_by_id(task.topic_id)
        return topic_row['name'] if topic_row else "—"

    def get_deadline_display(self, task: Task) -> str:
        """Возвращает отформатированный дедлайн"""
        if not task.deadline:
            return "—"

        dt = datetime.fromisoformat(task.deadline)
        return dt.strftime("%d.%m.%Y %H:%M")

    def is_deadline_today(self, task: Task) -> bool:
        """Проверяет, приходится ли дедлайн на сегодня"""
        if not task.deadline:
            return False

        today = date.today().isoformat()
        return task.deadline[:10] == today