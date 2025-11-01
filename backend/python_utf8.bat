@echo off
REM Force UTF-8 mode for Python
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1
set LANG=en_US.UTF-8
set LC_ALL=en_US.UTF-8

cd /d "%~dp0"
venv\Scripts\python.exe %*

