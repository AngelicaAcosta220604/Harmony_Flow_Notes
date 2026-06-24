# modules/analytics/controller.py
from typing import List, Dict, Any, Tuple
from datetime import datetime
from collections import defaultdict

import logging

from database.repositories import (
SessionRepository,
TaskRepository,
NoteRepository,
FlashcardRepository,
)

from database.db_manager import db
from models.session import Session
from models.task import Task
from models.note import Note
from models.flashcard import Flashcard
from services.time_service import TimeService

# Настройка логирования
logger = logging.getLogger(__name__)

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
            # Если список пустой - возвращаем ВСЕ сессии
            rows = self._session_repo.get_all()
        else:
            rows = self._session_repo.get_by_topics(topic_ids)
        return [Session.from_row(row) for row in rows]

    def get_tasks_for_topics(self, topic_ids: List[int], include_general: bool = False) -> List[Task]:
        """Возвращает задачи для указанных тем"""
        if not topic_ids:
            # Если список пустой - возвращаем ВСЕ задачи
            rows = self._task_repo.get_all()
        else:
            rows = self._task_repo.get_by_topics(topic_ids, include_general)
        return [Task.from_row(row) for row in rows]

    def get_notes_for_topics(self, topic_ids: List[int]) -> List[Note]:
        """Возвращает заметки для указанных тем"""
        if not topic_ids:
            # Если список пустой - возвращаем ВСЕ заметки
            rows = self._note_repo.get_all()
        else:
            rows = self._note_repo.get_by_topics(topic_ids)
        return [Note.from_row(row) for row in rows]

    def get_flashcards_for_topics(self, topic_ids: List[int]) -> List[Flashcard]:
        """Возвращает карточки для указанных тем"""
        if not topic_ids:
            # Если список пустой - возвращаем ВСЕ карточки
            rows = self._flashcard_repo.get_all()
        else:
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
        all_focus = []
        all_energy = []
        all_interest = []

        for session in sessions:
            logs = self._get_session_logs(session.id)

            # 🆕 ЛОГИРОВАНИЕ ДЛЯ ОТЛАДКИ
            logger.debug(f"Сессия {session.id}: получено {len(logs)} логов")

            for log in logs:
                if log['metric'] == 'focus':
                    all_focus.append(log['value'])
                elif log['metric'] == 'energy':
                    all_energy.append(log['value'])
                elif log['metric'] == 'interest':
                    all_interest.append(log['value'])

        # 🆕 ЛОГИРОВАНИЕ ДЛЯ ОТЛАДКИ
        logger.debug(f"Собрано метрик: focus={len(all_focus)}, energy={len(all_energy)}, interest={len(all_interest)}")
        logger.debug(f"Значения focus: {all_focus}")

        avg_focus = sum(all_focus) / len(all_focus) if all_focus else 0
        avg_energy = sum(all_energy) / len(all_energy) if all_energy else 0
        avg_interest = sum(all_interest) / len(all_interest) if all_interest else 0

        # 🆕 ЛОГИРОВАНИЕ ДЛЯ ОТЛАДКИ
        logger.debug(f"Средние значения: focus={avg_focus}, energy={avg_energy}, interest={avg_interest}")

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
            "total_hours_display": f"{total_hours}ч {total_remain_minutes}м",
            "avg_duration": round(avg_duration, 1),
            "avg_concentration": round(avg_focus, 2),
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

    def get_progress_trend(self, sessions: List[Session], metric: str = 'focus') -> Tuple[List[str], List[float]]:
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
            'concentration': self.get_progress_trend(sessions, 'focus'),
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
                if log['metric'] == "focus":
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
                if log['metric'] == "focus":  # ✅ ИСПРАВЛЕНО: было "concentration"
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

    # ==================== СТАТИСТИКА ПО КОНТЕНТУ .====================

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

        # ✅ ИСПРАВЛЕНО: используем total_hours_display вместо total_hours
        insights.append(
            f"📊 Всего проведено {session_stats['total_sessions']} сессий, "
            f"общей длительностью {session_stats['total_hours_display']}."
        )

        if session_stats['avg_concentration'] >= 70:
            insights.append(f"🧠 Отличная концентрация! Средний показатель {session_stats['avg_concentration']}/100.")
        elif session_stats['avg_concentration'] >= 50:
            insights.append(f"🧠 Хорошая концентрация: {session_stats['avg_concentration']}/100.")
        else:
            insights.append(f"🧠 Концентрация ниже среднего ({session_stats['avg_concentration']}/100).")

        if session_stats['avg_energy'] >= 70:
            insights.append(f"⚡ Энергия на высоте! Средний показатель {session_stats['avg_energy']}/100.")
        elif session_stats['avg_energy'] <= 30:
            insights.append(f"⚡ Уровень энергии низкий ({session_stats['avg_energy']}/100).")

        # ✅ ИСПРАВЛЕНО: добавлен анализ интереса
        if session_stats['avg_interest'] >= 70:
            insights.append(f"❤️ Отличный интерес! Средний показатель {session_stats['avg_interest']}/100.")
        elif session_stats['avg_interest'] <= 30:
            insights.append(
                f"❤️ Интерес низкий ({session_stats['avg_interest']}/100). Попробуйте более увлекательные темы.")

        best_hour, best_value = self.get_best_hour(sessions)
        if best_value > 0:
            insights.append(f"⏰ Лучшее время для занятий: {best_hour:02d}:00 (концентрация {best_value:.1f}/100).")

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

    def get_topic_analytics(self) -> List[Dict[str, Any]]:
        """
        Возвращает аналитику, сгруппированную по темам (как в дереве карточек).
        """
        # 1. Получаем все сессии с названиями тем
        sessions = db.fetchall("""
               SELECT s.id, s.topic_id, s.duration_minutes, t.name as topic_name
               FROM sessions s
               LEFT JOIN topics t ON s.topic_id = t.id
           """)

        # 2. Получаем все логи состояний
        logs = db.fetchall("SELECT session_id, metric, value FROM session_state_logs")

        # 3. Создаем маппинг session_id -> topic_id для быстрой связи
        session_to_topic = {
            s['id']: {'topic_id': s['topic_id'], 'topic_name': s['topic_name'] or 'Без темы'}
            for s in sessions
        }

        # 4. Агрегируем данные по темам
        stats = {}
        for s in sessions:
            tid = s['topic_id']
            tname = s['topic_name'] or 'Без темы'
            if tid not in stats:
                stats[tid] = {
                    'topic_id': tid,
                    'topic_name': tname,
                    'session_count': 0,
                    'total_minutes': 0,
                    'conc': [], 'energy': [], 'interest': []
                }
            stats[tid]['session_count'] += 1
            stats[tid]['total_minutes'] += s.get('duration_minutes') or 0

        for log in logs:
            sid = log['session_id']
            if sid in session_to_topic:
                tid = session_to_topic[sid]['topic_id']
                metric = log['metric']
                val = log['value']
                if metric == 'focus':  # ✅ ИСПРАВЛЕНО: было 'concentration'
                    stats[tid]['conc'].append(val)
                elif metric == 'energy':
                    stats[tid]['energy'].append(val)
                elif metric == 'interest':
                    stats[tid]['interest'].append(val)

        # 5. Форматируем итоговый результат
        result = []
        for tid, data in stats.items():
            result.append({
                'topic_id': tid,
                'topic_name': data['topic_name'],
                'session_count': data['session_count'],
                'total_minutes': data['total_minutes'],
                'total_hours': round(data['total_minutes'] / 60, 1),
                'avg_concentration': round(sum(data['conc']) / len(data['conc']), 1) if data['conc'] else 0,
                'avg_energy': round(sum(data['energy']) / len(data['energy']), 1) if data['energy'] else 0,
                'avg_interest': round(sum(data['interest']) / len(data['interest']), 1) if data['interest'] else 0,
            })

        # Сортируем по затраченному времени (по убыванию)
        result.sort(key=lambda x: x['total_minutes'], reverse=True)
        return result

    def _get_all_topics(self) -> List[Dict]:
        """Получает все темы и папки из БД для построения дерева"""
        return db.fetchall("SELECT id, name, parent_id, type FROM topics")

    def get_sessions_table_data(self, topic_ids: List[int]) -> List[Dict[str, Any]]:
        """Данные для таблицы сессий (как в истории)"""
        sessions = self.get_sessions_for_topics(topic_ids)
        topics_map = {t['id']: t for t in self._get_all_topics()}

        result = []
        for s in sessions:
            logs = self._get_session_logs(s.id)
            conc = [l['value'] for l in logs if l['metric'] == 'focus']
            energy = [l['value'] for l in logs if l['metric'] == 'energy']
            interest = [l['value'] for l in logs if l['metric'] == 'interest']

            topic_name = "—"
            if s.topic_id and s.topic_id in topics_map:
                topic_name = topics_map[s.topic_id]['name']

            result.append({
                'date': datetime.fromisoformat(s.start_time).strftime("%d.%m.%Y %H:%M") if s.start_time else "—",
                'topic_name': topic_name,
                'duration': f"{s.duration_minutes} мин",
                'avg_concentration': round(sum(conc) / len(conc), 1) if conc else 0,
                'avg_energy': round(sum(energy) / len(energy), 1) if energy else 0,
                'avg_interest': round(sum(interest) / len(interest), 1) if interest else 0,
            })
        # Сортируем по дате (новые сверху)
        result.sort(key=lambda x: x['date'], reverse=True)
        return result

    def get_topics_table_data(self, topic_ids: List[int]) -> List[Dict[str, Any]]:
        """Данные для таблицы тем (агрегация по topic_id)"""
        sessions = self.get_sessions_for_topics(topic_ids)
        topics_map = {t['id']: t for t in self._get_all_topics()}

        stats = {}
        for s in sessions:
            tid = s.topic_id if s.topic_id is not None else -1
            if tid not in stats:
                tname = topics_map.get(tid, {}).get('name', 'Без темы') if tid != -1 else 'Без темы'
                stats[tid] = {
                    'topic_name': tname,
                    'session_count': 0,
                    'total_minutes': 0,
                    'conc': [], 'energy': [], 'interest': []
                }
            stats[tid]['session_count'] += 1
            stats[tid]['total_minutes'] += s.duration_minutes or 0

            logs = self._get_session_logs(s.id)
            for log in logs:
                if log['metric'] == 'focus':  # ✅ ИСПРАВЛЕНО: было 'concentration'
                    stats[tid]['conc'].append(log['value'])
                elif log['metric'] == 'energy':
                    stats[tid]['energy'].append(log['value'])
                elif log['metric'] == 'interest':
                    stats[tid]['interest'].append(log['value'])

        result = []
        for tid, data in stats.items():
            result.append({
                'topic_name': data['topic_name'],
                'session_count': data['session_count'],
                'duration': f"{data['total_minutes']} мин",
                'avg_concentration': round(sum(data['conc']) / len(data['conc']), 1) if data['conc'] else 0,
                'avg_energy': round(sum(data['energy']) / len(data['energy']), 1) if data['energy'] else 0,
                'avg_interest': round(sum(data['interest']) / len(data['interest']), 1) if data['interest'] else 0,
            })
        result.sort(key=lambda x: x['session_count'], reverse=True)
        return result

    def get_folders_table_data(self, topic_ids: List[int]) -> List[Dict[str, Any]]:
        """Данные для таблицы папок (с учётом вложенности, как в дереве карточек)"""
        sessions = self.get_sessions_for_topics(topic_ids)
        all_topics = self._get_all_topics()
        topics_map = {t['id']: t for t in all_topics}
        folders = {t['id']: t for t in all_topics if t['type'] == 'folder'}

        topic_to_folder = {}
        for t in all_topics:
            if t['type'] == 'topic':
                current = t
                while current.get('parent_id'):
                    parent = topics_map.get(current['parent_id'])
                    if not parent: break
                    if parent['type'] == 'folder':
                        topic_to_folder[t['id']] = parent['id']
                        break
                    current = parent

        stats = {fid: {
            'folder_name': folder['name'],
            'session_count': 0,
            'total_minutes': 0,
            'conc': [], 'energy': [], 'interest': []
        } for fid, folder in folders.items()}

        stats[-1] = {
            'folder_name': 'Без папки',
            'session_count': 0,
            'total_minutes': 0,
            'conc': [], 'energy': [], 'interest': []
        }

        for s in sessions:
            tid = s.topic_id
            if tid is None:
                fid = -1
            else:
                fid = topic_to_folder.get(tid, -1)

            if fid in stats:
                stats[fid]['session_count'] += 1
                stats[fid]['total_minutes'] += s.duration_minutes or 0
                logs = self._get_session_logs(s.id)
                for log in logs:
                    if log['metric'] == 'focus':
                        # ✅ ИСПРАВЛЕНО: было stats[tid], должно быть stats[fid]
                        stats[fid]['conc'].append(log['value'])
                    elif log['metric'] == 'energy':
                        stats[fid]['energy'].append(log['value'])
                    elif log['metric'] == 'interest':
                        stats[fid]['interest'].append(log['value'])

        result = []
        for fid, data in stats.items():
            if data['session_count'] > 0:
                result.append({
                    'folder_name': data['folder_name'],
                    'session_count': data['session_count'],
                    'duration': f"{data['total_minutes']} мин",
                    'avg_concentration': round(sum(data['conc']) / len(data['conc']), 1) if data['conc'] else 0,
                    'avg_energy': round(sum(data['energy']) / len(data['energy']), 1) if data['energy'] else 0,
                    'avg_interest': round(sum(data['interest']) / len(data['interest']), 1) if data['interest'] else 0,
                })
        result.sort(key=lambda x: x['session_count'], reverse=True)
        return result

    def analyze_metric_patterns(self, sessions: List[Session]) -> Dict[str, Any]:
        """Анализирует временные паттерны метрик"""
        if not sessions:
            return {}

        # Собираем все логи по минутам сессий
        timeline = []
        for session in sessions:
            if not session.start_time:
                continue
            logs = self._get_session_logs(session.id)
            session_start = datetime.fromisoformat(session.start_time)

            for log in logs:
                minute_time = session_start.replace(
                    minute=log['minute'] % 60,
                    hour=session_start.hour + (log['minute'] // 60)
                )
                timeline.append({
                    'time': minute_time,
                    'minute': log['minute'],
                    'metric': log['metric'],
                    'value': log['value']
                })

        if not timeline:
            return {}

        # Анализируем каждую метрику
        result = {}
        for metric in ['focus', 'energy', 'interest']:  # ✅ ИСПРАВЛЕНО: было 'concentration'
            metric_data = [t for t in timeline if t['metric'] == metric]
            if not metric_data:
                continue

            # Сортируем по времени
            metric_data.sort(key=lambda x: x['time'])
            values = [m['value'] for m in metric_data]

            # Находим пики и спады
            peak_info = self._find_peaks_and_drops(values, metric_data)
            result[metric] = peak_info

        # Анализируем синергию
        result['synergy'] = self._analyze_synergy(timeline)

        return result

    def _find_peaks_and_drops(self, values: List[float], data: List[Dict]) -> Dict[str, Any]:
        """Находит пики, спады и лучшие периоды"""
        if not values:
            return {}

        max_value = max(values)
        min_value = min(values)
        avg_value = sum(values) / len(values)

        # Находим первый пик
        peak_minute = values.index(max_value)
        peak_time = data[peak_minute]['time'].strftime("%H:%M") if peak_minute < len(data) else "—"

        # Находим когда началось падение после пика
        drop_minute = None
        for i in range(peak_minute + 1, len(values)):
            if values[i] < values[i - 1] * 0.9:  # Падение на 10% и более
                drop_minute = i
                break

        drop_time = data[drop_minute]['time'].strftime("%H:%M") if drop_minute and drop_minute < len(data) else "—"
        time_to_drop = f"{drop_minute - peak_minute} мин" if drop_minute else "Не зафиксировано"

        # Находим лучший период (30 минут с наивысшим средним)
        best_period_start = None
        best_period_avg = 0
        window_size = min(30, len(values))

        for i in range(len(values) - window_size + 1):
            window_avg = sum(values[i:i + window_size]) / window_size
            if window_avg > best_period_avg:
                best_period_avg = window_avg
                best_period_start = i

        best_start_time = data[best_period_start]['time'].strftime(
            "%H:%M") if best_period_start is not None and best_period_start < len(data) else "—"
        best_duration = f"{window_size} мин" if best_period_start is not None else "—"

        # Находим когда начался спад от начального уровня
        initial_drop_minute = None
        initial_value = values[0] if values else 0
        for i in range(1, len(values)):
            if values[i] < initial_value * 0.85:  # Падение на 15% от начального
                initial_drop_minute = i
                break

        initial_drop_time = data[initial_drop_minute]['time'].strftime(
            "%H:%M") if initial_drop_minute and initial_drop_minute < len(data) else "—"
        time_to_initial_drop = f"{initial_drop_minute} мин" if initial_drop_minute else "Не зафиксировано"

        return {
            'peak_value': round(max_value, 1),
            'peak_time': peak_time,
            'peak_minute': peak_minute,
            'drop_time': drop_time,
            'time_to_drop': time_to_drop,
            'initial_drop_time': initial_drop_time,
            'time_to_initial_drop': time_to_initial_drop,
            'best_period_start': best_start_time,
            'best_period_duration': best_duration,
            'best_period_avg': round(best_period_avg, 1),
            'avg': round(avg_value, 1),
            'min': round(min_value, 1)
        }

    def _analyze_synergy(self, timeline: List[Dict]) -> Dict[str, Any]:
        """Анализирует синергию метрик"""
        if not timeline:
            return {}

        # Группируем по минутам
        by_minute = {}
        for t in timeline:
            minute = t['minute']
            if minute not in by_minute:
                by_minute[minute] = {}
            by_minute[minute][t['metric']] = t['value']

        # Находим минуты где все метрики высокие
        high_synergy_minutes = []
        for minute, metrics in by_minute.items():
            if all(metrics.get(m, 0) >= 70 for m in ['focus', 'energy', 'interest']):  # ✅ ИСПРАВЛЕНО
                high_synergy_minutes.append(minute)

        # Анализируем корреляции
        conc_values = [t['value'] for t in timeline if t['metric'] == 'focus']
        energy_values = [t['value'] for t in timeline if t['metric'] == 'energy']
        interest_values = [t['value'] for t in timeline if t['metric'] == 'interest']

        # Простая корреляция
        conc_energy_corr = self._calculate_correlation(conc_values, energy_values)
        conc_interest_corr = self._calculate_correlation(conc_values, interest_values)

        # Рекомендации
        recommendations = []

        if high_synergy_minutes:
            peak_synergy_time = min(high_synergy_minutes)
            recommendations.append(
                f"🎯 Пик продуктивности (все метрики >70) достигнут на {peak_synergy_time}-й минуте сессии"
            )

        if conc_energy_corr > 0.7:
            recommendations.append(
                "⚡ Энергия сильно влияет на концентрацию - следите за отдыхом"
            )

        if conc_interest_corr > 0.7:
            recommendations.append(
                "❤️ Интерес напрямую влияет на концентрацию - выбирайте engaging темы"
            )

        # Находим когда начинается общий спад
        synergy_drop = None
        for i in range(len(conc_values)):
            if i < len(energy_values) and i < len(interest_values):
                if (conc_values[i] < conc_values[0] * 0.8 and
                        energy_values[i] < energy_values[0] * 0.8):
                    synergy_drop = i
                    break

        if synergy_drop:
            recommendations.append(
                f"⏱️ Оптимальная длительность сессии: {synergy_drop} минут (после начинается спад)"
            )

        return {
            'high_synergy_minutes': len(high_synergy_minutes),
            'peak_synergy_minute': min(high_synergy_minutes) if high_synergy_minutes else None,
            'conc_energy_correlation': round(conc_energy_corr, 2),
            'conc_interest_correlation': round(conc_interest_corr, 2),
            'synergy_drop_minute': synergy_drop,
            'recommendations': recommendations
        }

    def _calculate_correlation(self, x: List[float], y: List[float]) -> float:
        """Вычисляет корреляцию Пирсона"""
        if len(x) != len(y) or len(x) < 2:
            return 0.0

        n = len(x)
        mean_x = sum(x) / n
        mean_y = sum(y) / n

        numerator = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(n))

        sum_sq_x = sum((xi - mean_x) ** 2 for xi in x)
        sum_sq_y = sum((yi - mean_y) ** 2 for yi in y)

        denominator = (sum_sq_x * sum_sq_y) ** 0.5

        if denominator == 0:
            return 0.0

        return numerator / denominator

    def generate_detailed_recommendations(self, sessions: List[Session], patterns: Dict[str, Any]) -> List[str]:
        """Генерирует детальные рекомендации на основе паттернов"""
        recommendations = []

        if not sessions or not patterns:
            return ["📭 Недостаточно данных для рекомендаций"]

        # Анализируем каждую метрику
        for metric, metric_name in [
            ('concentration', 'концентрации'),
            ('energy', 'энергии'),
            ('interest', 'интереса')
        ]:
            if metric not in patterns:
                continue

            data = patterns[metric]

            # Рекомендации по пику
            peak_minute = data.get('peak_minute', 0)
            if peak_minute < 15:
                recommendations.append(
                    f"🔥 {metric_name.capitalize()} достигает пика очень быстро ({peak_minute} мин) - "
                    f"начинайте с самых сложных задач"
                )
            elif peak_minute > 45:
                recommendations.append(
                    f" {metric_name.capitalize()} растет медленно (пик на {peak_minute} мин) - "
                    f"дайте себе время на раскачку"
                )

            # Рекомендации по спаду
            time_to_drop = data.get('time_to_initial_drop', '')
            if 'мин' in time_to_drop:
                minutes = int(time_to_drop.split()[0])
                if minutes < 20:
                    recommendations.append(
                        f"⚠️ {metric_name.capitalize()} падает уже через {minutes} мин - "
                        f"делайте микро-перерывы каждые 15 минут"
                    )
                elif minutes > 60:
                    recommendations.append(
                        f"💪 Отличная устойчивость {metric_name} ({minutes} мин) - "
                        f"можете работать длинными сессиями"
                    )

        # Рекомендации по синергии
        if 'synergy' in patterns:
            synergy = patterns['synergy']

            # Корреляции
            conc_energy = synergy.get('conc_energy_correlation', 0)
            conc_interest = synergy.get('conc_interest_correlation', 0)

            if conc_energy > 0.8:
                recommendations.append(
                    "⚡⚡ Энергия и концентрация сильно связаны - "
                    "следите за сном и питанием для лучшей фокусировки"
                )
            elif conc_energy < 0.3:
                recommendations.append(
                    "🔋 Концентрация не зависит от энергии - "
                    "можете эффективно работать даже при усталости"
                )

            if conc_interest > 0.8:
                recommendations.append(
                    "❤️🧠 Интерес критичен для концентрации - "
                    "разбивайте скучные задачи на интересные подзадачи"
                )

            # Оптимальная длительность
            synergy_drop = synergy.get('synergy_drop_minute')
            if synergy_drop:
                recommendations.append(
                    f"⏱️ Оптимальная длительность сессии: {synergy_drop} минут. "
                    f"После этого все метрики начинают падать"
                )

            # Пик синергии
            peak_synergy = synergy.get('peak_synergy_minute')
            if peak_synergy:
                recommendations.append(
                    f"🎯 Максимальная продуктивность на {peak_synergy}-й минуте - "
                    f"планируйте самые важные задачи на это время"
                )

        # Общие рекомендации по сессиям
        total_sessions = len(sessions)
        if total_sessions > 0:
            avg_duration = sum(s.duration_minutes or 0 for s in sessions) / total_sessions

            if avg_duration < 25:
                recommendations.append(
                    "📝 Среднее время сессии меньше 25 минут - "
                    "попробуйте технику Pomodoro (25 мин работа / 5 мин отдых)"
                )
            elif avg_duration > 90:
                recommendations.append(
                    "⏰ Среднее время сессии больше 90 минут - "
                    "риск выгорания. Разбивайте на блоки по 45-60 минут"
                )

        # Если мало рекомендаций
        if len(recommendations) < 3:
            recommendations.append(
                "💡 Продолжайте отслеживать метрики - "
                "чем больше данных, тем точнее будут рекомендации"
            )

        return recommendations