# modules/sessions/controller.py
from typing import List, Optional, Dict, Any
from datetime import datetime
from PySide6.QtCore import QTimer, QObject, Signal
import logging

from datebase.db_manager import db
from datebase.repositories.session_repo import SessionRepository
from datebase.repositories.session_state_log_repo import SessionStateLogRepository
from datebase.repositories.quick_note_repo import QuickNoteRepository
from datebase.repositories.topic_repo import TopicRepository
from models.session import Session
from models.quick_note import QuickNote
from services.time_service import TimeService

# Настройка логирования
logger = logging.getLogger(__name__)


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

        self._timer = QTimer()
        self._timer.timeout.connect(self._on_timer_tick)

        # ✅ ИСПРАВЛЕНО: отдельный таймер для каждой метрики
        self._last_log_time: Dict[str, datetime] = {
            'focus': None,
            'energy': None,
            'interest': None
        }

        logger.debug("SessionController инициализирован")

    # ==================== УПРАВЛЕНИЕ ТАЙМЕРОМ ====================

    def _start_timer(self):
        """Запускает таймер (если он ещё не запущен)"""
        try:
            if not self._timer.isActive():
                self._timer.start(1000)
                logger.debug("Таймер сессии запущен")
        except Exception as e:
            logger.error(f"Ошибка запуска таймера: {e}", exc_info=True)

    def _stop_timer(self):
        """Останавливает таймер"""
        try:
            if self._timer.isActive():
                self._timer.stop()
                logger.debug("Таймер сессии остановлен")
        except Exception as e:
            logger.error(f"Ошибка остановки таймера: {e}", exc_info=True)

    def _on_timer_tick(self):
        """Обновление таймера каждую секунду"""
        try:
            if not self._is_paused and self._current_session:
                self._elapsed_seconds += 1
                self.timer_updated.emit(self._elapsed_seconds)

                # ✅ ИСПРАВЛЕНО: безопасное сохранение в БД
                try:
                    db.execute(
                        "UPDATE sessions SET elapsed_seconds = ? WHERE id = ?",
                        (self._elapsed_seconds, self._current_session.id)
                    )
                except Exception as e:
                    # ❗ Критично: не даем ошибке БД остановить таймер
                    logger.warning(f"Не удалось сохранить elapsed_seconds в БД: {e}")
        except Exception as e:
            logger.error(f"Ошибка в _on_timer_tick: {e}", exc_info=True)

    # ==================== НОВАЯ СЕССИЯ ====================

    def start_new_session(self, topic_id: int) -> int:
        """Создаёт и запускает новую сессию"""
        try:
            # Если есть активная сессия - завершаем её
            if self._current_session:
                self.end_session()

            topic = self._topic_repo.get_by_id(topic_id)
            if not topic:
                logger.warning(f"Тема {topic_id} не найдена для сессии")
                return 0

            self._current_topic_id = topic_id
            self._elapsed_seconds = 0
            self._is_paused = False
           #self._last_slider_save_time = None

            # Создаём запись в БД
            session_id = self._session_repo.create(topic_id)
            if not session_id:
                logger.error("Не удалось создать сессию в БД")
                return 0

            self._current_session = Session.from_row(
                self._session_repo.get_by_id(session_id)
            )

            # 🆕 Используем локальное время для start_time
            from utils.local_time import now_local_iso
            start_time = now_local_iso()

            # Обновляем start_time в БД
            try:
                db.execute(
                    "UPDATE sessions SET start_time = ? WHERE id = ?",
                    (start_time, session_id)
                )
            except Exception as e:
                logger.warning(f"Не удалось обновить start_time в БД: {e}")

            self._start_time = datetime.now()

            # Начинаем первый интервал работы
            self.start_interval(session_id)

            # Запускаем таймер
            self._start_timer()

            logger.info(f"Начата новая сессия {session_id} для темы {topic_id}")
            return session_id
        except Exception as e:
            logger.error(f"Ошибка запуска новой сессии: {e}", exc_info=True)
            return 0

    # ==================== ВОЗОБНОВЛЕНИЕ СТАРОЙ СЕССИИ ====================

    def load_and_resume_session(self, session_id: int) -> bool:
        """Загружает старую сессию из БД и возобновляет её"""
        try:
            if self._current_session and self._current_session.id != session_id:
                self.end_session()

            row = self._session_repo.get_by_id(session_id)
            if not row:
                logger.warning(f"Сессия {session_id} не найдена")
                return False

            self._current_session = Session.from_row(row)
            self._current_topic_id = row['topic_id']
            #self._last_slider_save_time = None

            # 🆕 Восстанавливаем время из elapsed_seconds
            self._elapsed_seconds = row.get('elapsed_seconds', 0) or 0

            if row['status'] == 'active':
                self._is_paused = False
                self.start_interval(session_id)
                self._start_timer()
            else:
                self._is_paused = True

            logger.info(f"Возобновлена сессия {session_id}, elapsed: {self._elapsed_seconds} сек")
            return True
        except Exception as e:
            logger.error(f"Ошибка возобновления сессии {session_id}: {e}", exc_info=True)
            return False

    # ==================== ПАУЗА / ВОЗОБНОВЛЕНИЕ ====================

    def pause_session(self):
        """Ставит сессию на паузу"""
        try:
            if self._current_session and not self._is_paused:
                # Завершаем текущий интервал
                self.end_interval(self._current_session.id)

                self._is_paused = True
                self._stop_timer()

                try:
                    self._session_repo.update(self._current_session.id, status='paused')
                except Exception as e:
                    logger.warning(f"Не удалось обновить статус сессии в БД: {e}")

                self.session_paused.emit()
                logger.info(f"Сессия {self._current_session.id} на паузе")
        except Exception as e:
            logger.error(f"Ошибка паузы сессии: {e}", exc_info=True)

    def resume_session(self):
        """Возобновляет текущую сессию"""
        try:
            if self._current_session and self._is_paused:
                self._is_paused = False

                try:
                    self._session_repo.update(self._current_session.id, status='active')
                except Exception as e:
                    logger.warning(f"Не удалось обновить статус сессии в БД: {e}")

                # Начинаем новый интервал работы
                self.start_interval(self._current_session.id)

                # 🆕 Просто запускаем тот же таймер
                self._start_timer()

                self.session_resumed.emit()
                logger.info(f"Сессия {self._current_session.id} возобновлена")
        except Exception as e:
            logger.error(f"Ошибка возобновления сессии: {e}", exc_info=True)

    def end_session(self, auto: bool = False) -> int:
        """Завершает сессию"""
        try:
            if not self._current_session:
                return 0

            session_id = self._current_session.id

            # Завершаем последний интервал
            self.end_interval(session_id)

            # 🆕 Вычисляем длительность из активных интервалов
            intervals = self.get_session_intervals(session_id)
            total_active_seconds = sum(i.get('duration_seconds', 0) for i in intervals)
            duration_minutes = total_active_seconds // 60

            if duration_minutes == 0 and total_active_seconds > 0:
                duration_minutes = 1

            status = 'auto_completed' if auto else 'completed'

            # Используем локальное время для end_time
            from utils.local_time import now_local_iso
            end_time = now_local_iso()

            # Обновляем end_time и другие поля напрямую
            try:
                db.execute(
                    """UPDATE sessions SET end_time = ?, duration_minutes = ?, status = ? 
                    WHERE id = ?""",
                    (end_time, duration_minutes, status, session_id)
                )
            except Exception as e:
                logger.error(f"Не удалось обновить сессию {session_id} в БД: {e}")

            # Останавливаем таймер (но не удаляем)
            self._stop_timer()

            self.session_completed.emit(duration_minutes)

            self._current_session = None
            self._current_topic_id = None
            self._elapsed_seconds = 0
            self._is_paused = False
            #self._last_slider_save_time = None

            logger.info(f"Сессия {session_id} завершена, длительность: {duration_minutes} мин")
            return duration_minutes
        except Exception as e:
            logger.error(f"Ошибка завершения сессии: {e}", exc_info=True)
            # Все равно очищаем состояние
            self._current_session = None
            self._current_topic_id = None
            self._elapsed_seconds = 0
            self._is_paused = False
            #self._last_slider_save_time = None
            self._stop_timer()
            return 0

    # ==================== ИНТЕРВАЛЫ РАБОТЫ ====================

    def start_interval(self, session_id: int) -> int:
        """Начинает новый интервал активности"""
        try:
            from utils.local_time import now_local_iso
            now = now_local_iso()
            cursor = db.execute(
                "INSERT INTO session_intervals (session_id, start_time) VALUES (?, ?)",
                (session_id, now)
            )
            interval_id = cursor.lastrowid
            logger.debug(f"Начат интервал {interval_id} для сессии {session_id}")
            return interval_id
        except Exception as e:
            logger.error(f"Ошибка начала интервала для сессии {session_id}: {e}", exc_info=True)
            return 0

    def end_interval(self, session_id: int) -> int:
        """Завершает текущий интервал и возвращает его длительность"""
        try:
            from utils.local_time import now_local_iso
            row = db.fetchone(
                "SELECT id, start_time FROM session_intervals WHERE session_id = ? AND end_time IS NULL ORDER BY id DESC",
                (session_id,)
            )
            if row:
                now = now_local_iso()
                try:
                    start_time = datetime.fromisoformat(row['start_time'])
                    duration = int((datetime.now() - start_time).total_seconds())
                except (ValueError, TypeError) as e:
                    logger.warning(f"Неверный формат start_time для интервала {row['id']}: {e}")
                    duration = 0

                try:
                    db.execute(
                        "UPDATE session_intervals SET end_time = ?, duration_seconds = ? WHERE id = ?",
                        (now, duration, row['id'])
                    )
                except Exception as e:
                    logger.warning(f"Не удалось обновить интервал {row['id']} в БД: {e}")

                logger.debug(f"Завершен интервал {row['id']}, длительность: {duration} сек")
                return duration
            return 0
        except Exception as e:
            logger.error(f"Ошибка завершения интервала для сессии {session_id}: {e}", exc_info=True)
            return 0

    def get_session_intervals(self, session_id: int) -> list:
        """Возвращает все интервалы сессии"""
        try:
            return db.fetchall(
                "SELECT * FROM session_intervals WHERE session_id = ? ORDER BY start_time ASC",
                (session_id,)
            )
        except Exception as e:
            logger.error(f"Ошибка получения интервалов сессии {session_id}: {e}", exc_info=True)
            return []

    # ==================== ПОЛЗУНКИ СОСТОЯНИЯ ====================

    def log_state(self, metric: str, value: int):
        """Логирует изменение состояния (только при отпускании ползунка)"""
        try:
            if not self._current_session:
                return

            # ✅ Сохраняем значение ползунка в БД (теперь только при отпускании)
            self.save_slider_value(metric, value)

            now = datetime.now()
            should_log = False
            last_time = self._last_log_time.get(metric)

            if last_time is None:
                should_log = True
            elif (now - last_time).total_seconds() >= 60:
                should_log = True

            if should_log:
                minute = self.get_duration_minutes()
                try:
                    self._state_log_repo.create(
                        session_id=self._current_session.id,
                        metric=metric,
                        value=value,
                        minute=minute
                    )
                    self._last_log_time[metric] = now
                    logger.debug(f"Залогировано состояние {metric}={value} на {minute} минуте")
                except Exception as e:
                    logger.warning(f"Не удалось сохранить лог состояния в БД: {e}")

            self.state_changed.emit(metric, value)
        except Exception as e:
            logger.error(f"Ошибка логирования состояния {metric}: {e}", exc_info=True)

    def save_slider_value(self, metric: str, value: int):
        """Сохраняет одно значение ползунка в БД"""
        try:
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
        except Exception as e:
            logger.warning(f"Не удалось сохранить значение ползунка {metric} в БД: {e}")

    def save_slider_values(self, focus: int, energy: int, interest: int):
        """Сохраняет все значения ползунков в БД"""
        try:
            if not self._current_session:
                return

            db.execute(
                "UPDATE sessions SET focus = ?, energy = ?, interest = ? WHERE id = ?",
                (focus, energy, interest, self._current_session.id)
            )
        except Exception as e:
            logger.warning(f"Не удалось сохранить значения ползунков в БД: {e}")

    def get_slider_values(self, session_id: int) -> dict:
        """Возвращает сохранённые значения ползунков"""
        try:
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
        except Exception as e:
            logger.error(f"Ошибка получения значений ползунков сессии {session_id}: {e}", exc_info=True)
            return {"focus": 50, "energy": 50, "interest": 50}

    # ==================== УПРАВЛЕНИЕ СЕССИЯМИ ====================

    def delete_session(self, session_id: int):
        """Удаляет сессию и все связанные данные"""
        try:
            # Если удаляем текущую сессию - останавливаем таймер
            if self._current_session and self._current_session.id == session_id:
                self._stop_timer()
                self._current_session = None
                self._current_topic_id = None
                self._elapsed_seconds = 0
                self._is_paused = False

            try:
                db.execute("DELETE FROM session_state_logs WHERE session_id = ?", (session_id,))
                db.execute("DELETE FROM quick_notes WHERE session_id = ?", (session_id,))
                db.execute("DELETE FROM session_intervals WHERE session_id = ?", (session_id,))
                db.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
                logger.info(f"Удалена сессия {session_id} и все связанные данные")
            except Exception as e:
                logger.error(f"Ошибка удаления сессии {session_id} из БД: {e}", exc_info=True)
        except Exception as e:
            logger.error(f"Ошибка удаления сессии {session_id}: {e}", exc_info=True)

    def get_session(self, session_id: int) -> Optional[Session]:
        """Возвращает объект Session по ID"""
        try:
            row = self._session_repo.get_by_id(session_id)
            return Session.from_row(row) if row else None
        except Exception as e:
            logger.error(f"Ошибка получения сессии {session_id}: {e}", exc_info=True)
            return None

    def get_sessions_by_topic(self, topic_id: int) -> List[Session]:
        """Возвращает все сессии темы"""
        try:
            rows = db.fetchall(
                "SELECT * FROM sessions WHERE topic_id = ? ORDER BY start_time DESC",
                (topic_id,)
            )
            return [Session.from_row(row) for row in rows]
        except Exception as e:
            logger.error(f"Ошибка получения сессий темы {topic_id}: {e}", exc_info=True)
            return []

    # ==================== ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ ====================

    def get_elapsed_seconds(self) -> int:
        return self._elapsed_seconds

    def get_elapsed_display(self) -> str:
        try:
            return TimeService.format_time(self._elapsed_seconds)
        except Exception as e:
            logger.error(f"Ошибка форматирования времени: {e}", exc_info=True)
            return "0:00"

    def get_duration_minutes(self) -> int:
        return self._elapsed_seconds // 60

    def add_quick_note(self, content: str) -> int:
        try:
            if not self._current_session or not self._current_topic_id:
                return -1

            note_id = self._quick_note_repo.create(
                session_id=self._current_session.id,
                topic_id=self._current_topic_id,
                content=content
            )
            if note_id:
                logger.debug(f"Добавлена быстрая запись {note_id} в сессию {self._current_session.id}")
            return note_id
        except Exception as e:
            logger.error(f"Ошибка добавления быстрой записи: {e}", exc_info=True)
            return -1

    def get_quick_notes(self) -> List[QuickNote]:
        try:
            if not self._current_session:
                return []

            rows = self._quick_note_repo.get_by_session(self._current_session.id)
            return [QuickNote.from_row(row) for row in rows]
        except Exception as e:
            logger.error(f"Ошибка получения быстрых записей: {e}", exc_info=True)
            return []

    def get_current_session_id(self) -> Optional[int]:
        return self._current_session.id if self._current_session else None

    def is_session_active(self) -> bool:
        return self._current_session is not None and not self._is_paused

    def is_session_paused(self) -> bool:
        return self._current_session is not None and self._is_paused

    def has_active_or_paused_session(self, topic_id: int = None) -> tuple:
        try:
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
        except Exception as e:
            logger.error(f"Ошибка проверки активной сессии: {e}", exc_info=True)
            return False, None, None, None

    def check_and_pause_active_session(self):
        """При запуске приложения ставит на паузу все 'active' сессии"""
        try:
            rows = db.fetchall(
                """SELECT id FROM sessions WHERE status = 'active'"""
            )
            for row in rows:
                try:
                    db.execute(
                        "UPDATE sessions SET status = ? WHERE id = ?",
                        ('paused', row['id'])
                    )
                    logger.info(f"Сессия {row['id']} переведена в паузу при запуске")
                except Exception as e:
                    logger.warning(f"Не удалось поставить сессию {row['id']} на паузу: {e}")
        except Exception as e:
            logger.error(f"Ошибка проверки активных сессий при запуске: {e}", exc_info=True)

    def get_session_stats(self, session_id: int) -> Dict[str, Any]:
        try:
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
        except Exception as e:
            logger.error(f"Ошибка получения статистики сессии {session_id}: {e}", exc_info=True)
            return {}

    def get_all_sessions(self) -> List[Dict[str, Any]]:
        try:
            rows = self._session_repo.get_all()
            sessions = []
            for row in rows:
                try:
                    topic = self._topic_repo.get_by_id(row['topic_id'])
                    sessions.append({
                        'id': row['id'],
                        'topic_name': topic['name'] if topic else "—",
                        'date': row['start_time'][:10] if row['start_time'] else "—",
                        'duration_minutes': row.get('duration_minutes') or 0,
                        'duration_display': TimeService.format_duration(row.get('duration_minutes')),
                        'status': row.get('status')
                    })
                except Exception as e:
                    logger.warning(f"Не удалось загрузить данные сессии {row.get('id')}: {e}")
            return sessions
        except Exception as e:
            logger.error(f"Ошибка получения всех сессий: {e}", exc_info=True)
            return []

    def cleanup(self):
        """Очищает ресурсы"""
        try:
            self._stop_timer()
            logger.debug("SessionController очищен")
        except Exception as e:
            logger.error(f"Ошибка очистки SessionController: {e}", exc_info=True)