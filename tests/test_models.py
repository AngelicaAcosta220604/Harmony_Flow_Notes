import unittest
from datetime import datetime, timedelta
from models.note import Note
from models.task import Task
from models.flashcard import Flashcard
from models.session import Session


class TestNote(unittest.TestCase):
    def test_from_row_and_to_dict(self):
        row = {
            'id': 1, 'topic_id': 10, 'title': 'Test Note',
            'content': 'Content', 'created_at': '2023-01-01T00:00:00',
            'updated_at': '2023-01-02T00:00:00'
        }
        note = Note.from_row(row)
        self.assertEqual(note.id, 1)
        self.assertEqual(note.title, 'Test Note')

        d = note.to_dict()
        self.assertEqual(d['id'], 1)
        self.assertEqual(d['title'], 'Test Note')

    def test_update_content(self):
        note = Note(id=1, topic_id=10, title='Test', content='Old')
        note.update_content('New')
        self.assertEqual(note.content, 'New')
        # Проверяем, что updated_at обновился
        self.assertTrue(datetime.fromisoformat(note.updated_at) > datetime.now() - timedelta(seconds=1))

    def test_get_preview(self):
        note = Note(id=1, topic_id=10, title='Test', content='A' * 150)
        preview = note.get_preview(100)
        self.assertEqual(len(preview), 103)  # 100 символов + '...'
        self.assertTrue(preview.endswith('...'))

    def test_word_count(self):
        note = Note(id=1, topic_id=10, title='Test', content='one two three')
        self.assertEqual(note.word_count, 3)

        note_empty = Note(id=2, topic_id=10, title='Test', content='')
        self.assertEqual(note_empty.word_count, 0)


class TestTask(unittest.TestCase):
    def test_complete(self):
        task = Task(id=1, title='Test')
        task.complete()
        self.assertEqual(task.status, 'completed')
        self.assertIsNotNone(task.completed_at)

    def test_is_overdue(self):
        # Просроченная активная задача
        past = (datetime.now() - timedelta(days=1)).isoformat()
        task = Task(id=1, title='Test', deadline=past, status='active')
        self.assertTrue(task.is_overdue())

        # Выполненная задача с прошедшим дедлайном не считается просроченной
        task.complete()
        self.assertFalse(task.is_overdue())

        # Активная задача с будущим дедлайном
        future = (datetime.now() + timedelta(days=1)).isoformat()
        task2 = Task(id=2, title='Test', deadline=future, status='active')
        self.assertFalse(task2.is_overdue())

    def test_status_icon(self):
        task = Task(id=1, title='Test', status='active')
        self.assertEqual(task.status_icon, "⏳")

        task.complete()
        self.assertEqual(task.status_icon, "✅")

        past = (datetime.now() - timedelta(days=1)).isoformat()
        task2 = Task(id=2, title='Test', deadline=past, status='active')
        self.assertEqual(task2.status_icon, "⚠️")


class TestFlashcard(unittest.TestCase):
    def test_create_free(self):
        card = Flashcard.create_free(1, 'Free content')
        self.assertTrue(card.is_free)
        self.assertFalse(card.is_qa)
        self.assertEqual(card.display_front, 'Free content')
        self.assertEqual(card.display_back, 'Free content')

    def test_create_qa(self):
        card = Flashcard.create_qa(1, 'Q?', 'A!')
        self.assertFalse(card.is_free)
        self.assertTrue(card.is_qa)
        self.assertEqual(card.display_front, 'Q?')
        self.assertEqual(card.display_back, 'A!')


class TestSession(unittest.TestCase):
    def test_lifecycle(self):
        # По умолчанию сессия создается со статусом 'active'
        session = Session(id=1, topic_id=1)
        self.assertTrue(session.is_active)  # Исправлено: теперь ожидаем True
        self.assertFalse(session.is_completed)

        # Ставим на паузу
        session.pause()
        self.assertFalse(session.is_active)
        self.assertEqual(session.status, 'paused')

        # Возобновляем
        session.resume()
        self.assertTrue(session.is_active)
        self.assertEqual(session.status, 'active')

        # Завершаем (обязательно вызываем start(), чтобы установить start_time)
        session.start()
        session.complete()
        self.assertFalse(session.is_active)
        self.assertTrue(session.is_completed)
        self.assertEqual(session.status, 'completed')
        self.assertIsNotNone(session.end_time)
        self.assertIsNotNone(session.duration_minutes)

        # Бонус: проверяем автозавершение
        session2 = Session(id=2, topic_id=1)
        session2.start()
        session2.complete(auto=True)
        self.assertEqual(session2.status, 'auto_completed')

    def test_duration_display(self):
        session = Session(id=1, topic_id=1, duration_minutes=90)
        self.assertEqual(session.duration_display, "1ч 30м")

        session2 = Session(id=2, topic_id=1, duration_minutes=45)
        self.assertEqual(session2.duration_display, "45м")

        session3 = Session(id=3, topic_id=1)
        self.assertEqual(session3.duration_display, "—")


if __name__ == '__main__':
    unittest.main()