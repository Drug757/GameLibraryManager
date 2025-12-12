import tkinter as tk
from tkinter import ttk

class ThemeManager:
    """Менеджер тем оформления"""
    
    DARK_THEME = {
        'bg': '#2b2b2b',
        'fg': '#ffffff',
        'select_bg': '#404040',
        'select_fg': '#ffffff',
        'entry_bg': '#3c3f41',
        'entry_fg': '#ffffff',
        'button_bg': '#3c3f41',
        'button_fg': '#ffffff',
        'tree_bg': '#3c3f41',
        'tree_fg': '#ffffff',
        'tree_heading_bg': '#2b2b2b',
        'tree_heading_fg': '#ffffff',
        'frame_bg': '#2b2b2b',
        'label_bg': '#2b2b2b',
        'label_fg': '#ffffff',
        'accent': '#4a9cff',
        'success': '#4CAF50',
        'warning': '#FF9800',
        'error': '#F44336'
    }
    
    @classmethod
    def apply_dark_theme(cls, root):
        """Применение темной темы ко всему приложению"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Настройка цветов
        style.configure('.',
                       background=cls.DARK_THEME['bg'],
                       foreground=cls.DARK_THEME['fg'])
        
        # Treeview
        style.configure('Treeview',
                       background=cls.DARK_THEME['tree_bg'],
                       foreground=cls.DARK_THEME['tree_fg'],
                       fieldbackground=cls.DARK_THEME['tree_bg'],
                       rowheight=40)  # Увеличиваем высоту строк для иконок
        
        style.configure('Treeview.Heading',
                       background=cls.DARK_THEME['tree_heading_bg'],
                       foreground=cls.DARK_THEME['tree_heading_fg'])
        
        style.map('Treeview',
                 background=[('selected', cls.DARK_THEME['select_bg'])],
                 foreground=[('selected', cls.DARK_THEME['select_fg'])])
        
        # Button
        style.configure('TButton',
                       background=cls.DARK_THEME['button_bg'],
                       foreground=cls.DARK_THEME['button_fg'])
        
        style.map('TButton',
                 background=[('active', cls.DARK_THEME['accent'])])
        
        # Entry
        style.configure('TEntry',
                       fieldbackground=cls.DARK_THEME['entry_bg'],
                       foreground=cls.DARK_THEME['entry_fg'])
        
        # Label
        style.configure('TLabel',
                       background=cls.DARK_THEME['label_bg'],
                       foreground=cls.DARK_THEME['label_fg'])
        
        # Frame
        style.configure('TFrame',
                       background=cls.DARK_THEME['frame_bg'])
        
        # Notebook
        style.configure('TNotebook',
                       background=cls.DARK_THEME['bg'])
        
        style.configure('TNotebook.Tab',
                       background=cls.DARK_THEME['button_bg'],
                       foreground=cls.DARK_THEME['button_fg'])
        
        style.map('TNotebook.Tab',
                 background=[('selected', cls.DARK_THEME['accent'])])