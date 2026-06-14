# main.py.
import sys
import os

# Добавляем корневую папку проекта в PYTHONPATH
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

print(f"Project root added to sys.path: {project_root}")
print(f"sys.path: {sys.path}")

from PySide6.QtWidgets import QApplication
from core.app import HFlowApp
from core.main_window import MainWindow


def main():
    print("Hi, PyCharm")

    app = HFlowApp(sys.argv)
    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()