# Nola AI Agent v1.0

AI Assistant tu dong dieu khien may tinh bang giong noi - 100% Python

## Tinh nang

- Real-time Voice: Phan hoi < 500ms, streaming STT
- Autonomous: Tu phan tich lenh, tu tao prompt, tu chay code
- Parallel Mode: Chay song song voi ban, cua so rieng
- Zero Keyboard: Chi dung giong noi, khong can ban phim/chuot

## Cai dat

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install python3-pyaudio portaudio19-dev xdotool

# Cai Python dependencies
pip install -r requirements.txt
```

## Chay

```bash
python nola.py
```

## Su dung

1. Noi "Nola oi" de bat dau
2. Noi lenh vi du: "Tao website ban hang co gio hang"
3. Nola tu dong:
   - Phan tich yeu cau
   - Mo Claude.ai (cua so rieng)
   - Tao prompt chi tiet (luu tai ~/NolaProjects/)
   - Ban paste vao Claude, lay code ve
   - Nola chay project
4. Double-click avatar de xem lich su chat
5. Ctrl+Space de bat/tat mic
6. Ctrl+Shift+N de vao focus mode

## Cau truc

```
Nola/
|-- nola.py              # Entry point
|-- ui/
|   |-- main_window.py   # Giao dien overlay
|-- core/
|   |-- realtime_voice.py   # Voice pipeline
|   |-- autonomous_agent.py # Tu dong thuc thi
|   |-- virtual_input.py    # Chuot/phim ao
|   |-- window_manager.py   # Quan ly cua so
|-- config.nola          # Cau hinh
|-- requirements.txt     # Dependencies
```

## Luu y

- Can micro de dung giong noi
- Can Chrome/Chromium de mo AI tools
- Can xdotool (Linux) de dieu khien cua so
- Prompt duoc luu tai ~/NolaProjects/ de ban xem lai
# Nola
