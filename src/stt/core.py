"""Core transcription functions shared by daemon and tray app."""

import numpy as np
import soundfile as sf
import soxr
from faster_whisper import WhisperModel

from stt.config import WHISPER_RATE
from stt.log import setup_logging

log = setup_logging("stt.core")


def load_model(model_name, device="cuda"):
    compute_type = "float16" if device == "cuda" else "int8"
    log.info("loading model '%s' on %s (%s)", model_name, device, compute_type)
    model = WhisperModel(model_name, device=device, compute_type=compute_type)
    log.info("model ready")
    return model


def transcribe_file(model, path):
    audio, sr = sf.read(path, dtype="float32")
    if audio.ndim > 1:
        audio = audio[:, 0]
    if sr != WHISPER_RATE:
        audio = soxr.resample(audio, sr, WHISPER_RATE).astype(np.float32)
    if len(audio) < WHISPER_RATE * 0.3:
        return ""
    segments, _ = model.transcribe(audio, beam_size=5, vad_filter=True)
    return " ".join(seg.text.strip() for seg in segments)
