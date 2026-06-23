# modules/analytics/charts.py
import matplotlib
import logging

# ✅ ИСПРАВЛЕНО: используем Qt5Agg для совместимости с PySide6
matplotlib.use('Qt5Agg')

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from PySide6.QtWidgets import QWidget, QVBoxLayout, QSizePolicy
from PySide6.QtCore import Qt

import matplotlib.pyplot as plt
import numpy as np

# Настройка логирования
logger = logging.getLogger(__name__)


class AnalyticsCharts(QWidget):
    """
    Виджет для отображения графиков аналитики с использованием matplotlib.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        """Настраивает интерфейс"""
        try:
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
            logger.debug("AnalyticsCharts инициализирован")
        except Exception as e:
            logger.error(f"Ошибка настройки AnalyticsCharts: {e}", exc_info=True)

    def clear(self):
        """Очищает все графики"""
        try:
            self.figure.clear()
            self.axes = {}
            self.canvas.draw()
        except Exception as e:
            logger.error(f"Ошибка очистки графиков: {e}", exc_info=True)

    def plot_metric_trend(self, dates: list, values: list, title: str, ylabel: str, color: str = '#1976d2'):
        """
        Строит линейный график метрики по сессиям
        """
        try:
            # ✅ ИСПРАВЛЕНО: проверка на None и пустые данные
            if dates is None or values is None:
                logger.warning("plot_metric_trend: dates или values равно None")
                dates = dates or []
                values = values or []

            self.figure.clear()
            ax = self.figure.add_subplot(111)

            if dates and values and len(dates) == len(values):
                ax.plot(dates, values, marker='o', linewidth=2, color=color, markersize=6)
                ax.set_xlabel('Дата сессии')
                ax.set_ylabel(ylabel)
                ax.set_title(title)
                ax.grid(True, alpha=0.3)
                ax.set_ylim(0, 5.5)

                # Поворот подписей X
                if ax.get_xticklabels():
                    plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
            else:
                ax.text(0.5, 0.5, 'Нет данных для отображения',
                        ha='center', va='center', transform=ax.transAxes,
                        fontsize=12, color='#888888')
                ax.set_title(title)

            self.figure.tight_layout()
            self.canvas.draw()
            logger.debug(f"График '{title}' построен: {len(dates)} точек")
        except Exception as e:
            logger.error(f"Ошибка построения графика '{title}': {e}", exc_info=True)
            # Показываем ошибку на графике
            try:
                self.figure.clear()
                ax = self.figure.add_subplot(111)
                ax.text(0.5, 0.5, f'Ошибка построения графика:\n{str(e)[:100]}',
                        ha='center', va='center', transform=ax.transAxes,
                        fontsize=10, color='#EF4444')
                self.figure.tight_layout()
                self.canvas.draw()
            except:
                pass

    def plot_comparison_trend(self, data: dict, title: str = "Динамика показателей"):
        """
        Строит график сравнения всех трёх метрик

        Args:
            data: {'concentration': (dates, values), 'energy': (dates, values), 'interest': (dates, values)}
        """
        try:
            # ✅ ИСПРАВЛЕНО: проверка на None
            if data is None:
                logger.warning("plot_comparison_trend: data равно None")
                data = {}

            self.figure.clear()
            ax = self.figure.add_subplot(111)

            colors = {'concentration': '#1976d2', 'energy': '#ff9800', 'interest': '#4caf50'}
            labels = {'concentration': 'Концентрация', 'energy': 'Энергия', 'interest': 'Интерес'}

            has_data = False
            for metric, metric_data in data.items():
                if metric_data is None:
                    continue
                dates, values = metric_data
                if dates and values and len(dates) == len(values):
                    ax.plot(dates, values, marker='o', linewidth=2, color=colors.get(metric, '#888'),
                            label=labels.get(metric, metric), markersize=5)
                    has_data = True

            if has_data:
                ax.set_xlabel('Дата сессии')
                ax.set_ylabel('Уровень (1-5)')
                ax.set_title(title)
                ax.legend(loc='best')
                ax.grid(True, alpha=0.3)
                ax.set_ylim(0, 5.5)

                if ax.get_xticklabels():
                    plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
            else:
                ax.text(0.5, 0.5, 'Нет данных для отображения',
                        ha='center', va='center', transform=ax.transAxes,
                        fontsize=12, color='#888888')
                ax.set_title(title)

            self.figure.tight_layout()
            self.canvas.draw()
            logger.debug(f"График сравнения построен: {len(data)} метрик")
        except Exception as e:
            logger.error(f"Ошибка построения графика сравнения: {e}", exc_info=True)

    def plot_hour_stats(self, hour_stats: dict):
        """
        Строит график продуктивности по часам
        """
        try:
            # ✅ ИСПРАВЛЕНО: проверка на None
            if hour_stats is None:
                logger.warning("plot_hour_stats: hour_stats равно None")
                hour_stats = {}

            self.figure.clear()
            ax = self.figure.add_subplot(111)

            hours = list(range(24))
            conc_values = []
            for h in hours:
                if h in hour_stats and hour_stats[h] is not None:
                    conc_values.append(hour_stats[h].get('avg_concentration', 0))
                else:
                    conc_values.append(0)

            ax.bar(hours, conc_values, color='#1976d2', alpha=0.7)
            ax.set_xlabel('Час дня')
            ax.set_ylabel('Средняя концентрация (1-5)')
            ax.set_title('Продуктивность по часам')
            ax.set_xticks(range(0, 24, 2))
            ax.set_ylim(0, 5.5)
            ax.grid(True, alpha=0.3, axis='y')

            self.figure.tight_layout()
            self.canvas.draw()
            logger.debug("График продуктивности по часам построен")
        except Exception as e:
            logger.error(f"Ошибка построения графика по часам: {e}", exc_info=True)

    def plot_day_stats(self, day_stats: dict):
        """
        Строит график продуктивности по дням недели
        """
        try:
            # ✅ ИСПРАВЛЕНО: проверка на None
            if day_stats is None:
                logger.warning("plot_day_stats: day_stats равно None")
                day_stats = {}

            self.figure.clear()
            ax = self.figure.add_subplot(111)

            days = []
            conc_values = []
            for d in range(7):
                if d in day_stats and day_stats[d] is not None:
                    days.append(day_stats[d].get('name', f'День {d}'))
                    conc_values.append(day_stats[d].get('avg_concentration', 0))
                else:
                    days.append(f'День {d}')
                    conc_values.append(0)

            bars = ax.bar(days, conc_values,
                          color=['#1976d2', '#2196f3', '#42a5f5', '#64b5f6', '#90caf9', '#bbdefb', '#e3f2fd'])
            ax.set_xlabel('День недели')
            ax.set_ylabel('Средняя концентрация (1-5)')
            ax.set_title('Продуктивность по дням недели')
            ax.set_ylim(0, 5.5)
            ax.grid(True, alpha=0.3, axis='y')

            self.figure.tight_layout()
            self.canvas.draw()
            logger.debug("График продуктивности по дням построен")
        except Exception as e:
            logger.error(f"Ошибка построения графика по дням: {e}", exc_info=True)

    def plot_task_completion(self, timeline_data: dict):
        """
        Строит график выполнения задач по неделям
        """
        try:
            # ✅ ИСПРАВЛЕНО: проверка на None
            if timeline_data is None:
                logger.warning("plot_task_completion: timeline_data равно None")
                timeline_data = {}

            self.figure.clear()
            ax = self.figure.add_subplot(111)

            weeks = timeline_data.get('weeks', [])
            created = timeline_data.get('created', [])
            completed = timeline_data.get('completed', [])

            if weeks and len(weeks) == len(created) == len(completed):
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
            else:
                ax.text(0.5, 0.5, 'Нет данных для отображения',
                        ha='center', va='center', transform=ax.transAxes,
                        fontsize=12, color='#888888')
                ax.set_title('Динамика задач по неделям')

            self.figure.tight_layout()
            self.canvas.draw()
            logger.debug(f"График выполнения задач построен: {len(weeks)} недель")
        except Exception as e:
            logger.error(f"Ошибка построения графика выполнения задач: {e}", exc_info=True)

    def plot_session_duration_distribution(self, sessions):
        """
        Строит гистограмму распределения длительности сессий
        """
        try:
            # ✅ ИСПРАВЛЕНО: проверка на None
            if sessions is None:
                logger.warning("plot_session_duration_distribution: sessions равно None")
                sessions = []

            self.figure.clear()
            ax = self.figure.add_subplot(111)

            durations = []
            for s in sessions:
                if s is not None and hasattr(s, 'duration_minutes') and s.duration_minutes:
                    durations.append(s.duration_minutes)

            if durations:
                ax.hist(durations, bins=10, color='#1976d2', alpha=0.7, edgecolor='white')
                ax.set_xlabel('Длительность (минуты)')
                ax.set_ylabel('Количество сессий')
                ax.set_title('Распределение длительности сессий')
                ax.grid(True, alpha=0.3, axis='y')
            else:
                ax.text(0.5, 0.5, 'Нет данных для отображения',
                        ha='center', va='center', transform=ax.transAxes,
                        fontsize=12, color='#888888')
                ax.set_title('Распределение длительности сессий')

            self.figure.tight_layout()
            self.canvas.draw()
            logger.debug(f"Гистограмма длительности построена: {len(durations)} сессий")
        except Exception as e:
            logger.error(f"Ошибка построения гистограммы: {e}", exc_info=True)

    def plot_radar_chart(self, avg_concentration: float, avg_energy: float, avg_interest: float):
        """
        Строит лепестковую диаграмму средних показателей
        """
        try:
            # ✅ ИСПРАВЛЕНО: проверка на None
            if avg_concentration is None:
                avg_concentration = 0
            if avg_energy is None:
                avg_energy = 0
            if avg_interest is None:
                avg_interest = 0

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
            logger.debug("Лепестковая диаграмма построена")
        except Exception as e:
            logger.error(f"Ошибка построения лепестковой диаграммы: {e}", exc_info=True)


class ZoomableChart(QWidget):
    """
    Виджет с зумом для графиков (обёртка над FigureCanvas с дополнительными кнопками)
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        try:
            layout = QVBoxLayout(self)
            layout.setContentsMargins(0, 0, 0, 0)

            self.figure = Figure(figsize=(8, 5), dpi=100, facecolor='#f5f5f5')
            self.canvas = FigureCanvas(self.figure)
            self.toolbar = NavigationToolbar(self.canvas, self)

            layout.addWidget(self.toolbar)
            layout.addWidget(self.canvas)

            self.ax = None
            logger.debug("ZoomableChart инициализирован")
        except Exception as e:
            logger.error(f"Ошибка настройки ZoomableChart: {e}", exc_info=True)

    def set_data(self, x_data, y_data, title: str, xlabel: str, ylabel: str, color: str = '#1976d2'):
        """Устанавливает данные для отображения"""
        try:
            # ✅ ИСПРАВЛЕНО: проверка на None
            if x_data is None or y_data is None:
                logger.warning("set_data: x_data или y_data равно None")
                x_data = x_data or []
                y_data = y_data or []

            self.figure.clear()
            self.ax = self.figure.add_subplot(111)

            if x_data and y_data and len(x_data) == len(y_data):
                self.ax.plot(x_data, y_data, marker='o', linewidth=2, color=color, markersize=5)
                self.ax.set_xlabel(xlabel)
                self.ax.set_ylabel(ylabel)
                self.ax.set_title(title)
                self.ax.grid(True, alpha=0.3)
            else:
                self.ax.text(0.5, 0.5, 'Нет данных для отображения',
                             ha='center', va='center', transform=self.ax.transAxes,
                             fontsize=12, color='#888888')
                self.ax.set_title(title)

            self.figure.tight_layout()
            self.canvas.draw()
            logger.debug(f"ZoomableChart: данные установлены, {len(x_data)} точек")
        except Exception as e:
            logger.error(f"Ошибка установки данных в ZoomableChart: {e}", exc_info=True)

    def clear(self):
        """Очищает график"""
        try:
            self.figure.clear()
            self.canvas.draw()
        except Exception as e:
            logger.error(f"Ошибка очистки ZoomableChart: {e}", exc_info=True)