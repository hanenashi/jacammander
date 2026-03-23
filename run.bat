@echo off
title Jacammander Launcher

echo Waking up the LAN goblin...
cd /d "%~dp0"

:: Run the main python script
python main.py

:: If the app crashes, this prevents the window from instantly vanishing
pause