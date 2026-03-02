"""Build stt.exe for Windows using PyInstaller.

Run on a Windows machine with NVIDIA GPU:
    pip install -e .[windows] pyinstaller
    python build_windows.py

Produces dist/stt/ folder. Zip it for distribution:
    powershell Compress-Archive -Path dist/stt -DestinationPath dist/stt-windows.zip
"""

import os
import shutil
import subprocess
import sys


def generate_icon():
    """Generate assets/icon.ico from the same drawing code as tray.py."""
    from PIL import Image, ImageDraw

    os.makedirs("assets", exist_ok=True)

    img = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    # Microphone body
    draw.rounded_rectangle([88, 32, 168, 144], radius=40, fill="#4CAF50")
    # Microphone arc
    draw.arc([64, 80, 192, 192], start=0, end=180, fill="#4CAF50", width=10)
    # Stand
    draw.line([128, 192, 128, 224], fill="#4CAF50", width=10)
    draw.line([96, 224, 160, 224], fill="#4CAF50", width=10)

    # Save as .ico with multiple sizes
    img.save(
        "assets/icon.ico",
        format="ICO",
        sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
    )
    print("Generated assets/icon.ico")


def find_ctranslate2_libs():
    """Find CTranslate2 shared libraries needed for faster-whisper."""
    import ctranslate2

    ct2_dir = os.path.dirname(ctranslate2.__file__)
    binaries = []
    for f in os.listdir(ct2_dir):
        if f.endswith((".dll", ".pyd", ".so")):
            binaries.append((os.path.join(ct2_dir, f), "ctranslate2"))
    return binaries


def find_cuda_libs():
    """Collect CUDA runtime DLLs bundled with packages (nvidia-* wheels)."""
    binaries = []
    site_packages = None
    for p in sys.path:
        if "site-packages" in p and os.path.isdir(p):
            site_packages = p
            break

    if not site_packages:
        return binaries

    # nvidia-* packages install CUDA libs under nvidia/<package>/
    nvidia_dir = os.path.join(site_packages, "nvidia")
    if os.path.isdir(nvidia_dir):
        for root, dirs, files in os.walk(nvidia_dir):
            for f in files:
                if f.endswith(".dll"):
                    # Flatten all DLLs into the output root
                    binaries.append((os.path.join(root, f), "."))

    return binaries


def build():
    if sys.platform != "win32":
        print("This script must be run on Windows.")
        sys.exit(1)

    generate_icon()

    ct2_binaries = find_ctranslate2_libs()
    cuda_binaries = find_cuda_libs()
    all_binaries = ct2_binaries + cuda_binaries

    # Build --add-binary args
    add_binary_args = []
    for src, dst in all_binaries:
        add_binary_args += ["--add-binary", f"{src}{os.pathsep}{dst}"]

    cmd = [
        "pyinstaller",
        "--name", "stt",
        "--windowed",
        "--icon", "assets/icon.ico",
        "--noconfirm",
        # Hidden imports that PyInstaller can't detect
        "--hidden-import", "faster_whisper",
        "--hidden-import", "ctranslate2",
        "--hidden-import", "sounddevice",
        "--hidden-import", "soundfile",
        "--hidden-import", "soxr",
        "--hidden-import", "pynput",
        "--hidden-import", "pynput.keyboard",
        "--hidden-import", "pynput.keyboard._win32",
        "--hidden-import", "pystray",
        "--hidden-import", "pystray._win32",
        "--hidden-import", "PIL",
        *add_binary_args,
        # Collect all data files for these packages
        "--collect-data", "faster_whisper",
        "--collect-data", "ctranslate2",
        # Entry point
        "src/stt/tray.py",
    ]

    print("Running:", " ".join(cmd[:10]), "...")
    subprocess.run(cmd, check=True)

    # Copy the generated icon into dist for the tray to use at runtime
    dist_assets = os.path.join("dist", "stt", "assets")
    os.makedirs(dist_assets, exist_ok=True)
    shutil.copy("assets/icon.ico", dist_assets)

    print()
    print("Build complete: dist/stt/")
    print("To create release zip:")
    print('  powershell Compress-Archive -Path dist/stt -DestinationPath dist/stt-windows.zip')


if __name__ == "__main__":
    build()
