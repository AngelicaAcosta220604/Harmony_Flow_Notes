# modules/tasks/controller.py
from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta
import logging

from datebase.repositories.task_repo import TaskRepository
from datebase.repositories.topic_repo import TopicRepository
from models.task import Task
from services.notification_service import NotificationService
from services.time_service import TimeService
from core.event_bus import event_bus

# Настройка логирования
logger = logging.getLogger(__name__)


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
        logger.debug("TaskController инициализирован")

    # ==================== Базовые CRUD операции ====================

    def get_all_tasks(self) -> List[Task]:
        """Возвращает все задачи"""
        try:
            rows = self._task_repo.get_all()
            return [Task.from_row(row) for row in rows]
        except Exception as e:
            logger.error(f"Ошибка получения всех задач: {e}", exc_info=True)
            return []

    def get_task(self, task_id: int) -> Optional[Task]:
        """Возвращает задачу по ID"""
        try:
            row = self._task_repo.get_by_id(task_id)
            return Task.from_row(row) if row else None
        except Exception as e:
            logger.error(f"Ошибка получения задачи {task_id}: {e}", exc_info=True)
            return None

    def get_tasks_by_topic(self, topic_id: int) -> List[Task]:
        """Возвращает задачи темы"""
        try:
            rows = self._task_repo.get_by_topic(topic_id)
            return [Task.from_row(row) for row in rows]
        except Exception as e:
            logger.error(f"Ошибка получения задач темы {topic_id}: {e}", exc_info=True)
            return []

    def get_general_tasks(self) -> List[Task]:
        """Возвращает общие задачи (без привязки к теме)"""
        try:
            rows = self._task_repo.get_general()
            return [Task.from_row(row) for row in rows]
        except Exception as e:
            logger.error(f"Ошибка получения общих задач: {e}", exc_info=True)
            return []

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
        try:
            if not title.strip():
                raise ValueError("Название задачи не может быть пустым")

            task_id = self._task_repo.create(title.strip(), description, topic_id, deadline)

            if task_id:
                event_bus.task_created.emit(task_id)
                logger.info(f"Создана задача '{title}' (id={task_id}, topic={topic_id})")
            else:
                logger.warning(f"Не удалось создать задачу '{title}'")

            return task_id
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Ошибка создания задачи '{title}': {e}", exc_info=True)
            return 0

    def update_task(self, task_id: int, **kwargs) -> bool:
        """Обновляет задачу"""
        try:
            allowed_fields = ['title', 'description', 'deadline', 'topic_id']
            updates = {k: v for k, v in kwargs.items() if k in allowed_fields and v is not None}

            if not updates:
                return True

            rows_affected = self._task_repo.update(task_id, **updates)
            if rows_affected > 0:
                event_bus.task_updated.emit(task_id)
                logger.debug(f"Задача {task_id} обновлена: {list(updates.keys())}")
            else:
                logger.warning(f"Не удалось обновить задачу {task_id}")
            return rows_affected > 0
        except Exception as e:
            logger.error(f"Ошибка обновления задачи {task_id}: {e}", exc_info=True)
            return False

    def delete_task(self, task_id: int) -> bool:
        """Удаляет задачу"""
        try:
            success = self._task_repo.delete(task_id)
            if success:
                event_bus.task_deleted.emit(task_id)
                logger.info(f"Удалена задача {task_id}")
            else:
                logger.warning(f"Не удалось удалить задачу {task_id}")
            return success
        except Exception as e:
            logger.error(f"Ошибка удаления задачи {task_id}: {e}", exc_info=True)
            return False

    def delete_tasks_by_topic(self, topic_id: int) -> int:
        """Удаляет все задачи темы"""
        try:
            deleted_count = self._task_repo.delete_by_topic(topic_id)
            logger.info(f"Удалено {deleted_count} задач из темы {topic_id}")
            return deleted_count
        except Exception as e:
            logger.error(f"Ошибка удаления задач темы {topic_id}: {e}", exc_info=True)
            return 0

    # ==================== Статусы задачи ====================

    def complete_task(self, task_id: int) -> bool:
        """Отмечает задачу выполненной"""
        try:
            task = self.get_task(task_id)
            if not task:
                logger.warning(f"Задача {task_id} не найдена для завершения")
                return False

            success = self._task_repo.complete(task_id)
            if success:
                event_bus.task_completed.emit(task_id)
                logger.info(f"Задача {task_id} отмечена выполненной")
            return success
        except Exception as e:
            logger.error(f"Ошибка завершения задачи {task_id}: {e}", exc_info=True)
            return False

    def reopen_task(self, task_id: int) -> bool:
        """Возвращает задачу в активный статус"""
        try:
            success = self._task_repo.update(task_id, status='active', completed_at=None)
            if success:
                logger.info(f"Задача {task_id} возвращена в активный статус")
            return success
        except Exception as e:
            logger.error(f"Ошибка переоткрытия задачи {task_id}: {e}", exc_info=True)
            return False

    def get_overdue_tasks(self) -> List[Task]:
        """Возвращает просроченные задачи"""
        try:
            rows = self._task_repo.get_overdue()
            tasks = [Task.from_row(row) for row in rows]

            # Отправляем уведомления о просроченных задачах
            if self._notification_service:
                for task in tasks:
                    try:
                        self._notification_service.show_task_reminder(
                            task.title,
                            task.deadline_display
                        )
                    except Exception as e:
                        logger.warning(f"Не удалось показать уведомление для задачи {task.id}: {e}")

            return tasks
        except Exception as e:
            logger.error(f"Ошибка получения просроченных задач: {e}", exc_info=True)
            return []

    def get_tasks_for_today(self) -> List[Task]:
        """Возвращает задачи с дедлайном на сегодня"""
        try:
            rows = self._task_repo.get_for_today()
            return [Task.from_row(row) for row in rows]
        except Exception as e:
            logger.error(f"Ошибка получения задач на сегодня: {e}", exc_info=True)
            return []

    def get_urgent_tasks(self, limit: int = 10) -> List[Task]:
        """
        Возвращает срочные задачи (просроченные + сегодня + завтра)
        Отсортированы по срочности
        """
        try:
            today = date.today()
            # ✅ ИСПРАВЛЕНО: используем timedelta вместо replace() — безопасно для любого дня месяца
            tomorrow = today + timedelta(days=1)

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
                    logger.warning(f"Неверный формат дедлайна для задачи {task.id}: {task.deadline}")
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
        except Exception as e:
            logger.error(f"Ошибка получения срочных задач: {e}", exc_info=True)
            return []

    # ==================== Статистика ====================

    def get_task_stats(self, topic_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Возвращает статистику по задачам

        Args:
            topic_id: Если указан, статистика только по теме, иначе по всем
        """
        try:
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
        except Exception as e:
            logger.error(f"Ошибка получения статистики задач: {e}", exc_info=True)
            return {
                'total': 0,
                'completed': 0,
                'active': 0,
                'overdue': 0,
                'completion_rate': 0
            }

    def get_completion_timeline(self, weeks: int = 12) -> Dict[str, List[int]]:
        """Возвращает динамику создания и выполнения задач по неделям"""
        try:
            tasks = self.get_all_tasks()
            return self._task_repo.get_task_timeline(tasks, weeks)
        except Exception as e:
            logger.error(f"Ошибка получения таймлайна задач: {e}", exc_info=True)
            return {'weeks': [], 'created': [], 'completed': []}

    # ==================== Поиск ====================

    def search_tasks(self, query: str) -> List[Task]:
        """Ищет задачи по названию"""
        try:
            rows = self._task_repo.search(query)
            return [Task.from_row(row) for row in rows]
        except Exception as e:
            logger.error(f"Ошибка поиска задач по запросу '{query}': {e}", exc_info=True)
            return []

    # ==================== Вспомогательные методы ====================

    def get_topic_name(self, task: Task) -> str:
        """Возвращает название темы задачи (или 'Общие')"""
        try:
            if not task.topic_id:
                return "Общие задачи"

            topic_row = self._topic_repo.get_by_id(task.topic_id)
            return topic_row['name'] if topic_row else "—"
        except Exception as e:
            logger.error(f"Ошибка получения названия темы для задачи {task.id}: {e}", exc_info=True)
            return "—"

    def get_deadline_display(self, task: Task) -> str:
        """Возвращает отформатированный дедлайн"""
        try:
            if not task.deadline:
                return "—"

            dt = datetime.fromisoformat(task.deadline)
            return dt.strftime("%d.%m.%Y %H:%M")
        except (ValueError, TypeError) as e:
            logger.warning(f"Неверный формат дедлайна для задачи {task.id}: {task.deadline}")
            return str(task.deadline) if task.deadline else "—"
        except Exception as e:
            logger.error(f"Ошибка форматирования дедлайна задачи {task.id}: {e}", exc_info=True)
            return "—"

    def is_deadline_today(self, task: Task) -> bool:
        """Проверяет, приходится ли дедлайн на сегодня"""
        try:
            if not task.deadline:
                return False

            today = date.today().isoformat()
            return task.deadline[:10] == today
        except Exception as e:
            logger.error(f"Ошибка проверки дедлайна задачи {task.id}: {e}", exc_info=True)
            return False