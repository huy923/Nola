from __future__ import annotations

import threading
import queue
import time
import numpy as np
from faster_whisper import WhisperModel

class RealtimeVoicePipeline:
    def __init__(self, agent=None):
        self.agent = agent
        self.audio_queue = queue.Queue(maxsize=200)
        self.is_running = False
        self.is_listening = False

        self.RATE = 16000
        self.CHUNK = 512

        self.ENERGY_THRESHOLD = 0.010
        self.SILENCE_FRAMES = 10
        self.MIN_VOICE_FRAMES = 8
        self.PRE_BUFFER = 8
        self.AUTO_THRESHOLD = True
        self.noise_floor = 0.001
        self.noise_floor_decay = 0.995

        self.voice_buffer = []
        self.pre_buffer = []
        self.silence_count = 0
        self.voice_count = 0
        self.is_speaking = False
        self.mic_active = False

        self.on_audio_level = None
        self.on_speech_start = None
        self.on_speech_end = None
        self.on_partial = None
        self.on_listening_change = None

        self._whisper: WhisperModel | None = None
        self._pyaudio = None
        self._model_ready = False

    def load_model_async(self):
        def _load():
            try:
                print("[Voice] Đang tải Whisper tiny...")
                self._whisper = WhisperModel("tiny", device="cpu", compute_type="int8")
                self._model_ready = True
                print("[Voice] Whisper sẵn sàng!")
            except Exception as e:
                print(f"[Voice] Lỗi tải model: {e}")
        t = threading.Thread(target=_load, daemon=True)
        t.start()

    @property
    def whisper(self):
        return self._whisper

    def start(self):
        self.is_running = True
        self.load_model_async()
        t1 = threading.Thread(target=self._record_loop, daemon=True)
        t1.start()
        t2 = threading.Thread(target=self._stt_loop, daemon=True)
        t2.start()
        print("[Voice] Pipeline đã chạy. Nói 'Nola ơi' hoặc nhấn mic để bắt đầu.")

    def stop(self):
        self.is_running = False

    def _record_loop(self):
        try:
            import pyaudio
            self._pyaudio = pyaudio.PyAudio()

            dev_idx = self._find_input_device()
            if dev_idx is not None:
                info = self._pyaudio.get_device_info_by_index(dev_idx)
                print(f"[Voice] Mic: [{dev_idx}] {info['name']}")

            stream = self._pyaudio.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=self.RATE,
                input=True,
                input_device_index=dev_idx,
                frames_per_buffer=self.CHUNK,
            )
            self.mic_active = True

            while self.is_running:
                try:
                    data = stream.read(self.CHUNK, exception_on_overflow=False)
                    audio = np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0
                    self.audio_queue.put(audio)
                except:
                    time.sleep(0.01)

        except Exception as e:
            print(f"[Voice] Ghi âm lỗi: {e}")
            print("[Voice] Thử cài: sudo apt install portaudio19-dev python3-pyaudio")
            while self.is_running:
                time.sleep(3)

    def _find_input_device(self) -> int | None:
        if self._pyaudio is None:
            return None
        try:
            default = self._pyaudio.get_default_input_device_info()
            if int(default.get('maxInputChannels', 0)) > 0:
                return int(default['index'])
        except:
            pass
        for i in range(self._pyaudio.get_device_count()):
            info = self._pyaudio.get_device_info_by_index(i)
            if int(info.get('maxInputChannels', 0)) > 0:
                return i
        return None

    def _stt_loop(self):
        while self.is_running:
            if not self.audio_queue.empty():
                audio = self.audio_queue.get()
                self._process_audio(audio)
            else:
                time.sleep(0.005)

    def _process_audio(self, audio):
        volume = np.abs(audio).mean()

        if self.AUTO_THRESHOLD:
            if volume > self.noise_floor * 3:
                self.noise_floor *= self.noise_floor_decay
                self.noise_floor += (1 - self.noise_floor_decay) * volume
            threshold = max(self.ENERGY_THRESHOLD, self.noise_floor * 2.5)
        else:
            threshold = self.ENERGY_THRESHOLD

        if self.on_audio_level:
            level = min(1.0, volume / max(threshold, 0.001) * 2)
            self.on_audio_level(level)

        is_voice = volume > threshold
        self.pre_buffer.append(audio)
        if len(self.pre_buffer) > self.PRE_BUFFER:
            self.pre_buffer.pop(0)

        if is_voice:
            if not self.is_speaking:
                self.is_speaking = True
                self.voice_buffer = list(self.pre_buffer)
                self.voice_count = len(self.pre_buffer)
                if self.on_speech_start:
                    self.on_speech_start()
            else:
                self.voice_buffer.append(audio)
                self.voice_count += 1
            self.silence_count = 0
        else:
            if self.is_speaking:
                self.voice_buffer.append(audio)
                self.silence_count += 1
                if self.silence_count > self.SILENCE_FRAMES:
                    if self.voice_count > self.MIN_VOICE_FRAMES:
                        self._transcribe_buffer(final=True)
                    self._reset_buffer()

    def _transcribe_buffer(self, final=False):
        whisper = self.whisper
        if whisper is None or len(self.voice_buffer) < 5:
            return

        audio = np.concatenate(self.voice_buffer)
        if audio.max() < 0.001:
            return

        try:
            segments, _ = whisper.transcribe(
                audio, language="vi", beam_size=3,
                vad_filter=True,
                vad_parameters=dict(min_silence_duration_ms=300),
                condition_on_previous_text=False
            )
            text = " ".join([seg.text.strip() for seg in segments]).strip()

            if not text or len(text) < 2:
                return

            if final:
                print(f"[🎤 Bạn] {text}")
                if self.on_speech_end:
                    self.on_speech_end()
                if self.is_listening or "nola" in text.lower():
                    if "nola" in text.lower() and not self.is_listening:
                        self.is_listening = True
                        print("[Voice] Bật chế độ nghe liên tục")
                        if self.on_listening_change:
                            self.on_listening_change(True)
                    self._handle_command(text)
            elif self.on_partial:
                self.on_partial(text)

        except Exception as e:
            if final:
                print(f"[Voice] Lỗi: {e}")

    def _handle_command(self, text):
        if self.agent:
            self.agent.handle_voice_command(text)

    def _reset_buffer(self):
        self.voice_buffer = []
        self.pre_buffer = []
        self.silence_count = 0
        self.voice_count = 0
        self.is_speaking = False

    def speak(self, text):
        print(f"[Nola] {text}")
        try:
            from core.tts import tts
            tts.speak(text)
        except Exception as e:
            print(f"[TTS] Error: {e}")

