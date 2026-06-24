import unittest
from unittest.mock import patch
from database.repositories.note_repo import NoteRepository
from database.repositories.flashcard_repo import FlashcardRepository


class TestNoteRepository(unittest.TestCase):
    def setUp(self):
        self.repo = NoteRepository()

    @patch('database.repositories.note_repo.db')
    def test_get_all(self, mock_db):
        mock_db.fetchall.return_value = [{'id': 1, 'title': 'Note 1'}]
        result = self.repo.get_all()
        mock_db.fetchall.assert_called_once_with("SELECT * FROM notes ORDER BY updated_at DESC")
        self.assertEqual(len(result), 1)

    @patch('database.repositories.note_repo.db')
    def test_create(self, mock_db):
        mock_db.insert.return_value = 1
        result = self.repo.create(10, 'Title', 'Content')
        mock_db.insert.assert_called_once_with('notes', {
            'topic_id': 10, 'title': 'Title', 'content': 'Content'
        })
        self.assertEqual(result, 1)

    @patch('database.repositories.note_repo.db')
    def test_update_allowed_fields(self, mock_db):
        mock_db.update.return_value = 1
        # Пытаемся обновить разрешенное и запрещенное поле
        self.repo.update(1, title='New Title', invalid_field='Ignore')

        # Проверяем, что в БД ушли только разрешенные поля + updated_at
        call_args = mock_db.update.call_args[0]
        data = call_args[1]
        self.assertIn('title', data)
        self.assertNotIn('invalid_field', data)
        self.assertIn('updated_at', data)

    @patch('database.repositories.note_repo.db')
    def test_search(self, mock_db):
        mock_db.fetchall.return_value = []
        self.repo.search('query')
        mock_db.fetchall.assert_called_once()
        args = mock_db.fetchall.call_args[0]
        # Проверяем, что поисковый запрос обернут в %...%
        self.assertIn('%query%', args[1])


class TestFlashcardRepository(unittest.TestCase):
    def setUp(self):
        self.repo = FlashcardRepository()

    @patch('database.repositories.flashcard_repo.db')
    def test_create_free(self, mock_db):
        mock_db.insert.return_value = 1
        self.repo.create_free(10, 'Content')
        mock_db.insert.assert_called_once_with('flashcards', {
            'topic_id': 10, 'type': 'free', 'content': 'Content'
        })

    @patch('database.repositories.flashcard_repo.db')
    def test_create_qa(self, mock_db):
        mock_db.insert.return_value = 2
        self.repo.create_qa(10, 'Q', 'A')
        mock_db.insert.assert_called_once_with('flashcards', {
            'topic_id': 10, 'type': 'question_answer', 'question': 'Q', 'answer': 'A'
        })


if __name__ == '__main__':
    unittest.main()