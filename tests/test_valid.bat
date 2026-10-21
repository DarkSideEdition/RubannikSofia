@echo off
rem Этап 2: корректные параметры (закрывайте окно после просмотра)
chcp 65001 >nul
cd /d "%~dp0.."
set PYTHONUTF8=1
where py >nul 2>nul && (set PY=py -3) || (set PY=python)
echo [1] без параметров
%PY% src\emulator.py

echo [2] только --vfs
%PY% src\emulator.py --vfs vfs\minimal.csv

echo [3] только --script
%PY% src\emulator.py --script scripts\start_ok.txt

echo [4] --vfs и --script
%PY% src\emulator.py --vfs vfs\minimal.csv --script scripts\start_ok.txt

echo [5] скрипт с exit (окно закроется само)
%PY% src\emulator.py --script scripts\start_exit.txt

echo [6] --help
%PY% src\emulator.py --help
