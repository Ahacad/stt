"""Wrappers for xdotool, dunstify, and paplay."""

import subprocess

from stt.config import NOTIFY_ID


def type_text(text: str) -> None:
    if text:
        subprocess.run(
            ["xdotool", "type", "--clearmodifiers", "--", text], check=False
        )


def notify(title: str, body: str, timeout: int = 2000, urgency: str = "low") -> None:
    subprocess.run(
        ["dunstify", "-r", NOTIFY_ID, "-t", str(timeout), "-u", urgency, title, body],
        check=False,
    )


def play_sound(path: str) -> None:
    subprocess.Popen(
        ["paplay", path],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
