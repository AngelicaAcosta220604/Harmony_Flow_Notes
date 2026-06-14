# services/export_service.py
import json
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime


class ExportService:
    """Сервис для экспорта данных"""

    @staticmethod
    def export_topics_to_json(topics: List[Dict[str, Any]], file_path: str) -> bool:
        """Экспортирует темы в JSON файл"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(topics, f, ensure_ascii=False, indent=2, default=str)
            return True
        except Exception as e:
            print(f"[ExportService] Ошибка экспорта тем: {e}")
            return False

    @staticmethod
    def export_notes_to_json(notes: List[Dict[str, Any]], file_path: str) -> bool:
        """Экспортирует заметки в JSON файл"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(notes, f, ensure_ascii=False, indent=2, default=str)
            return True
        except Exception as e:
            print(f"[ExportService] Ошибка экспорта заметок: {e}")
            return False

    @staticmethod
    def export_tasks_to_csv(tasks: List[Dict[str, Any]], file_path: str) -> bool:
        """Экспортирует задачи в CSV файл"""
        if not tasks:
            return False

        try:
            fieldnames = ['id', 'title', 'description', 'status', 'deadline', 'created_at', 'completed_at']

            with open(file_path, 'w', encoding='utf-8-sig', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
                writer.writeheader()
                writer.writerows(tasks)
            return True
        except Exception as e:
            print(f"[ExportService] Ошибка экспорта задач: {e}")
            return False

    @staticmethod
    def export_flashcards_to_csv(flashcards: List[Dict[str, Any]], file_path: str) -> bool:
        """Экспортирует карточки в CSV файл"""
        if not flashcards:
            return False

        try:
            fieldnames = ['id', 'type', 'question', 'answer', 'content', 'created_at']

            with open(file_path, 'w', encoding='utf-8-sig', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
                writer.writeheader()

                for card in flashcards:
                    row = {k: card.get(k, '') for k in fieldnames}
                    writer.writerow(row)
            return True
        except Exception as e:
            print(f"[ExportService] Ошибка экспорта карточек: {e}")
            return False

    @staticmethod
    def export_sessions_to_json(sessions: List[Dict[str, Any]], file_path: str) -> bool:
        """Экспортирует сессии в JSON файл"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(sessions, f, ensure_ascii=False, indent=2, default=str)
            return True
        except Exception as e:
            print(f"[ExportService] Ошибка экспорта сессий: {e}")
            return False

    @staticmethod
    def export_all_data(data: Dict[str, List[Dict[str, Any]]], file_path: str) -> bool:
        """
        Экспортирует все данные в один JSON файл

        Args:
            data: Словарь { 'topics': [...], 'notes': [...], 'tasks': [...], ... }
            file_path: Путь для сохранения
        """
        try:
            export_data = {
                'export_date': datetime.now().isoformat(),
                'version': '1.0',
                **data
            }

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2, default=str)
            return True
        except Exception as e:
            print(f"[ExportService] Ошибка экспорта всех данных: {e}")
            return False