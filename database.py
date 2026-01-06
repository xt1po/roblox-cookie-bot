import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Optional, Tuple

class Database:
    def __init__(self, db_path: str = 'database.db'):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Таблица пользователей
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Таблица куки
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS cookies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            cookie_text TEXT,
            extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
        ''')
        
        conn.commit()
        conn.close()
    
    def add_user(self, user_id: int, username: str, first_name: str, last_name: str = ""):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT OR IGNORE INTO users (user_id, username, first_name, last_name)
        VALUES (?, ?, ?, ?)
        ''', (user_id, username, first_name, last_name))
        
        conn.commit()
        conn.close()
    
    def update_user_activity(self, user_id: int):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        UPDATE users SET last_activity = CURRENT_TIMESTAMP
        WHERE user_id = ?
        ''', (user_id,))
        
        conn.commit()
        conn.close()
    
    def save_cookie(self, user_id: int, cookie_text: str) -> bool:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT INTO cookies (user_id, cookie_text)
        VALUES (?, ?)
        ''', (user_id, cookie_text))
        
        conn.commit()
        conn.close()
        return True
    
    def get_user_cookies(self, user_id: int) -> List[Dict]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT cookie_text, extracted_at FROM cookies
        WHERE user_id = ?
        ORDER BY extracted_at DESC
        ''', (user_id,))
        
        cookies = [{'cookie': row[0], 'time': row[1]} for row in cursor.fetchall()]
        conn.close()
        return cookies
    
    def get_all_users(self) -> List[Dict]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT u.user_id, u.username, u.first_name, u.registered_at, u.last_activity,
               COUNT(c.id) as cookie_count
        FROM users u
        LEFT JOIN cookies c ON u.user_id = c.user_id
        GROUP BY u.user_id
        ORDER BY u.registered_at DESC
        ''')
        
        users = []
        for row in cursor.fetchall():
            users.append({
                'user_id': row[0],
                'username': row[1],
                'first_name': row[2],
                'registered_at': row[3],
                'last_activity': row[4],
                'cookie_count': row[5]
            })
        
        conn.close()
        return users
    
    def get_all_cookies(self) -> List[Dict]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT c.cookie_text, u.user_id, u.username, c.extracted_at
        FROM cookies c
        JOIN users u ON c.user_id = u.user_id
        ORDER BY c.extracted_at DESC
        ''')
        
        cookies = []
        for row in cursor.fetchall():
            cookies.append({
                'cookie': row[0],
                'user_id': row[1],
                'username': row[2],
                'extracted_at': row[3]
            })
        
        conn.close()
        return cookies
    
    def delete_user(self, user_id: int) -> bool:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM cookies WHERE user_id = ?', (user_id,))
        cursor.execute('DELETE FROM users WHERE user_id = ?', (user_id,))
        
        conn.commit()
        conn.close()
        return cursor.rowcount > 0
    
    def get_stats(self) -> Dict:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM users')
        total_users = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM cookies')
        total_cookies = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(DISTINCT user_id) FROM cookies')
        users_with_cookies = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'total_users': total_users,
            'total_cookies': total_cookies,
            'users_with_cookies': users_with_cookies,
            'avg_cookies_per_user': total_cookies / total_users if total_users > 0 else 0
        }
