@echo off
title Launching CYBER NOVA: ODYSSEY
echo Starting CYBER NOVA: ODYSSEY...
where py >nul 2>nul
if %errorlevel% equ 0 (
    py main.py
) else (
    python main.py
)
if %errorlevel% neq 0 (
    echo.
    echo Press any key to exit...
    pause >nul
)
