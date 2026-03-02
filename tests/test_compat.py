"""Test platform detection and path helpers."""

import os
import sys
from unittest.mock import patch

from stt.compat import LINUX, WINDOWS, data_dir, temp_dir


def test_platform_flags():
    if sys.platform == "linux":
        assert LINUX is True
        assert WINDOWS is False
    elif sys.platform == "win32":
        assert WINDOWS is True
        assert LINUX is False


def test_data_dir_linux():
    with patch("stt.compat.WINDOWS", False):
        result = data_dir()
        assert result == os.path.expanduser("~/.local/state/stt")


def test_data_dir_windows():
    with patch("stt.compat.WINDOWS", True), \
         patch.dict(os.environ, {"LOCALAPPDATA": "C:\\Users\\test\\AppData\\Local"}):
        result = data_dir()
        assert result == os.path.join("C:\\Users\\test\\AppData\\Local", "stt")


def test_data_dir_windows_fallback():
    with patch("stt.compat.WINDOWS", True), \
         patch.dict(os.environ, {}, clear=True):
        result = data_dir()
        assert "stt" in result


def test_temp_dir():
    result = temp_dir()
    assert os.path.isdir(result)
