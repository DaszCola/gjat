@echo off
setlocal enabledelayedexpansion
title Gjat Downloader! Setup & Installer

echo ========================================================
echo             Gjat Downloader! - Installation
echo ========================================================
echo.

set "TARGET_DIR=%LOCALAPPDATA%\Programs\GjatDownloader"
set "DESKTOP_LNK=%USERPROFILE%\Desktop\Gjat Downloader!.lnk"
set "START_MENU=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Gjat Downloader!.lnk"
set "SOURCE_DIR=%~dp0"

echo [1/4] Preparing installation directory...
if not exist "%TARGET_DIR%" mkdir "%TARGET_DIR%"

echo [2/4] Installing application files to %TARGET_DIR%...
if exist "%SOURCE_DIR%dist\GjatDownloader.exe" (
    copy /Y "%SOURCE_DIR%dist\GjatDownloader.exe" "%TARGET_DIR%\GjatDownloader.exe" >nul
) else (
    echo Note: Building standalone exe or copying runtime files...
    copy /Y "%SOURCE_DIR%main.py" "%TARGET_DIR%\" >nul
    xcopy /E /I /Y "%SOURCE_DIR%core" "%TARGET_DIR%\core" >nul
    xcopy /E /I /Y "%SOURCE_DIR%ui" "%TARGET_DIR%\ui" >nul
)

if exist "%SOURCE_DIR%app_icon.ico" (
    copy /Y "%SOURCE_DIR%app_icon.ico" "%TARGET_DIR%\app_icon.ico" >nul
)
if exist "%SOURCE_DIR%bin" (
    xcopy /E /I /Y "%SOURCE_DIR%bin" "%TARGET_DIR%\bin" >nul
)

echo [3/4] Creating Desktop and Start Menu Shortcuts...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "$ws = New-Object -ComObject WScript.Shell; " ^
    "$exePath = '%TARGET_DIR%\GjatDownloader.exe'; " ^
    "if (-not (Test-Path $exePath)) { $exePath = 'pythonw.exe'; $args = '\"%TARGET_DIR%\main.py\"'; } else { $args = ''; }; " ^
    "$ico = '%TARGET_DIR%\app_icon.ico'; " ^
    "$s1 = $ws.CreateShortcut('%DESKTOP_LNK%'); " ^
    "$s1.TargetPath = $exePath; " ^
    "if ($args) { $s1.Arguments = $args; }; " ^
    "if (Test-Path $ico) { $s1.IconLocation = $ico; }; " ^
    "$s1.WorkingDirectory = '%TARGET_DIR%'; " ^
    "$s1.Save(); " ^
    "$s2 = $ws.CreateShortcut('%START_MENU%'); " ^
    "$s2.TargetPath = $exePath; " ^
    "if ($args) { $s2.Arguments = $args; }; " ^
    "if (Test-Path $ico) { $s2.IconLocation = $ico; }; " ^
    "$s2.WorkingDirectory = '%TARGET_DIR%'; " ^
    "$s2.Save(); "

echo [4/4] Creating Uninstaller...
(
    echo @echo off
    echo title Gjat Downloader! Uninstaller
    echo echo Uninstalling Gjat Downloader!...
    echo del /f /q "%DESKTOP_LNK%" 2^>nul
    echo del /f /q "%START_MENU%" 2^>nul
    echo rd /s /q "%TARGET_DIR%" 2^>nul
    echo echo Gjat Downloader! has been uninstalled successfully.
    echo pause
) > "%TARGET_DIR%\uninstall.bat"

echo.
echo ========================================================
echo     Installation Completed Successfully!
echo ========================================================
echo  * Installed to: %TARGET_DIR%
echo  * Desktop Shortcut created: Gjat Downloader!
echo  * Start Menu item created
echo  * Default Downloads folder: C:\Users\%USERNAME%\Videos\gjats
echo.
echo Launching Gjat Downloader!...
start "" "%DESKTOP_LNK%"
timeout /t 3 >nul
exit
