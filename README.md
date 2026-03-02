# stt

Local speech-to-text for Linux and Windows. Uses [faster-whisper](https://github.com/SYSTRAN/faster-whisper) with CUDA to transcribe speech in real time, entirely offline.

A daemon keeps the Whisper model loaded in VRAM. You talk, it transcribes — either printing to stdout or typing directly into the focused window via xdotool. Bind a hotkey and you get push-to-talk dictation anywhere on your desktop.

## How it works

```
stt-toggle (hotkey)          stt (CLI)
     |                          |
     v                          v
stt-record ──> WAV ──> stt-daemon (GPU, model in VRAM)
                              |
                              v
                     transcribed text
                              |
                     ┌────────┴────────┐
                     v                 v
                  stdout          xdotool type
```

The daemon loads the model once and stays resident. Transcription requests come over a Unix socket. Cold start is slow (model load); after that, inference is fast.

## Requirements

- Linux with PulseAudio (or PipeWire-Pulse)
- NVIDIA GPU with CUDA (or use `--cpu`, but it's slow)
- Python 3.11+
- [uv](https://docs.astral.sh/uv/)
- `xdotool` — for typing text into windows
- `dunstify` — for desktop notifications (from [dunst](https://dunst-project.org/))
- `paplay` — for sound feedback (from PulseAudio)

## Install

```bash
git clone https://github.com/Ahacad/stt.git
cd stt
uv tool install -e .
```

This puts five commands on your PATH: `stt`, `stt-daemon`, `stt-record`, `stt-toggle`, `stt-transcribe`.

To update after pulling changes:

```bash
uv tool install -e . --force
```

## Usage

### Start the daemon

```bash
stt start                  # background, waits until ready
stt-daemon                 # foreground (useful for debugging)
stt-daemon -m large-v3     # different model
stt-daemon --cpu           # no GPU
```

### Transcribe

```bash
stt                        # record until Enter, print text
stt -t                     # record until Enter, type into focused window
stt -c                     # continuous mode — listen, segment by silence, print
stt -c -t                  # continuous + type
```

### Daemon management

```bash
stt status                 # check if daemon is running
stt start                  # start daemon in background
stt stop                   # shut down daemon
```

### List audio devices

```bash
stt -l                     # shows input devices, * marks current default
stt -d 5                   # use device index 5
stt -d "usb"              # match device by name substring
```

## Hotkey setup (push-to-talk)

`stt-toggle` implements a two-press workflow: first press starts recording, second press stops and transcribes. The result is typed into whatever window has focus.

### sxhkd

```
# ~/.config/sxhkd/sxhkdrc
super + v
    stt-toggle
```

### Hyprland

```
# ~/.config/hypr/hyprland.conf
bind = SUPER, V, exec, stt-toggle
```

### i3/sway

```
# ~/.config/i3/config or ~/.config/sway/config
bindsym $mod+v exec stt-toggle
```

## Configuration

No config files. Constants live in `src/stt/config.py` — edit directly if you need to change:

- `DEFAULT_DEVICE` — audio input device (default: `"pulse"`)
- `SILENCE_THRESHOLD` — VAD sensitivity for continuous mode
- `SILENCE_DURATION` — seconds of silence before a segment ends
- Notification sounds, socket path, etc.

## Logging

All components log to `~/.local/state/stt/stt.log` (DEBUG level). Stderr only gets WARNING+, so your terminal stays clean.

```bash
tail -f ~/.local/state/stt/stt.log
```

## Windows

### Requirements

- Windows 10 or later
- NVIDIA GPU with up-to-date drivers

### Install

1. Download `stt-windows.zip` from [Releases](https://github.com/Ahacad/stt/releases)
2. Extract to any folder
3. Double-click `stt.exe`

### Usage

- A microphone icon appears in the system tray
- Press **Ctrl+Shift+S** to start recording
- Press **Ctrl+Shift+S** again to stop — transcribed text is typed into the focused window
- Right-click the tray icon for settings

### Configuration

Right-click tray > Settings opens the config file (`%LOCALAPPDATA%\stt\config.toml`):

- `model` — Whisper model name (default: `large-v3`)
- `device` — `cuda` or `cpu` (default: `cuda`)
- `hotkey` — key combination (default: `<ctrl>+<shift>+s`)

### Building from source

Requires Python 3.11+, NVIDIA GPU, and CUDA drivers on a Windows machine:

```powershell
git clone https://github.com/Ahacad/stt.git
cd stt
pip install -e .[windows] pyinstaller
python build_windows.py
```

This produces `dist/stt/stt.exe`. To create a release zip:

```powershell
Compress-Archive -Path dist/stt -DestinationPath dist/stt-windows.zip
```

The Whisper model (~3GB) is not bundled — it downloads automatically on first run.

## Project structure

```
src/stt/
  compat.py      platform detection, path helpers
  config.py      shared constants and paths
  core.py        model loading, transcription (shared by daemon + tray)
  log.py         logging setup
  output.py      text input, notifications, sound (cross-platform)
  client.py      socket client for talking to daemon (Linux)
  daemon.py      socket server, transcription service (Linux)
  audio.py       device discovery, recording, VAD
  cli.py         main stt CLI entry point (Linux)
  toggle.py      hotkey toggle, push-to-talk (Linux)
  transcribe.py  transcribe WAV + type result (Linux)
  tray.py        system tray app (Windows)
```

## License

MIT
