"""Wrappers for text input, notifications, and sound playback."""

import subprocess

from stt.compat import WINDOWS
from stt.config import NOTIFY_ID


def type_text(text, window_id=None):
    if not text:
        return
    if WINDOWS:
        from pynput.keyboard import Controller
        Controller().type(text)
    elif window_id:
        # Text must already be on clipboard. Temporarily disable BSPWM's
        # focus_follows_pointer so it can't steal focus during the paste,
        # then activate target → ctrl+v → restore → re-enable.
        cur = subprocess.run(
            ["xdotool", "getactivewindow"],
            capture_output=True, text=True, check=False,
        )
        cur_id = cur.stdout.strip()
        ffp = subprocess.run(
            ["bspc", "config", "focus_follows_pointer"],
            capture_output=True, text=True, check=False,
        )
        had_ffp = ffp.stdout.strip() == "true"
        try:
            if had_ffp:
                subprocess.run(
                    ["bspc", "config", "focus_follows_pointer", "false"],
                    check=False,
                )
            subprocess.run([
                "xdotool",
                "windowactivate", "--sync", window_id,
                "key", "--clearmodifiers", "ctrl+shift+v",
            ], check=False)
            if cur_id and cur_id != window_id:
                subprocess.run([
                    "xdotool", "windowactivate", "--sync", cur_id,
                ], check=False)
        finally:
            if had_ffp:
                subprocess.run(
                    ["bspc", "config", "focus_follows_pointer", "true"],
                    check=False,
                )
    else:
        subprocess.run(
            ["xdotool", "type", "--clearmodifiers", "--", text], check=False,
        )


def copy_to_clipboard(text):
    if not text:
        return
    if WINDOWS:
        subprocess.run(
            ["powershell", "-Command", f"Set-Clipboard -Value '{text}'"],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    else:
        subprocess.run(
            ["xclip", "-selection", "clipboard"],
            input=text.encode(),
            check=False,
        )


def notify(title, body, timeout=2000, urgency="low"):
    if WINDOWS:
        # PowerShell toast notification
        ps = (
            f"[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, "
            f"ContentType = WindowsRuntime] | Out-Null; "
            f"$xml = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent(0); "
            f"$text = $xml.GetElementsByTagName('text'); "
            f"$text[0].AppendChild($xml.CreateTextNode('{title} - {body}')) | Out-Null; "
            f"$toast = [Windows.UI.Notifications.ToastNotification]::new($xml); "
            f"[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier('STT').Show($toast)"
        )
        subprocess.run(
            ["powershell", "-Command", ps],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    else:
        subprocess.run(
            ["dunstify", "-r", NOTIFY_ID, "-t", str(timeout), "-u", urgency, title, body],
            check=False,
        )


def play_sound(path):
    if WINDOWS:
        import winsound
        winsound.MessageBeep()
    else:
        subprocess.Popen(
            ["paplay", path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
