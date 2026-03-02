"""Test tray app config and hotkey binding."""

import os
from unittest.mock import MagicMock, patch

from stt.tray import _write_config


def test_read_config_defaults_when_missing(tmp_path):
    """Config file doesn't exist — should create it with defaults."""
    config_path = str(tmp_path / "config.toml")
    with patch("stt.tray.CONFIG_PATH", config_path), \
         patch("stt.hotkey_dialog.validate_hotkey", return_value=True):
        from stt.tray import _read_config
        config = _read_config()
    assert config["model"] == "large-v3"
    assert config["device"] == "cuda"
    assert config["hotkey"] == "<ctrl>+<shift>+s"
    assert os.path.exists(config_path)


def test_read_config_parses_values(tmp_path):
    config_path = str(tmp_path / "config.toml")
    with open(config_path, "w") as f:
        f.write('model = "base"\ndevice = "cpu"\nhotkey = "<alt>+r"\n')
    with patch("stt.tray.CONFIG_PATH", config_path), \
         patch("stt.hotkey_dialog.validate_hotkey", return_value=True):
        from stt.tray import _read_config
        config = _read_config()
    assert config["model"] == "base"
    assert config["device"] == "cpu"
    assert config["hotkey"] == "<alt>+r"


def test_read_config_invalid_hotkey_falls_back(tmp_path):
    config_path = str(tmp_path / "config.toml")
    with open(config_path, "w") as f:
        f.write('hotkey = "garbage"\n')
    with patch("stt.tray.CONFIG_PATH", config_path), \
         patch("stt.hotkey_dialog.validate_hotkey", return_value=False):
        from stt.tray import _read_config
        config = _read_config()
    assert config["hotkey"] == "<ctrl>+<shift>+s"


def test_write_config_roundtrip(tmp_path):
    config_path = str(tmp_path / "config.toml")
    original = {"model": "tiny", "device": "cpu", "hotkey": "<ctrl>+<alt>+r"}

    with patch("stt.tray.CONFIG_PATH", config_path):
        _write_config(original)

    with patch("stt.tray.CONFIG_PATH", config_path), \
         patch("stt.hotkey_dialog.validate_hotkey", return_value=True):
        from stt.tray import _read_config
        loaded = _read_config()

    assert loaded["model"] == "tiny"
    assert loaded["device"] == "cpu"
    assert loaded["hotkey"] == "<ctrl>+<alt>+r"


def _make_pynput_mocks():
    """Create linked pynput/pynput.keyboard mocks for import patching."""
    mock_ghk = MagicMock()
    mock_keyboard = MagicMock()
    mock_keyboard.GlobalHotKeys.return_value = mock_ghk
    mock_pynput = MagicMock()
    mock_pynput.keyboard = mock_keyboard
    return mock_pynput, mock_keyboard, mock_ghk


def test_bind_hotkey_stops_old_listener():
    from stt.tray import STTApp
    app = STTApp.__new__(STTApp)
    app.recording = False
    old_listener = MagicMock()
    app.hotkey_listener = old_listener

    mock_pynput, mock_keyboard, mock_ghk = _make_pynput_mocks()
    with patch.dict("sys.modules", {"pynput": mock_pynput, "pynput.keyboard": mock_keyboard}):
        app._bind_hotkey("<ctrl>+<shift>+s")

    old_listener.stop.assert_called_once()
    mock_ghk.start.assert_called_once()


def test_bind_hotkey_starts_new_listener():
    from stt.tray import STTApp
    app = STTApp.__new__(STTApp)
    app.recording = False
    app.hotkey_listener = None

    mock_pynput, mock_keyboard, mock_ghk = _make_pynput_mocks()
    with patch.dict("sys.modules", {"pynput": mock_pynput, "pynput.keyboard": mock_keyboard}):
        app._bind_hotkey("<ctrl>+<shift>+s")

    assert app.hotkey_listener == mock_ghk
    mock_ghk.start.assert_called_once()
