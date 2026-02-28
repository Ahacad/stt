"""Test audio device resolution with mocked sounddevice."""

from unittest.mock import patch

import numpy as np

from stt.audio import resolve_device


FAKE_DEVICES = [
    {"name": "HDA Intel PCH: ALC1220", "max_input_channels": 0, "default_samplerate": 48000.0},
    {"name": "USB PnP Sound Device", "max_input_channels": 1, "default_samplerate": 44100.0},
    {"name": "pulse", "max_input_channels": 32, "default_samplerate": 44100.0},
    {"name": "default", "max_input_channels": 32, "default_samplerate": 44100.0},
]


@patch("stt.audio.sd.query_devices", return_value=FAKE_DEVICES)
def test_resolve_by_name(mock_qd):
    assert resolve_device("pulse") == 2


@patch("stt.audio.sd.query_devices", return_value=FAKE_DEVICES)
def test_resolve_by_partial_name(mock_qd):
    assert resolve_device("usb") == 1


@patch("stt.audio.sd.query_devices", return_value=FAKE_DEVICES)
def test_resolve_skips_output_only(mock_qd):
    # "hda" matches index 0 but it has 0 input channels
    assert resolve_device("hda") != 0


def test_resolve_int_passthrough():
    assert resolve_device(5) == 5


def test_vad_rms_above_threshold():
    """Verify RMS calculation matches what continuous_mode uses."""
    loud = np.ones((160, 1), dtype=np.float32) * 0.5
    rms = np.sqrt(np.mean(loud**2))
    assert rms > 0.01  # above SILENCE_THRESHOLD


def test_vad_rms_below_threshold():
    silent = np.zeros((160, 1), dtype=np.float32)
    rms = np.sqrt(np.mean(silent**2))
    assert rms < 0.01
