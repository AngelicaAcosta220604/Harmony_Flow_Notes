# modules/analytics/controller.py
from typing import List, Dict, Any, Tuple
from datetime import datetime
from collections import defaultdict

from datebase.repositories import (
SessionRepository,
TaskRepository,
NoteRepository,
FlashcardRepository,
)

from datebase.db_manager import db
from models.session import Session
from models.task import Task
from models.note import Note
from models.flashcard import Flashcard
from services.time_service import TimeService


class AnalyticsController:
    """
    Контроллер для аналитики с поддержкой фильтрации по списку тем.
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

    # ==================== ПОЛУЧЕНИЕ ДАННЫХ ====================

    def get_sessions_for_topics(self, topic_ids: List[int]) -> List[Session]:
        """Возвращает все сессии для указанных тем"""
        if not topic_ids:
            return []

        rows = self._session_repo.get_by_topics(topic_ids)
        return [Session.from_row(row) for row in rows]

    def get_tasks_for_topics(self, topic_ids: List[int], include_general: bool = False) -> List[Task]:
        """Возвращает задачи для указанных тем"""
        if not topic_ids and not include_general:
            return []

        rows = self._task_repo.get_by_topics(topic_ids, include_general)
        return [Task.from_row(row) for row in rows]

    def get_notes_for_topics(self, topic_ids: List[int]) -> List[Note]:
        """Возвращает заметки для указанных тем"""
        if not topic_ids:
            return []

        rows = self._note_repo.get_by_topics(topic_ids)
        return [Note.from_row(row) for row in rows]

    def get_flashcards_for_topics(self, topic_ids: List[int]) -> List[Flashcard]:
        """Возвращает карточки для указанных тем"""
        if not topic_ids:
            return []

        rows = self._flashcard_repo.get_by_topics(topic_ids)
        return [Flashcard.from_row(row) for row in rows]

    # ==================== СТАТИСТИКА ПО СЕССИЯМ ====================

    def get_session_stats(self, sessions: List[Session]) -> Dict[str, Any]:
        """Общая статистика по списку сессий"""
        if not sessions:
            return self._empty_session_stats()

        total_sessions = len(sessions)
        total_minutes = sum(s.duration_minutes or 0 for s in sessions)
        avg_duration = total_minutes / total_sessions if total_sessions else 0

        total_hours = total_minutes // 60
        total_remain_minutes = total_minutes % 60

        # Средние показатели
        all_concentration = []
        all_energy = []
        all_interest = []

        for session in sessions:
            logs = self._get_session_logs(session.id)
            for log in logs:
                if log['metric'] == 'concentration':
                    all_concentration.append(log['value'])
                elif log['metric'] == 'energy':
                    all_energy.append(log['value'])
                elif log['metric'] == 'interest':
                    all_interest.append(log['value'])

        avg_concentration = sum(all_concentration) / len(all_concentration) if all_concentration else 0
        avg_energy = sum(all_energy) / len(all_energy) if all_energy else 0
        avg_interest = sum(all_interest) / len(all_interest) if all_interest else 0

        # Первая и последняя сессия
        dates = [datetime.fromisoformat(s.start_time) for s in sessions if s.start_time]
        first_session = min(dates).strftime("%d.%m.%Y") if dates else "—"
        last_session = max(dates).strftime("%d.%m.%Y") if dates else "—"
        unique_days = len(set(d.date() for d in dates)) if dates else 0

        return {
            "total_sessions": total_sessions,
            "total_minutes": total_minutes,
            "total_hours": total_hours,
            "total_minutes_remain": total_remain_minutes,
            "total_hours_display": f"{total_hours}ч {total_remain_minutes}м",  # <--- ДОБАВЛЯЕМ ЭТУ СТРОКУ
            "avg_duration": round(avg_duration, 1),
            "avg_concentration": round(avg_concentration, 2),
            "avg_energy": round(avg_energy, 2),
            "avg_interest": round(avg_interest, 2),
            "first_session": first_session,
            "last_session": last_session,
            "unique_days": unique_days,
            "avg_sessions_per_day": round(total_sessions / unique_days, 1) if unique_days > 0 else 0
        }

    def _get_session_logs(self, session_id: int) -> List[Dict]:
        """Получает логи сессии из БД"""
        return db.fetchall(
            "SELECT metric, value, minute FROM session_state_logs WHERE session_id = ? ORDER BY minute",
            (session_id,)
        )

    def get_progress_trend(self, sessions: List[Session], metric: str = 'concentration') -> Tuple[
        List[str], List[float]]:
        """Возвращает динамику метрики по сессиям"""
        if not sessions:
            return [], []

        dates = []
        values = []

        for session in sessions:
            if not session.start_time:
                continue

            dates.append(datetime.fromisoformat(session.start_time).strftime("%d.%m"))

            logs = self._get_session_logs(session.id)
            metric_values = [log['value'] for log in logs if log['metric'] == metric]

            if metric_values:
                values.append(sum(metric_values) / len(metric_values))
            else:
                values.append(0.0)

        return dates, values

    def get_all_metrics_trend(self, sessions: List[Session]) -> Dict[str, Tuple[List[str], List[float]]]:
        """Возвращает динамику всех трёх метрик"""
        return {
            'concentration': self.get_progress_trend(sessions, 'concentration'),
            'energy': self.get_progress_trend(sessions, 'energy'),
            'interest': self.get_progress_trend(sessions, 'interest')
        }

    def get_time_of_day_stats(self, sessions: List[Session]) -> Dict[int, Dict[str, Any]]:
        """Аналитика по часам суток"""
        hour_stats = {}
        for h in range(24):
            hour_stats[h] = {"count": 0, "concentration": [], "energy": [], "interest": []}

        for session in sessions:
            if not session.start_time:
                continue

            hour = datetime.fromisoformat(session.start_time).hour
            hour_stats[hour]["count"] += 1

            logs = self._get_session_logs(session.id)
            for log in logs:
                if log['metric'] == "concentration":
                    hour_stats[hour]["concentration"].append(log['value'])
                elif log['metric'] == "energy":
                    hour_stats[hour]["energy"].append(log['value'])
                elif log['metric'] == "interest":
                    hour_stats[hour]["interest"].append(log['value'])

        # Вычисляем средние
        for h in range(24):
            stats = hour_stats[h]
            stats["avg_concentration"] = sum(stats["concentration"]) / len(stats["concentration"]) if stats[
                "concentration"] else 0
            stats["avg_energy"] = sum(stats["energy"]) / len(stats["energy"]) if stats["energy"] else 0
            stats["avg_interest"] = sum(stats["interest"]) / len(stats["interest"]) if stats["interest"] else 0

        return hour_stats

    def get_day_of_week_stats(self, sessions: List[Session]) -> Dict[int, Dict[str, Any]]:
        """Аналитика по дням недели"""
        days_ru = ["ПН", "ВТ", "СР", "ЧТ", "ПТ", "СБ", "ВС"]
        day_stats = {i: {"count": 0, "name": days_ru[i], "concentration": [], "energy": [], "interest": []}
                     for i in range(7)}

        for session in sessions:
            if not session.start_time:
                continue

            dow = datetime.fromisoformat(session.start_time).weekday()
            day_stats[dow]["count"] += 1

            logs = self._get_session_logs(session.id)
            for log in logs:
                if log['metric'] == "concentration":
                    day_stats[dow]["concentration"].append(log['value'])
                elif log['metric'] == "energy":
                    day_stats[dow]["energy"].append(log['value'])
                elif log['metric'] == "interest":
                    day_stats[dow]["interest"].append(log['value'])

        for d in range(7):
            stats = day_stats[d]
            stats["avg_concentration"] = sum(stats["concentration"]) / len(stats["concentration"]) if stats[
                "concentration"] else 0
            stats["avg_energy"] = sum(stats["energy"]) / len(stats["energy"]) if stats["energy"] else 0
            stats["avg_interest"] = sum(stats["interest"]) / len(stats["interest"]) if stats["interest"] else 0

        return day_stats

    def get_best_hour(self, sessions: List[Session]) -> Tuple[int, float]:
        """Возвращает лучший час для занятий"""
        hour_stats = self.get_time_of_day_stats(sessions)

        best_hour = 0
        best_value = 0

        for h in range(24):
            avg_conc = hour_stats[h].get("avg_concentration", 0)
            count = hour_stats[h]["count"]
            if count > 0 and avg_conc > best_value:
                best_value = avg_conc
                best_hour = h

        return best_hour, best_value

    # ==================== СТАТИСТИКА ПО ЗАДАЧАМ ====================

    def get_task_stats(self, tasks: List[Task]) -> Dict[str, Any]:
        """Статистика по задачам"""
        if not tasks:
            return {
                "total": 0, "completed": 0, "active": 0, "overdue": 0,
                "completion_rate": 0, "on_time_rate": 0, "avg_overdue_days": 0
            }

        total = len(tasks)
        now = datetime.now()

        completed = 0
        active = 0
        overdue = 0
        completed_on_time = 0
        total_overdue_days = 0

        for task in tasks:
            if task.status == "completed":
                completed += 1
                if task.deadline and task.completed_at:
                    deadline = datetime.fromisoformat(task.deadline)
                    completed_at = datetime.fromisoformat(task.completed_at)
                    if completed_at <= deadline:
                        completed_on_time += 1
            elif task.status == "active":
                active += 1
                if task.deadline and datetime.fromisoformat(task.deadline) < now:
                    overdue += 1
            elif task.status == "overdue":
                overdue += 1
                if task.deadline:
                    deadline = datetime.fromisoformat(task.deadline)
                    days_overdue = (now - deadline).days
                    if days_overdue > 0:
                        total_overdue_days += days_overdue

        completion_rate = round(completed / total * 100, 1) if total else 0
        on_time_rate = round(completed_on_time / completed * 100, 1) if completed else 0
        avg_overdue_days = round(total_overdue_days / overdue, 1) if overdue else 0

        return {
            "total": total, "completed": completed, "active": active, "overdue": overdue,
            "completion_rate": completion_rate, "on_time_rate": on_time_rate,
            "avg_overdue_days": avg_overdue_days
        }

    # ==================== СТАТИСТИКА ПО КОНТЕНТУ ====================

    def get_content_stats(self, notes: List[Note], flashcards: List[Flashcard]) -> Dict[str, int]:
        """Статистика по заметкам и карточкам"""
        return {
            "total_notes": len(notes),
            "total_flashcards": len(flashcards),
            "free_cards": sum(1 for f in flashcards if f.is_free),
            "qa_cards": sum(1 for f in flashcards if f.is_qa)
        }

    # ==================== ТЕКСТОВЫЕ ИНСАЙТЫ ====================

    def generate_insights(self, sessions: List[Session], tasks: List[Task]) -> List[str]:
        """Генерирует текстовые выводы"""
        insights = []

        if not sessions:
            return ["📭 Нет данных для анализа. Проведите несколько сессий."]

        session_stats = self.get_session_stats(sessions)
        task_stats = self.get_task_stats(tasks)

        insights.append(
            f"📊 Всего проведено {session_stats['total_sessions']} сессий, "
            f"общей длительностью {session_stats['total_hours']} часов."
        )

        if session_stats['avg_concentration'] >= 4:
            insights.append(f"🧠 Отличная концентрация! Средний показатель {session_stats['avg_concentration']}/5.")
        elif session_stats['avg_concentration'] >= 3:
            insights.append(f"🧠 Хорошая концентрация: {session_stats['avg_concentration']}/5.")
        else:
            insights.append(f"🧠 Концентрация ниже среднего ({session_stats['avg_concentration']}/5).")

        if session_stats['avg_energy'] >= 4:
            insights.append(f"⚡ Энергия на высоте! Средний показатель {session_stats['avg_energy']}/5.")
        elif session_stats['avg_energy'] <= 2:
            insights.append(f"⚡ Уровень энергии низкий ({session_stats['avg_energy']}/5).")

        best_hour, best_value = self.get_best_hour(sessions)
        if best_value > 0:
            insights.append(f"⏰ Лучшее время для занятий: {best_hour:02d}:00 (концентрация {best_value:.1f}/5).")

        if task_stats['total'] > 0:
            insights.append(
                f"✅ Задачи: выполнено {task_stats['completed']}/{task_stats['total']} "
                f"({task_stats['completion_rate']}%), {task_stats['overdue']} просрочено."
            )

        if session_stats['avg_duration'] > 90:
            insights.append(
                f"💡 Сессии длиннее 90 минут могут снижать эффективность. "
                f"Ваша средняя длительность: {session_stats['avg_duration']} мин."
            )

        return insights

    # ==================== ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ ====================

    def _empty_session_stats(self) -> Dict[str, Any]:
        return {
            "total_sessions": 0,
            "total_minutes": 0,
            "total_hours": 0,
            "total_minutes_remain": 0,
            "total_hours_display": "0ч 0м",  # <--- ДОБАВЛЯЕМ
            "avg_duration": 0,
            "avg_concentration": 0,
            "avg_energy": 0,
            "avg_interest": 0,
            "first_session": "—",
            "last_session": "—",
            "unique_days": 0,
            "avg_sessions_per_day": 0
        }

    def get_complete_stats(self, topic_ids: List[int], include_general_tasks: bool = False) -> Dict[str, Any]:
        sessions = self.get_sessions_for_topics(topic_ids)
        tasks = self.get_tasks_for_topics(topic_ids, include_general_tasks)
        notes = self.get_notes_for_topics(topic_ids)
        flashcards = self.get_flashcards_for_topics(topic_ids)

        return {
            "session_stats": self.get_session_stats(sessions),
            "task_stats": self.get_task_stats(tasks),
            "content_stats": self.get_content_stats(notes, flashcards),
            "hour_stats": self.get_time_of_day_stats(sessions),
            "day_stats": self.get_day_of_week_stats(sessions),
            "trends": self.get_all_metrics_trend(sessions),
            "insights": self.generate_insights(sessions, tasks),
            "sessions": sessions,
            "tasks": tasks,
            "notes": notes,
            "flashcards": flashcards
        }