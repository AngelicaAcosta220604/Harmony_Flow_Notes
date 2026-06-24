# database/repositories/session_state_log_repo.py
from typing import List, Dict, Any
from database.db_manager import db


class SessionStateLogRepository:
    """Репозиторий для работы с логами состояния сессий"""

    def get_by_session(self, session_id: int) -> List[Dict[str, Any]]:
        """Возвращает все логи состояния для сессии"""
        return db.fetchall(
            "SELECT * FROM session_state_logs WHERE session_id = ? ORDER BY minute ASC",
            (session_id,)
        )

    def create(self, session_id: int, metric: str, value: int, minute: int) -> int:
        """Создаёт запись лога состояния"""
        return db.insert('session_state_logs', {
            'session_id': session_id,
            'metric': metric,
            'value': value,
            'minute': minute
        })

    def delete_by_session(self, session_id: int) -> int:
        """Удаляет все логи сессии"""
        return db.delete('session_state_logs', 'session_id = ?', (session_id,))

    def get_metrics_summary(self, session_id: int) -> Dict[str, Any]:
        """Возвращает сводку по метрикам сессии"""
        logs = self.get_by_session(session_id)

        summary = {
            'concentration': [],
            'energy': [],
            'interest': []
        }

        for log in logs:
            metric = log['metric']
            if metric in summary:
                summary[metric].append(log['value'])

        result = {}
        for metric, values in summary.items():
            if values:
                result[f'avg_{metric}'] = sum(values) / len(values)
                result[f'max_{metric}'] = max(values)
                result[f'min_{metric}'] = min(values)
                result[f'count_{metric}'] = len(values)
            else:
                result[f'avg_{metric}'] = 0
                result[f'max_{metric}'] = 0
                result[f'min_{metric}'] = 0
                result[f'count_{metric}'] = 0

        return result