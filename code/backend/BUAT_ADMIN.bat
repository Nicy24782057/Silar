@echo off
setlocal
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (
  echo Jalankan SETUP_LOKAL.bat terlebih dahulu.
  pause
  exit /b 1
)
.venv\Scripts\python.exe manage.py create_silar_admin
pause
