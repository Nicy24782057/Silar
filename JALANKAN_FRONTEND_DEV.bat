@echo off
setlocal
cd /d "%~dp0code\frontend"
call npm run dev
pause
