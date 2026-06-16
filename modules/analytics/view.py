# modules/analytics/view.py
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTabWidget, QScrollArea, QFrame, QComboBox, QMessageBox, QTableWidget, QTableWidgetItem, QHeaderView
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
        self.refresh_btn.setStyleSheet("color: #6B7280; font-size: 12px;")
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
        self.tab_widget.setTabEnabled(1, False)  # Отключаем вкладку графиков

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

        # 🆕 Блок инсайтов/рекомендаций
        self.insights_frame = QFrame()
        self.insights_frame.setFrameShape(QFrame.StyledPanel)
        self.insights_frame.setStyleSheet("""
                   QFrame {
                       background-color: #F0FDF4;
                       border-radius: 12px;
                       border: 1px solid #BBF7D0;
                   }
               """)
        insights_layout = QVBoxLayout(self.insights_frame)
        insights_layout.setContentsMargins(15, 15, 15, 15)

        insights_title = QLabel("💡 Рекомендации и выводы")
        insights_title.setStyleSheet(
            "font-size: 14px; font-weight: bold; color: #166534; background-color: transparent;")
        insights_layout.addWidget(insights_title)

        self.insights_label = QLabel()
        self.insights_label.setWordWrap(True)
        self.insights_label.setStyleSheet(
            "color: #15803D; font-size: 13px; background-color: transparent; line-height: 1.5;")
        insights_layout.addWidget(self.insights_label)

        content_layout.addWidget(self.insights_frame)

        # 🆕 Блок детального анализа паттернов
        self.patterns_frame = QFrame()
        self.patterns_frame.setFrameShape(QFrame.StyledPanel)
        self.patterns_frame.setStyleSheet("""
                   QFrame {
                       background-color: #FFFFFF;
                       border-radius: 12px;
                       border: 1px solid #E5E7EB;
                   }
               """)
        patterns_layout = QVBoxLayout(self.patterns_frame)
        patterns_layout.setContentsMargins(15, 15, 15, 15)

        patterns_title = QLabel("📈 Детальный анализ паттернов")
        patterns_title.setStyleSheet(
            "font-size: 14px; font-weight: bold; color: #1E2A3E; background-color: transparent;")
        patterns_layout.addWidget(patterns_title)

        # Сетка для метрик
        self.patterns_grid = QWidget()
        grid_layout = QHBoxLayout(self.patterns_grid)
        grid_layout.setSpacing(15)

        # Карточки для каждой метрики
        self.metric_cards = {}
        for metric, icon, color in [
            ('concentration', '🧠', '#10B981'),
            ('energy', '⚡', '#F59E0B'),
            ('interest', '❤️', '#EC4899')
        ]:
            card = self._create_metric_pattern_card(metric, icon, color)
            self.metric_cards[metric] = card
            grid_layout.addWidget(card)

        patterns_layout.addWidget(self.patterns_grid)

        # Блок синергии
        self.synergy_label = QLabel()
        self.synergy_label.setWordWrap(True)
        self.synergy_label.setStyleSheet(
            "color: #1F2937; font-size: 13px; background-color: transparent; margin-top: 10px;")
        patterns_layout.addWidget(self.synergy_label)

        content_layout.addWidget(self.patterns_frame)

        # 🆕 Переключатель режима детализации (код из прошлого шага)
        detail_layout = QHBoxLayout()
        detail_layout.addWidget(QLabel("🔍 Детализация:"))

        self.detail_mode_combo = QComboBox()
        self.detail_mode_combo.addItems(["📋 По сессиям", "📁 По темам", "📂 По папкам"])
        self.detail_mode_combo.setStyleSheet("""
            QComboBox {
                background-color: #FFFFFF; border: 1px solid #E5E7EB; border-radius: 8px;
                padding: 6px 12px; font-size: 13px; color: #1F2937;
            }
            QComboBox::drop-down { border: none; width: 30px; }
        """)
        self.detail_mode_combo.currentIndexChanged.connect(self._update_detail_table)
        detail_layout.addWidget(self.detail_mode_combo)
        detail_layout.addStretch()
        content_layout.addLayout(detail_layout)

        # Таблица детализации
        self.detail_table_frame = QFrame()
        self.detail_table_frame.setFrameShape(QFrame.StyledPanel)
        self.detail_table_frame.setStyleSheet(
            "background-color: #FFFFFF; border-radius: 12px; border: 1px solid #E5E7EB;")
        table_layout = QVBoxLayout(self.detail_table_frame)
        table_layout.setContentsMargins(0, 0, 0, 0)

        self.detail_table = QTableWidget()
        self.detail_table.setStyleSheet("""
            QTableWidget { background-color: transparent; border: none; gridline-color: #F3F4F6; font-size: 13px; color: #1F2937; }
            QTableWidget::item { padding: 10px; border-bottom: 1px solid #F3F4F6; }
            QHeaderView::section { background-color: #F9FAFB; color: #6B7280; font-weight: 600; font-size: 12px; padding: 10px; border: none; border-bottom: 2px solid #E5E7EB; }
        """)
        self.detail_table.verticalHeader().setVisible(False)
        self.detail_table.setShowGrid(False)
        table_layout.addWidget(self.detail_table)

        content_layout.addWidget(self.detail_table_frame)

        content_layout.addStretch()
        scroll.setWidget(content)
        layout.addWidget(scroll)

        return widget

    def _update_detail_table(self):
        """Обновляет таблицу детализации в зависимости от выбранного режима"""
        if not hasattr(self, '_current_stats') or not hasattr(self, 'detail_table'):
            return

        mode = self.detail_mode_combo.currentText()
        topic_ids = self._current_topic_ids

        # Выбираем данные и заголовки в зависимости от режима
        if "сессиям" in mode:
            data = self._analytics_controller.get_sessions_table_data(topic_ids)
            headers = ["Дата", "Тема", "Длительность", "Конц.", "Энергия", "Интерес"]
            keys = ['date', 'topic_name', 'duration', 'avg_concentration', 'avg_energy', 'avg_interest']
        elif "темам" in mode:
            data = self._analytics_controller.get_topics_table_data(topic_ids)
            headers = ["Тема", "Сессий", "Время", "Конц.", "Энергия", "Интерес"]
            keys = ['topic_name', 'session_count', 'duration', 'avg_concentration', 'avg_energy', 'avg_interest']
        elif "папкам" in mode:
            data = self._analytics_controller.get_folders_table_data(topic_ids)
            headers = ["Папка", "Сессий", "Время", "Конц.", "Энергия", "Интерес"]
            keys = ['folder_name', 'session_count', 'duration', 'avg_concentration', 'avg_energy', 'avg_interest']
        else:
            return

        # Настройка таблицы
        self.detail_table.setRowCount(len(data))
        self.detail_table.setColumnCount(len(headers))
        self.detail_table.setHorizontalHeaderLabels(headers)

        # 🆕 Отключаем редактирование и лишние эффекты
        self.detail_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.detail_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.detail_table.setSelectionMode(QTableWidget.SingleSelection)
        self.detail_table.setTabKeyNavigation(False)
        self.detail_table.setFocusPolicy(Qt.NoFocus)

        # Отключаем tooltip'ы
        self.detail_table.viewport().setMouseTracking(False)

        # Первая колонка растягивается, остальные по содержимому
        self.detail_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        for i in range(1, len(headers)):
            self.detail_table.horizontalHeader().setSectionResizeMode(i, QHeaderView.ResizeToContents)

        # Заполнение данными
        for row, item in enumerate(data):
            for col, key in enumerate(keys):
                val = item.get(key, 0)
                if isinstance(val, float):
                    val = f"{val:.1f}"

                table_item = QTableWidgetItem(str(val))
                table_item.setTextAlignment(Qt.AlignCenter if col > 0 else Qt.AlignLeft)

                # 🎨 Подсветка метрик цветом (как в дашборде)
                if key in ['avg_concentration', 'avg_energy', 'avg_interest']:
                    try:
                        v = float(val)
                        if v >= 80:
                            table_item.setForeground(QColor("#10B981"))  # Зеленый
                        elif v >= 50:
                            table_item.setForeground(QColor("#F59E0B"))  # Оранжевый
                        else:
                            table_item.setForeground(QColor("#EF4444"))  # Красный
                    except:
                        pass

                self.detail_table.setItem(row, col, table_item)

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
        """Обработчик изменения выбора тем - теперь с автообновлением"""
        data = self.topic_selector.currentData()

        if data == "select":
            # Открыть диалог множественного выбора
            dialog = AnalyticsSelectorDialog(self)
            dialog.topics_selected.connect(self._on_topics_selected)
            dialog.exec()
            # Возвращаем предыдущий выбор после закрытия диалога
            if self._current_topic_ids:
                # Если были выбраны темы, показываем "Выбрано N тем"
                count = len(self._current_topic_ids)
                self.topic_selector.blockSignals(True)
                self.topic_selector.setCurrentIndex(1)
                self.topic_selector.blockSignals(False)
            else:
                self.topic_selector.setCurrentIndex(0)
        elif data is not None:
            # 🆕 Выбрана конкретная тема из списка - обновляем автоматически
            self._current_topic_ids = [data]
            self._load_data()
        else:
            # 🆕 Выбрано "Все темы" (data == None) - обновляем автоматически
            self._current_topic_ids = []
            self._load_data()

    def _on_topics_selected(self, topic_ids: list):
        """Обработчик выбора тем из диалога"""
        self._current_topic_ids = topic_ids

        # 🆕 Автоматически обновляем данные
        self._load_data()

        # Обновляем отображение в комбобоксе
        if len(topic_ids) == 0:
            self.topic_selector.setCurrentIndex(0)
        else:
            # Показываем количество выбранных тем
            count = len(topic_ids)
            self.topic_selector.blockSignals(True)

            # Удаляем старый пункт "Выбрано N тем" если он есть
            if self.topic_selector.count() > 2:
                self.topic_selector.removeItem(1)

            self.topic_selector.insertItem(1, f"📁 Выбрано {count} тем", topic_ids)
            self.topic_selector.setCurrentIndex(1)
            self.topic_selector.blockSignals(False)

    def _load_data(self):
        """Загружает данные аналитики"""
        # 🆕 Визуальная обратная связь
        if hasattr(self, 'refresh_btn'):
            self.refresh_btn.setText(" Загрузка...")
            self.refresh_btn.setEnabled(False)

        try:
            stats = self._analytics_controller.get_complete_stats(
                self._current_topic_ids,
                include_general_tasks=True
            )

            self._current_stats = stats
            self._update_overview(stats)
            self._update_chart()
            self._update_insights(stats)
            self._update_detail_table()
            self._update_pattern_analysis()

            # Обновляем инсайты в основной вкладке
            if hasattr(self, 'insights_label'):
                insights_list = stats.get('insights', [])
                if insights_list:
                    html_insights = "<br>".join([f"• {ins}" for ins in insights_list])
                    self.insights_label.setText(html_insights)
                    self.insights_frame.show()
                else:
                    self.insights_frame.hide()
        finally:
            # 🆕 Возвращаем кнопку в исходное состояние
            if hasattr(self, 'refresh_btn'):
                self.refresh_btn.setText("🔄 Обновить")
                self.refresh_btn.setEnabled(True)




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

    def _create_metric_pattern_card(self, metric: str, icon: str, color: str) -> QFrame:
        """Создает карточку анализа паттерна метрики"""
        card = QFrame()
        card.setFrameShape(QFrame.StyledPanel)
        card.setStyleSheet(f"""
            QFrame {{
                background-color: #F9FAFB;
                border-radius: 8px;
                border-left: 4px solid {color};
            }}
        """)
        card.setFixedWidth(280)

        layout = QVBoxLayout(card)
        layout.setSpacing(8)

        # Заголовок
        title = QLabel(f"{icon} {metric.capitalize()}")
        title.setStyleSheet("font-size: 13px; font-weight: bold; color: #1E2A3E; background-color: transparent;")
        layout.addWidget(title)

        # Поля для данных
        fields = [
            ('peak_time', 'Пик:'),
            ('time_to_drop', 'До спада:'),
            ('best_period_start', 'Лучший период:'),
        ]

        self.metric_cards[f"{metric}_labels"] = {}
        for field_id, label_text in fields:
            field_layout = QHBoxLayout()
            label = QLabel(f"{label_text} ")
            label.setStyleSheet("color: #6B7280; font-size: 11px; background-color: transparent;")
            value = QLabel("—")
            value.setStyleSheet(f"color: {color}; font-size: 11px; font-weight: 600; background-color: transparent;")

            field_layout.addWidget(label)
            field_layout.addWidget(value)
            field_layout.addStretch()
            layout.addLayout(field_layout)

            self.metric_cards[f"{metric}_labels"][field_id] = value

        return card

    def _update_pattern_analysis(self):
        """Обновляет анализ паттернов"""
        if not hasattr(self, '_current_stats') or not hasattr(self, 'patterns_frame'):
            return

        sessions = self._current_stats.get('sessions', [])
        if not sessions:
            self.patterns_frame.hide()
            return

        patterns = self._analytics_controller.analyze_metric_patterns(sessions)

        if not patterns:
            self.patterns_frame.hide()
            return

        # Обновляем карточки метрик
        for metric in ['concentration', 'energy', 'interest']:
            if metric in patterns and self.metric_cards.get(f"{metric}_labels"):
                labels = self.metric_cards[f"{metric}_labels"]
                data = patterns[metric]

                if 'peak_time' in labels:
                    labels['peak_time'].setText(f"{data.get('peak_time', '—')} ({data.get('peak_value', 0)})")
                if 'time_to_drop' in labels:
                    labels['time_to_drop'].setText(data.get('time_to_initial_drop', '—'))
                if 'best_period_start' in labels:
                    labels['best_period_start'].setText(
                        f"{data.get('best_period_start', '—')} ({data.get('best_period_duration', '')})"
                    )

        # Обновляем синергию
        if 'synergy' in patterns and hasattr(self, 'synergy_label'):
            synergy = patterns['synergy']
            recommendations = synergy.get('recommendations', [])

            # Добавляем детальные рекомендации
            detailed_recs = self._analytics_controller.generate_detailed_recommendations(
                sessions, patterns
            )
            all_recommendations = recommendations + detailed_recs

            if all_recommendations:
                html_rec = "<br><br>".join([f"• {rec}" for rec in all_recommendations[:5]])  # Показываем топ-5
                self.synergy_label.setText(f"<b>💡 Рекомендации по оптимизации:</b><br><br>{html_rec}")
                self.synergy_label.show()
            else:
                self.synergy_label.hide()