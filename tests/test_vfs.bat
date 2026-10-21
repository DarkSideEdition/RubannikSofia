@echo off
rem Этап 3: варианты VFS (минимальная, несколько файлов, 3+ уровня, битые)
chcp 65001 >nul
cd /d "%~dp0.."
set PYTHONUTF8=1
where py >nul 2>nul && (set PY=py -3) || (set PY=python)
echo [1] минимальная VFS
%PY% src\emulator.py --vfs vfs\minimal.csv --script scripts\start_vfs.txt

echo [2] несколько файлов (текст, base64, кавычки)
%PY% src\emulator.py --vfs vfs\several.csv --script scripts\start_vfs.txt

echo [3] три и более уровней вложенности
%PY% src\emulator.py --vfs vfs\deep.csv --script scripts\start_vfs.txt

echo [4] битые CSV (ошибки загрузки)
%PY% src\emulator.py --vfs vfs\broken_type.csv --script scripts\start_vfs.txt
%PY% src\emulator.py --vfs vfs\broken_base64.csv --script scripts\start_vfs.txt
%PY% src\emulator.py --vfs vfs\broken_header.csv --script scripts\start_vfs.txt
%PY% src\emulator.py --vfs vfs\broken_duplicate.csv --script scripts\start_vfs.txt
