#!/usr/bin/env python3
"""
Nola UI Overlay - Desktop transparent window
Avatar hologram Fairy ZZZ style, speech bubble, chat panel
"""

import tkinter as tk
import math
import random
import time
import sys

class NolaOverlay(tk.Tk):
    def __init__(self, voice_pipeline=None, agent=None):
        
        super().__init__()

        self.voice = voice_pipeline
        self.agent = agent
        self.audio_level = 0.0

        if self.voice:
            self.voice.on_audio_level = self.set_audio_level
            self.voice.on_speech_start = self.on_voice_speech_start
            self.voice.on_speech_end = self.on_voice_speech_end
            self.voice.on_listening_change = self.on_voice_listening_change

        # === Cấu hình cửa sổ trong suốt ===
        self.title("Nola AI")
        self.geometry("200x200+100+100")
        self.overrideredirect(True)
        self.attributes('-topmost', True)
        if sys.platform == 'win32':
            self.attributes('-transparentcolor', '#000000')
        else:
            try:
                self.attributes('-alpha', 0.95)
            except:
                pass
        self.configure(bg='#000000')

        # === Canvas vẽ avatar ===
        self.canvas = tk.Canvas(self, width=200, height=200, 
                                bg='#000000', highlightthickness=0)
        self.canvas.pack()

        # === Trạng thái ===
        self.mood = 'idle'
        self.is_listening = False
        self.chat_visible = False
        self.speech_bubble = None
        self.vx, self.vy = 0, 0
        self.pulse_phase = 0
        self.trail_positions = []

        # === Bind events ===
        self.bind('<Double-Button-1>', self.toggle_chat)
        # self.bind('<Button-3>', self.show_context_menu)
        self.bind('<B1-Motion>', self.on_drag)
        self.bind('<Button-1>', self.on_click)

        # Hotkeys
        self.bind_all('<Control-space>', self.hotkey_mic)
        self.bind_all('<Control-Shift-N>', self.hotkey_focus)

        # === Bắt đầu animation ===
        self.animate()
        self.wander()

    def set_audio_level(self, level):
        self.audio_level = level * 0.5 + self.audio_level * 0.5

    def on_voice_speech_start(self):
        self.after(0, self._on_voice_speech_start)

    def _on_voice_speech_start(self):
        self.mood = 'listen'
        if self.voice and self.voice.is_listening:
            self.show_speech_bubble('🎤 Đang nghe...', duration=30000)

    def on_voice_listening_change(self, is_listening):
        self.after(0, lambda: self._on_voice_listening_change(is_listening))

    def _on_voice_listening_change(self, is_listening):
        self.is_listening = is_listening
        if hasattr(self, 'mic_btn'):
            self.mic_btn.config(bg='#22c55e' if is_listening else '#ef4444')

    def on_voice_speech_end(self):
        self.after(0, self._on_voice_speech_end)

    def _on_voice_speech_end(self):
        if self.mood != 'idle':
            self.mood = 'idle'
            if self.speech_bubble and self.speech_bubble.winfo_exists():
                try:
                    self.speech_bubble.destroy()
                except:
                    pass

    def draw_avatar(self):
        """Vẽ avatar hologram Fairy ZZZ style với animation đầy đủ"""
        self.canvas.delete('all')
        cx, cy = 100, 100

        # Pulse animation
        self.pulse_phase += 0.05
        pulse = 1 + 0.08 * math.sin(self.pulse_phase)

        # Outer glow (nhiều lớp với alpha khác nhau)
        glow_radii = [
            (int(95 * pulse), '#001133', 1),
            (int(80 * pulse), '#002255', 2),
            (int(65 * pulse), '#003377', 2),
        ]
        for r, color, width in glow_radii:
            self.canvas.create_oval(cx-r, cy-r, cx+r, cy+r, 
                fill='', outline=color, width=width, stipple='gray25')

        # Audio level ring (phản hồi mic real-time)
        if self.audio_level > 0.01:
            audio_r = int(55 + self.audio_level * 35)
            lw = max(1, int(self.audio_level * 4))
            self.canvas.create_oval(cx-audio_r, cy-audio_r, cx+audio_r, cy+audio_r,
                fill='', outline='#00ff88', width=lw, stipple='gray50')

        # Main body - vòng tròn chính
        body_r = int(50 * pulse)
        self.canvas.create_oval(cx-body_r, cy-body_r, cx+body_r, cy+body_r,
            fill='#001a33', outline='#00d4ff', width=2)

        # Inner rings (xoay chậm, offset)
        ring_rot = self.pulse_phase * 0.2
        for i, r in enumerate([40, 28, 15]):
            offset_x = math.sin(ring_rot + i * 2.1) * 4
            offset_y = math.cos(ring_rot + i * 1.7) * 3
            dash = (6, 4) if i % 2 == 0 else (3, 3)
            self.canvas.create_oval(
                cx-r+offset_x, cy-r+offset_y, cx+r+offset_x, cy+r+offset_y,
                fill='', outline='#00d4ff', width=1.5, dash=dash)

        # Core - nhấp nháy theo mood
        if self.mood == 'listen':
            core_color = '#ff4444'
            core_r = 14 + int(3 * math.sin(self.pulse_phase * 3))
        elif self.mood == 'think':
            core_color = '#ffaa00'
            core_r = 12
        elif self.mood == 'speak':
            core_color = '#00ff88'
            core_r = 12 + int(2 * math.sin(self.pulse_phase * 4))
        else:
            core_color = '#ffffff'
            core_r = 10

        self.canvas.create_oval(cx-core_r, cy-core_r, cx+core_r, cy+core_r,
            fill=core_color, outline='#00d4ff', width=2)

        # Scan lines (di chuyển)
        scan_offset = (self.pulse_phase * 15) % 90
        for i in range(7):
            y = cy - 45 + ((i * 15 + scan_offset) % 90)
            if cy - 50 < y < cy + 50:
                self.canvas.create_line(cx-48, y, cx+48, y,
                    fill='#00d4ff', width=0.5, stipple='gray25')

        # Trail particles khi di chuyển
        speed = math.sqrt(self.vx**2 + self.vy**2)
        if speed > 0.5:
            self.trail_positions.append((cx, cy, speed))
            if len(self.trail_positions) > 8:
                self.trail_positions.pop(0)

        for i, (tx, ty, ts) in enumerate(self.trail_positions):
            alpha = (i / len(self.trail_positions)) * 0.5 if self.trail_positions else 0
            r = 4 + ts * 2
            self.canvas.create_oval(tx-r, ty-r, tx+r, ty+r,
                fill='#00d4ff', outline='', stipple='gray50')

        # Label Nola
        self.canvas.create_text(cx, cy+78, text='Nola', 
            fill='#00d4ff', font=('Segoe UI', 12, 'bold'))

        # Status indicator
        status_map = {
            'idle': '', 'listen': '●', 'think': '◐', 
            'speak': '◉', 'happy': '☺', 'angry': '◈', 'sleep': '○'
        }
        status_text = status_map.get(self.mood, '')
        if status_text:
            status_color = '#ff4444' if self.mood == 'listen' else '#00ff88' if self.mood == 'speak' else '#00d4ff'
            self.canvas.create_text(cx+65, cy-65, text=status_text,
                fill=status_color, font=('Arial', 18))

    def show_speech_bubble(self, text, duration=8000):
        """Hiện speech bubble khi Nola nói - đẹp, dễ đọc"""
        if self.speech_bubble and self.speech_bubble.winfo_exists():
            self.speech_bubble.destroy()

        bubble = tk.Toplevel(self)
        bubble.overrideredirect(True)
        bubble.attributes('-topmost', True)
        if sys.platform == 'win32':
            bubble.attributes('-transparentcolor', '#000000')
        else:
            try:
                bubble.attributes('-alpha', 0.95)
            except:
                pass
        bubble.configure(bg='#000000')

        # Vị trí: bên trái hoặc phải avatar (tùy vị trí màn hình)
        screen_w = self.winfo_screenwidth()
        bx = self.winfo_x() - 280 if self.winfo_x() > 300 else self.winfo_x() + 210
        by = self.winfo_y() + 10
        bubble.geometry(f"260x120+{bx}+{by}")

        # Frame nội dung với border
        frame = tk.Frame(bubble, bg='#0d1b2a', padx=12, pady=10,
            highlightbackground='#00d4ff', highlightthickness=1)
        frame.pack(fill='both', expand=True)

        # Header
        header = tk.Frame(frame, bg='#0d1b2a')
        header.pack(fill='x', pady=(0, 5))
        tk.Label(header, text='◉ Nola', bg='#0d1b2a', fg='#00ff88', 
            font=('Segoe UI', 10, 'bold')).pack(side='left')
        tk.Label(header, text=time.strftime('%H:%M'), bg='#0d1b2a', fg='#666', 
            font=('Segoe UI', 8)).pack(side='right')

        # Text
        label = tk.Label(frame, text=text, wraplength=230,
            bg='#0d1b2a', fg='white', font=('Segoe UI', 11),
            justify='left')
        label.pack(fill='both', expand=True)

        self.speech_bubble = bubble
        bubble.after(duration, lambda: bubble.destroy() if bubble.winfo_exists() else None)

    def toggle_chat(self, event=None):
        """Double-click -> hiện/ẩn panel chat"""
        if self.chat_visible:
            self.hide_chat()
        else:
            self.show_chat()

    def show_chat(self):
        """Hiện panel lịch sử chat - đẹp, đầy đủ"""
        if self.chat_visible:
            return

        self.chat_panel = tk.Toplevel(self)
        self.chat_panel.geometry("400x600+30+30")
        self.chat_panel.attributes('-topmost', True)
        self.chat_panel.configure(bg='#0a0a1a')
        self.chat_panel.overrideredirect(False)
        self.chat_panel.title('')

        # Header
        header = tk.Frame(self.chat_panel, bg='#001a33', height=50)
        header.pack(fill='x')
        header.pack_propagate(False)

        tk.Label(header, text='💬 Lịch sử chat', 
            bg='#001a33', fg='#00d4ff', font=('Segoe UI', 13, 'bold')).pack(side='left', padx=15, pady=10)

        tk.Button(header, text='✕', bg='#001a33', fg='#ff6b6b', 
            font=('Arial', 14), bd=0, command=self.hide_chat,
            activebackground='#001a33', activeforeground='#ff4444').pack(side='right', padx=15)

        # Chat area
        chat_frame = tk.Frame(self.chat_panel, bg='#0a0a1a')
        chat_frame.pack(fill='both', expand=True, padx=10, pady=5)

        scrollbar = tk.Scrollbar(chat_frame, bg='#0a0a1a', troughcolor='#0a0a1a')
        scrollbar.pack(side='right', fill='y')

        self.chat_text = tk.Text(chat_frame, wrap='word', 
            bg='#0a0a1a', fg='white', font=('Segoe UI', 10),
            padx=10, pady=10, state='disabled',
            yscrollcommand=scrollbar.set,
            selectbackground='#00d4ff', selectforeground='black',
            spacing1=2, spacing3=2)
        self.chat_text.pack(side='left', fill='both', expand=True)
        scrollbar.config(command=self.chat_text.yview)

        # Tags
        self.chat_text.tag_config('timestamp', foreground='#555', font=('Segoe UI', 8))
        self.chat_text.tag_config('nola_name', foreground='#00d4ff', font=('Segoe UI', 10, 'bold'))
        self.chat_text.tag_config('user_name', foreground='#3b82f6', font=('Segoe UI', 10, 'bold'))
        self.chat_text.tag_config('msg', foreground='#eee', font=('Segoe UI', 10))
        self.chat_text.tag_config('bubble_nola', background='#001a33', foreground='white')
        self.chat_text.tag_config('bubble_user', background='#0d1b2a', foreground='white')

        # Input area
        input_frame = tk.Frame(self.chat_panel, bg='#001a33', height=60)
        input_frame.pack(fill='x', side='bottom')
        input_frame.pack_propagate(False)

        self.mic_btn = tk.Button(input_frame, text='🎤', bg='#ef4444', fg='white',
            command=self.toggle_mic, font=('Arial', 16), bd=0, width=3,
            activebackground='#ff4444')
        self.mic_btn.pack(side='left', padx=10, pady=10)

        self.msg_entry = tk.Entry(input_frame, bg='#0d1b2a', fg='white',
            insertbackground='#00d4ff', font=('Segoe UI', 11),
            highlightbackground='#00d4ff', highlightthickness=1, bd=0)
        self.msg_entry.pack(side='left', fill='x', expand=True, padx=5, pady=10)
        self.msg_entry.bind('<Return>', self.send_message)

        send_btn = tk.Button(input_frame, text='➤', bg='#001a33', fg='#00d4ff',
            command=lambda: self.send_message(), font=('Arial', 16), bd=0,
            activebackground='#001a33', activeforeground='#00ff88')
        send_btn.pack(side='right', padx=10, pady=10)

        self.chat_visible = True
        self.msg_entry.focus_set()

        # Welcome message
        self.add_message('Nola', 'Chào chủ nhân! 👋 Mình là Nola, AI assistant của bạn.\nNói "Nola ơi" hoặc nhấn 🎤 để bắt đầu nhé~')

    def hide_chat(self):
        """Ẩn panel chat"""
        if hasattr(self, 'chat_panel') and self.chat_panel:
            try:
                self.chat_panel.destroy()
            except:
                pass
        self.chat_visible = False

    def add_message(self, sender, text):
        """Thêm tin nhắn vào chat với formatting đẹp"""
        if not hasattr(self, 'chat_text') or not self.chat_text:
            return

        self.chat_text.config(state='normal')

        timestamp = time.strftime('%H:%M')
        is_nola = sender == 'Nola'

        # Timestamp
        self.chat_text.insert('end', f'{timestamp} ', 'timestamp')

        # Sender name
        tag = 'nola_name' if is_nola else 'user_name'
        self.chat_text.insert('end', f'{sender}: ', tag)

        # Message
        self.chat_text.insert('end', f'{text}\n\n', 'msg')

        self.chat_text.config(state='disabled')
        self.chat_text.see('end')

    def toggle_mic(self, event=None):
        """Bật/tắt mic với UI feedback"""
        self.is_listening = not self.is_listening

        if self.is_listening:
            self.mood = 'listen'
            if hasattr(self, 'mic_btn'):
                self.mic_btn.config(bg='#22c55e')
            self.show_speech_bubble('🎤 Đang nghe... Nói đi chủ nhân!', duration=30000)
            if self.voice:
                self.voice.is_listening = True
        else:
            self.mood = 'idle'
            if hasattr(self, 'mic_btn'):
                self.mic_btn.config(bg='#ef4444')
            if self.speech_bubble:
                self.speech_bubble.destroy()
            if self.voice:
                self.voice.is_listening = False

    def hotkey_mic(self, event):
        self.toggle_mic()

    def hotkey_focus(self, event):
        self.focus_mode()

    def on_drag(self, event):
        """Kéo thả avatar mượt"""
        x = self.winfo_pointerx() - 100
        y = self.winfo_pointery() - 100
        self.geometry(f"+{x}+{y}")

    def on_click(self, event):
        """Click đơn"""
        pass

    def show_context_menu(self, event):
        """Right-click menu đẹp"""
        menu = tk.Menu(self, tearoff=0, bg='#0d1b2a', fg='white',
            activebackground='#00d4ff', activeforeground='black',
            font=('Segoe UI', 10))
        menu.add_command(label='🎤 Voice Chat', command=self.toggle_mic)
        menu.add_command(label='💬 Chat History', command=self.show_chat)
        menu.add_separator()
        menu.add_command(label='⚙️ Settings', command=self.open_settings)
        menu.add_command(label='🎯 Focus Mode', command=self.focus_mode)
        menu.add_separator()
        menu.add_command(label='😴 Sleep', command=self.sleep_mode)
        menu.add_command(label='❌ Exit', command=self.quit)
        menu.post(event.x_root, event.y_root)

    def animate(self):
        """Animation loop 20 FPS"""
        self.draw_avatar()
        self.after(50, self.animate)

    def wander(self):
        """Tự do di chuyển - tự nhiên"""
        if self.mood in ('idle', 'sleep') and not self.is_listening:
            # Random walk với inertia
            self.vx += random.uniform(-0.4, 0.4)
            self.vy += random.uniform(-0.4, 0.4)

            # Damping
            self.vx *= 0.95
            self.vy *= 0.95

            # Giới hạn
            self.vx = max(-2, min(2, self.vx))
            self.vy = max(-2, min(2, self.vy))

            screen_w = self.winfo_screenwidth()
            screen_h = self.winfo_screenheight()
            new_x = self.winfo_x() + int(self.vx)
            new_y = self.winfo_y() + int(self.vy)

            # Bounce ở biên
            margin = 20
            if new_x < margin:
                self.vx = abs(self.vx) + 0.5
            if new_x > screen_w - 220:
                self.vx = -abs(self.vx) - 0.5
            if new_y < margin:
                self.vy = abs(self.vy) + 0.5
            if new_y > screen_h - 220:
                self.vy = -abs(self.vy) - 0.5

            new_x = max(margin, min(screen_w - 220, new_x))
            new_y = max(margin, min(screen_h - 220, new_y))

            self.geometry(f"+{new_x}+{new_y}")

        self.after(80, self.wander)

    def focus_mode(self):
        self.mood = 'focus'
        self.show_speech_bubble('🎯 Focus Mode: Mình sẽ im lặng~', duration=3000)

    def sleep_mode(self):
        self.mood = 'sleep'
        self.show_speech_bubble('😴 Đi ngủ đây... Gọi "Nola ơi" để đánh thức!', duration=5000)

    def open_settings(self):
        pass

    def send_message(self, event=None):
        """Gửi tin nhắn từ input"""
        if hasattr(self, 'msg_entry'):
            text = self.msg_entry.get().strip()
            if text:
                self.add_message('Bạn', text)
                self.msg_entry.delete(0, 'end')
                if self.agent:
                    self.agent.handle_text_command(text)
