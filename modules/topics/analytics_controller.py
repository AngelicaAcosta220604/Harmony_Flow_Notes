# modules/topics/analytics_controller.py
from typing import List, Dict, Any, Optional
from datebase.repositories import (
SessionRepository,
TaskRepository,
NoteRepository,
FlashcardRepository
)

from datebase.db_manager import db
from services.time_service import TimeService


class TopicAnalyticsController:
    """
    Контроллер для аналитики по конкретной теме.
    """

    def __init__(
            self,
            session_repo: SessionRepository,
            task_repo: TaskRepository,
            note_repo: NoteRepository,
            flashcard_repo: FlashcardRepository
    ):
        self._session_repo = session_repo
        self._task_repo = task_repo
        self._note_repo = note_repo
        self._flashcard_repo = flashcard_repo

    def get_topic_stats(self, topic_id: int) -> Dict[str, Any]:
        """
        Возвращает статистику по теме:
        - количество сессий
        - суммарное время
        - средняя концентрация/энергия/интерес
        - количество задач/выполненных
        - количество заметок/карточек
        """
        # Сессии
        sessions = self._session_repo.get_by_topic(topic_id)
        session_count = len(sessions)
        total_minutes = sum(s.get('duration_minutes') or 0 for s in sessions)

        # Логи состояния

        session_ids = [s['id'] for s in sessions]

        avg_concentration = 0
        avg_energy = 0
        avg_interest = 0

        if session_ids:
            placeholders = ','.join('?' * len(session_ids))
            logs = db.fetchall(
                f"SELECT metric, value FROM session_state_logs WHERE session_id IN ({placeholders})",
                tuple(session_ids)
            )

            conc_vals = [log['value'] for log in logs if log['metric'] == 'concentration']
            energy_vals = [log['value'] for log in logs if log['metric'] == 'energy']
            interest_vals = [log['value'] for log in logs if log['metric'] == 'interest']

            avg_concentration = round(sum(conc_vals) / len(conc_vals), 1) if conc_vals else 0
            avg_energy = round(sum(energy_vals) / len(energy_vals), 1) if energy_vals else 0
            avg_interest = round(sum(interest_vals) / len(interest_vals), 1) if interest_vals else 0

        # Задачи
        tasks = self._task_repo.get_by_topic(topic_id)
        task_count = len(tasks)
        completed_tasks = sum(1 for t in tasks if t.get('status') == 'completed')

        # Заметки
        notes = self._note_repo.get_by_topic(topic_id)
        note_count = len(notes)

        # Карточки
        flashcards = self._flashcard_repo.get_by_topic(topic_id)
        flashcard_count = len(flashcards)

        return {
            'session_count': session_count,
            'total_minutes': total_minutes,
            'total_hours': round(total_minutes / 60, 1),
            'avg_concentration': avg_concentration,
            'avg_energy': avg_energy,
            'avg_interest': avg_interest,
            'task_count': task_count,
            'completed_tasks': completed_tasks,
            'completion_rate': round(completed_tasks / task_count * 100, 1) if task_count else 0,
            'note_count': note_count,
            'flashcard_count': flashcard_count
        }

    def get_session_history(self, topic_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Возвращает историю сессий по теме с краткой статистикой.
        """
        sessions = self._session_repo.get_by_topic(topic_id)

        result = []



        for session in sessions[:limit]:
            # Получаем логи
            logs = db.fetchall(
                "SELECT metric, value FROM session_state_logs WHERE session_id = ?",
                (session['id'],)
            )

            conc_vals = [log['value'] for log in logs if log['metric'] == 'concentration']
            energy_vals = [log['value'] for log in logs if log['metric'] == 'energy']

            result.append({
                'id': session['id'],
                'date': session['start_time'][:10] if session['start_time'] else "—",
                'duration_minutes': session.get('duration_minutes', 0),
                'duration_display': TimeService.format_duration(session.get('duration_minutes', 0)),
                'avg_concentration': round(sum(conc_vals) / len(conc_vals), 1) if conc_vals else 0,
                'avg_energy': round(sum(energy_vals) / len(energy_vals), 1) if energy_vals else 0
            })

        return result

    def get_recent_notes(self, topic_id: int, limit: int = 5) -> List[Dict[str, Any]]:
        """Возвращает последние заметки по теме"""
        notes = self._note_repo.get_by_topic(topic_id)

        result = []
        for note in notes[:limit]:
            result.append({
                'id': note['id'],
                'title': note['title'],
                'preview': (note.get('content', '')[:100] + '...') if len(note.get('content', '')) > 100 else note.get(
                    'content', ''),
                'updated_at': note.get('updated_at', '')[:10]
            })

        return result

    def get_active_tasks(self, topic_id: int) -> List[Dict[str, Any]]:
        """Возвращает активные задачи по теме"""
        tasks = self._task_repo.get_by_topic(topic_id)

        result = []
        for task in tasks:
            if task.get('status') == 'active':
                result.append({
                    'id': task['id'],
                    'title': task['title'],
                    'deadline': task.get('deadline'),
                    'deadline_display': TimeService.format_datetime_from_iso(task.get('deadline')) if task.get(
                        'deadline') else "—"
                })

        return result