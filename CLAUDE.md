# STT — Local Speech-to-Text for Linux & Windows

## What This Is

Offline push-to-talk dictation using faster-whisper + CUDA. Different architectures per platform sharing a common core.

## Architecture

**Linux** — multi-process daemon + clients over Unix socket:
```
stt-daemon (model in VRAM, Unix socket server)
  ↑ transcribe <path>
stt-toggle (hotkey → record WAV → send to daemon → xdotool type result)
```

**Windows** — single-process tray app with in-process model:
```
stt-tray (model in VRAM, system tray icon)
  hotkey → record thread → transcribe in-process → pynput type result
```

### Shared Core
- **Core** (`core.py`): `load_model()`, `transcribe_file()` — used by both daemon and tray
- **Audio** (`audio.py`): sounddevice recording, device discovery, RMS-based VAD
- **Output** (`output.py`): text input, notifications, sound — platform backends (xdotool/pynput, dunstify/PowerShell toast, paplay/winsound)
- **Config** (`config.py`): all constants centralized, platform-aware paths via `compat.py`
- **Compat** (`compat.py`): platform detection, `data_dir()`, `temp_dir()`

### Linux-Only
- **Daemon** (`daemon.py`): socket server wrapping `core.py`
- **Client** (`client.py`): socket client, text protocol
- **Toggle** (`toggle.py`): file-based state machine for push-to-talk hotkey
- **CLI** (`cli.py`): argparse dispatcher

### Windows-Only
- **Tray** (`tray.py`): system tray app with pystray, pynput hotkey, in-process transcription

## Tech Stack

- Python 3.11+, `uv` package manager, hatchling build
- faster-whisper, sounddevice, soundfile, soxr, numpy (<2)
- Linux: PulseAudio/PipeWire, xdotool, dunstify, paplay
- Windows (optional deps): pynput, pystray, Pillow
- pytest for testing

## Commands

```bash
uv tool install -e .           # install (dev)
uv tool install -e . --force   # update after changes
pytest                         # run tests
stt-daemon --model large-v3    # start daemon
stt-toggle                     # push-to-talk (bind to hotkey)
stt --record out.wav           # record audio
stt --transcribe out.wav       # transcribe file
```

## Project Layout

```
src/stt/          # all source code
  compat.py       # platform detection, path helpers
  config.py       # constants, paths, thresholds
  core.py         # model loading, transcription (shared)
  log.py          # dual logging (file=DEBUG, stderr=WARNING)
  output.py       # text input, notifications, sound (cross-platform)
  client.py       # Unix socket client (Linux)
  daemon.py       # socket server (Linux)
  audio.py        # recording, device resolution, VAD
  cli.py          # CLI entry point (Linux)
  toggle.py       # push-to-talk state machine (Linux)
  transcribe.py   # WAV → transcription → type (Linux)
  tray.py         # system tray app (Windows)
tests/            # pytest unit tests
```

## Code Conventions

### Style
- snake_case functions/variables, UPPER_CASE module constants
- Self-documenting names over comments. `resolve_device()` not `get_dev()`
- One-line docstrings for modules. No docstrings on obvious functions
- No type annotations in signatures unless they clarify ambiguity
- ~80-100 char lines, flexible
- No dead code, no commented-out blocks

### Patterns
- Constants centralized in `config.py` — never hardcode paths/thresholds elsewhere
- `log = setup_logging("stt.module")` at module top
- subprocess calls: `check=False` for non-critical (notifications, sounds), `check=True` for critical (xdotool)
- Resource cleanup via try/finally, signal handlers for daemon
- Socket protocol: plain text, one command per connection, `ERROR:` prefix for failures

### Error Handling
- Handle at boundaries (socket I/O, audio devices, file system)
- Let failures propagate inside call stacks
- Log before raising or returning empty
- Graceful degradation for UX (notifications fail silently, transcription errors get logged)

## Testing

### Running Tests
```bash
pytest              # all tests
pytest -x           # stop on first failure
pytest -v           # verbose
pytest tests/test_audio.py::test_resolve_by_name  # single test
```

### Test Conventions
- File per module: `test_audio.py` tests `audio.py`
- Mock external deps: `@patch("stt.audio.sd.query_devices", ...)`
- Use `tmp_path` fixture for temp files/sockets
- Test behavior, not implementation — if internals change, tests shouldn't break
- Descriptive test names: `test_resolve_skips_output_only` not `test_resolve_3`
- No integration tests yet — unit tests with mocked hardware/sockets

### TDD Workflow
1. Write a failing test that describes the desired behavior
2. Write minimal code to make it pass
3. Refactor if needed, re-run tests
4. Commit the test and implementation together

When fixing bugs: write a test that reproduces the bug first, then fix it. The test proves the fix works and prevents regression.

### What to Test
- Pure logic: device resolution, VAD thresholds, config paths
- State machines: toggle lock file transitions
- Protocol: socket client/server message handling
- Edge cases: missing devices, empty audio, malformed responses

### What Not to Test
- Subprocess calls to xdotool/dunstify (mock them)
- Actual audio hardware (mock sounddevice)
- Whisper model inference (mock in unit tests)

## Development Guidelines

### Adding Features
1. Does it need a new module or does it fit in an existing one?
2. Add constants to `config.py`, not inline
3. Write tests before or alongside implementation
4. Keep functions single-purpose — if it needs "and" in the description, split it

### Dependencies
- Minimize. This project has 5 core deps for a reason
- System tools (xdotool, paplay, pynput, winsound) are wrapped in `output.py` — add new ones there
- Never add a dep for something trivially implementable

### Commits
- One logical change per commit
- Message format: `verb + what + why` — "Add continuous VAD silence timeout config"
- Test and implementation in the same commit

### Code Review Checklist
- [ ] Constants in config.py, not hardcoded
- [ ] Logging uses setup_logging pattern
- [ ] Error handling at boundaries only
- [ ] Tests cover the new behavior
- [ ] No unnecessary abstractions or premature generalization
- [ ] Functions do one thing
- [ ] Names are self-documenting
