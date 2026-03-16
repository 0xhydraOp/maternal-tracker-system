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

# Step 3: Run Inno Setup or create PowerShell installer
$isccPaths = @(
    "${env:ProgramFiles}\Inno Setup 6\ISCC.exe",
    "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
    (Get-Command iscc -ErrorAction SilentlyContinue).Source
)
$iscc = $null
foreach ($p in $isccPaths) {
    if ($p -and (Test-Path $p)) { $iscc = $p; break }
}

$distDir = Join-Path $projectRoot "dist"
if (-not (Test-Path $distDir)) { New-Item -ItemType Directory -Path $distDir -Force | Out-Null }

$innoSuccess = $false
if ($iscc) {
    Write-Host "`n[3/3] Compiling installer with Inno Setup..." -ForegroundColor Yellow
    Set-Location $projectRoot
    & $iscc "installer.iss"
    if ($LASTEXITCODE -eq 0) {
        $setupPath = Join-Path $distDir "MaternalTracker_Setup_1.0.0.exe"
        # Create zip for distribution
        $installTxt = Join-Path $distDir "Install_Instructions.txt"
        if (-not (Test-Path $installTxt)) {
            @"
Maternal Tracker System - Windows Installation
==============================================

1. Unzip this folder to your desired location (e.g. Desktop or Downloads)

2. Double-click: MaternalTracker_Setup_1.0.0.exe

3. Follow the installation wizard:
   - Accept the license
   - Choose install location (default: your user folder)
   - Optional: Create desktop shortcut
   - Click Install

4. Launch Maternal Tracker System from the Start Menu or desktop shortcut

Default login: admin / admin123
(Change the password after first login in Settings)
"@ | Out-File -FilePath $installTxt -Encoding utf8
        }
        $zipPath = Join-Path $distDir "MaternalTracker_Setup_1.0.0.zip"
        Compress-Archive -Path $setupPath, $installTxt -DestinationPath $zipPath -Force
        Write-Host "`nDone!" -ForegroundColor Green
        Write-Host "Installer: $setupPath" -ForegroundColor Green
        Write-Host "Zip (for distribution): $zipPath" -ForegroundColor Green
        $innoSuccess = $true
    } else {
        Write-Host "`nInno Setup compilation failed. Creating PowerShell installer..." -ForegroundColor Yellow
    }
}

if (-not $innoSuccess) {
    Write-Host "`n[3/3] Inno Setup not found. Creating PowerShell-based installer package..." -ForegroundColor Yellow
    Copy-Item (Join-Path $projectRoot "MaternalTracking.exe") (Join-Path $distDir "MaternalTracking.exe") -Force
    $psInstaller = Join-Path $distDir "Install_MaternalTracker.ps1"
    $script = @'
# Maternal Tracker System - Installer (run from same folder as MaternalTracking.exe)
$ErrorActionPreference = "Stop"
$appName = "Maternal Tracker System"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$exeSource = Join-Path $scriptDir "MaternalTracking.exe"
if (-not (Test-Path $exeSource)) { Write-Error "MaternalTracking.exe not found in $scriptDir"; exit 1 }
$installDir = Join-Path $env:LOCALAPPDATA $appName
if (-not (Test-Path $installDir)) { New-Item -ItemType Directory -Path $installDir -Force | Out-Null }
Copy-Item $exeSource (Join-Path $installDir "MaternalTracking.exe") -Force
$ws = New-Object -ComObject WScript.Shell
$shortcut = $ws.CreateShortcut((Join-Path ([Environment]::GetFolderPath("Desktop")) "$appName.lnk"))
$shortcut.TargetPath = Join-Path $installDir "MaternalTracking.exe"
$shortcut.WorkingDirectory = $installDir
$shortcut.Save()
Write-Host "Installed to $installDir" -ForegroundColor Green
Write-Host "Desktop shortcut created. Launch Maternal Tracker System from your Desktop." -ForegroundColor Cyan
'@
    [System.IO.File]::WriteAllText($psInstaller, $script)
    Write-Host "`nDone!" -ForegroundColor Green
    Write-Host "Installer package: $distDir" -ForegroundColor Green
    Write-Host "  - MaternalTracking.exe" -ForegroundColor Gray
    Write-Host "  - Install_MaternalTracker.ps1" -ForegroundColor Gray
    Write-Host "`nTo install: Run Install_MaternalTracker.ps1 from the dist folder" -ForegroundColor Cyan
}
