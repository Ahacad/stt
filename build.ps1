# build.ps1 — One-command Windows build for stt.exe
#
# Usage:
#     .\build.ps1
#
# Prerequisites:
#     - Python 3.11+ (python.org installer, NOT Microsoft Store)
#     - NVIDIA GPU with up-to-date drivers (nvidia-smi)
#
# Creates:
#     dist/stt/stt.exe        standalone app
#     dist/stt-windows.zip    release archive

$ErrorActionPreference = "Stop"

# --- Check Python ---
$py = Get-Command python -ErrorAction SilentlyContinue
if (-not $py) {
    Write-Host "ERROR: python not found on PATH" -ForegroundColor Red
    Write-Host "Install Python 3.11+ from https://www.python.org/downloads/"
    exit 1
}

$pyVersion = python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>&1
$pyPath = python -c "import sys; print(sys.executable)" 2>&1

# Detect Microsoft Store stub
if ($pyPath -like "*WindowsApps*") {
    Write-Host "ERROR: Detected Microsoft Store Python stub at $pyPath" -ForegroundColor Red
    Write-Host "Install Python from https://www.python.org/downloads/ instead"
    exit 1
}

$major, $minor = $pyVersion -split '\.'
if ([int]$major -lt 3 -or ([int]$major -eq 3 -and [int]$minor -lt 11)) {
    Write-Host "ERROR: Python 3.11+ required, found $pyVersion" -ForegroundColor Red
    exit 1
}
Write-Host "Python $pyVersion at $pyPath" -ForegroundColor Green

# --- Check NVIDIA driver ---
$nvsmi = Get-Command nvidia-smi -ErrorAction SilentlyContinue
if ($nvsmi) {
    $gpuInfo = nvidia-smi --query-gpu=name,driver_version --format=csv,noheader 2>&1
    Write-Host "GPU: $gpuInfo" -ForegroundColor Green
} else {
    Write-Host "WARNING: nvidia-smi not found — CUDA acceleration may not work" -ForegroundColor Yellow
    Write-Host "Install NVIDIA drivers from https://www.nvidia.com/Download/index.aspx"
}

# --- Create build venv ---
$venvDir = ".venv-build"
if (Test-Path $venvDir) {
    Write-Host "Removing old build venv..."
    Remove-Item -Recurse -Force $venvDir
}

Write-Host "`nCreating build venv at $venvDir..."
python -m venv $venvDir
$pip = Join-Path $venvDir "Scripts\pip.exe"
$python = Join-Path $venvDir "Scripts\python.exe"

# --- Install dependencies ---
Write-Host "`nInstalling dependencies..."
& $pip install --upgrade pip --quiet
& $pip install -e ".[windows]" pyinstaller nvidia-cublas-cu12 nvidia-cudnn-cu12 --quiet
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: pip install failed" -ForegroundColor Red
    exit 1
}
Write-Host "Dependencies installed" -ForegroundColor Green

# --- Run build ---
Write-Host "`nBuilding exe..."
& $python build_windows.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: build_windows.py failed" -ForegroundColor Red
    exit 1
}

# --- Verify output ---
$exePath = "dist\stt\stt.exe"
if (-not (Test-Path $exePath)) {
    Write-Host "ERROR: $exePath not found after build" -ForegroundColor Red
    exit 1
}

# --- Create zip ---
$zipPath = "dist\stt-windows.zip"
if (Test-Path $zipPath) {
    Remove-Item $zipPath
}
Write-Host "`nCreating release zip..."
Compress-Archive -Path "dist\stt" -DestinationPath $zipPath

# --- Summary ---
$exeSize = [math]::Round((Get-Item $exePath).Length / 1MB, 1)
$dllCount = (Get-ChildItem "dist\stt\*.dll" -ErrorAction SilentlyContinue).Count
$zipSize = [math]::Round((Get-Item $zipPath).Length / 1MB, 1)

Write-Host "`n--- Build Summary ---" -ForegroundColor Cyan
Write-Host "  Exe:  $exePath ($exeSize MB)"
Write-Host "  DLLs: $dllCount in dist/stt/"
Write-Host "  Zip:  $zipPath ($zipSize MB)"
Write-Host "---------------------" -ForegroundColor Cyan
Write-Host "`nDone!" -ForegroundColor Green
