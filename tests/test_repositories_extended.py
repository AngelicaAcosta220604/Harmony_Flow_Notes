import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime
from database.repositories.task_repo import TaskRepository
from database.repositories.topic_repo import TopicRepository
from database.repositories.session_repo import SessionRepository

class TestTaskRepository(unittest.TestCase):
    def setUp(self):
        self.repo = TaskRepository()

    @patch('database.repositories.task_repo.db')
    def test_get_all(self, mock_db):
        mock_db.fetchall.return_value = [{'id': 1, 'title': 'Task 1'}]
        result = self.repo.get_all()
        mock_db.fetchall.assert_called_once_with(
            "SELECT * FROM tasks ORDER BY deadline ASC, created_at DESC"
        )
        self.assertEqual(len(result), 1)

    @patch('database.repositories.task_repo.db')
    def test_get_by_topic(self, mock_db):
        mock_db.fetchall.return_value = [{'id': 1, 'title': 'Task 1', 'topic_id': 10}]
        result = self.repo.get_by_topic(10)
        mock_db.fetchall.assert_called_once()
        args = mock_db.fetchall.call_args[0]
        self.assertIn('topic_id = ?', args[0])
        self.assertEqual(args[1], (10,))

    @patch('database.repositories.task_repo.db')
    def test_get_by_topics_with_general(self, mock_db):
        mock_db.fetchall.side_effect = [
            [{'id': 1, 'topic_id': 10}],
            [{'id': 2, 'topic_id': None}]
        ]
        result = self.repo.get_by_topics([10, 20], include_general=True)
        self.assertEqual(mock_db.fetchall.call_count, 2)
        self.assertEqual(len(result), 2)

    @patch('database.repositories.task_repo.db')
    def test_get_general(self, mock_db):
        mock_db.fetchall.return_value = [{'id': 1, 'topic_id': None}]
        result = self.repo.get_general()
        mock_db.fetchall.assert_called_once()
        args = mock_db.fetchall.call_args[0]
        self.assertIn('topic_id IS NULL', args[0])

    @patch('database.repositories.task_repo.db')
    def test_create(self, mock_db):
        mock_db.insert.return_value = 1
        result = self.repo.create('Task Title', 'Description', 10, '2024-12-31')
        mock_db.insert.assert_called_once_with('tasks', {
            'title': 'Task Title',
            'description': 'Description',
            'topic_id': 10,
            'deadline': '2024-12-31',
            'status': 'active'
        })
        self.assertEqual(result, 1)

    @patch('database.repositories.task_repo.db')
    def test_update_filters_fields(self, mock_db):
        mock_db.update.return_value = 1
        self.repo.update(1, title='New Title', invalid_field='Ignore', status='completed')
        call_args = mock_db.update.call_args[0]
        data = call_args[1]
        self.assertIn('title', data)
        self.assertIn('status', data)
        self.assertNotIn('invalid_field', data)

    @patch('database.repositories.task_repo.db')
    def test_update_returns_zero_for_no_valid_fields(self, mock_db):
        result = self.repo.update(1, invalid_field='Ignore')
        self.assertEqual(result, 0)
        mock_db.update.assert_not_called()

    @patch('database.repositories.task_repo.db')
    def test_delete(self, mock_db):
        mock_db.delete.return_value = 1
        result = self.repo.delete(1)
        mock_db.delete.assert_called_once_with('tasks', 'id = ?', (1,))
        self.assertEqual(result, 1)

    @patch('database.repositories.task_repo.db')
    def test_delete_by_topic(self, mock_db):
        mock_db.delete.return_value = 5
        result = self.repo.delete_by_topic(10)
        mock_db.delete.assert_called_once_with('tasks', 'topic_id = ?', (10,))
        self.assertEqual(result, 5)

    @patch('database.repositories.task_repo.db')
    def test_complete(self, mock_db):
        mock_db.update.return_value = 1
        result = self.repo.complete(1)
        call_args = mock_db.update.call_args[0]
        data = call_args[1]
        self.assertEqual(data['status'], 'completed')
        self.assertIn('completed_at', data)
        self.assertEqual(result, 1)

    @patch('database.repositories.task_repo.db')
    def test_complete_with_custom_time(self, mock_db):
        mock_db.update.return_value = 1
        custom_time = '2024-01-01T12:00:00'
        self.repo.complete(1, completed_at=custom_time)
        call_args = mock_db.update.call_args[0]
        data = call_args[1]
        self.assertEqual(data['completed_at'], custom_time)

    @patch('database.repositories.task_repo.db')
    def test_get_overdue(self, mock_db):
        mock_db.fetchall.return_value = [{'id': 1, 'deadline': '2020-01-01'}]
        result = self.repo.get_overdue()
        mock_db.fetchall.assert_called_once()
        args = mock_db.fetchall.call_args[0]
        self.assertIn("status = 'active'", args[0])
        self.assertIn('deadline < ?', args[0])

    @patch('database.repositories.task_repo.db')
    def test_get_for_today(self, mock_db):
        mock_db.fetchall.return_value = []
        self.repo.get_for_today()
        mock_db.fetchall.assert_called_once()
        args = mock_db.fetchall.call_args[0]
        self.assertIn('deadline >= ?', args[0])
        self.assertIn('deadline < ?', args[0])

    @patch('database.repositories.task_repo.db')
    def test_search(self, mock_db):
        mock_db.fetchall.return_value = []
        self.repo.search('test query')
        mock_db.fetchall.assert_called_once()
        args = mock_db.fetchall.call_args[0]
        self.assertIn('%test query%', args[1])


class TestTopicRepository(unittest.TestCase):
    def setUp(self):
        self.repo = TopicRepository()

    @patch('database.repositories.topic_repo.db')
    def test_get_all(self, mock_db):
        mock_db.fetchall.return_value = [{'id': 1, 'name': 'Topic 1'}]
        result = self.repo.get_all()
        mock_db.fetchall.assert_called_once_with("SELECT * FROM topics ORDER BY created_at")
        self.assertEqual(len(result), 1)

    @patch('database.repositories.topic_repo.db')
    def test_get_by_id(self, mock_db):
        mock_db.fetchone.return_value = {'id': 1, 'name': 'Topic 1'}
        result = self.repo.get_by_id(1)
        mock_db.fetchone.assert_called_once_with("SELECT * FROM topics WHERE id = ?", (1,))
        self.assertEqual(result['id'], 1)

    @patch('database.repositories.topic_repo.db')
    def test_get_children_root(self, mock_db):
        mock_db.fetchall.return_value = []
        self.repo.get_children(None)
        mock_db.fetchall.assert_called_once_with("SELECT * FROM topics WHERE parent_id IS NULL")

    @patch('database.repositories.topic_repo.db')
    def test_get_children_with_parent(self, mock_db):
        mock_db.fetchall.return_value = []
        self.repo.get_children(10)
        mock_db.fetchall.assert_called_once_with(
            "SELECT * FROM topics WHERE parent_id = ?", (10,)
        )

    @patch('database.repositories.topic_repo.db')
    def test_get_tree(self, mock_db):
        mock_db.fetchall.return_value = []
        self.repo.get_tree()
        mock_db.fetchall.assert_called_once()
        args = mock_db.fetchall.call_args[0]
        self.assertIn('parent_id NULLS FIRST', args[0])

    @patch('database.repositories.topic_repo.db')
    def test_create(self, mock_db):
        mock_db.insert.return_value = 1
        result = self.repo.create('New Topic', 'topic', None, 'Description')
        mock_db.insert.assert_called_once_with('topics', {
            'name': 'New Topic',
            'description': 'Description',
            'parent_id': None,
            'type': 'topic'
        })
        self.assertEqual(result, 1)

    @patch('database.repositories.topic_repo.db')
    def test_create_folder(self, mock_db):
        mock_db.insert.return_value = 2
        self.repo.create('Folder', 'folder', None, '')
        mock_db.insert.assert_called_once_with('topics', {
            'name': 'Folder',
            'description': '',
            'parent_id': None,
            'type': 'folder'
        })

    @patch('database.repositories.topic_repo.db')
    def test_update_filters_fields(self, mock_db):
        mock_db.update.return_value = 1
        self.repo.update(1, name='New Name', invalid='Ignore')
        call_args = mock_db.update.call_args[0]
        data = call_args[1]
        self.assertIn('name', data)
        self.assertNotIn('invalid', data)

    @patch('database.repositories.topic_repo.db')
    def test_update_returns_zero_for_no_valid_fields(self, mock_db):
        result = self.repo.update(1, invalid='Ignore')
        self.assertEqual(result, 0)
        mock_db.update.assert_not_called()

    @patch('database.repositories.topic_repo.db')
    def test_delete(self, mock_db):
        mock_db.delete.return_value = 1
        result = self.repo.delete(1)
        mock_db.delete.assert_called_once_with('topics', 'id = ?', (1,))
        self.assertEqual(result, 1)

    @patch('database.repositories.topic_repo.db')
    def test_get_descendants_ids(self, mock_db):
        mock_db.fetchall.return_value = [{'id': 2}, {'id': 3}]
        result = self.repo.get_descendants_ids(1)
        self.assertEqual(result, [2, 3])
        mock_db.fetchall.assert_called_once()
        args = mock_db.fetchall.call_args[0]
        self.assertIn('WITH RECURSIVE', args[0])

    @patch('database.repositories.topic_repo.db')
    def test_search(self, mock_db):
        mock_db.fetchall.return_value = []
        self.repo.search('test')
        mock_db.fetchall.assert_called_once()
        args = mock_db.fetchall.call_args[0]
        self.assertIn('%test%', args[1])


class TestSessionRepository(unittest.TestCase):
    def setUp(self):
        self.repo = SessionRepository()

    @patch('database.repositories.session_repo.db')
    def test_get_all(self, mock_db):
        mock_db.fetchall.return_value = [{'id': 1}]
        result = self.repo.get_all()
        mock_db.fetchall.assert_called_once_with(
            "SELECT * FROM sessions ORDER BY start_time DESC"
        )
        self.assertEqual(len(result), 1)

    @patch('database.repositories.session_repo.db')
    def test_get_by_id(self, mock_db):
        mock_db.fetchone.return_value = {'id': 1}
        result = self.repo.get_by_id(1)
        mock_db.fetchone.assert_called_once_with("SELECT * FROM sessions WHERE id = ?", (1,))
        self.assertEqual(result['id'], 1)

    @patch('database.repositories.session_repo.db')
    def test_get_by_topic(self, mock_db):
        mock_db.fetchall.return_value = []
        self.repo.get_by_topic(10)
        mock_db.fetchall.assert_called_once()
        args = mock_db.fetchall.call_args[0]
        self.assertIn('topic_id = ?', args[0])
        self.assertEqual(args[1], (10,))

    @patch('database.repositories.session_repo.db')
    def test_get_by_topics_empty(self, mock_db):
        result = self.repo.get_by_topics([])
        self.assertEqual(result, [])
        mock_db.fetchall.assert_not_called()

    @patch('database.repositories.session_repo.db')
    def test_get_by_topics(self, mock_db):
        mock_db.fetchall.return_value = [{'id': 1}, {'id': 2}]
        result = self.repo.get_by_topics([10, 20])
        mock_db.fetchall.assert_called_once()
        args = mock_db.fetchall.call_args[0]
        self.assertIn('topic_id IN (?,?)', args[0])
        self.assertEqual(len(result), 2)

    @patch('database.repositories.session_repo.db')
    def test_create(self, mock_db):
        mock_db.insert.return_value = 1
        result = self.repo.create(10)
        mock_db.insert.assert_called_once()
        call_args = mock_db.insert.call_args[0]
        self.assertEqual(call_args[0], 'sessions')
        data = call_args[1]
        self.assertEqual(data['topic_id'], 10)
        self.assertEqual(data['status'], 'active')
        self.assertIn('start_time', data)
        self.assertEqual(result, 1)

    @patch('database.repositories.session_repo.db')
    def test_update_filters_fields(self, mock_db):
        mock_db.update.return_value = 1
        self.repo.update(1, status='completed', invalid='Ignore')
        call_args = mock_db.update.call_args[0]
        data = call_args[1]
        self.assertIn('status', data)
        self.assertNotIn('invalid', data)

    @patch('database.repositories.session_repo.db')
    def test_update_returns_zero_for_no_valid_fields(self, mock_db):
        result = self.repo.update(1, invalid='Ignore')
        self.assertEqual(result, 0)
        mock_db.update.assert_not_called()

    @patch('database.repositories.session_repo.db')
    def test_end_session(self, mock_db):
        mock_db.update.return_value = 1
        result = self.repo.end_session(1, 45, 'completed')
        mock_db.update.assert_called_once()
        call_args = mock_db.update.call_args[0]
        data = call_args[1]
        self.assertIn('end_time', data)
        self.assertEqual(data['duration_minutes'], 45)
        self.assertEqual(data['status'], 'completed')
        self.assertEqual(result, 1)

    @patch('database.repositories.session_repo.db')
    def test_delete(self, mock_db):
        mock_db.delete.return_value = 1
        result = self.repo.delete(1)
        mock_db.delete.assert_called_once_with('sessions', 'id = ?', (1,))
        self.assertEqual(result, 1)

    @patch('database.repositories.session_repo.db')
    def test_delete_by_topic(self, mock_db):
        mock_db.delete.return_value = 3
        result = self.repo.delete_by_topic(10)
        mock_db.delete.assert_called_once_with('sessions', 'topic_id = ?', (10,))
        self.assertEqual(result, 3)

    @patch('database.repositories.session_repo.db')
    def test_get_active(self, mock_db):
        mock_db.fetchone.return_value = {'id': 1, 'status': 'active'}
        result = self.repo.get_active()
        mock_db.fetchone.assert_called_once()
        args = mock_db.fetchone.call_args[0]
        self.assertIn("status = 'active'", args[0])
        self.assertEqual(result['status'], 'active')

    @patch('database.repositories.session_repo.db')
    def test_get_active_none(self, mock_db):
        mock_db.fetchone.return_value = None
        result = self.repo.get_active()
        self.assertIsNone(result)

    @patch('database.repositories.session_repo.db')
    def test_get_recent(self, mock_db):
        mock_db.fetchall.return_value = [{'id': 1}, {'id': 2}]
        result = self.repo.get_recent(5)
        mock_db.fetchall.assert_called_once()
        args = mock_db.fetchall.call_args[0]
        self.assertIn('LIMIT ?', args[0])
        self.assertEqual(args[1], (5,))
        self.assertEqual(len(result), 2)


if __name__ == '__main__':
    unittest.main()