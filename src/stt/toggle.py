"""Hotkey toggle for speech-to-text. Python rewrite of stt-toggle bash script.

First press:  beep + notification, start recording.
Second press: beep + notification, stop recording, transcribe, type.
"""

import os
import signal
import subprocess
import sys
import time

from stt.config import (
    SND_START,
    SND_STOP,
    TOGGLE_LOCK,
    TOGGLE_PIDFILE,
    TOGGLE_WAVPATH,
)
from stt.log import setup_logging
from stt.typing import notify, play_sound

log = setup_logging("stt.toggle")


def _read_file(path: str) -> str:
    try:
        with open(path) as f:
            return f.read().strip()
    except FileNotFoundError:
        return ""


def _remove(*paths):
    for p in paths:
        try:
            os.unlink(p)
        except FileNotFoundError:
            pass


def _stop():
    """Stop recording, transcribe, type."""
    log.info("STOP pressed")
    play_sound(SND_STOP)
    notify("STT", "Transcribing...", timeout=2000)

    pid_str = _read_file(TOGGLE_PIDFILE)
    if pid_str:
        pid = int(pid_str)
        log.debug("killing recorder PID=%d", pid)
        try:
            os.kill(pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        # Wait for process to exit
        for _ in range(50):
            try:
                os.kill(pid, 0)
            except ProcessLookupError:
                break
            time.sleep(0.1)
        log.debug("recorder exited")

    _remove(TOGGLE_LOCK, TOGGLE_PIDFILE)

    wavfile = _read_file(TOGGLE_WAVPATH)
    _remove(TOGGLE_WAVPATH)
    if wavfile and os.path.exists(wavfile):
        log.debug("launching transcribe for %s", wavfile)
        subprocess.Popen(
            ["stt-transcribe", wavfile],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    else:
        notify("STT", "No audio file produced")
        log.warning("no WAV file to transcribe")


def _start():
    """Ensure daemon, start recording."""
    log.info("START pressed")

    # Ensure daemon is running
    from stt.client import daemon_running

    if not daemon_running():
        notify("STT", "Starting daemon...", timeout=3000, urgency="normal")
        subprocess.run(
            ["stt", "start"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        time.sleep(3)

    play_sound(SND_START)
    notify("STT", "Recording...", timeout=0)

    wavfile = f"/tmp/stt-recording-{os.getpid()}.wav"
    with open(TOGGLE_WAVPATH, "w") as f:
        f.write(wavfile)

    open(TOGGLE_LOCK, "w").close()

    proc = subprocess.Popen(
        ["stt-record", wavfile],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    with open(TOGGLE_PIDFILE, "w") as f:
        f.write(str(proc.pid))
    log.info("recorder started PID=%d wav=%s", proc.pid, wavfile)


def main():
    if os.path.exists(TOGGLE_LOCK):
        _stop()
    else:
        _start()


if __name__ == "__main__":
    main()
