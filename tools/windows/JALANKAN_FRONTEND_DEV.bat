@echo off
setlocal
cd /d "%~dp0..\..\code\frontend"
call npm run dev
pause