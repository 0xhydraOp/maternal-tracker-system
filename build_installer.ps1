# Build Maternal Tracker System installer
# Prerequisites: Python, PyInstaller, Inno Setup 6 (https://jrsoftware.org/isinfo.php)
# Run from project folder: .\build_installer.ps1

$ErrorActionPreference = "Stop"
$projectRoot = $PSScriptRoot

Write-Host "Building Maternal Tracker System Installer..." -ForegroundColor Cyan

# Step 1: Build the .exe
Write-Host "`n[1/3] Building executable..." -ForegroundColor Yellow
& "$projectRoot\build_exe.ps1"
if ($LASTEXITCODE -ne 0) { exit 1 }

# Step 2: Ensure icon.ico exists for installer
$iconIco = Join-Path $projectRoot "assets\icon.ico"
if (-not (Test-Path $iconIco)) {
    Write-Host "`n[2/3] Creating icon.ico from icon.png..." -ForegroundColor Yellow
    Set-Location $projectRoot
    python -m scripts.create_icon_ico
} else {
    Write-Host "`n[2/3] Icon.ico OK" -ForegroundColor Gray
}

# Verify required files exist
$requiredFiles = @(
    (Join-Path $projectRoot "MaternalTracking.exe"),
    (Join-Path $projectRoot "WELCOME.txt"),
    (Join-Path $projectRoot "LICENSE.txt"),
    (Join-Path $projectRoot "assets\icon.ico")
)
foreach ($f in $requiredFiles) {
    if (-not (Test-Path $f)) {
        Write-Host "`nMissing required file: $f" -ForegroundColor Red
        exit 1
    }
}

# Step 3: Run Inno Setup
$isccPaths = @(
    "${env:ProgramFiles}\Inno Setup 6\ISCC.exe",
    "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe"
)
$iscc = $null
foreach ($p in $isccPaths) {
    if (Test-Path $p) { $iscc = $p; break }
}

if (-not $iscc) {
    Write-Host "`nInno Setup 6 not found. Please install from: https://jrsoftware.org/isinfo.php" -ForegroundColor Red
    Write-Host "Typical paths: C:\Program Files\Inno Setup 6\ or C:\Program Files (x86)\Inno Setup 6\" -ForegroundColor Gray
    exit 1
}

Write-Host "`n[3/3] Compiling installer with Inno Setup..." -ForegroundColor Yellow
$distDir = Join-Path $projectRoot "dist"
if (-not (Test-Path $distDir)) { New-Item -ItemType Directory -Path $distDir -Force | Out-Null }

Set-Location $projectRoot
& $iscc "installer.iss"

if ($LASTEXITCODE -eq 0) {
    $setupPath = Join-Path $distDir "MaternalTracker_Setup_1.0.0.exe"
    Write-Host "`nDone!" -ForegroundColor Green
    Write-Host "Installer: $setupPath" -ForegroundColor Green
} else {
    Write-Host "`nInstaller compilation failed." -ForegroundColor Red
    exit 1
}
