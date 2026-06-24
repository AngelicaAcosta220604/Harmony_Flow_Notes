import unittest
import tempfile
import os
import json
import csv
from services.export_service import ExportService
from services.backup_service import BackupService


class TestExportService(unittest.TestCase):
    def test_export_topics_to_json(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, 'topics.json')
            topics = [{'id': 1, 'name': 'Topic 1'}]
            result = ExportService.export_topics_to_json(topics, filepath)

            self.assertTrue(result)
            self.assertTrue(os.path.exists(filepath))

            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.assertEqual(data, topics)

    def test_export_tasks_to_csv(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, 'tasks.csv')
            tasks = [
                {'id': 1, 'title': 'Task 1', 'description': 'Desc', 'status': 'active',
                 'deadline': None, 'created_at': '2023-01-01', 'completed_at': None}
            ]
            result = ExportService.export_tasks_to_csv(tasks, filepath)

            self.assertTrue(result)
            with open(filepath, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]['title'], 'Task 1')

    def test_export_empty_tasks(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, 'tasks.csv')
            result = ExportService.export_tasks_to_csv([], filepath)
            self.assertFalse(result)  # Экспорт пустого списка должен вернуть False
            self.assertFalse(os.path.exists(filepath))


class TestBackupService(unittest.TestCase):
    def test_create_and_list_backup(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, 'test.db')
            with open(db_path, 'w') as f:
                f.write('dummy db data')

            service = BackupService(db_path=db_path, backup_dir=os.path.join(tmpdir, 'backups'))
            backup_path = service.create_backup('test_backup')

            self.assertIsNotNone(backup_path)
            self.assertTrue(backup_path.exists())

            # Проверяем, что бэкап попал в список
            backups = service.list_backups()
            self.assertEqual(len(backups), 1)
            self.assertEqual(backups[0]['name'], 'test_backup')

    def test_delete_backup(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, 'test.db')
            with open(db_path, 'w') as f:
                f.write('dummy')

            service = BackupService(db_path=db_path, backup_dir=os.path.join(tmpdir, 'backups'))
            backup_path = service.create_backup('to_delete')

            self.assertTrue(backup_path.exists())
            result = service.delete_backup(str(backup_path))
            self.assertTrue(result)
            self.assertFalse(backup_path.exists())


if __name__ == '__main__':
    unittest.main()