# modules/sessions/state_log_controller.py
from typing import List, Dict, Any
from datebase.repositories.session_state_log_repo import SessionStateLogRepository


class SessionStateLogController:
    """
    Контроллер для работы с логами состояния сессий.
    """

    def __init__(self, state_log_repo: SessionStateLogRepository):
        self._repo = state_log_repo

    def get_logs_for_session(self, session_id: int) -> List[Dict[str, Any]]:
        """Возвращает все логи состояния для сессии"""
        return self._repo.get_by_session(session_id)

    def get_metrics_summary(self, session_id: int) -> Dict[str, Any]:
        """Возвращает сводку по метрикам сессии"""
        return self._repo.get_metrics_summary(session_id)

    def get_focus_timeline(self, session_id: int) -> List[Dict[str, Any]]:
        """Возвращает таймлайн концентрации"""
        logs = self.get_logs_for_session(session_id)

        result = []
        for log in logs:
            if log['metric'] == 'focus':
                result.append({
                    'minute': log['minute'],
                    'value': log['value']
                })

        return result

    def get_energy_timeline(self, session_id: int) -> List[Dict[str, Any]]:
        """Возвращает таймлайн энергии"""
        logs = self.get_logs_for_session(session_id)

        result = []
        for log in logs:
            if log['metric'] == 'energy':
                result.append({
                    'minute': log['minute'],
                    'value': log['value']
                })

        return result

    def get_interest_timeline(self, session_id: int) -> List[Dict[str, Any]]:
        """Возвращает таймлайн интереса"""
        logs = self.get_logs_for_session(session_id)

        result = []
        for log in logs:
            if log['metric'] == 'interest':
                result.append({
                    'minute': log['minute'],
                    'value': log['value']
                })

        return result

    def get_all_metrics_timeline(self, session_id: int) -> Dict[str, List[Dict[str, Any]]]:
        """Возвращает таймлайны всех метрик"""
        return {
            'focus': self.get_focus_timeline(session_id),
            'energy': self.get_energy_timeline(session_id),
            'interest': self.get_interest_timeline(session_id)
        }