@echo off
rem Этап 2: ошибки в стартовом скрипте
chcp 65001 >nul
cd /d "%~dp0.."
set PYTHONUTF8=1
where py >nul 2>nul && (set PY=py -3) || (set PY=python)
echo [1] --script с ошибками (ошибочные строки пропускаются)
%PY% src\emulator.py --script scripts\start_errors.txt

echo [2] --vfs и --script с ошибками
%PY% src\emulator.py --vfs vfs\minimal.csv --script scripts\start_errors.txt

echo [3] неизвестный параметр
%PY% src\emulator.py --unknown-option
