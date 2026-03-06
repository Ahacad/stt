"""Transcribe a WAV file via stt-daemon and type result into the origin window."""

import argparse
import os
import sys

from stt.client import daemon_send
from stt.log import setup_logging
from stt.output import copy_to_clipboard, notify, type_text

log = setup_logging("stt.transcribe")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("wavpath")
    parser.add_argument("--window", default=None, help="target window ID for xdotool")
    args = parser.parse_args()

    if not os.path.exists(args.wavpath):
        log.error("file not found: %s", args.wavpath)
        sys.exit(1)

    try:
        log.debug("transcribing %s", args.wavpath)
        text = daemon_send(f"transcribe {args.wavpath}").strip()
    except Exception as e:
        log.error("daemon error: %s", e)
        text = ""
    finally:
        try:
            os.unlink(args.wavpath)
        except FileNotFoundError:
            pass

    if text and not text.startswith("ERROR:"):
        copy_to_clipboard(text)
        type_text(text, window_id=args.window)
        notify("STT", f"Typed: {text[:60]}")
        log.info("typed (window=%s): %s", args.window, text[:80])
    else:
        notify("STT", "No speech detected")
        log.debug("no speech detected")


if __name__ == "__main__":
    main()
