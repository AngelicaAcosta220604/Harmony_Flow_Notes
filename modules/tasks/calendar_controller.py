# modules/tasks/calendar_controller.py
from typing import List, Dict, Any, Optional
from datetime import datetime, date, timedelta

from .controller import TaskController
from models.task import Task


class CalendarController:
    """
    Контроллер для календаря задач.
    Предоставляет задачи для отображения по дням/неделям/месяцам.
    """

    def __init__(self, task_controller: TaskController):
        self._task_controller = task_controller

    def get_tasks_for_day(self, target_date: date) -> List[Task]:
        """Возвращает задачи на указанный день"""
        target_str = target_date.isoformat()

        all_tasks = self._task_controller.get_all_tasks()
        result = []

        for task in all_tasks:
            if task.status == 'completed':
                continue

            if not task.deadline:
                continue

            if task.deadline[:10] == target_str:
                result.append(task)

        return result

    def get_tasks_for_week(self, start_date: date) -> Dict[str, List[Task]]:
        """
        Возвращает задачи на неделю, начиная с start_date

        Returns:
            Словарь {день_в_формате_YYYY-MM-DD: [задачи]}
        """
        result = {}

        for i in range(7):
            current_date = start_date + timedelta(days=i)
            date_str = current_date.isoformat()
            result[date_str] = self.get_tasks_for_day(current_date)

        return result

    def get_tasks_for_month(self, year: int, month: int) -> Dict[str, List[Task]]:
        """Возвращает задачи на месяц"""
        result = {}

        # Первый день месяца
        first_day = date(year, month, 1)

        # Последний день месяца
        if month == 12:
            last_day = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            last_day = date(year, month + 1, 1) - timedelta(days=1)

        current = first_day
        while current <= last_day:
            date_str = current.isoformat()
            tasks = self.get_tasks_for_day(current)
            if tasks:
                result[date_str] = tasks
            current += timedelta(days=1)

        return result

    def get_tasks_for_range(self, start_date: date, end_date: date) -> Dict[str, List[Task]]:
        """Возвращает задачи за период"""
        result = {}

        current = start_date
        while current <= end_date:
            date_str = current.isoformat()
            tasks = self.get_tasks_for_day(current)
            if tasks:
                result[date_str] = tasks
            current += timedelta(days=1)

        return result

    def get_upcoming_tasks(self, days: int = 7) -> List[Task]:
        """Возвращает задачи на ближайшие N дней"""
        today = date.today()
        end_date = today + timedelta(days=days)

        all_tasks = self._task_controller.get_all_tasks()
        result = []

        for task in all_tasks:
            if task.status == 'completed':
                continue

            if not task.deadline:
                continue

            try:
                deadline_date = datetime.fromisoformat(task.deadline).date()
                if today <= deadline_date <= end_date:
                    result.append(task)
            except (ValueError, TypeError):
                continue

        # Сортируем по дате
        result.sort(key=lambda x: x.deadline or '')

        return result

    def has_tasks_on_date(self, target_date: date) -> bool:
        """Проверяет, есть ли задачи на указанную дату"""
        return len(self.get_tasks_for_day(target_date)) > 0

    def get_task_count_for_month(self, year: int, month: int) -> Dict[str, int]:
        """
        Возвращает количество задач по дням месяца
        (для отображения маркеров в календаре)
        """
        result = {}

        first_day = date(year, month, 1)

        if month == 12:
            last_day = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            last_day = date(year, month + 1, 1) - timedelta(days=1)

        current = first_day
        while current <= last_day:
            count = len(self.get_tasks_for_day(current))
            if count > 0:
                result[current.isoformat()] = count
            current += timedelta(days=1)

        return result

    def refresh(self):
        """Обновляет календарь и список задач"""
        self._load_tasks()  # или как у вас называется метод загрузки задач
        self._highlight_deadline_dates()  # если есть такой метод