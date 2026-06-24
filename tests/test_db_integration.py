import unittest
import sqlite3
from datetime import datetime


class TestDatabaseIntegration(unittest.TestCase):
    """Интеграционные тесты с in-memory SQLite базой данных"""

    def setUp(self):
        """Создаем in-memory БД и таблицы перед каждым тестом"""
        self.conn = sqlite3.connect(':memory:')
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self._create_tables()

    def tearDown(self):
        """Закрываем соединение после каждого теста"""
        self.conn.close()

    def _create_tables(self):
        """Создаем таблицы по схеме из db_manager.py"""
        cursor = self.conn.cursor()

        cursor.execute('''
            CREATE TABLE topics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                parent_id INTEGER,
                type TEXT DEFAULT 'topic',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (parent_id) REFERENCES topics(id) ON DELETE CASCADE
            )
        ''')

        cursor.execute('''
            CREATE TABLE notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                topic_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                content TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (topic_id) REFERENCES topics(id) ON DELETE CASCADE
            )
        ''')

        cursor.execute('''
            CREATE TABLE tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                topic_id INTEGER,
                title TEXT NOT NULL,
                description TEXT,
                deadline DATETIME,
                status TEXT DEFAULT 'active',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                completed_at DATETIME,
                FOREIGN KEY (topic_id) REFERENCES topics(id) ON DELETE SET NULL
            )
        ''')

        cursor.execute('''
            CREATE TABLE sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                topic_id INTEGER NOT NULL,
                start_time DATETIME,
                end_time DATETIME,
                duration_minutes INTEGER,
                status TEXT DEFAULT 'active',
                focus INTEGER DEFAULT 50,
                energy INTEGER DEFAULT 50,
                interest INTEGER DEFAULT 50,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (topic_id) REFERENCES topics(id) ON DELETE CASCADE
            )
        ''')

        cursor.execute('''
            CREATE TABLE flashcards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                topic_id INTEGER NOT NULL,
                type TEXT NOT NULL,
                question TEXT,
                answer TEXT,
                content TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (topic_id) REFERENCES topics(id) ON DELETE CASCADE
            )
        ''')

        self.conn.commit()

    def _execute(self, query, params=()):
        """Вспомогательный метод для выполнения запросов"""
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        self.conn.commit()
        return cursor

    def _fetchone(self, query, params=()):
        """Вспомогательный метод для получения одной строки"""
        cursor = self._execute(query, params)
        row = cursor.fetchone()
        return dict(row) if row else None

    def _fetchall(self, query, params=()):
        """Вспомогательный метод для получения всех строк"""
        cursor = self._execute(query, params)
        return [dict(row) for row in cursor.fetchall()]

    def test_topics_crud(self):
        """Тест CRUD операций для таблицы topics"""
        # Create
        cursor = self._execute(
            "INSERT INTO topics (name, description, type) VALUES (?, ?, ?)",
            ('Test Topic', 'Description', 'topic')
        )
        topic_id = cursor.lastrowid
        self.assertIsNotNone(topic_id)

        # Read
        topic = self._fetchone("SELECT * FROM topics WHERE id = ?", (topic_id,))
        self.assertEqual(topic['name'], 'Test Topic')
        self.assertEqual(topic['description'], 'Description')
        self.assertEqual(topic['type'], 'topic')

        # Update
        self._execute(
            "UPDATE topics SET name = ? WHERE id = ?",
            ('Updated Topic', topic_id)
        )
        topic = self._fetchone("SELECT * FROM topics WHERE id = ?", (topic_id,))
        self.assertEqual(topic['name'], 'Updated Topic')

        # Delete
        self._execute("DELETE FROM topics WHERE id = ?", (topic_id,))
        topic = self._fetchone("SELECT * FROM topics WHERE id = ?", (topic_id,))
        self.assertIsNone(topic)

    def test_topics_hierarchy(self):
        """Тест иерархии тем (parent_id)"""
        # Создаем родительскую тему
        cursor = self._execute(
            "INSERT INTO topics (name, type) VALUES (?, ?)",
            ('Parent', 'folder')
        )
        parent_id = cursor.lastrowid

        # Создаем дочерние темы
        self._execute(
            "INSERT INTO topics (name, parent_id, type) VALUES (?, ?, ?)",
            ('Child 1', parent_id, 'topic')
        )
        self._execute(
            "INSERT INTO topics (name, parent_id, type) VALUES (?, ?, ?)",
            ('Child 2', parent_id, 'topic')
        )

        # Проверяем получение дочерних тем
        children = self._fetchall(
            "SELECT * FROM topics WHERE parent_id = ?",
            (parent_id,)
        )
        self.assertEqual(len(children), 2)

        # Проверяем каскадное удаление
        self._execute("DELETE FROM topics WHERE id = ?", (parent_id,))
        children = self._fetchall(
            "SELECT * FROM topics WHERE parent_id = ?",
            (parent_id,)
        )
        self.assertEqual(len(children), 0)

    def test_notes_crud(self):
        """Тест CRUD операций для таблицы notes"""
        # Создаем тему
        cursor = self._execute(
            "INSERT INTO topics (name, type) VALUES (?, ?)",
            ('Topic', 'topic')
        )
        topic_id = cursor.lastrowid

        # Create note
        cursor = self._execute(
            "INSERT INTO notes (topic_id, title, content) VALUES (?, ?, ?)",
            (topic_id, 'Test Note', 'Content')
        )
        note_id = cursor.lastrowid

        # Read
        note = self._fetchone("SELECT * FROM notes WHERE id = ?", (note_id,))
        self.assertEqual(note['title'], 'Test Note')
        self.assertEqual(note['content'], 'Content')
        self.assertEqual(note['topic_id'], topic_id)

        # Update
        self._execute(
            "UPDATE notes SET content = ?, updated_at = ? WHERE id = ?",
            ('New Content', datetime.now().isoformat(), note_id)
        )
        note = self._fetchone("SELECT * FROM notes WHERE id = ?", (note_id,))
        self.assertEqual(note['content'], 'New Content')

        # Delete
        self._execute("DELETE FROM notes WHERE id = ?", (note_id,))
        note = self._fetchone("SELECT * FROM notes WHERE id = ?", (note_id,))
        self.assertIsNone(note)

    def test_tasks_crud(self):
        """Тест CRUD операций для таблицы tasks"""
        # Создаем тему
        cursor = self._execute(
            "INSERT INTO topics (name, type) VALUES (?, ?)",
            ('Topic', 'topic')
        )
        topic_id = cursor.lastrowid

        # Create task
        cursor = self._execute(
            "INSERT INTO tasks (topic_id, title, description, status) VALUES (?, ?, ?, ?)",
            (topic_id, 'Test Task', 'Description', 'active')
        )
        task_id = cursor.lastrowid

        # Read
        task = self._fetchone("SELECT * FROM tasks WHERE id = ?", (task_id,))
        self.assertEqual(task['title'], 'Test Task')
        self.assertEqual(task['status'], 'active')

        # Complete task
        self._execute(
            "UPDATE tasks SET status = ?, completed_at = ? WHERE id = ?",
            ('completed', datetime.now().isoformat(), task_id)
        )
        task = self._fetchone("SELECT * FROM tasks WHERE id = ?", (task_id,))
        self.assertEqual(task['status'], 'completed')
        self.assertIsNotNone(task['completed_at'])

        # Get overdue tasks
        past_deadline = '2020-01-01T00:00:00'
        self._execute(
            "INSERT INTO tasks (topic_id, title, deadline, status) VALUES (?, ?, ?, ?)",
            (topic_id, 'Overdue Task', past_deadline, 'active')
        )
        overdue = self._fetchall(
            "SELECT * FROM tasks WHERE status = 'active' AND deadline < ?",
            (datetime.now().isoformat(),)
        )
        self.assertEqual(len(overdue), 1)
        self.assertEqual(overdue[0]['title'], 'Overdue Task')

    def test_sessions_crud(self):
        """Тест CRUD операций для таблицы sessions"""
        # Создаем тему
        cursor = self._execute(
            "INSERT INTO topics (name, type) VALUES (?, ?)",
            ('Topic', 'topic')
        )
        topic_id = cursor.lastrowid

        # Create session
        now = datetime.now().isoformat()
        cursor = self._execute(
            "INSERT INTO sessions (topic_id, start_time, status) VALUES (?, ?, ?)",
            (topic_id, now, 'active')
        )
        session_id = cursor.lastrowid

        # Read
        session = self._fetchone("SELECT * FROM sessions WHERE id = ?", (session_id,))
        self.assertEqual(session['status'], 'active')
        self.assertEqual(session['topic_id'], topic_id)

        # End session
        end_time = datetime.now().isoformat()
        self._execute(
            "UPDATE sessions SET end_time = ?, duration_minutes = ?, status = ? WHERE id = ?",
            (end_time, 45, 'completed', session_id)
        )
        session = self._fetchone("SELECT * FROM sessions WHERE id = ?", (session_id,))
        self.assertEqual(session['status'], 'completed')
        self.assertEqual(session['duration_minutes'], 45)
        self.assertIsNotNone(session['end_time'])

        # Get active sessions
        active = self._fetchall(
            "SELECT * FROM sessions WHERE status = 'active' LIMIT 1"
        )
        self.assertEqual(len(active), 0)

    def test_flashcards_crud(self):
        """Тест CRUD операций для таблицы flashcards"""
        # Создаем тему
        cursor = self._execute(
            "INSERT INTO topics (name, type) VALUES (?, ?)",
            ('Topic', 'topic')
        )
        topic_id = cursor.lastrowid

        # Create QA flashcard
        cursor = self._execute(
            "INSERT INTO flashcards (topic_id, type, question, answer) VALUES (?, ?, ?, ?)",
            (topic_id, 'question_answer', 'What is Python?', 'A programming language')
        )
        card_id = cursor.lastrowid

        # Read
        card = self._fetchone("SELECT * FROM flashcards WHERE id = ?", (card_id,))
        self.assertEqual(card['type'], 'question_answer')
        self.assertEqual(card['question'], 'What is Python?')
        self.assertEqual(card['answer'], 'A programming language')

        # Create free flashcard
        cursor = self._execute(
            "INSERT INTO flashcards (topic_id, type, content) VALUES (?, ?, ?)",
            (topic_id, 'free', 'Free content')
        )
        free_card_id = cursor.lastrowid

        free_card = self._fetchone("SELECT * FROM flashcards WHERE id = ?", (free_card_id,))
        self.assertEqual(free_card['type'], 'free')
        self.assertEqual(free_card['content'], 'Free content')

        # Get all cards for topic
        cards = self._fetchall(
            "SELECT * FROM flashcards WHERE topic_id = ?",
            (topic_id,)
        )
        self.assertEqual(len(cards), 2)

    def test_cascade_delete(self):
        """Тест каскадного удаления связанных данных"""
        # Создаем тему
        cursor = self._execute(
            "INSERT INTO topics (name, type) VALUES (?, ?)",
            ('Topic', 'topic')
        )
        topic_id = cursor.lastrowid

        # Создаем связанные данные
        self._execute(
            "INSERT INTO notes (topic_id, title, content) VALUES (?, ?, ?)",
            (topic_id, 'Note', 'Content')
        )
        self._execute(
            "INSERT INTO tasks (topic_id, title, status) VALUES (?, ?, ?)",
            (topic_id, 'Task', 'active')
        )
        self._execute(
            "INSERT INTO sessions (topic_id, start_time, status) VALUES (?, ?, ?)",
            (topic_id, datetime.now().isoformat(), 'active')
        )
        self._execute(
            "INSERT INTO flashcards (topic_id, type, content) VALUES (?, ?, ?)",
            (topic_id, 'free', 'Content')
        )

        # Удаляем тему
        self._execute("DELETE FROM topics WHERE id = ?", (topic_id,))

        # Проверяем, что все связанные данные удалены
        notes = self._fetchall("SELECT * FROM notes WHERE topic_id = ?", (topic_id,))
        self.assertEqual(len(notes), 0)

        # Задачи должны остаться, но topic_id = NULL (ON DELETE SET NULL)
        tasks = self._fetchall("SELECT * FROM tasks WHERE title = 'Task'")
        self.assertEqual(len(tasks), 1)
        self.assertIsNone(tasks[0]['topic_id'])

        sessions = self._fetchall("SELECT * FROM sessions WHERE topic_id = ?", (topic_id,))
        self.assertEqual(len(sessions), 0)

        flashcards = self._fetchall("SELECT * FROM flashcards WHERE topic_id = ?", (topic_id,))
        self.assertEqual(len(flashcards), 0)

    def test_search_queries(self):
        """Тест поисковых запросов с LIKE"""
        # Создаем тему
        cursor = self._execute(
            "INSERT INTO topics (name, type) VALUES (?, ?)",
            ('Python Programming', 'topic')
        )
        topic_id = cursor.lastrowid

        # Создаем заметки
        self._execute(
            "INSERT INTO notes (topic_id, title, content) VALUES (?, ?, ?)",
            (topic_id, 'Python Basics', 'Learn Python')
        )
        self._execute(
            "INSERT INTO notes (topic_id, title, content) VALUES (?, ?, ?)",
            (topic_id, 'Java Basics', 'Learn Java')
        )

        # Поиск по названию
        results = self._fetchall(
            "SELECT * FROM notes WHERE title LIKE ?",
            ('%Python%',)
        )
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['title'], 'Python Basics')

        # Поиск по содержимому
        results = self._fetchall(
            "SELECT * FROM notes WHERE content LIKE ?",
            ('%Learn%',)
        )
        self.assertEqual(len(results), 2)


if __name__ == '__main__':
    unittest.main()