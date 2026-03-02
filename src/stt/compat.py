"""Platform detection and path helpers."""

import os
import sys
import tempfile

WINDOWS = sys.platform == "win32"
LINUX = sys.platform == "linux"


def data_dir():
    if WINDOWS:
        base = os.environ.get("LOCALAPPDATA", os.path.expanduser("~/AppData/Local"))
        return os.path.join(base, "stt")
    return os.path.expanduser("~/.local/state/stt")


def temp_dir():
    return tempfile.gettempdir()
