@echo off
title Gjat Downloader!
cd /d "%~dp0"
echo Starting Gjat Downloader!...
python main.py
if errorlevel 1 (
    echo.
    echo An error occurred while launching. Press any key to exit.
    pause >nul
)
