"""Main `stt` CLI entry point."""

import argparse
import subprocess
import sys

from stt.config import DEFAULT_DEVICE, PID_PATH
from stt.log import setup_logging

log = setup_logging("stt.cli")


def cmd_start(args):
    from stt.client import daemon_running

    if daemon_running():
        print("Daemon already running.")
        return
    cmd = ["stt-daemon"]
    if args.model:
        cmd += ["-m", args.model]
    if args.cpu:
        cmd += ["--cpu"]
    subprocess.Popen(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    print("Daemon starting...")
    import time

    for _ in range(20):
        time.sleep(0.5)
        if daemon_running():
            print("Daemon ready.")
            return
    print(
        "Daemon failed to start. Run 'stt-daemon' manually to see errors.",
        file=sys.stderr,
    )


def cmd_stop():
    from stt.client import daemon_running, daemon_send

    if not daemon_running():
        print("Daemon not running.")
        return
    daemon_send("shutdown")
    print("Daemon stopped.")


def cmd_status():
    from stt.client import daemon_running

    if daemon_running():
        pid = ""
        try:
            with open(PID_PATH) as f:
                pid = f" (PID {f.read().strip()})"
        except FileNotFoundError:
            pass
        print(f"Daemon running{pid}")
    else:
        print("Daemon not running. Start with: stt start")


def ensure_daemon(args):
    from stt.client import daemon_running

    if not daemon_running():
        print("Starting daemon...", file=sys.stderr)
        cmd_start(args)
        if not daemon_running():
            sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Speech-to-text using faster-whisper")
    parser.add_argument(
        "command",
        nargs="?",
        choices=["start", "stop", "status"],
        help="Daemon control commands",
    )
    parser.add_argument(
        "-t", "--type", action="store_true", help="Type into focused window via xdotool"
    )
    parser.add_argument(
        "-c", "--continuous", action="store_true", help="Continuous listening mode with VAD"
    )
    parser.add_argument(
        "-m", "--model", default="medium.en", help="Whisper model (default: medium.en)"
    )
    parser.add_argument(
        "-d",
        "--device",
        default=DEFAULT_DEVICE,
        help="Audio input device ID or name (default: pulse)",
    )
    parser.add_argument(
        "-l", "--list-devices", action="store_true", help="List audio input devices"
    )
    parser.add_argument("--cpu", action="store_true", help="Force CPU inference")
    args = parser.parse_args()

    if args.list_devices:
        from stt.audio import list_devices

        list_devices()
        return

    if args.command == "start":
        cmd_start(args)
        return
    if args.command == "stop":
        cmd_stop()
        return
    if args.command == "status":
        cmd_status()
        return

    # Recording modes — lazy import heavy deps
    from stt.audio import continuous_mode, record_until_stop
    from stt.client import save_and_transcribe
    from stt.typing import type_text

    ensure_daemon(args)

    if args.continuous:

        def on_segment(text):
            print(text)
            sys.stdout.flush()
            if args.type:
                type_text(text + " ")

        continuous_mode(device_id=args.device, on_segment=on_segment)
    else:
        result = record_until_stop(device_id=args.device)
        if result is None:
            print("No audio recorded.", file=sys.stderr)
            return
        audio, native_rate = result
        print("Transcribing...", file=sys.stderr)
        text = save_and_transcribe(audio, native_rate)
        if text:
            print(text)
            if args.type:
                type_text(text)
        else:
            print("(no speech detected)", file=sys.stderr)


if __name__ == "__main__":
    main()
