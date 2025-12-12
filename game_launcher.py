import subprocess
import threading
import time
from database import DatabaseManager

class GameLauncher:
    def __init__(self):
        self.db = DatabaseManager()
        self.active_sessions = {}
        self.on_game_end_callbacks = []
    
    def add_game_end_callback(self, callback):
        """Добавление callback функции при завершении игры"""
        self.on_game_end_callbacks.append(callback)
    
    def _notify_game_end(self, game_id, duration):
        """Вызов всех callback функций при завершении игры"""
        for callback in self.on_game_end_callbacks:
            try:
                callback(game_id, duration)
            except Exception as e:
                print(f"Ошибка в callback: {e}")
    
    def launch_game(self, game_id, executable_path):
        """Запуск игры с отслеживанием времени"""
        try:
            session_id = self.db.start_play_session(game_id)
            process = subprocess.Popen(executable_path)
            
            self.active_sessions[process.pid] = {
                'game_id': game_id,
                'session_id': session_id,
                'process': process,
                'start_time': time.time()
            }
            
            monitor_thread = threading.Thread(
                target=self._monitor_process, 
                args=(process.pid,)
            )
            monitor_thread.daemon = True
            monitor_thread.start()
            
            return True
            
        except Exception as e:
            print(f"Ошибка при запуске игры: {e}")
            return False
    
    def _monitor_process(self, pid):
        """Мониторинг процесса игры"""
        session_info = self.active_sessions.get(pid)
        if not session_info:
            return
        
        process = session_info['process']
        game_id = session_info['game_id']
        
        try:
            process.wait()
            duration = self.db.end_play_session(session_info['session_id'])
            self._notify_game_end(game_id, duration)
            
            if pid in self.active_sessions:
                del self.active_sessions[pid]
                
        except Exception as e:
            print(f"Ошибка при мониторинге процесса: {e}")
    
    def get_active_sessions(self):
        """Получение списка активных сессий"""
        return self.active_sessions
    
    def force_end_session(self, pid):
        """Принудительное завершение сессии"""
        if pid in self.active_sessions:
            session_info = self.active_sessions[pid]
            try:
                session_info['process'].terminate()
                duration = self.db.end_play_session(session_info['session_id'])
                self._notify_game_end(session_info['game_id'], duration)
            except:
                pass
            finally:
                if pid in self.active_sessions:
                    del self.active_sessions[pid]