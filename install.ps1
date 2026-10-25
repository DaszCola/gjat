# Gjat Downloader! One-Click Installer
$ErrorActionPreference = "Stop"

$AppName = "Gjat Downloader!"
$TargetDir = Join-Path $env:LOCALAPPDATA "Programs\GjatDownloader"
$DesktopLnk = Join-Path ([Environment]::GetFolderPath("Desktop")) "$AppName.lnk"
$StartMenuDir = Join-Path ([Environment]::GetFolderPath("StartMenu")) "Programs"
$StartMenuLnk = Join-Path $StartMenuDir "$AppName.lnk"
$SourceDir = $PSScriptRoot

Write-Host "========================================================" -ForegroundColor Magenta
Write-Host "            Gjat Downloader! - Installation              " -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Magenta
Write-Host ""

# 1. Create target directory
if (-not (Test-Path $TargetDir)) {
    New-Item -ItemType Directory -Path $TargetDir -Force | Out-Null
}

# 2. Copy Executable
$ExeSource = Join-Path $SourceDir "dist\GjatDownloader.exe"
$ExeTarget = Join-Path $TargetDir "GjatDownloader.exe"

if (Test-Path $ExeSource) {
    Write-Host "[1/4] Installing GjatDownloader.exe to $TargetDir..." -ForegroundColor Green
    Copy-Item -Path $ExeSource -Destination $ExeTarget -Force
} else {
    Write-Host "[1/4] Copying application files..." -ForegroundColor Yellow
    Copy-Item -Path (Join-Path $SourceDir "main.py") -Destination $TargetDir -Force
    Copy-Item -Path (Join-Path $SourceDir "core") -Destination (Join-Path $TargetDir "core") -Recurse -Force
    Copy-Item -Path (Join-Path $SourceDir "ui") -Destination (Join-Path $TargetDir "ui") -Recurse -Force
}

# 3. Copy Icon
$IconSource = Join-Path $SourceDir "app_icon.ico"
$IconTarget = Join-Path $TargetDir "app_icon.ico"
if (Test-Path $IconSource) {
    Copy-Item -Path $IconSource -Destination $IconTarget -Force
}

# 4. Copy Binaries (yt-dlp.exe etc)
$BinSource = Join-Path $SourceDir "bin"
if (Test-Path $BinSource) {
    Copy-Item -Path $BinSource -Destination (Join-Path $TargetDir "bin") -Recurse -Force
}

# 5. Create Shortcuts
Write-Host "[2/4] Creating Desktop Shortcut..." -ForegroundColor Green
$WScriptShell = New-Object -ComObject WScript.Shell

$Shortcut = $WScriptShell.CreateShortcut($DesktopLnk)
$Shortcut.TargetPath = $ExeTarget
$Shortcut.WorkingDirectory = $TargetDir
if (Test-Path $IconTarget) {
    $Shortcut.IconLocation = "$IconTarget,0"
}
$Shortcut.Save()

Write-Host "[3/4] Creating Start Menu Shortcut..." -ForegroundColor Green
if (-not (Test-Path $StartMenuDir)) {
    New-Item -ItemType Directory -Path $StartMenuDir -Force | Out-Null
}
$StartMenuShortcut = $WScriptShell.CreateShortcut($StartMenuLnk)
$StartMenuShortcut.TargetPath = $ExeTarget
$StartMenuShortcut.WorkingDirectory = $TargetDir
if (Test-Path $IconTarget) {
    $StartMenuShortcut.IconLocation = "$IconTarget,0"
}
$StartMenuShortcut.Save()

# 6. Create Uninstaller
Write-Host "[4/4] Creating Uninstaller..." -ForegroundColor Green
$UninstallerScript = @"
@echo off
title Gjat Downloader! Uninstaller
echo Uninstalling Gjat Downloader!...
del /f /q "$DesktopLnk" 2>nul
del /f /q "$StartMenuLnk" 2>nul
rd /s /q "$TargetDir" 2>nul
echo Gjat Downloader! has been uninstalled successfully.
pause
"@
Set-Content -Path (Join-Path $TargetDir "uninstall.bat") -Value $UninstallerScript

Write-Host ""
Write-Host "========================================================" -ForegroundColor Magenta
Write-Host "     Installation Completed Successfully!               " -ForegroundColor Green
Write-Host "========================================================" -ForegroundColor Magenta
Write-Host " * Executable: $ExeTarget"
Write-Host " * Desktop Shortcut: $DesktopLnk"
Write-Host " * Start Menu: $StartMenuLnk"
Write-Host " * Default Downloads: C:\Users\$env:USERNAME\Videos\gjats"
Write-Host ""
Write-Host "You can now launch Gjat Downloader! from your Desktop or Start Menu." -ForegroundColor Cyan
