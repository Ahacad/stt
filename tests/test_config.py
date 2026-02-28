"""Test config constants and path expansion."""

import os

from stt.config import (
    CHANNELS,
    LOG_PATH,
    MIN_AUDIO_DURATION,
    PID_PATH,
    SILENCE_DURATION,
    SILENCE_THRESHOLD,
    SOCKET_PATH,
    WHISPER_RATE,
)


def test_paths_are_expanded():
    assert "~" not in SOCKET_PATH
    assert "~" not in PID_PATH
    assert "~" not in LOG_PATH


def test_paths_under_home():
    home = os.path.expanduser("~")
    assert SOCKET_PATH.startswith(home)
    assert PID_PATH.startswith(home)
    assert LOG_PATH.startswith(home)


def test_audio_constants():
    assert CHANNELS == 1
    assert WHISPER_RATE == 16000
    assert SILENCE_THRESHOLD > 0
    assert SILENCE_DURATION > 0
    assert MIN_AUDIO_DURATION > 0
