# modules/dashboard/__init__.py
from .controller import DashboardController
from .view import DashboardView
from .widgets import KpiCard, KpiRow

__all__ = [
    'DashboardController',
    'DashboardView',
    'KpiCard',
    'KpiRow',
]