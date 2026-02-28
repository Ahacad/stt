"""Test toggle lock file state machine."""

import os

import stt.config as cfg
from stt.toggle import _read_file, _remove


def test_read_file_missing(tmp_path):
    assert _read_file(str(tmp_path / "nonexistent")) == ""


def test_read_file_content(tmp_path):
    p = tmp_path / "test"
    p.write_text("hello\n")
    assert _read_file(str(p)) == "hello"


def test_remove_nonexistent(tmp_path):
    # Should not raise
    _remove(str(tmp_path / "a"), str(tmp_path / "b"))


def test_remove_existing(tmp_path):
    p = tmp_path / "test"
    p.write_text("x")
    _remove(str(p))
    assert not p.exists()


def test_lock_state_machine(tmp_path):
    """Simulate start/stop cycle with temp paths."""
    lock = str(tmp_path / "lock")
    pidfile = str(tmp_path / "pid")
    wavpath_file = str(tmp_path / "wavpath")

    # Initially no lock → start state
    assert not os.path.exists(lock)

    # Simulate start
    open(lock, "w").close()
    with open(pidfile, "w") as f:
        f.write("12345")
    with open(wavpath_file, "w") as f:
        f.write("/tmp/test.wav")

    assert os.path.exists(lock)

    # Simulate stop cleanup
    _remove(lock, pidfile)
    assert not os.path.exists(lock)
    assert not os.path.exists(pidfile)

    # Wavpath file still there for transcription
    assert _read_file(wavpath_file) == "/tmp/test.wav"
    _remove(wavpath_file)


def test_double_start_idempotent(tmp_path):
    """Creating lock twice doesn't error."""
    lock = str(tmp_path / "lock")
    open(lock, "w").close()
    open(lock, "w").close()
    assert os.path.exists(lock)


def test_double_stop_idempotent(tmp_path):
    """Removing already-removed lock doesn't error."""
    lock = str(tmp_path / "lock")
    _remove(lock)
    _remove(lock)
    assert not os.path.exists(lock)
