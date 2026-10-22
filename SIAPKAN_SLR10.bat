@echo off
setlocal
cd /d "%~dp0"
py -3.13 tools\setup_slr10.py
if errorlevel 1 echo Setup belum selesai. Baca pesan di atas.
pause
