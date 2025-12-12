import tkinter as tk
from gui_main import GameLibraryManager

def main():
    root = tk.Tk()
    root.title("Game Library Manager")
    root.geometry("1300x850")
    
    # Центрирование окна
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f'{width}x{height}+{x}+{y}')
    
    app = GameLibraryManager(root)
    root.mainloop()

if __name__ == "__main__":
    main()