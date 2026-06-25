#!/usr/bin/env python3
"""
Nola Autonomous Agent
Tu phan tich -> tu tao prompt -> tu mo trinh duyet -> tu paste -> tu chay -> tu sua loi
"""

from __future__ import annotations

import subprocess
import time
import os
import re
import threading
import requests
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ui.main_window import NolaOverlay

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = os.getenv("MODEL_OLLAMA")
print(f"✅✅✅ Sử dụng LLM: {OLLAMA_MODEL} tại {OLLAMA_URL}")
class AutonomousAgent:
    def __init__(self, virtual_input=None, window_manager=None):
        self.vinput = virtual_input
        self.wm = window_manager
        self.ui: NolaOverlay | None = None
        self.project_dir = os.path.expanduser("~/NolaProjects")
        os.makedirs(self.project_dir, exist_ok=True)
        self.current_project = None
        self._chat_history = []
        self._ollama_ready = False
        threading.Thread(target=self._warm_ollama, daemon=True).start()

    def _warm_ollama(self):
        try:
            print("[Agent] Đang khởi tạo LLM...")
            requests.post(OLLAMA_URL, json={
                "model": OLLAMA_MODEL, "prompt": "Xin chào",
                "stream": False, "options": {"num_predict": 5}
            }, timeout=180)
            self._ollama_ready = True
            print("[Agent] LLM sẵn sàng!")
        except Exception as e:
            print(f"[Agent] LLM không khả dụng: {e}")

    def handle_voice_command(self, text):
        text_lower = text.lower()
        text_clean = re.sub(r'\b(nola|oi|hey|hello|a|ạ|o|ọ)\b', '', text_lower).strip()
        text_clean = re.sub(r'\s+', ' ', text_clean).strip()

        if not text_clean or len(text_clean) < 3:
            self._say("Dạ, em đây! Chủ nhân cần gì ạ?")
            return

        print(f"[Agent] Lệnh: '{text_clean}'")

        if any(k in text_clean for k in ['tạo', 'làm', 'create', 'build', 'make', 'code', 'viết']):
            self._handle_create(text_clean)
        elif any(k in text_clean for k in ['mở', 'open', 'launch', 'bật']):
            self._handle_open(text_clean)
        elif any(k in text_clean for k in ['chạy', 'run', 'execute', 'start']):
            self._handle_run(text_clean)
        elif any(k in text_clean for k in ['sửa', 'fix', 'repair', 'debug']):
            self._handle_fix(text_clean)
        elif any(k in text_clean for k in ['dừng', 'stop', 'tắt', 'kill']):
            self._handle_stop(text_clean)
        else:
            self._handle_chat(text_clean)

    def handle_text_command(self, text):
        """Xử lý lệnh text từ chat panel"""
        self.handle_voice_command(text)

    def _say(self, text):
        """Nola nói + hiển thị bubble + TTS"""
        print(f"[Nola] {text}")
        if self.ui:
            self.ui.after(0, self.ui.show_speech_bubble, text)
            self.ui.after(0, self.ui.add_message, 'Nola', text)
        try:
            from core.tts import tts
            tts.speak(text)
        except Exception as e:
            print(f"[TTS] Error: {e}")

    def _handle_create(self, text):
        """Tạo project mới"""
        self._say(f"Được rồi! Mình đang phân tích yêu cầu: '{text}'")

        project_type = self._detect_project_type(text)
        project_name = self._extract_project_name(text) or f"project_{int(time.time())}"

        self._say(f"Mình sẽ tạo {project_type} tên '{project_name}'. Đang mở Claude để code...")

        # Tạo prompt chi tiết
        prompt = self._generate_prompt(text, project_type, project_name)

        # Lưu prompt để user xem
        prompt_path = os.path.join(self.project_dir, f"{project_name}_prompt.txt")
        with open(prompt_path, 'w', encoding='utf-8') as f:
            f.write(prompt)

        # Mở AI tool
        self._open_ai_tool("claude", prompt, project_name)

        self.current_project = project_name

    def _detect_project_type(self, text):
        """Phát hiện loại project"""
        text = text.lower()
        if any(k in text for k in ['web', 'website', 'trang web', 'react', 'frontend', 'html']):
            return 'react_web'
        elif any(k in text for k in ['app', 'mobile', 'android', 'ios', 'flutter']):
            return 'mobile_app'
        elif any(k in text for k in ['python', 'script', 'tool', 'automation', 'bot']):
            return 'python_script'
        elif any(k in text for k in ['game', 'tro choi', 'unity', 'pygame']):
            return 'game'
        elif any(k in text for k in ['api', 'backend', 'server', 'node', 'express']):
            return 'backend_api'
        return 'generic'

    def _extract_project_name(self, text):
        """Trích xuất tên project từ lệnh"""
        # Tìm "tên ..." hoặc "gọi ..."
        match = re.search(r't[eê]n\s+([\w\-]+)', text.lower())
        if match:
            return match.group(1)
        match = re.search(r'g[oọ]i\s+([\w\-]+)', text.lower())
        if match:
            return match.group(1)
        return None

    def _generate_prompt(self, description, project_type, project_name):
        """Tạo prompt chi tiết từ mô tả ngắn"""

        base_prompt = f"""# Yêu cầu: {description}

# Tên project: {project_name}

Bạn là senior developer với 10+ năm kinh nghiệm. Hãy tạo project hoàn chỉnh, production-ready.

## Yêu cầu kỹ thuật:
"""

        tech_stacks = {
            'react_web': """- React 18 + TypeScript + Vite (build tool)
- Tailwind CSS + shadcn/ui hoặc Material-UI
- React Router DOM v6 (routing)
- Zustand hoặc Redux Toolkit (state management)
- React Query hoặc SWR (data fetching)
- Axios (HTTP client)
- React Hook Form + Zod (form validation)

## Cấu trúc project:
```
{project_name}/
├── src/
│   ├── components/          # UI components (Button, Card, Modal...)
│   ├── pages/               # Các trang (Home, About, Dashboard...)
│   ├── hooks/               # Custom hooks (useAuth, useApi...)
│   ├── stores/              # Zustand stores
│   ├── services/            # API calls
│   ├── utils/               # Helpers, constants
│   ├── types/               # TypeScript interfaces
│   └── styles/              # Global styles
├── public/                  # Static assets
├── package.json
├── vite.config.ts
├── tailwind.config.js
├── tsconfig.json
└── README.md
```

## Yêu cầu chi tiết:
1. Responsive design (mobile-first approach)
2. Dark mode support (toggle + system preference)
3. Loading states skeleton
4. Error boundaries + toast notifications
5. Form validation real-time
6. API mock data (JSON server hoặc MSW)
7. Unit tests (Vitest + React Testing Library)
8. SEO meta tags
9. PWA support (service worker)

Hãy tạo TẤT CẢ file, bao gồm:
- package.json đầy đủ dependencies
- vite.config.ts với plugins
- tailwind.config.js với theme custom
- tsconfig.json strict mode
- src/main.tsx (entry point)
- src/App.tsx với routing
- Tất cả components và pages
- Custom hooks
- Zustand stores
- API services với mock data
- TypeScript types

Format output:
```filename
// code here
```""",

            'python_script': """- Python 3.10+ với type hints đầy đủ
- Pydantic (data validation)
- Loguru (logging)
- python-dotenv (config)
- pytest + coverage (testing)
- Black + Ruff (formatting/linting)

## Cấu trúc project:
```
{project_name}/
├── src/
│   ├── __init__.py
│   ├── main.py              # Entry point
│   ├── core/                # Logic chính
│   ├── utils/               # Helpers
│   └── config.py            # Configuration
├── tests/
│   ├── __init__.py
│   └── test_*.py
├── requirements.txt
├── pyproject.toml
└── README.md
```

Hãy tạo TẤT CẢ file, bao gồm:
- requirements.txt đầy đủ
- pyproject.toml (Black, pytest config)
- src/main.py với CLI args
- src/core/ với logic chính
- src/utils/ với helpers
- tests/ với unit tests
- README.md hướng dẫn

Format output:
```filename
# code here
```""",

            'backend_api': """- Node.js + Express + TypeScript
- Prisma ORM + PostgreSQL
- JWT authentication
- Zod validation
- Swagger/OpenAPI docs
- Jest testing
- Docker support

## Cấu trúc project:
```
{project_name}/
├── src/
│   ├── routes/              # API routes
│   ├── controllers/         # Business logic
│   ├── models/              # Prisma schema
│   ├── middleware/          # Auth, error handling
│   ├── utils/               # Helpers
│   └── config/              # Environment config
├── prisma/
│   └── schema.prisma
├── tests/
├── docker-compose.yml
├── package.json
├── tsconfig.json
└── README.md
```

Hãy tạo TẤT CẢ file, bao gồm:
- package.json đầy đủ
- prisma/schema.prisma
- src/server.ts
- Tất cả routes + controllers
- Middleware (auth, error)
- Docker setup
- Tests

Format output:
```filename
// code here
```""",

            'generic': """Hãy phân tích yêu cầu và chọn tech stack phù hợp nhất.
Tạo project hoàn chỉnh, production-ready với:
- Clean code
- Error handling
- Documentation
- Testing

Format output:
```filename
// code here
```"""
        }

        return base_prompt + tech_stacks.get(project_type, tech_stacks['generic'])

    def _open_ai_tool(self, tool, prompt, project_name):
        """Mở AI tool và paste prompt"""
        urls = {
            'claude': 'https://claude.ai',
            'chatgpt': 'https://chatgpt.com',
            'gemini': 'https://gemini.google.com'
        }

        url = urls.get(tool, 'https://claude.ai')

        # Mở trình duyệt
        if self.wm:
            self.wm.open_browser(url)
        else:
            subprocess.Popen(['xdg-open', url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        self._say(f"Đã mở {tool}. Prompt đã lưu tại ~/NolaProjects/{project_name}_prompt.txt")
        self._say("Bạn có thể copy paste prompt vào Claude, hoặc mình sẽ tự động hóa trong tương lai.")

    def _handle_open(self, text):
        """Mở ứng dụng/website"""
        apps = {
            'chrome': ['google-chrome', 'chromium', 'chromium-browser'],
            'firefox': ['firefox'],
            'code': ['code', 'codium'],
            'terminal': ['gnome-terminal', 'konsole', 'xterm'],
            'file': ['nautilus', 'dolphin', 'thunar']
        }

        for app_name, cmds in apps.items():
            if app_name in text:
                for cmd in cmds:
                    try:
                        subprocess.Popen([cmd], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        self._say(f"Đã mở {app_name}")
                        return
                    except FileNotFoundError:
                        continue
                self._say(f"Không tìm thấy {app_name}")
                return

        # Mở URL
        url_match = re.search(r'https?://[^\\s]+', text)
        if url_match:
            subprocess.Popen(['xdg-open', url_match.group()], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self._say(f"Đã mở {url_match.group()}")
            return

        self._say("Mình không hiểu bạn muốn mở gì. Hãy nói rõ hơn nhé!")

    def _handle_run(self, text):
        """Chạy code/project"""
        if not self.current_project:
            # Tìm project gần nhất
            projects = [d for d in os.listdir(self.project_dir) if os.path.isdir(os.path.join(self.project_dir, d))]
            if projects:
                self.current_project = sorted(projects)[-1]
            else:
                self._say("Chưa có project nào. Hãy tạo project trước nhé!")
                return

        path = os.path.join(self.project_dir, self.current_project)

        # Detect loại project
        if os.path.exists(os.path.join(path, 'package.json')):
            # Node.js project
            cmd = f'cd "{path}" && npm install && npm run dev'
            self._say(f"Đang chạy {self.current_project} (npm)...")
        elif os.path.exists(os.path.join(path, 'requirements.txt')):
            # Python project
            cmd = f'cd "{path}" && python -m venv venv && source venv/bin/activate && pip install -r requirements.txt && python src/main.py'
            self._say(f"Đang chạy {self.current_project} (Python)...")
        else:
            self._say(f"Không nhận diện được loại project tại {path}")
            return

        if self.wm:
            self.wm.open_terminal(cmd)
        else:
            subprocess.Popen(['gnome-terminal', '--', 'bash', '-c', cmd + '; read'], 
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def _handle_fix(self, text):
        """Sửa lỗi"""
        self._say("Mình đang phân tích lỗi...")
        # TODO: Đọc log, paste vào AI, lấy fix
        self._say("Tính năng sửa lỗi tự động đang phát triển. Bạn có thể paste lỗi vào chat nhé!")

    def _handle_stop(self, text):
        """Dừng process"""
        if self.wm:
            self.wm.close_all()
        self._say("Đã dừng tất cả process của Nola.")

    def _handle_chat(self, text):
        self._say("Đang suy nghĩ...")
        self._chat_history.append({"role": "user", "content": text})
        threading.Thread(target=self._llm_respond, daemon=True).start()

    def _llm_respond(self):
        try:
            system = (
                "Bạn là Nola, một trợ lý AI giọng nói thông minh, thân thiện, nói tiếng Việt. "
                "Trả lời ngắn gọn, tự nhiên như đang nói chuyện. Tối đa 3 câu."
            )
            messages = [{"role": "system", "content": system}]
            for msg in self._chat_history[-6:]:
                messages.append(msg)

            payload = {
                "model": OLLAMA_MODEL,
                "prompt": self._format_prompt(messages),
                "stream": False,
                "options": {"num_predict": 200, "temperature": 0.7}
            }
            r = requests.post(OLLAMA_URL, json=payload, timeout=120)
            reply = r.json().get("response", "").strip()
            if reply:
                self._chat_history.append({"role": "assistant", "content": reply})
                self._say(reply)
            else:
                self._say("Xin lỗi, em chưa trả lời được. Chủ nhân nói lại nhé?")
        except Exception as e:
            print(f"[Agent] LLM lỗi: {e}")
            self._say("Xin lỗi, em đang bị lỗi kết nối. Chủ nhân thử lại sau nhé!")

    def _format_prompt(self, messages):
        parts = []
        for m in messages:
            role = m["role"]
            content = m["content"]
            if role == "system":
                parts.append(f"<s>{content}</s>")
            elif role == "user":
                parts.append(f"[INST] {content} [/INST]")
            elif role == "assistant":
                parts.append(f"{content}</s>")
        return "\n".join(parts)
