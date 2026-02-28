"""Socket client for talking to stt-daemon."""

import os
import socket
import tempfile

from stt.config import SOCKET_PATH
from stt.log import setup_logging

log = setup_logging("stt.client")


def daemon_running() -> bool:
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.connect(SOCKET_PATH)
        s.sendall(b"ping")
        resp = s.recv(64)
        s.close()
        return resp == b"pong"
    except (ConnectionRefusedError, FileNotFoundError, OSError):
        return False


def daemon_send(command: str, timeout: int = 30) -> str:
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    s.settimeout(timeout)
    s.connect(SOCKET_PATH)
    s.sendall(command.encode("utf-8"))
    chunks = []
    while True:
        try:
            data = s.recv(4096)
            if not data:
                break
            chunks.append(data)
        except socket.timeout:
            break
    s.close()
    return b"".join(chunks).decode("utf-8")


def save_and_transcribe(audio, native_rate: int) -> str:
    """Save audio to temp WAV, send to daemon, return text."""
    import soundfile as sf

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        tmp = f.name
    sf.write(tmp, audio, native_rate, subtype="FLOAT")
    try:
        log.debug("sending %s to daemon for transcription", tmp)
        text = daemon_send(f"transcribe {tmp}")
        if text.startswith("ERROR:"):
            log.error("transcription error: %s", text)
            return ""
        return text
    finally:
        os.unlink(tmp)
