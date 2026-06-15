# modules/dashboard/__init__.py
from .controller import DashboardController
from .view import DashboardView
from .widgets import KpiRow, KpiCard

__all__ = [
    'DashboardController',
    'DashboardView',
    'KpiCard',
    'KpiRow',
]