"""Test core transcription functions with mocked model."""

from unittest.mock import MagicMock, patch

import numpy as np


def test_transcribe_file_short_audio(tmp_path):
    """Audio shorter than 0.3s returns empty string."""
    import soundfile as sf

    from stt.core import transcribe_file

    wavpath = str(tmp_path / "short.wav")
    # 0.1s of audio at 16kHz = 1600 samples (below 4800 threshold)
    audio = np.zeros(1600, dtype=np.float32)
    sf.write(wavpath, audio, 16000, subtype="FLOAT")

    model = MagicMock()
    result = transcribe_file(model, wavpath)
    assert result == ""
    model.transcribe.assert_not_called()


def test_transcribe_file_returns_text(tmp_path):
    """Normal audio returns joined segment text."""
    import soundfile as sf

    from stt.core import transcribe_file

    wavpath = str(tmp_path / "speech.wav")
    # 1s of audio at 16kHz
    audio = np.random.randn(16000).astype(np.float32) * 0.1
    sf.write(wavpath, audio, 16000, subtype="FLOAT")

    seg1 = MagicMock()
    seg1.text = " hello "
    seg2 = MagicMock()
    seg2.text = " world "

    model = MagicMock()
    model.transcribe.return_value = ([seg1, seg2], None)

    result = transcribe_file(model, wavpath)
    assert result == "hello world"


def test_transcribe_file_resamples(tmp_path):
    """Audio at non-16kHz gets resampled."""
    import soundfile as sf

    from stt.core import transcribe_file

    wavpath = str(tmp_path / "48k.wav")
    # 1s at 48kHz
    audio = np.random.randn(48000).astype(np.float32) * 0.1
    sf.write(wavpath, audio, 48000, subtype="FLOAT")

    seg = MagicMock()
    seg.text = " resampled "
    model = MagicMock()
    model.transcribe.return_value = ([seg], None)

    result = transcribe_file(model, wavpath)
    assert result == "resampled"
    # Verify transcribe was called (audio was long enough after resampling)
    model.transcribe.assert_called_once()


def test_transcribe_file_stereo_to_mono(tmp_path):
    """Stereo audio gets converted to mono."""
    import soundfile as sf

    from stt.core import transcribe_file

    wavpath = str(tmp_path / "stereo.wav")
    audio = np.random.randn(16000, 2).astype(np.float32) * 0.1
    sf.write(wavpath, audio, 16000, subtype="FLOAT")

    seg = MagicMock()
    seg.text = " mono "
    model = MagicMock()
    model.transcribe.return_value = ([seg], None)

    result = transcribe_file(model, wavpath)
    assert result == "mono"


@patch("stt.core.WhisperModel")
def test_load_model_cuda(mock_whisper):
    from stt.core import load_model

    load_model("medium.en", device="cuda")
    mock_whisper.assert_called_once_with("medium.en", device="cuda", compute_type="float16")


@patch("stt.core.WhisperModel")
def test_load_model_cpu(mock_whisper):
    from stt.core import load_model

    load_model("tiny", device="cpu")
    mock_whisper.assert_called_once_with("tiny", device="cpu", compute_type="int8")
