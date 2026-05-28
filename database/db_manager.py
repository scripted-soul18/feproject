import sqlite3
import os
import time
import numpy as np
from config import DB_PATH, REGISTERED_DIR, SNAPSHOTS_DIR

class DatabaseManager:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Access columns by name like dict
        return conn

    def _init_db(self):
        """Creates the necessary tables if they do not exist."""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Users Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                photo_path TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Encodings Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS encodings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                encoding BLOB NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)

        # Logs Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                timestamp TEXT NOT NULL,
                confidence REAL NOT NULL,
                snapshot_path TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)

        conn.commit()
        conn.close()

    def add_user(self, name, photo_path, encoding):
        """
        Registers a new user and stores their face encoding.
        :param name: Unique name of the user.
        :param photo_path: Relative or absolute path to the stored photo.
        :param encoding: 128-dimensional numpy array of the face encoding.
        :return: (bool, str) Success flag and message.
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            # 1. Insert user
            cursor.execute(
                "INSERT INTO users (name, photo_path) VALUES (?, ?)",
                (name, photo_path)
            )
            user_id = cursor.lastrowid

            # 2. Serialize encoding to bytes
            encoding_blob = encoding.tobytes()

            # 3. Insert encoding
            cursor.execute(
                "INSERT INTO encodings (user_id, encoding) VALUES (?, ?)",
                (user_id, encoding_blob)
            )
            
            conn.commit()
            return True, f"User '{name}' registered successfully."
        except sqlite3.IntegrityError:
            return False, f"User '{name}' is already registered."
        except Exception as e:
            return False, f"Error registering user: {str(e)}"
        finally:
            conn.close()

    def get_all_users(self):
        """
        Retrieves all registered users along with their face encodings.
        :return: List of dicts representing each user.
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT u.id, u.name, u.photo_path, u.created_at, e.encoding 
            FROM users u
            JOIN encodings e ON u.id = e.user_id
        """)
        
        rows = cursor.fetchall()
        users = []
        for r in rows:
            # Deserialize the encoding
            encoding = np.frombuffer(r['encoding'], dtype=np.float64)
            users.append({
                "id": r['id'],
                "name": r['name'],
                "photo_path": r['photo_path'],
                "created_at": r['created_at'],
                "encoding": encoding
            })
            
        conn.close()
        return users

    def delete_user(self, user_id):
        """
        Deletes a user from the database and removes their registered image file.
        :param user_id: ID of the user to delete.
        :return: bool success
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            # Get photo path first to clean up physical file
            cursor.execute("SELECT photo_path FROM users WHERE id = ?", (user_id,))
            row = cursor.fetchone()
            if row and row['photo_path']:
                photo_path = row['photo_path']
                if os.path.exists(photo_path):
                    try:
                        os.remove(photo_path)
                    except OSError:
                        pass # Ignore if failed to delete file

            # Enable PRAGMA foreign_keys = ON to cascade delete encodings and logs
            cursor.execute("PRAGMA foreign_keys = ON")
            cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
            conn.commit()
            return True
        except Exception as e:
            print("DB Delete Error:", e)
            return False
        finally:
            conn.close()

    def log_detection(self, name, confidence, snapshot_path=None):
        """
        Logs a face detection event into the database.
        :param name: Name of the detected user, or "Unknown".
        :param confidence: The match score/distance (lower is better, shown as confidence).
        :param snapshot_path: Filepath of the captured frame snapshot.
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        
        try:
            # Find user ID if it's a known user
            user_id = None
            if name != "Unknown":
                cursor.execute("SELECT id FROM users WHERE name = ?", (name,))
                row = cursor.fetchone()
                if row:
                    user_id = row['id']
            
            cursor.execute(
                "INSERT INTO logs (user_id, timestamp, confidence, snapshot_path) VALUES (?, ?, ?, ?)",
                (user_id, timestamp, confidence, snapshot_path)
            )
            conn.commit()
        except Exception as e:
            print("DB Log Error:", e)
        finally:
            conn.close()

    def get_logs(self, search_query=None):
        """
        Retrieves logs from the database, optionally filtered.
        :param search_query: Name to filter by.
        :return: List of dicts.
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        if search_query:
            cursor.execute("""
                SELECT l.id, COALESCE(u.name, 'Unknown') as name, l.timestamp, l.confidence, l.snapshot_path
                FROM logs l
                LEFT JOIN users u ON l.user_id = u.id
                WHERE u.name LIKE ? OR (u.name IS NULL AND 'Unknown' LIKE ?)
                ORDER BY l.id DESC
            """, (f"%{search_query}%", f"%{search_query}%"))
        else:
            cursor.execute("""
                SELECT l.id, COALESCE(u.name, 'Unknown') as name, l.timestamp, l.confidence, l.snapshot_path
                FROM logs l
                LEFT JOIN users u ON l.user_id = u.id
                ORDER BY l.id DESC
            """)
            
        rows = cursor.fetchall()
        logs = [dict(r) for r in rows]
        conn.close()
        return logs

    def clear_all_logs(self):
        """Clears all records in the logs table and deletes log snapshot files."""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            # Delete physical files
            cursor.execute("SELECT snapshot_path FROM logs")
            rows = cursor.fetchall()
            for r in rows:
                path = r['snapshot_path']
                if path and os.path.exists(path):
                    try:
                        os.remove(path)
                    except OSError:
                        pass
            
            cursor.execute("DELETE FROM logs")
            conn.commit()
            return True
        except Exception as e:
            print("DB Clear Logs Error:", e)
            return False
        finally:
            conn.close()
