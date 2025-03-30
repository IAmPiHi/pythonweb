import os
import sqlite3

class Database:
    def __init__(self, db_path="db/database.db"):
        os.makedirs("db", exist_ok=True)
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self._create_tables()

    def _create_tables(self):
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL 
        )
        """)
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL,
            postby TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)
        self.conn.commit()

    def get_user(self, username):
        self.cursor.execute("SELECT id, username, password FROM users WHERE username = ?", (username,))
        return self.cursor.fetchone()
    
    def get_user_by_id(self, user_id):
        self.cursor.execute("SELECT id, username, password FROM users WHERE id = ?", (user_id,))
        return self.cursor.fetchone()
    
    def add_user(self, username, password):
        self.cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        self.conn.commit()

    def delete_user(self, user_id):
        self.cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        self.conn.commit()

    def get_all_users(self):
        self.cursor.execute("SELECT id, username FROM users")
        return self.cursor.fetchall()

    def add_note(self, content,username):
        self.cursor.execute("INSERT INTO notes (content,postby) VALUES (?, ?)", (content,username))
        self.conn.commit()

    def get_all_notes(self):
        self.cursor.execute("SELECT id, content, postby FROM notes ORDER BY timestamp DESC")
        return self.cursor.fetchall()

    def delete_note(self, note_id):  # 新增：刪除便利貼
        self.cursor.execute("DELETE FROM notes WHERE id = ?", (note_id,))
        self.conn.commit()

    def close(self):
        self.conn.close()