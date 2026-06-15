# modules/analytics/view.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTabWidget, QScrollArea, QFrame, QComboBox, QMessageBox
)
from PySide6.QtCore import Qt, Signal

from .controller import AnalyticsController
from .charts import AnalyticsCharts
from .insights import AnalyticsInsights
from .dialogs import AnalyticsSelectorDialog
from modules.topics.controller import TopicController
from services.time_service import TimeService


class AnalyticsView(QWidget):
    """
    Экран аналитики с графиками и инсайтами.
    """

    def __init__(
            self,
            analytics_controller: AnalyticsController,
            topic_controller: TopicController,
            parent=None
    ):
        super().__init__(parent)
        self._analytics_controller = analytics_controller
        self._topic_controller = topic_controller
        self._current_topic_ids = []  # пустой список = все темы
        self._setup_ui()
        self._connect_signals()
        self._load_data()

    def _setup_ui(self):
        """Настраивает интерфейс"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Заголовок
        header_layout = QHBoxLayout()

        title_label = QLabel("📊 Аналитика продуктивности")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        header_layout.addWidget(title_label)

        header_layout.addStretch()

        # Выбор тем.
        self.topic_selector = QComboBox()
        self.topic_selector.addItem("📚 Все темы", None)
        self.topic_selector.addItem("📁 Выбрать темы...", "select")
        self._load_topics_to_selector()
        header_layout.addWidget(QLabel("Анализировать:"))
        header_layout.addWidget(self.topic_selector)

        self.refresh_btn = QPushButton("🔄 Обновить")
        header_layout.addWidget(self.refresh_btn)

        layout.addLayout(header_layout)

        # Основная область (вкладки)
        self.tab_widget = QTabWidget()

        # Вкладка "Обзор"
        self.overview_tab = self._create_overview_tab()
        self.tab_widget.addTab(self.overview_tab, "📊 Обзор")

        # Вкладка "Графики"
        self.charts_tab = self._create_charts_tab()
        self.tab_widget.addTab(self.charts_tab, "📈 Графики")

        # Вкладка "Инсайты"
        self.insights_tab = self._create_insights_tab()
        self.tab_widget.addTab(self.insights_tab, "💡 Инсайты")

        layout.addWidget(self.tab_widget)

    def _create_overview_tab(self) -> QWidget:
        """Создаёт вкладку обзора"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setSpacing(20)

        # Карточки KPI
        self.kpi_container = QWidget()
        self.kpi_layout = QHBoxLayout(self.kpi_container)
        self.kpi_layout.setSpacing(15)
        content_layout.addWidget(self.kpi_container)

        # Дополнительная статистика
        self.stats_container = QFrame()
        self.stats_container.setFrameShape(QFrame.StyledPanel)
        self.stats_layout = QVBoxLayout(self.stats_container)
        self.stats_label = QLabel()
        self.stats_label.setWordWrap(True)
        self.stats_layout.addWidget(self.stats_label)
        content_layout.addWidget(self.stats_container)

        content_layout.addStretch()
        scroll.setWidget(content)
        layout.addWidget(scroll)

        return widget

    def _create_charts_tab(self) -> QWidget:
        """Создаёт вкладку с графиками"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Выбор типа графика
        chart_selector_layout = QHBoxLayout()
        chart_selector_layout.addWidget(QLabel("Тип графика:"))

        self.chart_type_combo = QComboBox()
        self.chart_type_combo.addItem("Динамика концентрации", "concentration")
        self.chart_type_combo.addItem("Динамика энергии", "energy")
        self.chart_type_combo.addItem("Динамика интереса", "interest")
        self.chart_type_combo.addItem("Сравнение метрик", "comparison")
        self.chart_type_combo.addItem("Продуктивность по часам", "hours")
        self.chart_type_combo.addItem("Продуктивность по дням", "days")
        chart_selector_layout.addWidget(self.chart_type_combo)
        chart_selector_layout.addStretch()

        layout.addLayout(chart_selector_layout)

        # Виджет графиков
        self.charts_widget = AnalyticsCharts()
        layout.addWidget(self.charts_widget)

        return widget

    def _create_insights_tab(self) -> QWidget:
        """Создаёт вкладку с инсайтами"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        self.insights_widget = AnalyticsInsights()
        layout.addWidget(self.insights_widget)

        return widget

    def _connect_signals(self):
        """Подключает сигналы"""
        self.topic_selector.currentIndexChanged.connect(self._on_topic_changed)
        self.refresh_btn.clicked.connect(self._load_data)
        self.chart_type_combo.currentIndexChanged.connect(self._update_chart)

    def _load_topics_to_selector(self):
        """Загружает темы в выпадающий список"""
        topics = self._topic_controller.get_all_topics()

        # Сохраняем текущий индекс
        current_index = self.topic_selector.currentIndex()

        # Очищаем всё, кроме первых двух пунктов
        while self.topic_selector.count() > 2:
            self.topic_selector.removeItem(2)

        for topic in topics:
            if topic.is_topic:
                self.topic_selector.addItem(topic.name, topic.id)

        if current_index >= 0:
            self.topic_selector.setCurrentIndex(current_index)

    def _on_topic_changed(self, index: int):
        """Обработчик изменения выбора тем"""
        data = self.topic_selector.currentData()

        if data == "select":
            dialog = AnalyticsSelectorDialog(self)
            dialog.topics_selected.connect(self._on_topics_selected)
            dialog.exec()
            # Возвращаем предыдущий выбор
            self.topic_selector.setCurrentIndex(0)

    def _on_topics_selected(self, topic_ids: list):
        """Обработчик выбора тем из диалога"""
        self._current_topic_ids = topic_ids
        self._load_data()

        # Обновляем отображение в комбобоксе
        if len(topic_ids) == 0:
            self.topic_selector.setCurrentIndex(0)
        else:
            # Показываем количество выбранных тем
            count = len(topic_ids)
            self.topic_selector.blockSignals(True)
            self.topic_selector.insertItem(1, f"📁 Выбрано {count} тем", topic_ids)
            self.topic_selector.setCurrentIndex(1)
            self.topic_selector.blockSignals(False)

    def _load_data(self):
        """Загружает данные аналитики"""
        stats = self._analytics_controller.get_complete_stats(
            self._current_topic_ids,
            include_general_tasks=True
        )

        self._current_stats = stats
        self._update_overview(stats)
        self._update_chart()
        self._update_insights(stats)

    def _update_overview(self, stats: dict):
        """Обновляет вкладку обзора с защитой от пустых данных"""
        # Гарантируем, что stats и его вложенные структуры являются словарями
        stats = stats if isinstance(stats, dict) else {}
        session_stats = stats.get('session_stats', {}) if stats.get('session_stats') else {}
        task_stats = stats.get('task_stats', {}) if stats.get('task_stats') else {}
        content_stats = stats.get('content_stats', {}) if stats.get('content_stats') else {}

        # Очищаем KPI контейнер
        while self.kpi_layout.count():
            child = self.kpi_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        # Безопасное извлечение значений метрик
        total_sessions = str(session_stats.get('total_sessions', 0))
        total_hours = session_stats.get('total_hours_display', '0.0 ч')
        avg_concentration = session_stats.get('avg_concentration', '0.0')
        avg_energy = session_stats.get('avg_energy', '0.0')
        avg_interest = session_stats.get('avg_interest', '0.0')
        completion_rate = task_stats.get('completion_rate', 0)

        tasks_completed = task_stats.get('completed', 0)
        tasks_total = task_stats.get('total', 0)

        total_notes = content_stats.get('total_notes', 0)
        total_flashcards = content_stats.get('total_flashcards', 0)
        free_cards = content_stats.get('free_cards', 0)
        qa_cards = content_stats.get('qa_cards', 0)

        first_session = session_stats.get('first_session', '—')
        last_session = session_stats.get('last_session', '—')
        unique_days = session_stats.get('unique_days', 0)

        # Создаём карточки KPI
        self.kpi_layout.addWidget(self._create_kpi_card("🎯 Сессии", total_sessions))
        self.kpi_layout.addWidget(self._create_kpi_card("⏱️ Время", total_hours))
        self.kpi_layout.addWidget(self._create_kpi_card("🧠 Концентрация", f"{avg_concentration}/100"))
        self.kpi_layout.addWidget(self._create_kpi_card("⚡ Энергия", f"{avg_energy}/100"))
        self.kpi_layout.addWidget(self._create_kpi_card("❤️ Интерес", f"{avg_interest}/100"))
        self.kpi_layout.addWidget(self._create_kpi_card("✅ Задачи", f"{completion_rate}%"))

        # Формирование детальной статистики
        stats_text = f"""
        <b>📊 Детальная статистика</b><br><br>
        <b>Сессии:</b> {total_sessions} сессий, {total_hours}<br>
        <b>Задачи:</b> {tasks_completed}/{tasks_total} выполнено ({completion_rate}%)<br>
        <b>Заметки:</b> {total_notes} шт.<br>
        <b>Карточки:</b> {total_flashcards} шт. (свободных: {free_cards}, Q&A: {qa_cards})<br>
        <b>Период:</b> с {first_session} по {last_session}<br>
        <b>Дней с активностью:</b> {unique_days}<br>
        """

        self.stats_label.setText(stats_text)

    def _create_kpi_card(self, title: str, value: str) -> QFrame:
        """Создаёт карточку KPI"""
        card = QFrame()
        card.setFrameShape(QFrame.StyledPanel)
        card.setFixedWidth(120)

        layout = QVBoxLayout(card)
        layout.setAlignment(Qt.AlignCenter)

        title_label = QLabel(title)
        title_label.setStyleSheet("color: #888888; font-size: 11px;")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        value_label = QLabel(value)
        value_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        value_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(value_label)

        return card

    def _update_chart(self):
        """Обновляет текущий график с валидацией ключей трендов"""
        if not hasattr(self, '_current_stats') or not self._current_stats:
            return

        stats = self._current_stats
        chart_type = self.chart_type_combo.currentData()

        # Безопасная проверка наличия базовых ключей графиков
        if not isinstance(stats, dict) or 'trends' not in stats:
            return

        trends = stats.get('trends', {})

        if chart_type == 'concentration' and 'concentration' in trends:
            dates, values = trends['concentration']
            self.charts_widget.plot_metric_trend(dates, values, "Динамика концентрации", "Концентрация (1-100)", '#1976d2')

        elif chart_type == 'energy' and 'energy' in trends:
            dates, values = trends['energy']
            self.charts_widget.plot_metric_trend(dates, values, "Динамика энергии", "Энергия (1-100)", '#ff9800')

        elif chart_type == 'interest' and 'interest' in trends:
            dates, values = trends['interest']
            self.charts_widget.plot_metric_trend(dates, values, "Динамика интереса", "Интерес (1-100)", '#4cafz0')

        elif chart_type == 'comparison':
            self.charts_widget.plot_comparison_trend(trends)

        elif chart_type == 'hours' and 'hour_stats' in stats:
            self.charts_widget.plot_hour_stats(stats['hour_stats'])

        elif chart_type == 'days' and 'day_stats' in stats:
            self.charts_widget.plot_day_stats(stats['day_stats'])

    def _update_insights(self, stats: dict):
        """Обновляет инсайты"""
        if isinstance(stats, dict) and 'insights' in stats:
            self.insights_widget.set_insights(stats['insights'])

    def refresh(self):
        """Обновляет данные"""
        self._load_topics_to_selector()
        self._load_data()