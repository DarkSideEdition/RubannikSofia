@echo off
rem Запуск эмулятора: run.bat [--vfs PATH] [--script PATH]
chcp 65001 >nul
cd /d "%~dp0"
set PYTHONUTF8=1
where py >nul 2>nul && (set PY=py -3) || (set PY=python)
%PY% src\emulator.py %*
