# modules/analytics/charts.py
import matplotlib

matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from PySide6.QtWidgets import QWidget, QVBoxLayout, QSizePolicy
from PySide6.QtCore import Qt

import matplotlib.pyplot as plt
import numpy as np


class AnalyticsCharts(QWidget):
    """
    Виджет для отображения графиков аналитики с использованием matplotlib.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        """Настраивает интерфейс"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.figure = Figure(figsize=(8, 4), dpi=100, facecolor='#f5f5f5')
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Добавляем тулбар
        self.toolbar = NavigationToolbar(self.canvas, self)

        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)

        self.axes = {}

    def clear(self):
        """Очищает все графики"""
        self.figure.clear()
        self.axes = {}
        self.canvas.draw()

    def plot_metric_trend(self, dates: list, values: list, title: str, ylabel: str, color: str = '#1976d2'):
        """
        Строит линейный график метрики по сессиям
        """
        self.figure.clear()
        ax = self.figure.add_subplot(111)

        if dates and values:
            ax.plot(dates, values, marker='o', linewidth=2, color=color, markersize=6)
            ax.set_xlabel('Дата сессии')
            ax.set_ylabel(ylabel)
            ax.set_title(title)
            ax.grid(True, alpha=0.3)
            ax.set_ylim(0, 5.5)

            # Поворот подписей X
            plt.setp(ax.get_xticklabels(), rotation=45, ha='right')

        self.figure.tight_layout()
        self.canvas.draw()

    def plot_comparison_trend(self, data: dict, title: str = "Динамика показателей"):
        """
        Строит график сравнения всех трёх метрик

        Args:
            data: {'concentration': (dates, values), 'energy': (dates, values), 'interest': (dates, values)}
        """
        self.figure.clear()
        ax = self.figure.add_subplot(111)

        colors = {'concentration': '#1976d2', 'energy': '#ff9800', 'interest': '#4caf50'}
        labels = {'concentration': 'Концентрация', 'energy': 'Энергия', 'interest': 'Интерес'}

        for metric, (dates, values) in data.items():
            if dates and values:
                ax.plot(dates, values, marker='o', linewidth=2, color=colors.get(metric, '#888'),
                        label=labels.get(metric, metric), markersize=5)

        ax.set_xlabel('Дата сессии')
        ax.set_ylabel('Уровень (1-5)')
        ax.set_title(title)
        ax.legend(loc='best')
        ax.grid(True, alpha=0.3)
        ax.set_ylim(0, 5.5)

        plt.setp(ax.get_xticklabels(), rotation=45, ha='right')

        self.figure.tight_layout()
        self.canvas.draw()

    def plot_hour_stats(self, hour_stats: dict):
        """
        Строит график продуктивности по часам
        """
        self.figure.clear()
        ax = self.figure.add_subplot(111)

        hours = list(range(24))
        conc_values = [hour_stats[h].get('avg_concentration', 0) for h in hours]

        ax.bar(hours, conc_values, color='#1976d2', alpha=0.7)
        ax.set_xlabel('Час дня')
        ax.set_ylabel('Средняя концентрация (1-5)')
        ax.set_title('Продуктивность по часам')
        ax.set_xticks(range(0, 24, 2))
        ax.set_ylim(0, 5.5)
        ax.grid(True, alpha=0.3, axis='y')

        self.figure.tight_layout()
        self.canvas.draw()

    def plot_day_stats(self, day_stats: dict):
        """
        Строит график продуктивности по дням недели
        """
        self.figure.clear()
        ax = self.figure.add_subplot(111)

        days = [day_stats[d]['name'] for d in range(7)]
        conc_values = [day_stats[d].get('avg_concentration', 0) for d in range(7)]

        bars = ax.bar(days, conc_values,
                      color=['#1976d2', '#2196f3', '#42a5f5', '#64b5f6', '#90caf9', '#bbdefb', '#e3f2fd'])
        ax.set_xlabel('День недели')
        ax.set_ylabel('Средняя концентрация (1-5)')
        ax.set_title('Продуктивность по дням недели')
        ax.set_ylim(0, 5.5)
        ax.grid(True, alpha=0.3, axis='y')

        self.figure.tight_layout()
        self.canvas.draw()

    def plot_task_completion(self, timeline_data: dict):
        """
        Строит график выполнения задач по неделям
        """
        self.figure.clear()
        ax = self.figure.add_subplot(111)

        weeks = timeline_data.get('weeks', [])
        created = timeline_data.get('created', [])
        completed = timeline_data.get('completed', [])

        if weeks:
            x = np.arange(len(weeks))
            width = 0.35

            bars1 = ax.bar(x - width / 2, created, width, label='Создано', color='#ff9800', alpha=0.7)
            bars2 = ax.bar(x + width / 2, completed, width, label='Выполнено', color='#4caf50', alpha=0.7)

            ax.set_xlabel('Неделя')
            ax.set_ylabel('Количество задач')
            ax.set_title('Динамика задач по неделям')
            ax.set_xticks(x)
            ax.set_xticklabels(weeks, rotation=45, ha='right')
            ax.legend()
            ax.grid(True, alpha=0.3, axis='y')

        self.figure.tight_layout()
        self.canvas.draw()

    def plot_session_duration_distribution(self, sessions):
        """
        Строит гистограмму распределения длительности сессий
        """
        self.figure.clear()
        ax = self.figure.add_subplot(111)

        durations = [s.duration_minutes for s in sessions if s.duration_minutes]

        if durations:
            ax.hist(durations, bins=10, color='#1976d2', alpha=0.7, edgecolor='white')
            ax.set_xlabel('Длительность (минуты)')
            ax.set_ylabel('Количество сессий')
            ax.set_title('Распределение длительности сессий')
            ax.grid(True, alpha=0.3, axis='y')

        self.figure.tight_layout()
        self.canvas.draw()

    def plot_radar_chart(self, avg_concentration: float, avg_energy: float, avg_interest: float):
        """
        Строит лепестковую диаграмму средних показателей
        """
        self.figure.clear()
        ax = self.figure.add_subplot(111, projection='polar')

        categories = ['Концентрация', 'Энергия', 'Интерес']
        values = [avg_concentration, avg_energy, avg_interest]

        angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False).tolist()
        values += values[:1]
        angles += angles[:1]

        ax.plot(angles, values, 'o-', linewidth=2, color='#1976d2')
        ax.fill(angles, values, alpha=0.25, color='#1976d2')
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(categories)
        ax.set_ylim(0, 5)
        ax.set_title('Средние показатели состояния', pad=20)

        self.figure.tight_layout()
        self.canvas.draw()


class ZoomableChart(QWidget):
    """
    Виджет с зумом для графиков (обёртка над FigureCanvas с дополнительными кнопками)
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.figure = Figure(figsize=(8, 5), dpi=100, facecolor='#f5f5f5')
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)

        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)

        self.ax = None

    def set_data(self, x_data, y_data, title: str, xlabel: str, ylabel: str, color: str = '#1976d2'):
        """Устанавливает данные для отображения"""
        self.figure.clear()
        self.ax = self.figure.add_subplot(111)

        self.ax.plot(x_data, y_data, marker='o', linewidth=2, color=color, markersize=5)
        self.ax.set_xlabel(xlabel)
        self.ax.set_ylabel(ylabel)
        self.ax.set_title(title)
        self.ax.grid(True, alpha=0.3)

        self.figure.tight_layout()
        self.canvas.draw()

    def clear(self):
        """Очищает график"""
        self.figure.clear()
        self.canvas.draw()