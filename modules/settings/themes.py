# modules/settings/themes.py
from pathlib import Path
from typing import Optional


class ThemeManager:
    """Менеджер для переключения светлой и тёмной темы"""

    # Базовые стили QSS для светлой и тёмной темы
    LIGHT_STYLE = """
        /* Основные цвета */
        QMainWindow {
            background-color: #f5f5f5;
        }

        QWidget {
            background-color: #f5f5f5;
            color: #333333;
            font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif;
        }

        /* Сайдбар */
        QListWidget {
            background-color: #ffffff;
            border: none;
            outline: none;
        }

        QListWidget::item {
            padding: 8px;
            border-radius: 4px;
        }

        QListWidget::item:selected {
            background-color: #e0e0e0;
            color: #1976d2;
        }

        QListWidget::item:hover {
            background-color: #f0f0f0;
        }

        /* Кнопки */
        QPushButton {
            background-color: #1976d2;
            color: white;
            border: none;
            padding: 6px 12px;
            border-radius: 4px;
        }

        QPushButton:hover {
            background-color: #1565c0;
        }

        QPushButton:pressed {
            background-color: #0d47a1;
        }

        QPushButton:disabled {
            background-color: #cccccc;
        }

        /* Текстовые поля */
        QTextEdit, QPlainTextEdit, QLineEdit {
            background-color: #ffffff;
            border: 1px solid #cccccc;
            border-radius: 4px;
            padding: 4px;
        }

        QTextEdit:focus, QPlainTextEdit:focus, QLineEdit:focus {
            border-color: #1976d2;
        }

        /* Дерево */
        QTreeWidget {
            background-color: #ffffff;
            border: 1px solid #e0e0e0;
            border-radius: 4px;
        }

        QTreeWidget::item {
            padding: 4px;
        }

        QTreeWidget::item:selected {
            background-color: #1976d2;
        }

        /* Табы */
        QTabWidget::pane {
            border: 1px solid #e0e0e0;
            border-radius: 4px;
            background-color: #ffffff;
        }

        QTabBar::tab {
            background-color: #e0e0e0;
            padding: 6px 12px;
            margin-right: 2px;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
        }

        QTabBar::tab:selected {
            background-color: #1976d2;
            color: white;
        }

        QTabBar::tab:hover:!selected {
            background-color: #eeeeee;
        }

        /* Слайдеры */
        QSlider::groove:horizontal {
            height: 4px;
            background-color: #e0e0e0;
            border-radius: 2px;
        }

        QSlider::handle:horizontal {
            background-color: #1976d2;
            width: 12px;
            height: 12px;
            margin: -4px 0;
            border-radius: 6px;
        }

        /* Scrollbar */
        QScrollBar:vertical {
            background-color: #f0f0f0;
            width: 10px;
            border-radius: 5px;
        }

        QScrollBar::handle:vertical {
            background-color: #c0c0c0;
            border-radius: 5px;
            min-height: 20px;
        }

        QScrollBar::handle:vertical:hover {
            background-color: #a0a0a0;
        }
    """

    DARK_STYLE = """
        /* Основные цвета */
        QMainWindow {
            background-color: #1e1e1e;
        }

        QWidget {
            background-color: #1e1e1e;
            color: #e0e0e0;
            font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif;
        }

        /* Сайдбар */
        QListWidget {
            background-color: #2d2d2d;
            border: none;
            outline: none;
        }

        QListWidget::item {
            padding: 8px;
            border-radius: 4px;
        }

        QListWidget::item:selected {
            background-color: #3d3d3d;
            color: #64b5f6;
        }

        QListWidget::item:hover {
            background-color: #353535;
        }

        /* Кнопки */
        QPushButton {
            background-color: #64b5f6;
            color: #1e1e1e;
            border: none;
            padding: 6px 12px;
            border-radius: 4px;
        }

        QPushButton:hover {
            background-color: #42a5f5;
        }

        QPushButton:pressed {
            background-color: #2196f3;
        }

        QPushButton:disabled {
            background-color: #555555;
            color: #888888;
        }

        /* Текстовые поля */
        QTextEdit, QPlainTextEdit, QLineEdit {
            background-color: #2d2d2d;
            border: 1px solid #555555;
            border-radius: 4px;
            padding: 4px;
            color: #e0e0e0;
        }

        QTextEdit:focus, QPlainTextEdit:focus, QLineEdit:focus {
            border-color: #64b5f6;
        }

        /* Дерево */
        QTreeWidget {
            background-color: #2d2d2d;
            border: 1px solid #444444;
            border-radius: 4px;
        }

        QTreeWidget::item {
            padding: 4px;
        }

        QTreeWidget::item:selected {
            background-color: #3d3d3d;
        }

        QTreeWidget::item:hover {
            background-color: #353535;
        }

        /* Табы */
        QTabWidget::pane {
            border: 1px solid #444444;
            border-radius: 4px;
            background-color: #2d2d2d;
        }

        QTabBar::tab {
            background-color: #3d3d3d;
            padding: 6px 12px;
            margin-right: 2px;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
        }

        QTabBar::tab:selected {
            background-color: #64b5f6;
            color: #1e1e1e;
        }

        QTabBar::tab:hover:!selected {
            background-color: #4a4a4a;
        }

        /* Слайдеры */
        QSlider::groove:horizontal {
            height: 4px;
            background-color: #444444;
            border-radius: 2px;
        }

        QSlider::handle:horizontal {
            background-color: #64b5f6;
            width: 12px;
            height: 12px;
            margin: -4px 0;
            border-radius: 6px;
        }

        /* Scrollbar */
        QScrollBar:vertical {
            background-color: #2d2d2d;
            width: 10px;
            border-radius: 5px;
        }

        QScrollBar::handle:vertical {
            background-color: #555555;
            border-radius: 5px;
            min-height: 20px;
        }

        QScrollBar::handle:vertical:hover {
            background-color: #666666;
        }
    """

    def __init__(self, styles_dir: Optional[str] = None):
        """
        Args:
            styles_dir: Директория с QSS файлами (опционально)
        """
        self.styles_dir = Path(styles_dir) if styles_dir else None

    def get_style(self, theme: str) -> str:
        """
        Возвращает QSS стиль для указанной темы

        Args:
            theme: 'light' или 'dark'
        """
        if theme == 'dark':
            return self.DARK_STYLE
        return self.LIGHT_STYLE

    def load_qss_file(self, file_path: str) -> str:
        """Загружает QSS из файла"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"[ThemeManager] Ошибка загрузки QSS: {e}")
            return ""

    def apply_theme(self, app, theme: str):
        """
        Применяет тему к приложению

        Args:
            app: QApplication instance
            theme: 'light' или 'dark'
        """
        style = self.get_style(theme)

        # Если есть файлы стилей, пробуем загрузить их
        if self.styles_dir and self.styles_dir.exists():
            qss_file = self.styles_dir / f"{theme}_style.qss"
            if qss_file.exists():
                style = self.load_qss_file(str(qss_file))

        app.setStyleSheet(style)