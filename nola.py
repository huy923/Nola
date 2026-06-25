#!/usr/bin/env python3
"""
Nola AI Agent - Entry Point
AI Assistant tự động điều khiển máy tính bằng giọng nói
Real-time voice, autonomous execution, parallel mode
"""

import sys
import os
import threading

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ui.main_window import NolaOverlay
from core.realtime_voice import RealtimeVoicePipeline
from core.autonomous_agent import AutonomousAgent
from core.window_manager import WindowManager
from core.virtual_input import VirtualInput

class NolaApp:
    def __init__(self):
        print("[Nola] ╔══════════════════════════════════════╗")
        print("[Nola] ║   NOLA AI AGENT v1.0               ║")
        print("[Nola] ║   Real-time | Autonomous | Parallel ║")
        print("[Nola] ╚══════════════════════════════════════╝")
        print("[Nola] Đang khởi động...")

        self.window_manager = WindowManager()
        self.virtual_input = VirtualInput()
        self.agent = AutonomousAgent(self.virtual_input, self.window_manager)
        self.voice = RealtimeVoicePipeline(self.agent)

        # UI nhận voice và agent để callback
        self.ui = NolaOverlay(self.voice, self.agent)

        # Kết nối agent với UI để hiển thị speech bubble
        self.agent.ui = self.ui

        # Tải TTS trong nền
        threading.Thread(target=self._init_tts, daemon=True).start()

        print("[Nola] ✅ Đã sẵn sàng! Nói 'Nola ơi' để bắt đầu.")
        print("[Nola] Hotkeys: Ctrl+Space = Mic | Ctrl+Shift+N = Focus Mode")

    def _init_tts(self):
        from core.tts import tts
        tts.ensure_downloaded()
        tts.load()

    def run(self):
        
        voice_thread = threading.Thread(target=self.voice.start, daemon=True)
        voice_thread.start()
        self.ui.mainloop()

    def stop(self):
        self.voice.stop()
        self.ui.destroy()

def main():
    app = NolaApp()
    try:
        app.run()
    except KeyboardInterrupt:
        print("\n[Nola] 👋 Tạm biệt chủ nhân!")
        app.stop()

if __name__ == "__main__":
    main()
