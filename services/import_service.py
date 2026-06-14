# services/import_service.py
import json
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple


class ImportService:
    """Сервис для импорта данных"""

    @staticmethod
    def import_topics_from_json(file_path: str) -> Tuple[bool, List[Dict[str, Any]]]:
        """Импортирует темы из JSON файла"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                topics = json.load(f)

            if isinstance(topics, list):
                return True, topics
            else:
                return False, []
        except Exception as e:
            print(f"[ImportService] Ошибка импорта тем: {e}")
            return False, []

    @staticmethod
    def import_notes_from_json(file_path: str) -> Tuple[bool, List[Dict[str, Any]]]:
        """Импортирует заметки из JSON файла"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                notes = json.load(f)

            if isinstance(notes, list):
                return True, notes
            else:
                return False, []
        except Exception as e:
            print(f"[ImportService] Ошибка импорта заметок: {e}")
            return False, []

    @staticmethod
    def import_tasks_from_csv(file_path: str) -> Tuple[bool, List[Dict[str, Any]]]:
        """Импортирует задачи из CSV файла"""
        tasks = []

        try:
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Очищаем от пустых полей
                    task = {k: v for k, v in row.items() if v}
                    tasks.append(task)

            return True, tasks
        except Exception as e:
            print(f"[ImportService] Ошибка импорта задач: {e}")
            return False, []

    @staticmethod
    def import_flashcards_from_csv(file_path: str) -> Tuple[bool, List[Dict[str, Any]]]:
        """Импортирует карточки из CSV файла"""
        flashcards = []

        try:
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    card = {}

                    # Определяем тип карточки
                    if row.get('type') == 'free':
                        card = {
                            'type': 'free',
                            'content': row.get('content', '')
                        }
                    else:
                        card = {
                            'type': 'question_answer',
                            'question': row.get('question', ''),
                            'answer': row.get('answer', '')
                        }

                    flashcards.append(card)

            return True, flashcards
        except Exception as e:
            print(f"[ImportService] Ошибка импорта карточек: {e}")
            return False, []

    @staticmethod
    def import_text_file(file_path: str) -> Tuple[bool, str]:
        """
        Импортирует текстовый файл (для заметок)

        Returns:
            (успех, содержимое_файла)
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return True, content
        except UnicodeDecodeError:
            try:
                with open(file_path, 'r', encoding='cp1251') as f:
                    content = f.read()
                return True, content
            except Exception as e:
                print(f"[ImportService] Ошибка импорта текста: {e}")
                return False, ""
        except Exception as e:
            print(f"[ImportService] Ошибка импорта текста: {e}")
            return False, ""