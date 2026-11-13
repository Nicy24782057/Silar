@echo off
setlocal
cd /d "%~dp0"
py -3.12 --version >nul 2>&1
if errorlevel 1 (
  echo Python 3.12 belum terbaca. Pasang Python 3.12 dan Python Launcher, lalu jalankan kembali.
  pause
  exit /b 1
)
py -3.12 tools\setup_silar.py
set "silar_setup_result=%errorlevel%"
if not "%silar_setup_result%"=="0" echo Setup belum selesai. Baca pesan langkah yang gagal di atas.
pause
exit /b %silar_setup_result%
