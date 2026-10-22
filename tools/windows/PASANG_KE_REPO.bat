@echo off
setlocal
cd /d "%~dp0..\..\"
py -3.13 tools\install_slr10.py
if errorlevel 1 echo Pemasangan belum selesai. Baca pesan di atas.
pause
