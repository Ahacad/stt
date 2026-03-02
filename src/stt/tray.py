"""Windows system tray app for speech-to-text."""

import os
import threading

from stt.compat import temp_dir
from stt.config import CONFIG_PATH, DEFAULT_HOTKEY, DEFAULT_MODEL
from stt.core import load_model, transcribe_file
from stt.log import setup_logging
from stt.output import notify, play_sound, type_text

log = setup_logging("stt.tray")

DEFAULT_CONFIG = f"""\
model = "{DEFAULT_MODEL}"
device = "cuda"
hotkey = "{DEFAULT_HOTKEY}"
"""


def _read_config():
    config = {"model": DEFAULT_MODEL, "device": "cuda", "hotkey": DEFAULT_HOTKEY}
    if not os.path.exists(CONFIG_PATH):
        os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
        with open(CONFIG_PATH, "w") as f:
            f.write(DEFAULT_CONFIG)
        return config

    with open(CONFIG_PATH) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, _, val = line.partition("=")
                key = key.strip()
                val = val.strip().strip('"').strip("'")
                if key in config:
                    config[key] = val

    # Validate hotkey — fall back to default if invalid
    from stt.hotkey_dialog import validate_hotkey
    if not validate_hotkey(config["hotkey"]):
        log.warning("invalid hotkey %r in config, using default %s",
                    config["hotkey"], DEFAULT_HOTKEY)
        config["hotkey"] = DEFAULT_HOTKEY

    return config


def _write_config(config):
    """Write config dict back to config.toml."""
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        for key, val in config.items():
            f.write(f'{key} = "{val}"\n')


def _make_icon():
    from PIL import Image, ImageDraw

    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    # Microphone body
    draw.rounded_rectangle([22, 8, 42, 36], radius=10, fill="#4CAF50")
    # Microphone arc
    draw.arc([16, 20, 48, 48], start=0, end=180, fill="#4CAF50", width=3)
    # Stand
    draw.line([32, 48, 32, 56], fill="#4CAF50", width=3)
    draw.line([24, 56, 40, 56], fill="#4CAF50", width=3)
    return img


class STTApp:
    def __init__(self):
        self.model = None
        self.recording = False
        self.stop_event = threading.Event()
        self.record_thread = None
        self._current_wav = None
        self.hotkey_listener = None
        self.config = _read_config()

    def start(self):
        import pystray

        notify("STT", "Loading model...")
        log.info("loading model %s on %s", self.config["model"], self.config["device"])
        self.model = load_model(self.config["model"], self.config["device"])
        notify("STT", f"Ready. Press {self.config['hotkey']} to dictate.")

        self._bind_hotkey(self.config["hotkey"])

        menu = pystray.Menu(
            pystray.MenuItem("About", self._on_about),
            pystray.MenuItem("Change Hotkey", self._on_change_hotkey),
            pystray.MenuItem("Open Config", self._on_open_config),
            pystray.MenuItem("Quit", self._on_quit),
        )

        self.icon = pystray.Icon("STT", icon=_make_icon(), title="STT", menu=menu)
        log.info("tray app started")
        self.icon.run()

    def _bind_hotkey(self, hotkey_str):
        """Stop old hotkey listener and start a new one."""
        import pynput.keyboard

        if self.hotkey_listener:
            self.hotkey_listener.stop()
            self.hotkey_listener = None

        self.hotkey_listener = pynput.keyboard.GlobalHotKeys(
            {hotkey_str: self._on_toggle}
        )
        self.hotkey_listener.start()
        log.info("hotkey bound: %s", hotkey_str)

    def _on_hotkey_changed(self, new_hotkey):
        """Callback from hotkey dialog."""
        if new_hotkey is None:
            # Cancelled — re-bind old hotkey
            self._bind_hotkey(self.config["hotkey"])
            log.info("hotkey change cancelled")
            return

        old = self.config["hotkey"]
        self.config["hotkey"] = new_hotkey
        _write_config(self.config)
        self._bind_hotkey(new_hotkey)
        notify("STT", f"Hotkey changed: {new_hotkey}")
        log.info("hotkey changed from %s to %s", old, new_hotkey)

    def _on_change_hotkey(self, icon, item):
        from stt.hotkey_dialog import show_hotkey_dialog

        # Stop current listener to prevent double-firing during capture
        if self.hotkey_listener:
            self.hotkey_listener.stop()
            self.hotkey_listener = None

        show_hotkey_dialog(self.config["hotkey"], self._on_hotkey_changed)

    def _on_toggle(self):
        if not self.recording:
            self._start_recording()
        else:
            self._stop_recording()

    def _start_recording(self):
        from stt.audio import record_to_file

        self.recording = True
        self.stop_event.clear()
        play_sound(None)
        notify("STT", "Recording...")

        wavpath = os.path.join(temp_dir(), f"stt-{os.getpid()}.wav")
        self._current_wav = wavpath
        self.record_thread = threading.Thread(
            target=record_to_file,
            args=(wavpath,),
            kwargs={"stop_event": self.stop_event},
            daemon=True,
        )
        self.record_thread.start()
        log.info("recording started: %s", wavpath)

    def _stop_recording(self):
        self.stop_event.set()
        if self.record_thread:
            self.record_thread.join(timeout=5)
        self.recording = False
        play_sound(None)

        wavpath = self._current_wav
        self._current_wav = None

        if not wavpath or not os.path.exists(wavpath):
            notify("STT", "No audio file produced")
            return

        log.info("transcribing %s", wavpath)
        try:
            text = transcribe_file(self.model, wavpath)
        except Exception as e:
            log.error("transcription failed: %s", e)
            notify("STT", f"Error: {e}")
            return
        finally:
            try:
                os.unlink(wavpath)
            except FileNotFoundError:
                pass

        if text:
            type_text(text)
            notify("STT", f"Typed: {text[:60]}")
            log.info("typed: %s", text[:80])
        else:
            notify("STT", "No speech detected")
            log.debug("no speech detected")

    def _on_about(self, icon, item):
        notify("STT", "Local speech-to-text. github.com/Ahacad/stt")

    def _on_open_config(self, icon, item):
        os.startfile(CONFIG_PATH)

    def _on_quit(self, icon, item):
        log.info("quit requested")
        if self.hotkey_listener:
            self.hotkey_listener.stop()
        self.icon.stop()


def main():
    app = STTApp()
    app.start()


if __name__ == "__main__":
    main()
