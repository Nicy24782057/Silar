@echo off
setlocal
cd /d "%~dp0..\..\code\backend"
powershell -NoProfile -Command "Get-ChildItem '.\private_outbox\*.eml' | Sort-Object LastWriteTime -Descending | Select-Object -First 1 | ForEach-Object { notepad.exe $_.FullName }"
pause
