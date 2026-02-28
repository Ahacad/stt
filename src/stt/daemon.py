"""STT daemon — keeps faster-whisper model loaded in VRAM.

Listens on a unix socket. Commands:
  - "transcribe <path>"  → transcribe a WAV file, return text
  - "ping"               → respond "pong"
  - "shutdown"           → exit daemon
"""

import argparse
import os
import signal
import socket
import sys

import numpy as np
import soundfile as sf
import soxr
from faster_whisper import WhisperModel

from stt.config import PID_PATH, SOCKET_PATH, WHISPER_RATE
from stt.log import setup_logging

log = setup_logging("stt.daemon")


def load_model(model_name: str, device: str = "cuda") -> WhisperModel:
    compute_type = "float16" if device == "cuda" else "int8"
    log.info("loading model '%s' on %s (%s)", model_name, device, compute_type)
    model = WhisperModel(model_name, device=device, compute_type=compute_type)
    log.info("model ready")
    return model


def transcribe_file(model: WhisperModel, path: str) -> str:
    audio, sr = sf.read(path, dtype="float32")
    if audio.ndim > 1:
        audio = audio[:, 0]
    if sr != WHISPER_RATE:
        audio = soxr.resample(audio, sr, WHISPER_RATE).astype(np.float32)
    if len(audio) < WHISPER_RATE * 0.3:
        return ""
    segments, _ = model.transcribe(audio, beam_size=5, vad_filter=True)
    return " ".join(seg.text.strip() for seg in segments)


def handle_client(conn: socket.socket, model: WhisperModel) -> bool:
    """Handle one client connection. Returns False to shut down."""
    try:
        data = conn.recv(4096).decode("utf-8").strip()
        if not data:
            return True

        if data == "ping":
            conn.sendall(b"pong")
        elif data == "shutdown":
            conn.sendall(b"ok")
            log.info("shutdown requested")
            return False
        elif data.startswith("transcribe "):
            path = data[len("transcribe "):]
            log.debug("transcribing %s", path)
            try:
                text = transcribe_file(model, path)
                conn.sendall(text.encode("utf-8"))
                log.debug("result: %s", text[:80] if text else "(empty)")
            except Exception as e:
                log.error("transcription failed: %s", e)
                conn.sendall(f"ERROR: {e}".encode("utf-8"))
        else:
            conn.sendall(b"ERROR: unknown command")
    except Exception as e:
        log.error("client error: %s", e)
    finally:
        conn.close()
    return True


def cleanup(*_):
    for path in (SOCKET_PATH, PID_PATH):
        try:
            os.unlink(path)
        except FileNotFoundError:
            pass
    log.info("cleaned up, exiting")
    sys.exit(0)


def main():
    parser = argparse.ArgumentParser(description="STT daemon")
    parser.add_argument(
        "-m", "--model", default="medium.en", help="Whisper model (default: medium.en)"
    )
    parser.add_argument("--cpu", action="store_true", help="Force CPU inference")
    args = parser.parse_args()

    os.makedirs(os.path.dirname(SOCKET_PATH), exist_ok=True)
    os.makedirs(os.path.dirname(PID_PATH), exist_ok=True)

    # Clean stale socket
    if os.path.exists(SOCKET_PATH):
        try:
            s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            s.connect(SOCKET_PATH)
            s.sendall(b"ping")
            resp = s.recv(64)
            s.close()
            if resp == b"pong":
                log.error("daemon already running")
                sys.exit(1)
        except (ConnectionRefusedError, FileNotFoundError):
            os.unlink(SOCKET_PATH)

    device = "cpu" if args.cpu else "cuda"
    model = load_model(args.model, device=device)

    signal.signal(signal.SIGTERM, cleanup)
    signal.signal(signal.SIGINT, cleanup)

    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.bind(SOCKET_PATH)
    sock.listen(5)

    with open(PID_PATH, "w") as f:
        f.write(str(os.getpid()))

    log.info("listening on %s (PID %d)", SOCKET_PATH, os.getpid())

    try:
        while True:
            conn, _ = sock.accept()
            keep_running = handle_client(conn, model)
            if not keep_running:
                break
    finally:
        cleanup()


if __name__ == "__main__":
    main()
