"""Test hotkey dialog pure functions (no tkinter, no display)."""

from unittest.mock import MagicMock, patch

from stt.hotkey_dialog import key_to_str, keys_to_hotkey_string


# --- key_to_str ---

def test_key_to_str_regular_char():
    key = MagicMock(spec=["char", "vk"])
    key.char = "s"
    key.vk = 83
    assert key_to_str(key) == "s"


def test_key_to_str_uppercase_normalizes():
    key = MagicMock(spec=["char", "vk"])
    key.char = "S"
    key.vk = 83
    assert key_to_str(key) == "s"


def test_key_to_str_modifier_left():
    key = MagicMock(spec=["name"])
    key.name = "ctrl_l"
    assert key_to_str(key) == "ctrl"


def test_key_to_str_modifier_right():
    key = MagicMock(spec=["name"])
    key.name = "ctrl_r"
    assert key_to_str(key) == "ctrl"


def test_key_to_str_shift():
    key = MagicMock(spec=["name"])
    key.name = "shift"
    assert key_to_str(key) == "shift"


def test_key_to_str_function_key():
    key = MagicMock(spec=["name"])
    key.name = "f1"
    assert key_to_str(key) == "f1"


def test_key_to_str_special_key():
    key = MagicMock(spec=["name"])
    key.name = "space"
    assert key_to_str(key) == "space"


def test_key_to_str_vk_fallback():
    """KeyCode with no char but valid vk (held-modifier edge case)."""
    key = MagicMock(spec=["char", "vk"])
    key.char = None
    key.vk = 65
    assert key_to_str(key) == "a"


def test_key_to_str_vk_fallback_z():
    key = MagicMock(spec=["char", "vk"])
    key.char = None
    key.vk = 90
    assert key_to_str(key) == "z"


# --- keys_to_hotkey_string ---

def test_hotkey_string_basic():
    assert keys_to_hotkey_string({"ctrl", "shift"}, "s") == "<ctrl>+<shift>+s"


def test_hotkey_string_single_modifier():
    assert keys_to_hotkey_string({"alt"}, "r") == "<alt>+r"


def test_hotkey_string_canonical_order():
    """Modifiers always appear in ctrl, shift, alt, cmd order."""
    result = keys_to_hotkey_string({"cmd", "alt", "ctrl", "shift"}, "x")
    assert result == "<ctrl>+<shift>+<alt>+<cmd>+x"


def test_hotkey_string_function_key():
    result = keys_to_hotkey_string({"ctrl"}, "f1")
    assert result == "<ctrl>+<f1>"


def test_hotkey_string_special_key():
    result = keys_to_hotkey_string({"ctrl", "shift"}, "space")
    assert result == "<ctrl>+<shift>+<space>"


# --- validate_hotkey (mocked pynput — no display required) ---

def test_validate_default_hotkey():
    mock_hotkey = MagicMock()
    mock_hotkey.parse.return_value = frozenset(["ctrl", "shift", "s"])
    with patch.dict("sys.modules", {"pynput": MagicMock(), "pynput.keyboard": MagicMock(HotKey=mock_hotkey)}):
        from stt.hotkey_dialog import validate_hotkey
        assert validate_hotkey("<ctrl>+<shift>+s") is True


def test_validate_ctrl_alt():
    mock_hotkey = MagicMock()
    mock_hotkey.parse.return_value = frozenset(["ctrl", "alt", "r"])
    with patch.dict("sys.modules", {"pynput": MagicMock(), "pynput.keyboard": MagicMock(HotKey=mock_hotkey)}):
        from stt.hotkey_dialog import validate_hotkey
        assert validate_hotkey("<ctrl>+<alt>+r") is True


def test_validate_single_key_invalid():
    mock_hotkey = MagicMock()
    mock_hotkey.parse.return_value = frozenset(["s"])
    with patch.dict("sys.modules", {"pynput": MagicMock(), "pynput.keyboard": MagicMock(HotKey=mock_hotkey)}):
        from stt.hotkey_dialog import validate_hotkey
        assert validate_hotkey("s") is False


def test_validate_parse_raises():
    mock_hotkey = MagicMock()
    mock_hotkey.parse.side_effect = ValueError("bad")
    with patch.dict("sys.modules", {"pynput": MagicMock(), "pynput.keyboard": MagicMock(HotKey=mock_hotkey)}):
        from stt.hotkey_dialog import validate_hotkey
        assert validate_hotkey("garbage!!!") is False
