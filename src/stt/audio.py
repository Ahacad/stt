"""Audio device discovery, recording, and VAD."""

import queue
import signal
import sys
import threading

import numpy as np
import sounddevice as sd
import soundfile as sf

from stt.client import save_and_transcribe
from stt.config import (
    CHANNELS,
    DEFAULT_DEVICE,
    MIN_AUDIO_DURATION,
    SILENCE_DURATION,
    SILENCE_THRESHOLD,
)
from stt.log import setup_logging

log = setup_logging("stt.audio")


def resolve_device(device_id):
    """Resolve device name to index, or return int as-is."""
    if isinstance(device_id, int):
        return device_id
    if isinstance(device_id, str):
        for i, d in enumerate(sd.query_devices()):
            if device_id in d["name"].lower() and d["max_input_channels"] > 0:
                return i
    return sd.default.device[0]


def get_device_rate(device_id) -> int:
    idx = resolve_device(device_id)
    info = sd.query_devices(idx, "input")
    return int(info["default_samplerate"])


def list_devices():
    devices = sd.query_devices()
    pulse_idx = resolve_device("pulse")
    for i, d in enumerate(devices):
        if d["max_input_channels"] > 0:
            default = " *" if i == pulse_idx else ""
            print(
                f"  {i}: {d['name']} ({int(d['default_samplerate'])}Hz){default}"
            )


def record_until_stop(device_id):
    """Record from mic until Enter or Ctrl+C. Returns (audio, native_rate) or None."""
    dev_idx = resolve_device(device_id)
    native_rate = get_device_rate(device_id)
    audio_chunks = []
    stop = threading.Event()

    def callback(indata, frames, time_info, status):
        if status:
            log.warning("audio callback: %s", status)
        audio_chunks.append(indata.copy())

    log.debug("recording from device %d at %d Hz", dev_idx, native_rate)
    print("Recording... (press Enter to stop)", file=sys.stderr)
    stream = sd.InputStream(
        samplerate=native_rate,
        channels=CHANNELS,
        dtype="float32",
        callback=callback,
        device=dev_idx,
    )
    stream.start()

    def wait_enter():
        try:
            input()
        except EOFError:
            pass
        stop.set()

    t = threading.Thread(target=wait_enter, daemon=True)
    t.start()

    try:
        stop.wait()
    except KeyboardInterrupt:
        pass
    finally:
        stream.stop()
        stream.close()

    if not audio_chunks:
        return None
    raw = np.concatenate(audio_chunks, axis=0).flatten()
    return raw, native_rate


def record_to_file(outpath: str, device_id=DEFAULT_DEVICE):
    """Record to WAV file until SIGTERM/SIGINT."""
    dev_idx = resolve_device(device_id)
    native_rate = get_device_rate(device_id)
    audio_chunks = []
    stop = False

    def on_signal(sig, frame):
        nonlocal stop
        stop = True

    signal.signal(signal.SIGTERM, on_signal)
    signal.signal(signal.SIGINT, on_signal)

    def callback(indata, frames, time_info, status):
        audio_chunks.append(indata.copy())

    log.debug("recording to %s from device %d at %d Hz", outpath, dev_idx, native_rate)
    stream = sd.InputStream(
        samplerate=native_rate,
        channels=CHANNELS,
        dtype="float32",
        callback=callback,
        device=dev_idx,
    )
    stream.start()

    try:
        while not stop:
            sd.sleep(100)
    except KeyboardInterrupt:
        pass
    finally:
        stream.stop()
        stream.close()

    if audio_chunks:
        audio = np.concatenate(audio_chunks, axis=0)
        sf.write(outpath, audio, native_rate, subtype="FLOAT")
        log.info("saved %s (%d samples)", outpath, len(audio))


def record_to_file_cli():
    """Entry point for stt-record."""
    if len(sys.argv) < 2:
        print("Usage: stt-record <output.wav>", file=sys.stderr)
        sys.exit(1)
    record_to_file(sys.argv[1])


def continuous_mode(device_id, on_segment=None):
    """Listen and transcribe segments via VAD. Calls on_segment(text) for each."""
    dev_idx = resolve_device(device_id)
    native_rate = get_device_rate(device_id)
    chunk_duration = 0.1
    frames_per_chunk = int(native_rate * chunk_duration)
    silence_limit = int(SILENCE_DURATION / chunk_duration)
    min_frames = int(MIN_AUDIO_DURATION * native_rate)

    audio_buffer = []
    silence_frames = 0
    has_speech = False
    audio_q = queue.Queue()

    def callback(indata, frames, time_info, status):
        if status:
            log.warning("audio callback: %s", status)
        audio_q.put(indata.copy())

    log.info("continuous mode on device %d at %d Hz", dev_idx, native_rate)
    print("Listening... (Ctrl+C to stop)", file=sys.stderr)
    stream = sd.InputStream(
        samplerate=native_rate,
        channels=CHANNELS,
        dtype="float32",
        callback=callback,
        blocksize=frames_per_chunk,
        device=dev_idx,
    )
    stream.start()

    def flush_buffer():
        if not audio_buffer:
            return
        raw = np.concatenate(audio_buffer, axis=0).flatten()
        if len(raw) >= min_frames:
            text = save_and_transcribe(raw, native_rate)
            if text and on_segment:
                on_segment(text)
        audio_buffer.clear()

    try:
        while True:
            chunk = audio_q.get()
            rms = np.sqrt(np.mean(chunk**2))
            if rms > SILENCE_THRESHOLD:
                has_speech = True
                silence_frames = 0
                audio_buffer.append(chunk)
            elif has_speech:
                silence_frames += 1
                audio_buffer.append(chunk)
                if silence_frames >= silence_limit:
                    flush_buffer()
                    silence_frames = 0
                    has_speech = False
    except KeyboardInterrupt:
        flush_buffer()
    finally:
        stream.stop()
        stream.close()
        print("", file=sys.stderr)


if __name__ == "__main__":
    record_to_file_cli()
