import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
from pathlib import Path
import pyperclip
import webbrowser
from database import DatabaseManager
from game_launcher import GameLauncher
from icon_manager import IconManager
from theme_manager import ThemeManager

class GameLibraryManager:
    def __init__(self, root):
        self.root = root
        self.root.title("Game Library Manager")
        self.root.geometry("1300x900")
        
        # Применение темной темы
        ThemeManager.apply_dark_theme(root)
        
        # Инициализация менеджеров
        self.db = DatabaseManager()
        self.launcher = GameLauncher()
        self.icon_manager = IconManager()
        
        # Кэш для иконок
        self.icon_cache = {}
        
        # Переменные для сортировки
        self.sort_column = 'name'
        self.sort_reverse = False
        
        # Регистрируем callback для завершения игры
        self.launcher.add_game_end_callback(self.on_game_end)
        
        # Переменные
        self.notebook = None
        self.bookmarks_frame = None
        self.last_played_game_id = None
        
        # Создание интерфейса
        self.create_widgets()
        
        # Загрузка данных
        self.load_games()
        
        # Обновление активных сессий
        self.update_active_sessions()
    
    def get_game_icon(self, exe_path):
        """Получение иконки игры (с кэшированием)"""
        if not exe_path or not os.path.exists(exe_path):
            return None
            
        if exe_path in self.icon_cache:
            return self.icon_cache[exe_path]
        
        try:
            icon = self.icon_manager.get_icon_image(exe_path)
            if icon:
                self.icon_cache[exe_path] = icon
                return icon
        except Exception as e:
            print(f"Ошибка загрузки иконки {exe_path}: {e}")
        
        return None
    
    def create_widgets(self):
        """Создание элементов интерфейса"""
        # Notebook (вкладки)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Вкладка библиотеки игр
        self.library_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.library_frame, text="Библиотека игр")
        
        # Вкладка закладок
        self.bookmarks_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.bookmarks_frame, text="Закладки", state="hidden")
        
        # Настройка библиотеки
        self.library_frame.columnconfigure(1, weight=1)
        self.library_frame.rowconfigure(3, weight=1)
        
        # Заголовок
        title_label = ttk.Label(self.library_frame, 
                               text="Game Library Manager", 
                               font=('Arial', 18, 'bold'))
        title_label.grid(row=0, column=0, columnspan=5, pady=(0, 20))
        
        # Активные сессии
        self.sessions_frame = ttk.LabelFrame(self.library_frame, 
                                           text="Активные сессии", 
                                           padding="5")
        self.sessions_frame.grid(row=1, column=0, columnspan=5, 
                                sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.sessions_label = ttk.Label(self.sessions_frame, 
                                       text="Нет активных сессий")
        self.sessions_label.pack()
        
        # Панель управления
        control_frame = ttk.Frame(self.library_frame)
        control_frame.grid(row=2, column=0, columnspan=5, pady=(0, 10), sticky=tk.W)
        
        # Кнопка добавления игры
        add_button = ttk.Button(control_frame, 
                               text="Добавить игру", 
                               command=self.show_add_game_dialog)
        add_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # Поиск
        search_frame = ttk.Frame(control_frame)
        search_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        ttk.Label(search_frame, text="Поиск:").pack(side=tk.LEFT, padx=(20, 5))
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(search_frame, 
                                     textvariable=self.search_var,
                                     width=40)
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.search_entry.bind('<KeyRelease>', self.on_search)
        
        # Кнопки сортировки
        sort_frame = ttk.Frame(control_frame)
        sort_frame.pack(side=tk.LEFT, padx=(20, 0))
        
        ttk.Label(sort_frame, text="Сортировка:").pack(side=tk.LEFT, padx=(10, 5))
        
        self.sort_var = tk.StringVar(value="Название")
        sort_combo = ttk.Combobox(sort_frame, 
                                 textvariable=self.sort_var, 
                                 width=15,
                                 state="readonly")
        sort_combo['values'] = ('Название', 'Статус', 'Время игры', 'Платформа', 'Дата добавления')
        sort_combo.pack(side=tk.LEFT)
        sort_combo.bind('<<ComboboxSelected>>', self.on_sort_changed)
        
        self.sort_order_btn = ttk.Button(sort_frame, 
                                        text="↑", 
                                        width=3,
                                        command=self.toggle_sort_order)
        self.sort_order_btn.pack(side=tk.LEFT, padx=(5, 0))
        
        # Таблица игр с иконками
        columns = ('Иконка', 'ID', 'Название', 'Платформа', 'Статус', 'Время игры', 'Дата добавления', 'Секунды')
        self.tree = ttk.Treeview(self.library_frame, 
                                columns=columns, 
                                show='headings',
                                height=20,
                                selectmode='browse')
        
        # Настройка колонок
        column_configs = {
            'Иконка': {'width': 50, 'anchor': 'center'},
            'ID': {'width': 50, 'anchor': 'center'},
            'Название': {'width': 200},
            'Платформа': {'width': 100},
            'Статус': {'width': 100},
            'Время игры': {'width': 100, 'anchor': 'center'},
            'Дата добавления': {'width': 120, 'anchor': 'center'},
            'Секунды': {'width': 0, 'stretch': False, 'minwidth': 0}  # Скрытая колонка
        }
        
        for col in columns:
            self.tree.heading(col, text=col, command=lambda c=col: self.sort_by_column(c))
            self.tree.column(col, **column_configs.get(col, {'width': 100}))
        
        self.tree.grid(row=3, column=0, columnspan=4, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(self.library_frame, 
                                 orient=tk.VERTICAL, 
                                 command=self.tree.yview)
        scrollbar.grid(row=3, column=4, sticky=(tk.N, tk.S))
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Панель действий
        action_frame = ttk.Frame(self.library_frame)
        action_frame.grid(row=4, column=0, columnspan=5, pady=(10, 0))
        
        buttons = [
            ("Запустить", self.launch_selected_game),
            ("Редактировать", self.edit_selected_game),
            ("Удалить", self.delete_selected_game),
            ("Статистика", self.show_stats),
            ("Закладки", self.manage_bookmarks),
            ("Обновить", self.load_games),
        ]
        
        for text, command in buttons:
            ttk.Button(action_frame, text=text, command=command).pack(side=tk.LEFT, padx=2)
        
        # Привязка событий
        self.tree.bind('<Double-1>', self.on_double_click)
        
        # Инициализация вкладки закладок
        self.init_bookmarks_tab()
    
    def load_games(self):
        """Загрузка игр в таблицу с АВТОМАТИЧЕСКИМИ иконками"""
        # Очистка таблицы
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        games = self.db.get_all_games()
        
        # Сортировка данных перед отображением
        sorted_games = self.sort_games(games)
        
        for game in sorted_games:
            game_id = game[0]
            name = game[1]
            platform = game[2]
            exe_path = game[3]
            status = game[4]
            total_time = game[7]
            date_added = game[8]
            
            play_time = self.format_play_time(total_time)
            
            # Получаем иконку АВТОМАТИЧЕСКИ
            icon = self.get_game_icon(exe_path)
            
            # Вставляем игру в таблицу
            if icon:
                # С иконкой
                self.tree.insert('', tk.END, 
                               image=icon,
                               values=('', game_id, name, platform, status, play_time, date_added, total_time))
            else:
                # Без иконки
                self.tree.insert('', tk.END,
                               values=('', game_id, name, platform, status, play_time, date_added, total_time))
    
    def sort_games(self, games):
        """Сортировка списка игр"""
        if self.sort_column == 'name':
            return sorted(games, key=lambda x: x[1].lower(), reverse=self.sort_reverse)
        elif self.sort_column == 'platform':
            return sorted(games, key=lambda x: (x[2] or '').lower(), reverse=self.sort_reverse)
        elif self.sort_column == 'status':
            # Порядок статусов для сортировки
            status_order = {'Не пройдена': 0, 'В процессе': 1, 'Пройдена': 2, 'Отложена': 3}
            return sorted(games, key=lambda x: status_order.get(x[4], 4), reverse=self.sort_reverse)
        elif self.sort_column == 'play_time':
            return sorted(games, key=lambda x: x[7] or 0, reverse=self.sort_reverse)
        elif self.sort_column == 'date_added':
            return sorted(games, key=lambda x: x[8] or '', reverse=self.sort_reverse)
        else:
            return games
    
    def sort_by_column(self, column):
        """Сортировка по выбранной колонке"""
        column_map = {
            'Название': 'name',
            'Платформа': 'platform',
            'Статус': 'status',
            'Время игры': 'play_time',
            'Дата добавления': 'date_added'
        }
        
        if column in column_map:
            if self.sort_column == column_map[column]:
                self.sort_reverse = not self.sort_reverse
            else:
                self.sort_column = column_map[column]
                self.sort_reverse = False
            
            self.update_sort_indicator()
            self.load_games()
    
    def on_sort_changed(self, event=None):
        """Обработчик изменения сортировки через комбобокс"""
        sort_map = {
            'Название': 'name',
            'Платформа': 'platform',
            'Статус': 'status',
            'Время игры': 'play_time',
            'Дата добавления': 'date_added'
        }
        
        selected = self.sort_var.get()
        if selected in sort_map:
            self.sort_column = sort_map[selected]
            self.update_sort_indicator()
            self.load_games()
    
    def toggle_sort_order(self):
        """Переключение порядка сортировки"""
        self.sort_reverse = not self.sort_reverse
        self.update_sort_indicator()
        self.load_games()
    
    def update_sort_indicator(self):
        """Обновление индикатора порядка сортировки"""
        self.sort_order_btn.config(text="↓" if self.sort_reverse else "↑")
        
        # Обновление выбранного значения в комбобоксе
        reverse_map = {
            'name': 'Название',
            'platform': 'Платформа',
            'status': 'Статус',
            'play_time': 'Время игры',
            'date_added': 'Дата добавления'
        }
        if self.sort_column in reverse_map:
            self.sort_var.set(reverse_map[self.sort_column])
    
    def format_play_time(self, seconds):
        """Форматирование времени игры"""
        if not seconds:
            return "0м"
        
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        
        if hours > 0:
            return f"{hours}ч {minutes}м"
        else:
            return f"{minutes}м"
    
    def on_search(self, event):
        """Поиск игр"""
        query = self.search_var.get().lower()
        
        for item in self.tree.get_children():
            values = self.tree.item(item)['values']
            game_name = values[2].lower() if len(values) > 2 else ''
            if query in game_name:
                self.tree.selection_set(item)
                self.tree.see(item)
            else:
                self.tree.selection_remove(item)
    
    def show_add_game_dialog(self):
        """Диалог добавления игры"""
        AddGameDialog(self.root, self.db, self)
    
    def edit_selected_game(self):
        """Редактирование выбранной игры"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Внимание", "Выберите игру для редактирования")
            return
        
        item = selection[0]
        values = self.tree.item(item)['values']
        game_id = values[1]  # ID находится во второй колонке
        
        EditGameDialog(self.root, self.db, self, game_id)
    
    def delete_selected_game(self):
        """Удаление выбранной игры"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Внимание", "Выберите игру для удаления")
            return
        
        if messagebox.askyesno("Подтверждение", "Удалить выбранную игру?"):
            item = selection[0]
            values = self.tree.item(item)['values']
            game_id = values[1]
            self.db.delete_game(game_id)
            self.load_games()
    
    def launch_selected_game(self):
        """Запуск выбранной игры"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Внимание", "Выберите игру для запуска")
            return
        
        item = selection[0]
        values = self.tree.item(item)['values']
        game_id = values[1]
        
        games = self.db.get_all_games()
        game_info = next((game for game in games if game[0] == game_id), None)
        
        if game_info and os.path.exists(game_info[3]):
            success = self.launcher.launch_game(game_id, game_info[3])
            if success:
                messagebox.showinfo("Успех", f"Игра '{game_info[1]}' запускается!")
                self.update_active_sessions()
            else:
                messagebox.showerror("Ошибка", "Не удалось запустить игру")
        else:
            messagebox.showerror("Ошибка", "Файл игры не найден")
    
    def on_double_click(self, event):
        """Обработка двойного клика - запуск игры"""
        self.launch_selected_game()
    
    def show_stats(self):
        """Показать статистику выбранной игры"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Внимание", "Выберите игру для просмотра статистики")
            return
        
        item = selection[0]
        values = self.tree.item(item)['values']
        game_id = values[1]
        
        stats = self.db.get_play_stats(game_id)
        
        messagebox.showinfo(
            "Статистика игры",
            f"Общее время игры: {self.format_play_time(stats['total_play_time'])}\n"
            f"Количество сессий: {stats['session_count']}\n"
            f"Средняя продолжительность сессии: {self.format_play_time(stats['average_session'])}"
        )
    
    def update_active_sessions(self):
        """Обновление информации об активных сессиях"""
        active_sessions = self.launcher.get_active_sessions()
        if active_sessions:
            session_text = f"Активных сессий: {len(active_sessions)}"
            self.sessions_label.config(text=session_text)
        else:
            self.sessions_label.config(text="Нет активных сессий")
        
        self.root.after(10000, self.update_active_sessions)
    
    def on_game_end(self, game_id, duration):
        """Callback при завершении игры"""
        self.last_played_game_id = game_id
        
        games = self.db.get_all_games()
        game_name = next((game[1] for game in games if game[0] == game_id), "Неизвестная игра")
        
        result = messagebox.askyesno(
            "Игра завершена", 
            f"Игра '{game_name}' завершена.\nВремя игры: {self.format_play_time(duration)}\n\nХотите посмотреть закладки для этой игры?"
        )
        
        if result:
            self.show_bookmarks_for_game(game_id)
    
    def init_bookmarks_tab(self):
        """Инициализация вкладки закладок"""
        for widget in self.bookmarks_frame.winfo_children():
            widget.destroy()
        
        title_label = ttk.Label(self.bookmarks_frame, 
                               text="Закладки для игры", 
                               font=('Arial', 14, 'bold'))
        title_label.pack(pady=(0, 10))
        
        self.game_info_frame = ttk.Frame(self.bookmarks_frame)
        self.game_info_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.game_title_label = ttk.Label(self.game_info_frame, 
                                         text="Выберите игру", 
                                         font=('Arial', 12))
        self.game_title_label.pack()
        
        bookmark_buttons_frame = ttk.Frame(self.bookmarks_frame)
        bookmark_buttons_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(bookmark_buttons_frame, 
                  text="Добавить закладку", 
                  command=self.add_bookmark).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(bookmark_buttons_frame, 
                  text="Назад к библиотеке", 
                  command=self.show_library).pack(side=tk.LEFT)
        
        columns = ('ID', 'Название', 'URL', 'Категория', 'Описание')
        self.bookmarks_tree = ttk.Treeview(self.bookmarks_frame, 
                                          columns=columns, 
                                          show='headings',
                                          height=15)
        
        for col in columns:
            self.bookmarks_tree.heading(col, text=col)
        
        self.bookmarks_tree.column('ID', width=50)
        self.bookmarks_tree.column('Название', width=150)
        self.bookmarks_tree.column('URL', width=200)
        self.bookmarks_tree.column('Категория', width=100)
        self.bookmarks_tree.column('Описание', width=250)
        
        self.bookmarks_tree.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(self.bookmarks_frame, 
                                 orient=tk.VERTICAL, 
                                 command=self.bookmarks_tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.bookmarks_tree.configure(yscrollcommand=scrollbar.set)
        
        bookmark_action_frame = ttk.Frame(self.bookmarks_frame)
        bookmark_action_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(bookmark_action_frame, 
                  text="Открыть в браузере", 
                  command=self.open_bookmark).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(bookmark_action_frame, 
                  text="Редактировать", 
                  command=self.edit_bookmark).pack(side=tk.LEFT, padx=5)
        ttk.Button(bookmark_action_frame, 
                  text="Удалить", 
                  command=self.delete_bookmark).pack(side=tk.LEFT, padx=5)
        ttk.Button(bookmark_action_frame, 
                  text="Копировать URL", 
                  command=self.copy_bookmark_url).pack(side=tk.LEFT, padx=5)
        
        self.bookmarks_tree.bind('<Double-1>', lambda e: self.open_bookmark())
    
    def show_bookmarks_for_game(self, game_id):
        """Показать закладки для указанной игры"""
        self.last_played_game_id = game_id
        
        games = self.db.get_all_games()
        game_info = next((game for game in games if game[0] == game_id), None)
        
        if game_info:
            self.game_title_label.config(text=f"Закладки для: {game_info[1]}")
            self.load_bookmarks(game_id)
            self.notebook.tab(1, state="normal")
            self.notebook.select(1)
    
    def load_bookmarks(self, game_id):
        """Загрузка закладок в таблицу"""
        for item in self.bookmarks_tree.get_children():
            self.bookmarks_tree.delete(item)
        
        bookmarks = self.db.get_bookmarks_by_game(game_id)
        for bookmark in bookmarks:
            self.bookmarks_tree.insert('', tk.END, values=(
                bookmark[0], bookmark[2], bookmark[3], bookmark[5], bookmark[4]
            ))
    
    def manage_bookmarks(self):
        """Управление закладками для выбранной игры"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Внимание", "Выберите игру для управления закладками")
            return
        
        item = selection[0]
        values = self.tree.item(item)['values']
        game_id = values[1]
        self.show_bookmarks_for_game(game_id)
    
    def show_library(self):
        """Вернуться к вкладке библиотеки"""
        self.notebook.select(0)
    
    def add_bookmark(self):
        """Добавление новой закладки"""
        if not self.last_played_game_id:
            messagebox.showwarning("Внимание", "Сначала выберите игру")
            return
        
        AddBookmarkDialog(self.root, self.db, self, self.last_played_game_id)
    
    def open_bookmark(self):
        """Открытие закладки в браузере"""
        selection = self.bookmarks_tree.selection()
        if not selection:
            messagebox.showwarning("Внимание", "Выберите закладку")
            return
        
        item = selection[0]
        url = self.bookmarks_tree.item(item)['values'][2]
        
        try:
            webbrowser.open(url)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось открыть URL: {e}")
    
    def edit_bookmark(self):
        """Редактирование закладки"""
        selection = self.bookmarks_tree.selection()
        if not selection:
            messagebox.showwarning("Внимание", "Выберите закладку для редактирования")
            return
        
        item = selection[0]
        bookmark_id = self.bookmarks_tree.item(item)['values'][0]
        EditBookmarkDialog(self.root, self.db, self, bookmark_id)
    
    def delete_bookmark(self):
        """Удаление закладки"""
        selection = self.bookmarks_tree.selection()
        if not selection:
            messagebox.showwarning("Внимание", "Выберите закладку для удаления")
            return
        
        if messagebox.askyesno("Подтверждение", "Удалить выбранную закладку?"):
            item = selection[0]
            bookmark_id = self.bookmarks_tree.item(item)['values'][0]
            self.db.delete_bookmark(bookmark_id)
            self.load_bookmarks(self.last_played_game_id)
    
    def copy_bookmark_url(self):
        """Копирование URL закладки в буфер обмена"""
        selection = self.bookmarks_tree.selection()
        if not selection:
            messagebox.showwarning("Внимание", "Выберите закладку")
            return
        
        item = selection[0]
        url = self.bookmarks_tree.item(item)['values'][2]
        
        try:
            pyperclip.copy(url)
            messagebox.showinfo("Успех", "URL скопирован в буфер обмена")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось скопировать URL: {e}")

class AddGameDialog:
    def __init__(self, parent, db, callback):
        self.db = db
        self.callback = callback
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Добавить игру")
        self.dialog.geometry("500x400")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self.create_widgets()
    
    def create_widgets(self):
        main_frame = ttk.Frame(self.dialog, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Название
        ttk.Label(main_frame, text="Название игры:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.name_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.name_var, width=40).grid(row=0, column=1, pady=5, sticky=(tk.W, tk.E))
        
        # Платформа
        ttk.Label(main_frame, text="Платформа:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.platform_var = tk.StringVar()
        platform_combo = ttk.Combobox(main_frame, textvariable=self.platform_var, width=37)
        platform_combo['values'] = ('Steam', 'Epic Games', 'GOG', 'Battle.net', 'Ubisoft Connect', 'Другая')
        platform_combo.grid(row=1, column=1, pady=5, sticky=(tk.W, tk.E))
        
        # Исполняемый файл
        ttk.Label(main_frame, text="EXE файл:").grid(row=2, column=0, sticky=tk.W, pady=5)
        file_frame = ttk.Frame(main_frame)
        file_frame.grid(row=2, column=1, pady=5, sticky=(tk.W, tk.E))
        
        self.exe_path_var = tk.StringVar()
        ttk.Entry(file_frame, textvariable=self.exe_path_var, width=30).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(file_frame, text="Обзор", command=self.browse_exe).pack(side=tk.RIGHT, padx=(5, 0))
        
        # Статус
        ttk.Label(main_frame, text="Статус:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.status_var = tk.StringVar(value="Не пройдена")
        status_combo = ttk.Combobox(main_frame, textvariable=self.status_var, width=37)
        status_combo['values'] = ('Не пройдена', 'В процессе', 'Пройдена', 'Отложена')
        status_combo.grid(row=3, column=1, pady=5, sticky=(tk.W, tk.E))
        
        # Ключ активации
        ttk.Label(main_frame, text="Ключ активации:").grid(row=4, column=0, sticky=tk.W, pady=5)
        key_frame = ttk.Frame(main_frame)
        key_frame.grid(row=4, column=1, pady=5, sticky=(tk.W, tk.E))
        
        self.key_var = tk.StringVar()
        ttk.Entry(key_frame, textvariable=self.key_var, width=30, show="*").pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(key_frame, text="Показать", command=self.toggle_key_visibility).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(key_frame, text="Копировать", command=self.copy_key).pack(side=tk.RIGHT, padx=(5, 0))
        
        # Заметки
        ttk.Label(main_frame, text="Заметки:").grid(row=5, column=0, sticky=tk.W, pady=5)
        self.notes_text = tk.Text(main_frame, width=40, height=8)
        self.notes_text.grid(row=5, column=1, pady=5, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Кнопки
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=6, column=0, columnspan=2, pady=10)
        
        ttk.Button(button_frame, text="Добавить", command=self.add_game).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Отмена", command=self.dialog.destroy).pack(side=tk.LEFT)
        
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(5, weight=1)
    
    def browse_exe(self):
        filename = filedialog.askopenfilename(
            title="Выберите исполняемый файл игры",
            filetypes=[("Executable files", "*.exe"), ("All files", "*.*")]
        )
        if filename:
            self.exe_path_var.set(filename)
            if not self.name_var.get():
                game_name = Path(filename).stem
                self.name_var.set(game_name)
    
    def toggle_key_visibility(self):
        current_show = self.key_var.get()
        # Здесь должна быть логика переключения видимости
        pass
    
    def copy_key(self):
        key = self.key_var.get()
        if key:
            pyperclip.copy(key)
            messagebox.showinfo("Успех", "Ключ скопирован в буфер обмена")
    
    def add_game(self):
        name = self.name_var.get().strip()
        exe_path = self.exe_path_var.get().strip()
        
        if not name:
            messagebox.showerror("Ошибка", "Введите название игры")
            return
        
        if not exe_path:
            messagebox.showerror("Ошибка", "Укажите путь к исполняемому файлу")
            return
        
        if not os.path.exists(exe_path):
            messagebox.showerror("Ошибка", "Указанный файл не существует")
            return
        
        try:
            self.db.add_game(
                name=name,
                platform=self.platform_var.get(),
                executable_path=exe_path,
                status=self.status_var.get(),
                activation_key=self.key_var.get(),
                notes=self.notes_text.get("1.0", tk.END).strip()
            )
            
            messagebox.showinfo("Успех", "Игра добавлена в библиотеку")
            self.dialog.destroy()
            self.callback.load_games()
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось добавить игру: {e}")

class EditGameDialog(AddGameDialog):
    def __init__(self, parent, db, callback, game_id):
        self.game_id = game_id
        self.db = db
        self.callback = callback
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Редактировать игру")
        self.dialog.geometry("500x400")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self.create_widgets()
        self.load_game_data()
    
    def load_game_data(self):
        games = self.db.get_all_games()
        game_info = next((game for game in games if game[0] == self.game_id), None)
        
        if game_info:
            self.name_var.set(game_info[1])
            self.platform_var.set(game_info[2] or "")
            self.exe_path_var.set(game_info[3])
            self.status_var.set(game_info[4] or "Не пройдена")
            self.key_var.set(game_info[5] or "")
            self.notes_text.delete("1.0", tk.END)
            self.notes_text.insert("1.0", game_info[6] or "")
    
    def add_game(self):
        name = self.name_var.get().strip()
        exe_path = self.exe_path_var.get().strip()
        
        if not name:
            messagebox.showerror("Ошибка", "Введите название игры")
            return
        
        if not exe_path:
            messagebox.showerror("Ошибка", "Укажите путь к исполняемому файлу")
            return
        
        if not os.path.exists(exe_path):
            messagebox.showerror("Ошибка", "Указанный файл не существует")
            return
        
        try:
            self.db.update_game(
                game_id=self.game_id,
                name=name,
                platform=self.platform_var.get(),
                executable_path=exe_path,
                status=self.status_var.get(),
                activation_key=self.key_var.get(),
                notes=self.notes_text.get("1.0", tk.END).strip()
            )
            
            messagebox.showinfo("Успех", "Информация об игре обновлена")
            self.dialog.destroy()
            self.callback.load_games()
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось обновить игру: {e}")

class AddBookmarkDialog:
    def __init__(self, parent, db, callback, game_id):
        self.db = db
        self.callback = callback
        self.game_id = game_id
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Добавить закладку")
        self.dialog.geometry("500x300")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self.create_widgets()
    
    def create_widgets(self):
        main_frame = ttk.Frame(self.dialog, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(main_frame, text="Название:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.title_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.title_var, width=40).grid(row=0, column=1, pady=5, sticky=(tk.W, tk.E))
        
        ttk.Label(main_frame, text="URL:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.url_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.url_var, width=40).grid(row=1, column=1, pady=5, sticky=(tk.W, tk.E))
        
        ttk.Label(main_frame, text="Категория:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.category_var = tk.StringVar(value="Общее")
        category_combo = ttk.Combobox(main_frame, textvariable=self.category_var, width=37)
        category_combo['values'] = ('Общее', 'Гайды', 'Форумы', 'Вики', 'Моды', 'Видео', 'Сообщество')
        category_combo.grid(row=2, column=1, pady=5, sticky=(tk.W, tk.E))
        
        ttk.Label(main_frame, text="Описание:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.description_text = tk.Text(main_frame, width=40, height=6)
        self.description_text.grid(row=3, column=1, pady=5, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=4, column=0, columnspan=2, pady=10)
        
        ttk.Button(button_frame, text="Добавить", command=self.add_bookmark).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Отмена", command=self.dialog.destroy).pack(side=tk.LEFT)
        
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(3, weight=1)
    
    def add_bookmark(self):
        title = self.title_var.get().strip()
        url = self.url_var.get().strip()
        
        if not title:
            messagebox.showerror("Ошибка", "Введите название закладки")
            return
        
        if not url:
            messagebox.showerror("Ошибка", "Введите URL")
            return
        
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        try:
            self.db.add_bookmark(
                game_id=self.game_id,
                title=title,
                url=url,
                description=self.description_text.get("1.0", tk.END).strip(),
                category=self.category_var.get()
            )
            
            messagebox.showinfo("Успех", "Закладка добавлена")
            self.dialog.destroy()
            self.callback.load_bookmarks(self.game_id)
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось добавить закладку: {e}")

class EditBookmarkDialog(AddBookmarkDialog):
    def __init__(self, parent, db, callback, bookmark_id):
        self.bookmark_id = bookmark_id
        self.db = db
        self.callback = callback
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Редактировать закладку")
        self.dialog.geometry("500x300")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self.create_widgets()
        self.load_bookmark_data()
    
    def load_bookmark_data(self):
        bookmark = self.db.get_bookmark_by_id(self.bookmark_id)
        
        if bookmark:
            self.title_var.set(bookmark[2])
            self.url_var.set(bookmark[3])
            self.category_var.set(bookmark[5] or "Общее")
            self.description_text.delete("1.0", tk.END)
            self.description_text.insert("1.0", bookmark[4] or "")
    
    def add_bookmark(self):
        title = self.title_var.get().strip()
        url = self.url_var.get().strip()
        
        if not title:
            messagebox.showerror("Ошибка", "Введите название закладки")
            return
        
        if not url:
            messagebox.showerror("Ошибка", "Введите URL")
            return
        
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        try:
            self.db.update_bookmark(
                bookmark_id=self.bookmark_id,
                title=title,
                url=url,
                description=self.description_text.get("1.0", tk.END).strip(),
                category=self.category_var.get()
            )
            
            messagebox.showinfo("Успех", "Закладка обновлена")
            self.dialog.destroy()
            self.callback.load_bookmarks(self.callback.last_played_game_id)
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось обновить закладку: {e}")