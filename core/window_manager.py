#!/usr/bin/env python3
"""
Nola Window Manager
Mo cua so rieng cho Nola, khong anh huong cua so cua user
"""

import subprocess
import os
import signal

class WindowManager:
    def __init__(self):
        self.nola_windows = []
        self.chrome_profile = '/tmp/nola-chrome-profile'
        os.makedirs(self.chrome_profile, exist_ok=True)

    def open_browser(self, url, name='Nola-Browser'):
        """Mo Chrome cho Nola dung - profile rieng"""
        chrome_cmds = [
            ['google-chrome', f'--user-data-dir={self.chrome_profile}', '--new-window', 
             '--window-size=1200,800', '--window-position=50,50', '--no-first-run', 
             '--no-default-browser-check', url],
            ['chromium', f'--user-data-dir={self.chrome_profile}', '--new-window', url],
            ['chromium-browser', f'--user-data-dir={self.chrome_profile}', '--new-window', url]
        ]

        for cmd in chrome_cmds:
            try:
                proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                self.nola_windows.append({'pid': proc.pid, 'type': 'browser', 'url': url})
                print(f"[WindowManager] Mo Chrome: {url}")
                return proc
            except FileNotFoundError:
                continue

        print("[WindowManager] ⚠️ Chrome/Chromium khong tim thay. Cai dat: sudo apt install chromium-browser")
        return None

    def open_terminal(self, command, name='Nola-Terminal'):
        """Mo terminal cho Nola dung"""
        terminals = [
            ['gnome-terminal', '--geometry=120x30+50+50', '--title', name, '--', 'bash', '-c', f'{command}; read -n1'],
            ['konsole', '--geometry', '120x30+50+50', '--title', name, '-e', f'bash -c "{command}; read -n1"'],
            ['xterm', '-geometry', '120x30+50+50', '-title', name, '-e', f'bash -c "{command}; read -n1"']
        ]

        for cmd in terminals:
            try:
                proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                self.nola_windows.append({'pid': proc.pid, 'type': 'terminal', 'cmd': command})
                print(f"[WindowManager] Mo terminal")
                return proc
            except FileNotFoundError:
                continue

        print("[WindowManager] ⚠️ Terminal khong tim thay")
        return None

    def open_vscode(self, path):
        """Mo VS Code tai folder"""
        try:
            proc = subprocess.Popen(['code', path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self.nola_windows.append({'pid': proc.pid, 'type': 'vscode', 'path': path})
            print(f"[WindowManager] Mo VS Code: {path}")
            return proc
        except FileNotFoundError:
            print("[WindowManager] ⚠️ VS Code khong tim thay")
            return None

    def close_all(self):
        """Dong tat ca cua so cua Nola"""
        for win in self.nola_windows:
            try:
                os.kill(win['pid'], signal.SIGTERM)
            except ProcessLookupError:
                pass
            except Exception as e:
                print(f"[WindowManager] Loi dong cua so: {e}")
        self.nola_windows = []
        print("[WindowManager] Da dong tat ca cua so")

    def list_windows(self):
        """Liet ke cua so dang mo"""
        return self.nola_windows
