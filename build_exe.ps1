# Build Maternal Tracking System to .exe
# Run from project folder: .\build_exe.ps1

$ErrorActionPreference = "Stop"
$projectRoot = $PSScriptRoot
Set-Location $projectRoot

Write-Host "Building Maternal Tracking System..." -ForegroundColor Cyan

# Ensure assets/icon.png and icon.ico exist
$assetsDir = Join-Path $projectRoot "assets"
$iconPng = Join-Path $assetsDir "icon.png"
$iconIco = Join-Path $assetsDir "icon.ico"
if (-not (Test-Path $assetsDir)) { New-Item -ItemType Directory -Path $assetsDir -Force | Out-Null }
if (-not (Test-Path $iconPng)) {
    Write-Host "Creating icon.png..." -ForegroundColor Yellow
    python -c "from utils.icon_utils import ensure_icon_exists; ensure_icon_exists()"
}
if (-not (Test-Path $iconIco)) {
    Write-Host "Creating icon.ico for Windows..." -ForegroundColor Yellow
    pip install pillow -q 2>$null
    python -m scripts.create_icon_ico
}

# Install PyInstaller if needed
$pyinstaller = pip show pyinstaller 2>$null
if (-not $pyinstaller) {
    Write-Host "Installing PyInstaller..." -ForegroundColor Yellow
    pip install pyinstaller
}

# Build - output exe to project folder
Set-Location $projectRoot
pyinstaller --clean --noconfirm maternal_tracking.spec --distpath .

if ($LASTEXITCODE -eq 0) {
    $exePath = Join-Path $projectRoot "MaternalTracking.exe"
    Write-Host "`nDone! Executable: $exePath" -ForegroundColor Green
    Write-Host "`nNote: On first run, config.json and database/ will be created next to the exe." -ForegroundColor Gray
} else {
    Write-Host "`nBuild failed." -ForegroundColor Red
    exit 1
}
