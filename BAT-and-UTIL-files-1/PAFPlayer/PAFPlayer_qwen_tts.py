"""Small local HTTP adapter for Qwen3-TTS CustomVoice models.

PAFPlayer starts this process on demand so the 1.7B model stays resident
between DJ turns instead of being loaded once for every sentence.
"""
from __future__ import annotations

import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import io
import json
from pathlib import Path
import threading
import traceback


MAX_TEXT = 12000
MAX_INSTRUCT = 2000


class ModelRuntime:
    def __init__(self, model_path: str):
        self.model_path = str(Path(model_path).expanduser())
        self.lock = threading.RLock()
        self.model = None
        self.error = None
        self.loading = True
        self.thread = threading.Thread(target=self._load, name="qwen3-tts-load", daemon=True)

    def start(self):
        self.thread.start()

    def _load(self):
        try:
            import torch
            from qwen_tts import Qwen3TTSModel

            if not Path(self.model_path).is_dir():
                raise RuntimeError("Qwen3-TTS model folder does not exist")
            cuda = bool(torch.cuda.is_available())
            kwargs = {
                "device_map": "cuda:0" if cuda else "cpu",
                "dtype": torch.bfloat16 if cuda else torch.float32,
            }
            model = Qwen3TTSModel.from_pretrained(self.model_path, **kwargs)
            with self.lock:
                self.model = model
                self.loading = False
        except Exception as exc:
            with self.lock:
                self.error = f"{type(exc).__name__}: {exc}"
                self.loading = False

    def status(self):
        with self.lock:
            return {
                "ready": self.model is not None,
                "loading": self.loading,
                "error": self.error or "",
                "model": self.model_path,
            }

    def synthesize(self, payload):
        text = payload.get("text", "")
        speaker = payload.get("speaker", "Ryan")
        language = payload.get("language", "English")
        instruct = payload.get("instruct", "")
        if not isinstance(text, str) or not text.strip() or len(text) > MAX_TEXT:
            raise ValueError("Speech text is empty or too long")
        if not isinstance(speaker, str) or not speaker.strip() or len(speaker) > 80:
            raise ValueError("Invalid Qwen3-TTS speaker")
        if not isinstance(language, str) or not language.strip() or len(language) > 80:
            raise ValueError("Invalid Qwen3-TTS language")
        if not isinstance(instruct, str) or len(instruct) > MAX_INSTRUCT:
            raise ValueError("Qwen3-TTS instruction is too long")
        with self.lock:
            if self.model is None:
                if self.error:
                    raise RuntimeError(self.error)
                raise RuntimeError("Qwen3-TTS model is still loading")
            model = self.model
        import soundfile as sf

        wavs, sample_rate = model.generate_custom_voice(
            text=text.strip(), speaker=speaker.strip(), language=language.strip(),
            instruct=instruct.strip() or None,
        )
        if not wavs:
            raise RuntimeError("Qwen3-TTS returned no audio")
        output = io.BytesIO()
        sf.write(output, wavs[0], sample_rate, format="WAV", subtype="PCM_16")
        return output.getvalue()


class Handler(BaseHTTPRequestHandler):
    runtime: ModelRuntime

    def _json(self, value, status=200):
        body = json.dumps(value, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/health":
            status = self.runtime.status()
            self._json(status, 200 if status["ready"] else 503)
            return
        self._json({"error": "Not found"}, 404)

    def do_POST(self):
        if self.path != "/synthesize":
            self._json({"error": "Not found"}, 404)
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length <= 0 or length > 256 * 1024:
                raise ValueError("Invalid request size")
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            audio = self.runtime.synthesize(payload)
            self.send_response(200)
            self.send_header("Content-Type", "audio/wav")
            self.send_header("Content-Length", str(len(audio)))
            self.end_headers()
            self.wfile.write(audio)
        except Exception as exc:
            self._json({"error": f"{type(exc).__name__}: {exc}"}, 503 if "loading" in str(exc).lower() else 400)

    def log_message(self, *_args):
        return


def instructions():
    print("PAFPlayer Qwen3-TTS local speech adapter")
    print("Use the Qwen3-TTS speech provider in PAFPlayer AI DJ settings.")
    print("Model folder: T:\\models\\qwen-large-8oxzkzzr\\model")
    print("Runtime: T:\\models\\qwen-large-8oxzkzzr\\venv\\Scripts\\python.exe")
    print("The model is not an Ollama model; PAFPlayer talks to this local adapter.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--server", action="store_true")
    parser.add_argument("--model", default=r"T:\models\qwen-large-8oxzkzzr\model")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--instructions", action="store_true")
    args = parser.parse_args()
    if args.instructions or not args.server:
        instructions()
        return 0
    if not 1 <= args.port <= 65535:
        parser.error("port must be between 1 and 65535")
    runtime = ModelRuntime(args.model)
    Handler.runtime = runtime
    runtime.start()
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        return 0
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
