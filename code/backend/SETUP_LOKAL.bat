@echo off
setlocal
cd /d "%~dp0"
py -3.12 --version >nul 2>&1
if not errorlevel 1 (
  py -3.12 scripts\setup_local.py
  goto done
)
py -3.13 --version >nul 2>&1
if not errorlevel 1 (
  py -3.13 scripts\setup_local.py
  goto done
)
python scripts\setup_local.py
:done
if errorlevel 1 echo Setup belum selesai. Baca pesan di atas.
pause
