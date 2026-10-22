@echo off
setlocal
cd /d "%~dp0..\..\"
py -3.13 -m unittest discover -s tools\tests -v
if errorlevel 1 goto gagal
cd /d "%~dp0code\backend"
.venv\Scripts\python.exe manage.py test --settings=config.test_settings --verbosity=1
if errorlevel 1 goto gagal
cd /d "%~dp0code\frontend"
call npm test
if errorlevel 1 goto gagal
call npm run build
if errorlevel 1 goto gagal
echo Seluruh pemeriksaan yang dijalankan selesai. Catat hasil aktual Windows pada docs/slr10.
pause
exit /b 0
:gagal
echo Pengujian belum lulus. Baca pesan kegagalan di atas; jangan menandai card selesai.
pause
exit /b 1
