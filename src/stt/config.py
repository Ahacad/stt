"""Shared constants and paths for the STT system."""

import os

# Paths
SOCKET_PATH = os.path.expanduser("~/.local/state/stt.sock")
PID_PATH = os.path.expanduser("~/.local/state/stt-daemon.pid")
LOG_DIR = os.path.expanduser("~/.local/state/stt")
LOG_PATH = os.path.join(LOG_DIR, "stt.log")

# Audio
DEFAULT_DEVICE = "pulse"
CHANNELS = 1
WHISPER_RATE = 16000

# VAD (continuous mode)
SILENCE_THRESHOLD = 0.01
SILENCE_DURATION = 1.5
MIN_AUDIO_DURATION = 0.5

# Toggle paths
TOGGLE_LOCK = "/tmp/stt-recording.lock"
TOGGLE_PIDFILE = "/tmp/stt-recording.pid"
TOGGLE_WAVPATH = "/tmp/stt-recording-wavpath"

# Sounds
SND_START = "/usr/share/sounds/freedesktop/stereo/message-new-instant.oga"
SND_STOP = "/usr/share/sounds/freedesktop/stereo/audio-volume-change.oga"

# Notification
NOTIFY_ID = "9999"
