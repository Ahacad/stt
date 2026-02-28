"""Transcribe a WAV file via stt-daemon and type result into focused window."""

import os
import sys

from stt.client import daemon_send
from stt.log import setup_logging
from stt.typing import notify, type_text

log = setup_logging("stt.transcribe")


def main():
    if len(sys.argv) < 2:
        print("Usage: stt-transcribe <file.wav>", file=sys.stderr)
        sys.exit(1)

    wavpath = sys.argv[1]
    if not os.path.exists(wavpath):
        log.error("file not found: %s", wavpath)
        sys.exit(1)

    try:
        log.debug("transcribing %s", wavpath)
        text = daemon_send(f"transcribe {wavpath}").strip()
    except Exception as e:
        log.error("daemon error: %s", e)
        text = ""
    finally:
        try:
            os.unlink(wavpath)
        except FileNotFoundError:
            pass

    if text and not text.startswith("ERROR:"):
        type_text(text)
        notify("STT", f"Typed: {text[:60]}")
        log.info("typed: %s", text[:80])
    else:
        notify("STT", "No speech detected")
        log.debug("no speech detected")


if __name__ == "__main__":
    main()
