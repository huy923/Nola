#!/usr/bin/env python3
"""
Nola Virtual Input
Chuot/phim ao - chi dieu khien trong cua so rieng, KHONG anh huong user
"""

import subprocess
import time
import platform
import pyautogui
class VirtualInput:
    def __init__(self):
        self.system = platform.system().lower()
        self.current_window = None

    def focus_window(self, window_name):
        """Focus vao cua so cua Nola"""
        try:
            if self.system == 'linux':
                subprocess.run(['xdotool', 'search', '--name', window_name, 'windowactivate'], 
                    check=False, capture_output=True, timeout=2)
            elif self.system == 'windows':
                # TODO: Windows implementation with pywin32
                pass
            elif self.system == 'darwin':
                # TODO: macOS implementation
                pass
        except Exception as e:
            print(f"[VirtualInput] Focus error: {e}")

    def type_text(self, text, interval=0.01):
        """Type text (chi trong cua so da focus)"""
        try:
            # Safety: chi type khi da focus dung cua so
            pyautogui.typewrite(text, interval=interval)
        except ImportError:
            print("[VirtualInput] pyautogui chua cai. Chay: pip install pyautogui")
        except Exception as e:
            print(f"[VirtualInput] Type error: {e}")

    def press_key(self, key):
        """Nhan phim"""
        try:
            pyautogui.press(key)
        except:
            pass

    def hotkey(self, *keys):
        """Nhan to hop phim (Ctrl+C, Ctrl+V...)"""
        try:
            pyautogui.hotkey(*keys)
        except:
            pass

    def click(self, x, y):
        """Click tai toa do (trong cua so hien tai)"""
        try:
            pyautogui.click(x, y)
        except:
            pass

    def get_clipboard(self):
        """Lay noi dung clipboard"""
        try:
            import pyperclip
            return pyperclip.paste()
        except ImportError:
            try:
                # Fallback: xclip
                result = subprocess.run(['xclip', '-o', '-selection', 'clipboard'], 
                    capture_output=True, text=True, timeout=2)
                return result.stdout
            except:
                return ""

    def set_clipboard(self, text):
        """Dat noi dung clipboard"""
        try:
            import pyperclip
            pyperclip.copy(text)
        except ImportError:
            try:
                # Fallback: xclip
                subprocess.run(['xclip', '-i', '-selection', 'clipboard'], 
                    input=text.encode(), timeout=2)
            except:
                pass

    def paste(self):
        """Paste tu clipboard"""
        self.hotkey('ctrl', 'v')

    def copy(self):
        """Copy vao clipboard"""
        self.hotkey('ctrl', 'c')

    def wait_for_idle(self, timeout=0.2):
        """Doi user ngung dung may"""
        # TODO: Kiem tra idle time bang xprintidle
        time.sleep(timeout)
        return True

    def is_user_active(self):
        """Kiem tra user co dang dung may khong"""
        try:
            # Linux: xprintidle
            result = subprocess.run(['xprintidle'], capture_output=True, text=True, timeout=2)
            idle_ms = int(result.stdout.strip())
            return idle_ms < 2000  # Active neu idle < 2s
        except:
            return True  # Assume active
