from __future__ import annotations

import os
import sys
import threading
import tempfile
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
TTS_REPO = ROOT / "TTS"
MODEL_DIR = ROOT / "model"

if TTS_REPO.exists():
    sys.path.insert(0, str(TTS_REPO))


class ViXTTS:
    def __init__(self):
        self._model = None
        self._ready = False
        self._lock = threading.Lock()

    def ensure_downloaded(self):
        if not TTS_REPO.exists():
            print("[TTS] Cloning thinhlpg/TTS fork...")
            import subprocess
            subprocess.run(
                ["git", "clone", "--branch", "add-vietnamese-xtts", "-q",
                 "https://github.com/thinhlpg/TTS.git", str(TTS_REPO)],
                check=True, capture_output=True
            )
            sys.path.insert(0, str(TTS_REPO))
        if not MODEL_DIR.exists():
            print("[TTS] Downloading viXTTS model...")
            from huggingface_hub import snapshot_download
            snapshot_download(
                repo_id="thinhlpg/viXTTS",
                repo_type="model",
                local_dir=str(MODEL_DIR)
            )

    def load(self):
        with self._lock:
            if self._ready:
                return
            self.ensure_downloaded()
            print("[TTS] Loading viXTTS model...")
            try:
                import torch
                from TTS.tts.configs.xtts_config import XttsConfig
                from TTS.tts.models.xtts import Xtts

                config = XttsConfig()
                config.load_json(str(MODEL_DIR / "config.json"))
                model = Xtts.init_from_config(config)
                model.load_checkpoint(
                    config,
                    checkpoint_path=str(MODEL_DIR / "model.pth"),
                    vocab_path=str(MODEL_DIR / "vocab.json"),
                    use_deepspeed=False,
                )
                if torch.cuda.is_available():
                    model.cuda()
                self._model = model
                self._ready = True
                print("[TTS] viXTTS ready!")
            except Exception as e:
                print(f"[TTS] Load failed: {e}")

    def speak(self, text: str, language: str = "vi",
              reference_audio: str | None = None, blocking: bool = False):
        if not self._ready:
            self.load()
        if not self._ready:
            return
        if not text or not text.strip():
            return
        if reference_audio is None:
            candidate = MODEL_DIR / "vi_sample.wav"
            if not candidate.exists():
                candidates = list(MODEL_DIR.glob("*.wav"))
                if candidates:
                    reference_audio = str(candidates[0])
                else:
                    print("[TTS] No reference audio found")
                    return
            else:
                reference_audio = str(candidate)

        fn = self._speak_sync if blocking else \
            lambda *a: threading.Thread(target=self._speak_sync, args=a, daemon=True).start()
        fn(text, language, reference_audio)

    def _speak_sync(self, text: str, language: str, reference_audio: str):
        try:
            wav_path = self._synthesize(text, language, reference_audio)
            if wav_path:
                self._play(wav_path)
        except Exception as e:
            print(f"[TTS] Speak error: {e}")

    def _synthesize(self, text: str, lang: str, speaker_audio: str) -> str | None:
        import torch
        import torchaudio
        from underthesea import sent_tokenize

        gpt_latent, speaker_emb = self._model.get_conditioning_latents(
            audio_path=speaker_audio,
            gpt_cond_len=self._model.config.gpt_cond_len,
            max_ref_length=self._model.config.max_ref_len,
            sound_norm_refs=self._model.config.sound_norm_refs,
        )

        if lang == "vi":
            text = self._normalize(text)

        sentences = sent_tokenize(text)
        chunks = []

        for sentence in sentences:
            if not sentence.strip():
                continue
            result = self._model.inference(
                text=sentence,
                language=lang,
                gpt_cond_latent=gpt_latent,
                speaker_embedding=speaker_emb,
                temperature=0.3,
                length_penalty=1.0,
                repetition_penalty=10.0,
                top_k=30,
                top_p=0.85,
            )
            keep = self._keep_len(sentence, lang)
            result["wav"] = torch.tensor(result["wav"][:keep])
            chunks.append(result["wav"])

        if not chunks:
            return None

        out = torch.cat(chunks, dim=0).unsqueeze(0)
        out_dir = tempfile.mkdtemp(prefix="nola_tts_")
        out_path = os.path.join(out_dir, "speech.wav")
        torchaudio.save(out_path, out, 24000)
        return out_path

    def _normalize(self, text: str) -> str:
        from vinorm import TTSnorm
        text = TTSnorm(text, unknown=False, lower=False, rule=True)
        for a, b in [("..", "."), ("!.", "!"), ("?.", "?"),
                      (" .", "."), (" ,", ","), ('"', ""),
                      ("'", ""), ("AI", "Ây Ai"), ("A.I", "Ây Ai")]:
            text = text.replace(a, b)
        return text

    @staticmethod
    def _keep_len(text: str, lang: str) -> int:
        if lang in ("ja", "zh-cn"):
            return -1
        words = len(text.split())
        punct = sum(text.count(c) for c in ".!?,")
        if words < 5:
            return 15000 * words + 2000 * punct
        if words < 10:
            return 13000 * words + 2000 * punct
        return -1

    @staticmethod
    def _play(wav_path: str):
        import pyaudio
        import soundfile as sf
        data, sr = sf.read(wav_path)
        channels = 1 if data.ndim == 1 else data.shape[1]
        p = pyaudio.PyAudio()
        stream = p.open(
            format=pyaudio.paFloat32,
            channels=channels,
            rate=sr,
            output=True,
        )
        stream.write(data.astype(np.float32).tobytes())
        stream.close()
        p.terminate()


tts = ViXTTS()
