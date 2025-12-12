from PIL import Image, ImageTk
import os
import tempfile

class IconManager:
    
    @staticmethod
    def get_icon_image(exe_path, size=(32, 32)):
        try:
            if not os.path.exists(exe_path):
                return None
            
            try:
                import win32ui
                import win32gui
                import win32con
                import win32api
                
                # Извлекаем иконку из EXE файла
                large_icons, small_icons = win32gui.ExtractIconEx(exe_path, 0)
                if len(large_icons) == 0:
                    return None
                
                # Используем первую иконку
                icon_handle = large_icons[0]
                
                # Создаем DC и bitmap
                hdc = win32ui.CreateDCFromHandle(win32gui.GetDC(0))
                hbmp = win32ui.CreateBitmap()
                hbmp.CreateCompatibleBitmap(hdc, size[0], size[1])
                hdc = hdc.CreateCompatibleDC()
                hdc.SelectObject(hbmp)
                
                # Заливаем фон прозрачным
                hdc.FillSolidRect((0, 0, size[0], size[1]), win32api.RGB(255, 255, 255))
                
                # Рисуем иконку
                win32gui.DrawIconEx(
                    hdc.GetHandleOutput(),
                    0, 0,
                    icon_handle,
                    size[0], size[1],
                    0, None, win32con.DI_NORMAL
                )
                
                # Конвертируем в PIL Image
                bmpinfo = hbmp.GetInfo()
                bmpstr = hbmp.GetBitmapBits(True)
                img = Image.frombuffer(
                    'RGB',
                    (bmpinfo['bmWidth'], bmpinfo['bmHeight']),
                    bmpstr, 'raw', 'BGRX', 0, 1
                )
                
                # Уничтожаем иконки
                for icon in large_icons:
                    win32gui.DestroyIcon(icon)
                for icon in small_icons:
                    win32gui.DestroyIcon(icon)
                
                # Конвертируем в формат для tkinter
                return ImageTk.PhotoImage(img)
                
            except ImportError:
                # Если pywin32 не установлен, создаем простую иконку
                img = Image.new('RGBA', size, (70, 130, 180, 255))
                return ImageTk.PhotoImage(img)
                
        except Exception as e:
            print(f"Ошибка при загрузке иконки {exe_path}: {e}")
            return None
    
    @staticmethod
    def create_default_icon(size=(32, 32)):
        """Создание иконки по умолчанию"""
        img = Image.new('RGBA', size, (70, 130, 180, 255))
        return ImageTk.PhotoImage(img)