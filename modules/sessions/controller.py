# modules/sessions/controller.py
from typing import List, Optional, Dict, Any
from datetime import datetime
from PySide6.QtCore import QTimer, QObject, Signal

from datebase.repositories.session_repo import SessionRepository
from datebase.repositories.session_state_log_repo import SessionStateLogRepository
from datebase.repositories.quick_note_repo import QuickNoteRepository
from datebase.repositories.topic_repo import TopicRepository
from models.session import Session
from models.quick_note import QuickNote
from services.time_service import TimeService


class SessionController(QObject):
    """
    Контроллер для управления фокус-сессиями.
    Управляет таймером, паузами, состоянием сессии.
    """

    # Сигналы
    timer_updated = Signal(int)  # seconds elapsed
    session_paused = Signal()
    session_resumed = Signal()
    session_completed = Signal(int)  # duration_minutes
    state_changed = Signal(str, int)  # metric, value

    def __init__(
            self,
            session_repo: SessionRepository,
            state_log_repo: SessionStateLogRepository,
            quick_note_repo: QuickNoteRepository,
            topic_repo: TopicRepository
    ):
        super().__init__()
        self._session_repo = session_repo
        self._state_log_repo = state_log_repo
        self._quick_note_repo = quick_note_repo
        self._topic_repo = topic_repo

        self._current_session: Optional[Session] = None
        self._current_topic_id: Optional[int] = None
        self._elapsed_seconds: int = 0
        self._timer: Optional[QTimer] = None
        self._is_paused: bool = False
        self._start_time: Optional[datetime] = None

    def prepare_session(self, topic_id: int) -> bool:
        """
        Подготавливает сессию для темы
        """
        topic = self._topic_repo.get_by_id(topic_id)
        if not topic:
            return False

        self._current_topic_id = topic_id
        self._elapsed_seconds = 0
        self._is_paused = False
        return True

    def start_session(self) -> int:
        """
        Начинает сессию
        Returns:
            ID сессии
        """
        session_id = self._session_repo.create(self._current_topic_id)
        self._current_session = Session.from_row(
            self._session_repo.get_by_id(session_id)
        )
        self._start_time = datetime.now()

        # Запускаем таймер
        self._timer = QTimer()
        self._timer.timeout.connect(self._on_timer_tick)
        self._timer.start(1000)  # каждую секунду

        return session_id

    def _on_timer_tick(self):
        """Обновление таймера каждую секунду"""
        if not self._is_paused and self._current_session:
            self._elapsed_seconds += 1
            self.timer_updated.emit(self._elapsed_seconds)

    def pause_session(self):
        """Ставит сессию на паузу"""
        if self._current_session and not self._is_paused:
            self._is_paused = True
            self._current_session.pause()
            self._session_repo.update(self._current_session.id, status='paused')
            self.session_paused.emit()

    def resume_session(self):
        """Возобновляет сессию"""
        if self._current_session and self._is_paused:
            self._is_paused = False
            self._current_session.resume()
            self._session_repo.update(self._current_session.id, status='active')
            self.session_resumed.emit()

    def end_session(self, auto: bool = False) -> int:
        """
        Завершает сессию

        Returns:
            Длительность в минутах
        """
        if not self._current_session:
            return 0

        duration_minutes = self._elapsed_seconds // 60
        if duration_minutes == 0 and self._elapsed_seconds > 0:
            duration_minutes = 1  # минимум 1 минута

        status = 'auto_completed' if auto else 'completed'
        self._session_repo.end_session(
            self._current_session.id,
            duration_minutes,
            status
        )

        if self._timer:
            self._timer.stop()

        self.session_completed.emit(duration_minutes)

        session_id = self._current_session.id
        self._current_session = None
        self._is_paused = False

        return duration_minutes

    def get_elapsed_seconds(self) -> int:
        """Возвращает прошедшее время в секундах"""
        return self._elapsed_seconds

    def get_elapsed_display(self) -> str:
        """Возвращает отформатированное время"""
        return TimeService.format_time(self._elapsed_seconds)

    def get_duration_minutes(self) -> int:
        """Возвращает текущую длительность в минутах"""
        return self._elapsed_seconds // 60

    def log_state(self, metric: str, value: int):
        """
        Логирует изменение состояния (концентрация/энергия/интерес)
        """
        if not self._current_session:
            return

        minute = self.get_duration_minutes()

        self._state_log_repo.create(
            session_id=self._current_session.id,
            metric=metric,
            value=value,
            minute=minute
        )

        self.state_changed.emit(metric, value)

    def add_quick_note(self, content: str) -> int:
        """
        Добавляет быструю запись
        """
        if not self._current_session or not self._current_topic_id:
            return -1

        return self._quick_note_repo.create(
            session_id=self._current_session.id,
            topic_id=self._current_topic_id,
            content=content
        )

    def get_quick_notes(self) -> List[QuickNote]:
        """Возвращает быстрые записи текущей сессии"""
        if not self._current_session:
            return []

        rows = self._quick_note_repo.get_by_session(self._current_session.id)
        return [QuickNote.from_row(row) for row in rows]

    def get_current_session_id(self) -> Optional[int]:
        """Возвращает ID текущей сессии"""
        return self._current_session.id if self._current_session else None

    def is_session_active(self) -> bool:
        """Возвращает, активна ли сессия"""
        return self._current_session is not None and not self._is_paused

    def is_session_paused(self) -> bool:
        """Возвращает, на паузе ли сессия"""
        return self._current_session is not None and self._is_paused

    def get_session_stats(self, session_id: int) -> Dict[str, Any]:
        """Возвращает статистику по завершённой сессии"""
        session = self._session_repo.get_by_id(session_id)
        if not session:
            return {}

        logs = self._state_log_repo.get_by_session(session_id)
        quick_notes = self._quick_note_repo.get_by_session(session_id)

        conc_vals = [log['value'] for log in logs if log['metric'] == 'concentration']
        energy_vals = [log['value'] for log in logs if log['metric'] == 'energy']
        interest_vals = [log['value'] for log in logs if log['metric'] == 'interest']

        return {
            'id': session['id'],
            'topic_id': session['topic_id'],
            'duration_minutes': session.get('duration_minutes', 0),
            'duration_display': TimeService.format_duration(session.get('duration_minutes', 0)),
            'start_time': session.get('start_time'),
            'end_time': session.get('end_time'),
            'status': session.get('status'),
            'avg_concentration': round(sum(conc_vals) / len(conc_vals), 1) if conc_vals else 0,
            'avg_energy': round(sum(energy_vals) / len(energy_vals), 1) if energy_vals else 0,
            'avg_interest': round(sum(interest_vals) / len(interest_vals), 1) if interest_vals else 0,
            'quick_notes_count': len(quick_notes),
            'state_logs_count': len(logs)
        }

    def get_all_sessions(self) -> List[Dict[str, Any]]:
        """Возвращает все сессии для истории"""
        rows = self._session_repo.get_all()
        sessions = []

        for row in rows:
            topic = self._topic_repo.get_by_id(row['topic_id'])
            sessions.append({
                'id': row['id'],
                'topic_name': topic['name'] if topic else "—",
                'date': row['start_time'][:10] if row['start_time'] else "—",
                'duration_minutes': row.get('duration_minutes', 0),
                'duration_display': TimeService.format_duration(row.get('duration_minutes', 0)),
                'status': row.get('status')
            })

        return sessions

    def cleanup(self):
        """Очищает ресурсы"""
        if self._timer:
            self._timer.stop()
            self._timer = None