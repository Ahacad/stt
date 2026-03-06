"""Shared constants and paths for the STT system."""

import os

from stt.compat import WINDOWS, data_dir, temp_dir

# Paths
_data = data_dir()
os.makedirs(_data, exist_ok=True)

SOCKET_PATH = os.path.join(_data, "stt.sock")
PID_PATH = os.path.join(_data, "stt-daemon.pid")
LOG_DIR = _data
LOG_PATH = os.path.join(_data, "stt.log")

# Audio
DEFAULT_DEVICE = None if WINDOWS else "pulse"
CHANNELS = 1
WHISPER_RATE = 16000

# VAD (continuous mode)
SILENCE_THRESHOLD = 0.01
SILENCE_DURATION = 1.5
MIN_AUDIO_DURATION = 0.5

# Toggle paths
_tmp = temp_dir()
TOGGLE_LOCK = os.path.join(_tmp, "stt-recording.lock")
TOGGLE_PIDFILE = os.path.join(_tmp, "stt-recording.pid")
TOGGLE_WAVPATH = os.path.join(_tmp, "stt-recording-wavpath")
TOGGLE_WINDOWID = os.path.join(_tmp, "stt-recording-windowid")

# Sounds
SND_START = None if WINDOWS else "/usr/share/sounds/freedesktop/stereo/message-new-instant.oga"
SND_STOP = None if WINDOWS else "/usr/share/sounds/freedesktop/stereo/audio-volume-change.oga"

# Notification
NOTIFY_ID = "9999"

# Windows tray config
CONFIG_PATH = os.path.join(_data, "config.toml")
DEFAULT_HOTKEY = "<ctrl>+<shift>+s"
DEFAULT_MODEL = "large-v3"
