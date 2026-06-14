# modules/dashboard/controller.py
from typing import List, Dict, Any, Optional
from datetime import datetime, date

from datebase.repositories import (
TopicRepository,
TaskRepository,
SessionRepository,
NoteRepository,
FlashcardRepository,
SettingsRepository
)

from datebase.db_manager import db

from models.task import Task
from models.session import Session
from services.time_service import TimeService


class DashboardController:
    """
    Контроллер для главного экрана (Dashboard)
    Собирает данные из разных репозиториев.
    """

    def __init__(
            self,
            topic_repo: TopicRepository,
            task_repo: TaskRepository,
            session_repo: SessionRepository,
            note_repo: NoteRepository,
            flashcard_repo: FlashcardRepository,
            settings_repo: SettingsRepository
    ):
        self._topic_repo = topic_repo
        self._task_repo = task_repo
        self._session_repo = session_repo
        self._note_repo = note_repo
        self._flashcard_repo = flashcard_repo
        self._settings_repo = settings_repo

    def get_user_name(self) -> str:
        """Возвращает имя пользователя из настроек"""
        return self._settings_repo.get_user_name()

    def get_greeting(self) -> str:
        """Возвращает приветствие в зависимости от времени суток"""
        hour = datetime.now().hour

        if 5 <= hour < 12:
            return "Доброе утро"
        elif 12 <= hour < 18:
            return "Добрый день"
        elif 18 <= hour < 23:
            return "Добрый вечер"
        else:
            return "Доброй ночи"

    def get_today_stats(self) -> Dict[str, Any]:
        """
        Возвращает статистику за сегодня:
        - количество выполненных задач
        - отработанное время (минуты)
        """
        today = date.today().isoformat()

        # Задачи, выполненные сегодня
        tasks = self._task_repo.get_all()
        completed_today = 0
        for task in tasks:
            if task.get('completed_at'):
                completed_date = task['completed_at'][:10]
                if completed_date == today:
                    completed_today += 1

        # Сессии за сегодня
        all_sessions = self._session_repo.get_all()
        today_minutes = 0
        for session in all_sessions:
            if session.get('start_time'):
                session_date = session['start_time'][:10]
                if session_date == today and session.get('duration_minutes'):
                    today_minutes += session['duration_minutes'] or 0

        return {
            'completed_tasks_today': completed_today,
            'worked_minutes_today': today_minutes,
            'worked_hours_today': round(today_minutes / 60, 1)
        }

    def get_active_topic(self) -> Optional[Dict[str, Any]]:
        """
        Возвращает последнюю использованную тему
        (по последней сессии или последней заметке)
        """
        # Ищем последнюю сессию
        sessions = self._session_repo.get_all()
        if sessions:
            last_session = sessions[0]  # уже отсортированы по start_time DESC
            topic_id = last_session.get('topic_id')
            if topic_id:
                topic = self._topic_repo.get_by_id(topic_id)
                if topic:
                    topic['last_activity'] = last_session.get('start_time')
                    return topic

        # Если сессий нет, ищем последнюю заметку
        notes = self._note_repo.get_recent(1)
        if notes:
            topic_id = notes[0].get('topic_id')
            if topic_id:
                topic = self._topic_repo.get_by_id(topic_id)
                if topic:
                    topic['last_activity'] = notes[0].get('updated_at')
                    return topic

        return None

    def get_last_session(self) -> Optional[Dict[str, Any]]:
        """Возвращает последнюю сессию с аналитикой"""
        sessions = self._session_repo.get_all()
        if not sessions:
            return None

        last_session = sessions[0]

        # Получаем логи состояния для этой сессии
        logs = db.fetchall(
            "SELECT metric, value FROM session_state_logs WHERE session_id = ?",
            (last_session['id'],)
        )

        conc_values = [log['value'] for log in logs if log['metric'] == 'concentration']
        energy_values = [log['value'] for log in logs if log['metric'] == 'energy']

        avg_concentration = sum(conc_values) / len(conc_values) if conc_values else 0
        avg_energy = sum(energy_values) / len(energy_values) if energy_values else 0

        # Получаем название темы
        topic_name = "—"
        if last_session.get('topic_id'):
            topic = self._topic_repo.get_by_id(last_session['topic_id'])
            if topic:
                topic_name = topic['name']

        return {
            'id': last_session['id'],
            'topic_name': topic_name,
            'duration_minutes': last_session.get('duration_minutes') or 0,
            'duration_display': TimeService.format_duration(last_session.get('duration_minutes') or 0),
            'avg_concentration': round(avg_concentration, 1),
            'avg_energy': round(avg_energy, 1),
            'start_time': last_session.get('start_time')
        }

    def get_urgent_tasks(self, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Возвращает срочные задачи:
        - просроченные (красные)
        - с дедлайном сегодня/завтра
        """
        now = datetime.now()
        today = now.date()
        tomorrow = today.replace(day=today.day + 1)

        all_tasks = self._task_repo.get_all()
        urgent = []

        for task in all_tasks:
            if task.get('status') == 'completed':
                continue

            task_deadline = task.get('deadline')
            if not task_deadline:
                continue

            try:
                deadline_date = datetime.fromisoformat(task_deadline).date()
            except (ValueError, TypeError):
                continue

            is_overdue = deadline_date < today
            is_today = deadline_date == today
            is_tomorrow = deadline_date == tomorrow

            if is_overdue or is_today or is_tomorrow:
                # Получаем название темы
                topic_name = "Общие"
                if task.get('topic_id'):
                    topic = self._topic_repo.get_by_id(task['topic_id'])
                    if topic:
                        topic_name = topic['name']

                urgent.append({
                    'id': task['id'],
                    'title': task['title'],
                    'topic_name': topic_name,
                    'deadline': task_deadline,
                    'deadline_display': TimeService.format_datetime(
                        datetime.fromisoformat(task_deadline)
                    ) if task_deadline else "—",
                    'is_overdue': is_overdue
                })

        # Сортируем: сначала просроченные, потом сегодня, потом завтра
        urgent.sort(key=lambda x: (
            0 if x['is_overdue'] else (1 if x['deadline'][:10] == today.isoformat() else 2),
            x['deadline'] or ''
        ))

        return urgent[:limit]

    def get_today_analytics(self) -> Dict[str, Any]:
        """
        Возвращает мини-аналитику за сегодня:
        - время сегодня
        - средняя концентрация
        - средняя энергия
        - средний интерес
        """
        today = date.today().isoformat()
        today_start = f"{today}T00:00:00"
        today_end = f"{today}T23:59:59"

        # Сессии за сегодня
        sessions = db.fetchall("SELECT id, duration_minutes FROM sessions WHERE start_time >= ? AND start_time <= ?",
            (today_start, today_end)
        )

        if not sessions:
            return {
                'total_minutes': 0,
                'avg_concentration': 0,
                'avg_energy': 0,
                'avg_interest': 0,
                'has_data': False
            }

        session_ids = [s['id'] for s in sessions]
        placeholders = ','.join('?' * len(session_ids))

        # Получаем все логи
        logs = db.fetchall(
            f"SELECT metric, value FROM session_state_logs WHERE session_id IN ({placeholders})",
            tuple(session_ids)
        )

        conc_values = [log['value'] for log in logs if log['metric'] == 'concentration']
        energy_values = [log['value'] for log in logs if log['metric'] == 'energy']
        interest_values = [log['value'] for log in logs if log['metric'] == 'interest']

        # Общее время
        total_minutes = sum(s.get('duration_minutes') or 0 for s in sessions)

        return {
            'total_minutes': total_minutes,
            'total_hours': round(total_minutes / 60, 1),
            'avg_concentration': round(sum(conc_values) / len(conc_values), 1) if conc_values else 0,
            'avg_energy': round(sum(energy_values) / len(energy_values), 1) if energy_values else 0,
            'avg_interest': round(sum(interest_values) / len(interest_values), 1) if interest_values else 0,
            'has_data': True
        }

    def get_total_stats(self) -> Dict[str, Any]:
        """Возвращает общую статистику для дашборда"""
        topics = self._topic_repo.get_all()
        notes = self._note_repo.get_all()
        flashcards = self._flashcard_repo.get_all()
        tasks = self._task_repo.get_all()
        sessions = self._session_repo.get_all()

        completed_tasks = sum(1 for t in tasks if t.get('status') == 'completed')
        total_minutes = sum(s.get('duration_minutes') or 0 for s in sessions)

        return {
            'total_topics': len(topics),
            'total_notes': len(notes),
            'total_flashcards': len(flashcards),
            'total_tasks': len(tasks),
            'completed_tasks': completed_tasks,
            'total_sessions': len(sessions),
            'total_hours': round(total_minutes / 60, 1),
            'completion_rate': round(completed_tasks / len(tasks) * 100, 1) if tasks else 0
        }

    def has_data(self) -> bool:
        """Проверяет, есть ли какие-либо данные в приложении"""
        topics = self._topic_repo.get_all()
        return len(topics) > 0