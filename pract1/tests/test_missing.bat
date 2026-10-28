@echo off
rem Этап 2: несуществующие пути и параметр без значения
chcp 65001 >nul
cd /d "%~dp0.."
set PYTHONUTF8=1
where py >nul 2>nul && (set PY=py -3) || (set PY=python)
echo [1] несуществующая VFS
%PY% src\emulator.py --vfs vfs\no_such_vfs.csv

echo [2] несуществующий скрипт
%PY% src\emulator.py --script scripts\no_such_script.txt

echo [3] оба пути несуществующие
%PY% src\emulator.py --vfs vfs\no_such_vfs.csv --script scripts\no_such_script.txt

echo [4] параметр без значения
%PY% src\emulator.py --vfs
