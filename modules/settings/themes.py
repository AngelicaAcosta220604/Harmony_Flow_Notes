# modules/settings/themes.py
from pathlib import Path
from typing import Optional

#
class ThemeManager:
    """Менеджер для переключения светлой и тёмной темы"""

    # Базовые стили QSS для светлой и тёмной темы
    LIGHT_STYLE = """
        /* Основные цвета */
        QMainWindow {
            background-color: #dee5ee;
        }

        QWidget {
            background-color: #dee5ee;
            color: #333333;
            font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif;
        }

        /* Сайдбар */
        QListWidget {
            background-color: #FFFFFF;
            border: none;
            outline: none;
            border-radius: 12px;
            margin: 6px;
        }

        QListWidget::item {
            padding: 8px;
            border-radius: 8px;
            margin: 2px 4px;
        }

        QListWidget::item:selected {
            background-color: #B6D4F9;
            color: #0F56DC;
            border-radius: 8px;
        }

        QListWidget::item:hover {
            background-color: #B6D4F9;
            color: #0F56DC;
            border-radius: 8px;
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

        /* Дерево тем */
QTreeWidget {
    background-color: #FFFFFF;
    border: 1px solid #E6EEF6;
    border-radius: 16px;
    outline: none;
    padding: 8px 0px;
}

QTreeWidget::item {
    min-height: 38px;
    padding: 4px 12px;
    margin: 1px 8px;
    border-radius: 8px;
    font-size: 13px;
    border: none;
}

/* Выделение для папок (жёлтое) */
QTreeWidget::item:selected {
    background-color: #FFF7EB;
    border-left: 3px solid #F59E0B;
    border-radius: 6px;
    color: #1F2937;
}

/* Выделение для тем (голубое) */
QTreeWidget::item:selected:!has-children {
    background-color: #EBF5FF;
    border-left: 3px solid #3B82F6;
    border-radius: 6px;
    color: #1F2937;
}

/* Наведение на элемент */
QTreeWidget::item:hover:!selected {
    background-color: #F9FAFB;
    border-radius: 8px;
}
/* Стили для QInputDialog и QMessageBox */
QInputDialog, QMessageBox {
    background-color: #FFFFFF;
    border-radius: 16px;
}

QInputDialog QLabel, QMessageBox QLabel {
    font-family: 'Segoe UI', 'Inter', sans-serif;
    font-size: 14px;
    font-weight: 600;
    color: #1F2937;
    background-color: transparent;
}

QInputDialog QLineEdit {
    background-color: #F0F4F8;
    border: 1px solid #E6EEF6;
    border-radius: 8px;
    padding: 8px 12px;
    font-size: 14px;
    color: #1F2937;
    min-height: 24px;
}

QInputDialog QLineEdit:focus {
    background-color: #FFFFFF;
    border: 1.5px solid #3B82F6;
}

QInputDialog QPushButton, QMessageBox QPushButton {
    background-color: #F0F4F8;
    color: #1F2937;
    border: none;
    border-radius: 8px;
    padding: 6px 16px;
    font-size: 13px;
    font-weight: 500;
    min-width: 80px;
    min-height: 28px;
}

QInputDialog QPushButton:hover, QMessageBox QPushButton:hover {
    background-color: #E2E8F0;
}

QInputDialog QPushButton:default, QMessageBox QPushButton:default {
    background-color: #3B82F6;
    color: #FFFFFF;
}

QInputDialog QPushButton:default:hover {
    background-color: #2563EB;
}

QInputDialog QDialogButtonBox {
    button-layout: 0;
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
/* ========== РАЗДЕЛ ТЕМ (СТРУКТУРА ЗНАНИЙ) ========== */

/* Контейнер дерева тем */
QTreeWidget {
    background-color: #FFFFFF;
    border: 1px solid #E6EEF6;
    border-radius: 16px;
    outline: none;
    padding: 8px 0px;
}

/* Элементы дерева - общие настройки */
QTreeWidget::item {
    min-height: 38px;
    padding: 4px 12px;
    margin: 1px 8px;
    border-radius: 8px;
    font-size: 13px;
}

/* Папки - более плотный шрифт и тёмный цвет */
QTreeWidget::item:has-children {
    font-weight: 500;
    color: #1F2937;
}

/* Темы - обычный вес и мягкий цвет */
QTreeWidget::item:!has-children {
    font-weight: 400;
    color: #374151;
}

/* Выделенный элемент */
QTreeWidget::item:selected {
    background-color: rgba(59, 130, 246, 0.08);
    color: #3B82F6;
    font-weight: 500;
    border: none;
    border-radius: 8px;
}

/* Наведение на элемент */
QTreeWidget::item:hover:!selected {
    background-color: #F9FAFB;
    border-radius: 8px;
}

/* Стрелочки раскрытия (кастомные иконки) */
QTreeWidget::branch:closed:has-children {
    image: url(resources/icons/right.png);
}

QTreeWidget::branch:open:has-children {
    image: url(resources/icons/down.png);
}

QTreeWidget::branch:has-children {
    min-width: 24px;
    max-width: 24px;
}

/* ========== КНОПКИ ПАНЕЛИ ИНСТРУМЕНТОВ ========== */

/* Базовое состояние кнопок (для кнопок внутри виджета тем) */
QPushButton {
    background-color: rgba(240, 244, 248, 0.8);
    color: #1F2937;
    border: none;
    border-radius: 8px;
    padding: 6px 12px;
    font-size: 13px;
    font-weight: 500;
}

QPushButton:hover {
    background-color: #FFFFFF;
    border: 1.5px solid #3B82F6;
    color: #3B82F6;
}

QPushButton:pressed {
    background-color: #EBF2FF;
}

QPushButton:disabled {
    opacity: 0.5;
    background-color: rgba(240, 244, 248, 0.5);
    color: #9CA3AF;
}

QPushButton:disabled:hover {
    border: none;
    background-color: rgba(240, 244, 248, 0.5);
    cursor: not-allowed;
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