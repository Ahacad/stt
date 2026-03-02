"""Hotkey capture dialog for changing the push-to-talk key combo."""

import threading

from stt.log import setup_logging

log = setup_logging("stt.hotkey_dialog")

# Canonical modifier order for hotkey strings
_MODIFIER_ORDER = ["ctrl", "shift", "alt", "cmd"]

# pynput Key names that map to modifier groups (left/right variants collapse)
_MODIFIER_MAP = {
    "ctrl_l": "ctrl", "ctrl_r": "ctrl",
    "shift_l": "shift", "shift_r": "shift", "shift": "shift",
    "alt_l": "alt", "alt_r": "alt", "alt": "alt",
    "alt_gr": "alt",
    "cmd_l": "cmd", "cmd_r": "cmd", "cmd": "cmd",
}


def key_to_str(key):
    """Convert a pynput Key or KeyCode to a string name.

    Key.ctrl_l → "ctrl", Key.f1 → "f1"
    KeyCode(char="s") → "s", KeyCode(vk=65) → "a"
    """
    # pynput.keyboard.Key enum members (modifiers, function keys, etc.)
    if hasattr(key, "name"):
        name = key.name
        if name in _MODIFIER_MAP:
            return _MODIFIER_MAP[name]
        # Function keys, special keys: strip Key. prefix
        return name.lower()

    # pynput.keyboard.KeyCode (regular characters)
    if hasattr(key, "char") and key.char is not None:
        return key.char.lower()

    # Fallback: vk code for held-modifier edge cases
    if hasattr(key, "vk") and key.vk is not None:
        # vk 65-90 = A-Z
        if 65 <= key.vk <= 90:
            return chr(key.vk).lower()
        return str(key.vk)

    return str(key)


def keys_to_hotkey_string(modifiers, key):
    """Build a pynput-compatible hotkey string from modifier set and a key.

    modifiers: set of modifier names like {"ctrl", "shift"}
    key: string name of the regular key like "s" or "f1"

    Returns: "<ctrl>+<shift>+s" with canonical modifier order.
    """
    parts = []
    for mod in _MODIFIER_ORDER:
        if mod in modifiers:
            parts.append(f"<{mod}>")
    # Wrap special/function keys in angle brackets
    if len(key) > 1:
        parts.append(f"<{key}>")
    else:
        parts.append(key)
    return "+".join(parts)


def validate_hotkey(hotkey_str):
    """Check if a hotkey string is valid for pynput.

    Returns True if pynput.keyboard.HotKey.parse() accepts it.
    """
    try:
        from pynput.keyboard import HotKey
        parsed = HotKey.parse(hotkey_str)
        return len(parsed) >= 2  # at least modifier + key
    except (ValueError, ImportError):
        return False


def show_hotkey_dialog(current_hotkey, callback):
    """Open a tkinter dialog to capture a new hotkey combo.

    Runs in a daemon thread (pystray owns the main thread on Windows).
    Calls callback(new_hotkey_str) on OK, callback(None) on Cancel/close.
    """
    def _run():
        try:
            _dialog(current_hotkey, callback)
        except Exception as e:
            log.error("hotkey dialog error: %s", e)
            callback(None)

    t = threading.Thread(target=_run, daemon=True)
    t.start()


def _dialog(current_hotkey, callback):
    import tkinter as tk
    from pynput import keyboard

    result = {"value": None}
    modifiers = set()
    capturing = False
    listener = None

    root = tk.Tk()
    root.title("Change Hotkey")
    root.geometry("320x180")
    root.resizable(False, False)

    tk.Label(root, text="Current hotkey:").pack(pady=(12, 0))
    current_label = tk.Label(root, text=current_hotkey, font=("", 12, "bold"))
    current_label.pack()

    preview_var = tk.StringVar(value="")
    preview_label = tk.Label(root, textvariable=preview_var, font=("", 11),
                             fg="#666666")
    preview_label.pack(pady=(4, 0))

    btn_frame = tk.Frame(root)
    btn_frame.pack(pady=8)

    def start_capture():
        nonlocal capturing, listener, modifiers
        capturing = True
        modifiers = set()
        capture_btn.config(text="Press keys...", state="disabled")
        preview_var.set("Waiting for input...")
        ok_btn.config(state="disabled")

        def on_press(key):
            nonlocal capturing
            if not capturing:
                return False

            name = key_to_str(key)
            if name in _MODIFIER_MAP.values():
                modifiers.add(name)
                preview_var.set(" + ".join(sorted(modifiers, key=lambda m: _MODIFIER_ORDER.index(m) if m in _MODIFIER_ORDER else 99)))
            else:
                # Non-modifier key pressed — finish capture
                if not modifiers:
                    preview_var.set("Need at least one modifier!")
                    return False
                hotkey_str = keys_to_hotkey_string(modifiers, name)
                preview_var.set(hotkey_str)
                if validate_hotkey(hotkey_str):
                    result["value"] = hotkey_str
                    ok_btn.config(state="normal")
                    preview_label.config(fg="#228B22")
                else:
                    preview_var.set(f"{hotkey_str} (invalid)")
                    preview_label.config(fg="#CC0000")
                capturing = False
                capture_btn.config(text="Press to capture...", state="normal")
                return False  # stop listener

        listener = keyboard.Listener(on_press=on_press)
        listener.start()

    def on_ok():
        if result["value"]:
            root.destroy()
            callback(result["value"])
        return

    def on_cancel():
        root.destroy()
        callback(None)

    capture_btn = tk.Button(btn_frame, text="Press to capture...",
                            command=start_capture, width=20)
    capture_btn.pack(side="left", padx=4)

    ok_btn = tk.Button(btn_frame, text="OK", command=on_ok, width=8,
                       state="disabled")
    ok_btn.pack(side="left", padx=4)

    cancel_btn = tk.Button(btn_frame, text="Cancel", command=on_cancel, width=8)
    cancel_btn.pack(side="left", padx=4)

    root.protocol("WM_DELETE_WINDOW", on_cancel)
    root.mainloop()
