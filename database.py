import sqlite3
import os
from datetime import datetime

class DatabaseManager:
    def __init__(self, db_path='game_library.db'):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Инициализация базы данных"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Таблица игр
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS games (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                platform TEXT,
                executable_path TEXT NOT NULL,
                status TEXT DEFAULT 'Не пройдена',
                activation_key TEXT,
                notes TEXT,
                total_play_time INTEGER DEFAULT 0,
                date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Таблица сессий игры
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS play_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                game_id INTEGER,
                start_time TIMESTAMP,
                end_time TIMESTAMP,
                duration INTEGER,
                FOREIGN KEY (game_id) REFERENCES games (id)
            )
        ''')
        
        # Таблица закладок
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bookmarks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                game_id INTEGER,
                title TEXT NOT NULL,
                url TEXT NOT NULL,
                description TEXT,
                category TEXT DEFAULT 'Общее',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (game_id) REFERENCES games (id)
            )
        ''')
        
        # Создание индексов для ускорения сортировки
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_games_name ON games(name)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_games_status ON games(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_games_play_time ON games(total_play_time)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_games_platform ON games(platform)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_games_date_added ON games(date_added)')
        
        conn.commit()
        conn.close()
    
    def add_game(self, name, platform, executable_path, status, activation_key, notes):
        """Добавление новой игры"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO games (name, platform, executable_path, status, activation_key, notes)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (name, platform, executable_path, status, activation_key, notes))
        
        game_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return game_id
    
    def get_all_games(self, sort_by='name', reverse=False):
        """Получение всех игр с возможностью сортировки"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Маппинг названий колонок для сортировки
        column_map = {
            'name': 'name',
            'platform': 'platform',
            'status': 'status',
            'play_time': 'total_play_time',
            'date_added': 'date_added'
        }
        
        order_by = column_map.get(sort_by, 'name')
        order_dir = 'DESC' if reverse else 'ASC'
        
        cursor.execute(f'''
            SELECT * FROM games 
            ORDER BY {order_by} {order_dir}, name ASC
        ''')
        games = cursor.fetchall()
        conn.close()
        return games
    
    def update_game(self, game_id, name, platform, executable_path, status, activation_key, notes):
        """Обновление информации об игре"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE games 
            SET name=?, platform=?, executable_path=?, status=?, activation_key=?, notes=?
            WHERE id=?
        ''', (name, platform, executable_path, status, activation_key, notes, game_id))
        
        conn.commit()
        conn.close()
    
    def delete_game(self, game_id):
        """Удаление игры"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM games WHERE id=?', (game_id,))
        cursor.execute('DELETE FROM play_sessions WHERE game_id=?', (game_id,))
        cursor.execute('DELETE FROM bookmarks WHERE game_id=?', (game_id,))
        
        conn.commit()
        conn.close()
    
    def start_play_session(self, game_id):
        """Начало игровой сессии"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO play_sessions (game_id, start_time)
            VALUES (?, ?)
        ''', (game_id, datetime.now()))
        
        session_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return session_id
    
    def end_play_session(self, session_id):
        """Завершение игровой сессии и подсчет времени"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT game_id, start_time FROM play_sessions WHERE id=?', (session_id,))
        session = cursor.fetchone()
        
        if session:
            game_id, start_time = session
            end_time = datetime.now()
            start_dt = datetime.fromisoformat(start_time)
            duration = int((end_time - start_dt).total_seconds())
            
            cursor.execute('''
                UPDATE play_sessions 
                SET end_time=?, duration=?
                WHERE id=?
            ''', (end_time, duration, session_id))
            
            cursor.execute('''
                UPDATE games 
                SET total_play_time = total_play_time + ?
                WHERE id=?
            ''', (duration, game_id))
            
            conn.commit()
        
        conn.close()
        return duration if session else 0
    
    def get_play_stats(self, game_id):
        """Получение статистики игры"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT total_play_time FROM games WHERE id=?', (game_id,))
        result = cursor.fetchone()
        total_time = result[0] if result else 0
        
        cursor.execute('''
            SELECT COUNT(*), SUM(duration) 
            FROM play_sessions 
            WHERE game_id=? AND duration IS NOT NULL
        ''', (game_id,))
        
        stats = cursor.fetchone()
        session_count = stats[0] or 0
        total_duration = stats[1] or 0
        
        conn.close()
        
        return {
            'total_play_time': total_time,
            'session_count': session_count,
            'average_session': total_duration // session_count if session_count > 0 else 0
        }
    
    def add_bookmark(self, game_id, title, url, description, category):
        """Добавление закладки для игры"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO bookmarks (game_id, title, url, description, category)
            VALUES (?, ?, ?, ?, ?)
        ''', (game_id, title, url, description, category))
        
        bookmark_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return bookmark_id
    
    def get_bookmarks_by_game(self, game_id):
        """Получение всех закладок для игры"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM bookmarks WHERE game_id = ? ORDER BY category, title', (game_id,))
        bookmarks = cursor.fetchall()
        conn.close()
        return bookmarks
    
    def delete_bookmark(self, bookmark_id):
        """Удаление закладки"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM bookmarks WHERE id=?', (bookmark_id,))
        conn.commit()
        conn.close()
    
    def update_bookmark(self, bookmark_id, title, url, description, category):
        """Обновление закладки"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE bookmarks 
            SET title=?, url=?, description=?, category=?
            WHERE id=?
        ''', (title, url, description, category, bookmark_id))
        
        conn.commit()
        conn.close()
    
    def get_bookmark_by_id(self, bookmark_id):
        """Получение закладки по ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM bookmarks WHERE id=?', (bookmark_id,))
        bookmark = cursor.fetchone()
        conn.close()
        return bookmark
    
    def get_games_by_status(self, status):
        """Получение игр по статусу"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM games WHERE status = ? ORDER BY name', (status,))
        games = cursor.fetchall()
        conn.close()
        return games
    
    def get_games_by_platform(self, platform):
        """Получение игр по платформе"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM games WHERE platform = ? ORDER BY name', (platform,))
        games = cursor.fetchall()
        conn.close()
        return games
    
    def get_total_play_time_stats(self):
        """Получение общей статистики по времени игры"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT SUM(total_play_time) FROM games')
        total = cursor.fetchone()[0] or 0
        
        cursor.execute('SELECT COUNT(*) FROM games WHERE total_play_time > 0')
        played = cursor.fetchone()[0] or 0
        
        cursor.execute('SELECT AVG(total_play_time) FROM games WHERE total_play_time > 0')
        avg = cursor.fetchone()[0] or 0
        
        conn.close()
        
        return {
            'total_time': total,
            'games_played': played,
            'average_time': int(avg)
        }