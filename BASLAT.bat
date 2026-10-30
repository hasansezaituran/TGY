@echo off
cd /d "%~dp0"
where py >nul 2>&1
if errorlevel 1 (
  python baslat.py
) else (
  py -3 baslat.py
)
if errorlevel 1 pause
