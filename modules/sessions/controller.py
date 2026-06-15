from typing import List, Optional, Dict, Any
from datetime import datetime
from PySide6.QtCore import QTimer, QObject, Signal

from datebase.db_manager import db
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
    Управляет таймером, паузами, состоянием сессии, интервалами работы.
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
        self._is_paused: bool = False
        self._start_time: Optional[datetime] = None

        # 🆕 ОДИН таймер на весь жизненный цикл контроллера
        self._timer = QTimer()
        self._timer.timeout.connect(self._on_timer_tick)

        # Для ограничения сохранения ползунков (не чаще раза в минуту)
        self._last_slider_save_time: Optional[datetime] = None

    # ==================== УПРАВЛЕНИЕ ТАЙМЕРОМ ====================

    def _start_timer(self):
        """Запускает таймер (если он ещё не запущен)"""
        if not self._timer.isActive():
            self._timer.start(1000)

    def _stop_timer(self):
        """Останавливает таймер"""
        if self._timer.isActive():
            self._timer.stop()

    def _on_timer_tick(self):
        """Обновление таймера каждую секунду"""
        if not self._is_paused and self._current_session:
            self._elapsed_seconds += 1
            self.timer_updated.emit(self._elapsed_seconds)

    # ==================== НОВАЯ СЕССИЯ ====================

    def start_new_session(self, topic_id: int) -> int:
        """Создаёт и запускает новую сессию"""
        # Если есть активная сессия - завершаем её
        if self._current_session:
            self.end_session()

        topic = self._topic_repo.get_by_id(topic_id)
        if not topic:
            return 0

        self._current_topic_id = topic_id
        self._elapsed_seconds = 0
        self._is_paused = False
        self._last_slider_save_time = None

        # Создаём запись в БД
        session_id = self._session_repo.create(topic_id)
        self._current_session = Session.from_row(
            self._session_repo.get_by_id(session_id)
        )
        self._start_time = datetime.now()

        # Начинаем первый интервал работы
        self.start_interval(session_id)

        # Запускаем таймер
        self._start_timer()

        return session_id

    # ==================== ВОЗОБНОВЛЕНИЕ СТАРОЙ СЕССИИ ====================

    def load_and_resume_session(self, session_id: int) -> bool:
        """
        Загружает старую сессию из БД и возобновляет её.
        Возвращает True если успешно.
        """
        # Если есть другая активная сессия - завершаем её
        if self._current_session and self._current_session.id != session_id:
            self.end_session()

        row = self._session_repo.get_by_id(session_id)
        if not row:
            return False

        # Восстанавливаем состояние
        self._current_session = Session.from_row(row)
        self._current_topic_id = row['topic_id']
        self._last_slider_save_time = None

        # Восстанавливаем время
        duration_minutes = row.get('duration_minutes', 0) or 0
        self._elapsed_seconds = duration_minutes * 60

        # Если сессия была активна - продолжаем
        if row['status'] == 'active':
            self._is_paused = False
            # Начинаем новый интервал работы
            self.start_interval(session_id)
            # Запускаем таймер
            self._start_timer()
        else:
            # Сессия на паузе - таймер не запускаем
            self._is_paused = True

        return True

    # ==================== ПАУЗА / ВОЗОБНОВЛЕНИЕ ====================

    def pause_session(self):
        """Ставит сессию на паузу"""
        if self._current_session and not self._is_paused:
            # Завершаем текущий интервал
            self.end_interval(self._current_session.id)

            self._is_paused = True
            self._stop_timer()  # 🆕 Просто останавливаем таймер
            self._session_repo.update(self._current_session.id, status='paused')
            self.session_paused.emit()

    def resume_session(self):
        """Возобновляет текущую сессию"""
        if self._current_session and self._is_paused:
            self._is_paused = False
            self._session_repo.update(self._current_session.id, status='active')

            # Начинаем новый интервал работы
            self.start_interval(self._current_session.id)

            # 🆕 Просто запускаем тот же таймер
            self._start_timer()

            self.session_resumed.emit()

    def end_session(self, auto: bool = False) -> int:
        """Завершает сессию"""
        if not self._current_session:
            return 0

        # Завершаем последний интервал
        self.end_interval(self._current_session.id)

        duration_minutes = self._elapsed_seconds // 60
        if duration_minutes == 0 and self._elapsed_seconds > 0:
            duration_minutes = 1

        status = 'auto_completed' if auto else 'completed'
        self._session_repo.end_session(
            self._current_session.id,
            duration_minutes,
            status
        )

        # 🆕 Останавливаем таймер (но не удаляем)
        self._stop_timer()

        self.session_completed.emit(duration_minutes)

        session_id = self._current_session.id
        self._current_session = None
        self._current_topic_id = None
        self._elapsed_seconds = 0
        self._is_paused = False
        self._last_slider_save_time = None

        return duration_minutes

    # ==================== ИНТЕРВАЛЫ РАБОТЫ ====================

    def start_interval(self, session_id: int) -> int:
        """Начинает новый интервал активности"""
        from utils.local_time import now_local_iso
        now = now_local_iso()
        cursor = db.execute(
            "INSERT INTO session_intervals (session_id, start_time) VALUES (?, ?)",
            (session_id, now)
        )
        return cursor.lastrowid

    def end_interval(self, session_id: int) -> int:
        """Завершает текущий интервал и возвращает его длительность"""
        from utils.local_time import now_local_iso
        row = db.fetchone(
            "SELECT id, start_time FROM session_intervals WHERE session_id = ? AND end_time IS NULL ORDER BY id DESC",
            (session_id,)
        )
        if row:
            now = now_local_iso()
            start_time = datetime.fromisoformat(row['start_time'])
            duration = int((datetime.now() - start_time).total_seconds())
            db.execute(
                "UPDATE session_intervals SET end_time = ?, duration_seconds = ? WHERE id = ?",
                (now, duration, row['id'])
            )
            return duration
        return 0

    def get_session_intervals(self, session_id: int) -> list:
        """Возвращает все интервалы сессии"""
        return db.fetchall(
            "SELECT * FROM session_intervals WHERE session_id = ? ORDER BY start_time ASC",
            (session_id,)
        )

    # ==================== ПОЛЗУНКИ СОСТОЯНИЯ ====================

    def log_state(self, metric: str, value: int):
        """Логирует изменение состояния с ограничением (не чаще раза в минуту)"""
        if not self._current_session:
            return

        now = datetime.now()

        should_save = False
        if self._last_slider_save_time is None:
            should_save = True
        elif (now - self._last_slider_save_time).total_seconds() >= 60:
            should_save = True

        if should_save:
            minute = self.get_duration_minutes()
            self._state_log_repo.create(
                session_id=self._current_session.id,
                metric=metric,
                value=value,
                minute=minute
            )

            self.save_slider_value(metric, value)
            self._last_slider_save_time = now

        self.state_changed.emit(metric, value)

    def save_slider_value(self, metric: str, value: int):
        """Сохраняет одно значение ползунка в БД"""
        if not self._current_session:
            return

        column_map = {
            'focus': 'focus',
            'energy': 'energy',
            'interest': 'interest'
        }

        column = column_map.get(metric)
        if column:
            db.execute(
                f"UPDATE sessions SET {column} = ? WHERE id = ?",
                (value, self._current_session.id)
            )

    def save_slider_values(self, focus: int, energy: int, interest: int):
        """Сохраняет все значения ползунков в БД"""
        if not self._current_session:
            return

        db.execute(
            "UPDATE sessions SET focus = ?, energy = ?, interest = ? WHERE id = ?",
            (focus, energy, interest, self._current_session.id)
        )

    def get_slider_values(self, session_id: int) -> dict:
        """Возвращает сохранённые значения ползунков"""
        row = db.fetchone(
            "SELECT focus, energy, interest FROM sessions WHERE id = ?",
            (session_id,)
        )
        if row:
            return {
                "focus": row.get("focus", 50),
                "energy": row.get("energy", 50),
                "interest": row.get("interest", 50)
            }
        return {"focus": 50, "energy": 50, "interest": 50}

    # ==================== УПРАВЛЕНИЕ СЕССИЯМИ ====================

    def delete_session(self, session_id: int):
        """Удаляет сессию и все связанные данные"""
        # Если удаляем текущую сессию - останавливаем таймер
        if self._current_session and self._current_session.id == session_id:
            self._stop_timer()
            self._current_session = None
            self._current_topic_id = None
            self._elapsed_seconds = 0
            self._is_paused = False

        db.execute("DELETE FROM session_state_logs WHERE session_id = ?", (session_id,))
        db.execute("DELETE FROM quick_notes WHERE session_id = ?", (session_id,))
        db.execute("DELETE FROM session_intervals WHERE session_id = ?", (session_id,))
        db.execute("DELETE FROM sessions WHERE id = ?", (session_id,))

    def get_session(self, session_id: int) -> Optional[Session]:
        """Возвращает объект Session по ID"""
        row = self._session_repo.get_by_id(session_id)
        return Session.from_row(row) if row else None

    def get_sessions_by_topic(self, topic_id: int) -> List[Session]:
        """Возвращает все сессии темы"""
        rows = db.fetchall(
            "SELECT * FROM sessions WHERE topic_id = ? ORDER BY start_time DESC",
            (topic_id,)
        )
        return [Session.from_row(row) for row in rows]

    # ==================== ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ ====================

    def get_elapsed_seconds(self) -> int:
        return self._elapsed_seconds

    def get_elapsed_display(self) -> str:
        return TimeService.format_time(self._elapsed_seconds)

    def get_duration_minutes(self) -> int:
        return self._elapsed_seconds // 60

    def add_quick_note(self, content: str) -> int:
        if not self._current_session or not self._current_topic_id:
            return -1

        return self._quick_note_repo.create(
            session_id=self._current_session.id,
            topic_id=self._current_topic_id,
            content=content
        )

    def get_quick_notes(self) -> List[QuickNote]:
        if not self._current_session:
            return []

        rows = self._quick_note_repo.get_by_session(self._current_session.id)
        return [QuickNote.from_row(row) for row in rows]

    def get_current_session_id(self) -> Optional[int]:
        return self._current_session.id if self._current_session else None

    def is_session_active(self) -> bool:
        return self._current_session is not None and not self._is_paused

    def is_session_paused(self) -> bool:
        return self._current_session is not None and self._is_paused

    def has_active_or_paused_session(self, topic_id: int = None) -> tuple:
        if topic_id:
            rows = db.fetchall(
                """SELECT id, status, topic_id FROM sessions 
                WHERE topic_id = ? AND status IN ('active', 'paused')
                ORDER BY start_time DESC""",
                (topic_id,)
            )
        else:
            rows = db.fetchall(
                """SELECT id, status, topic_id FROM sessions 
                WHERE status IN ('active', 'paused')
                ORDER BY start_time DESC""",
            )

        if rows:
            session = rows[0]
            return True, session['id'], session['status'], session['topic_id']
        return False, None, None, None

    def check_and_pause_active_session(self):
        """При запуске приложения ставит на паузу все 'active' сессии"""
        rows = db.fetchall(
            """SELECT id FROM sessions WHERE status = 'active'"""
        )
        for row in rows:
            db.execute(
                "UPDATE sessions SET status = ? WHERE id = ?",
                ('paused', row['id'])
            )

    def get_session_stats(self, session_id: int) -> Dict[str, Any]:
        session = self._session_repo.get_by_id(session_id)
        if not session:
            return {}

        logs = self._state_log_repo.get_by_session(session_id)
        quick_notes = self._quick_note_repo.get_by_session(session_id)
        intervals = self.get_session_intervals(session_id)

        focus_vals = [log['value'] for log in logs if log['metric'] == 'focus']
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
            'avg_focus': round(sum(focus_vals) / len(focus_vals), 1) if focus_vals else 0,
            'avg_energy': round(sum(energy_vals) / len(energy_vals), 1) if energy_vals else 0,
            'avg_interest': round(sum(interest_vals) / len(interest_vals), 1) if interest_vals else 0,
            'quick_notes_count': len(quick_notes),
            'intervals_count': len(intervals),
            'total_active_seconds': sum(i.get('duration_seconds', 0) for i in intervals)
        }

    def get_all_sessions(self) -> List[Dict[str, Any]]:
        rows = self._session_repo.get_all()
        sessions = []
        for row in rows:
            topic = self._topic_repo.get_by_id(row['topic_id'])
            sessions.append({
                'id': row['id'],
                'topic_name': topic['name'] if topic else "—",
                'date': row['start_time'][:10] if row['start_time'] else "—",
                'duration_minutes': row.get('duration_minutes') or 0,
                'duration_display': TimeService.format_duration(row.get('duration_minutes')),
                'status': row.get('status')
            })
        return sessions

    def cleanup(self):
        """Очищает ресурсы"""
        self._stop_timer()