import os
import sqlite3
from datetime import datetime

db_path = os.path.abspath('tasks.db')


class User:
    def __init__(self):
        self.users = {}

    def add_user(self, user_id):
        if user_id not in self.users:
            self.users[user_id] = []


class Task:
    def __init__(self):
        self.db_path = db_path

        conn = sqlite3.connect('tasks.db')
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                created_at TEXT NOT NULL,
                deadline TEXT,
                status TEXT NOT NULL DEFAULT 'в процессе выполнения'
            )
        """)
        conn.commit()
        conn.close()

    def add_task(self, user_id, title, description, deadline):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute("""
            INSERT INTO tasks
            (user_id, title, description, created_at, deadline)
            VALUES (?, ?, ?, ?, ?)
            """, (user_id, title, description, now, deadline))

        conn.commit()
        conn.close()

    def get_task(self, user_id, task_id):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM tasks WHERE id = ? AND user_id = ?
        """, (task_id, user_id))
        task = cursor.fetchone()
        conn.close()
        return task

    def get_all_tasks(self, user_id):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM tasks WHERE user_id = ?",
            (user_id,)
        )
        tasks = cursor.fetchall()
        conn.close()
        return tasks

    def update_task(
        self,
        user_id,
        task_id,
        title=None,
        description=None,
        deadline=None
    ):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        task = self.get_task(user_id, task_id)
        if task is None:
            return False
        if title is None:
            title = task[2]
        if description is None:
            description = task[3]
        if deadline is None:
            deadline = task[5]
        cursor.execute("""
            UPDATE tasks SET
            title = ?, description = ?, deadline = ?
            WHERE id = ? AND user_id = ?
        """, (title, description, deadline, task_id, user_id))
        conn.commit()
        conn.close()
        return True

    def delete_task(self, user_id, task_id):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            "DELETE FROM tasks WHERE id = ? AND user_id = ?",
            (task_id, user_id)
        )
        conn.commit()
        conn.close()

    def mark_as_done(self, user_id, task_id):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE tasks SET
            status = 'Выполнено'
            WHERE id = ? AND user_id = ?
        """, (task_id, user_id))
        conn.commit()
        conn.close()
        return True
