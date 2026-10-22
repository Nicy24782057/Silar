@echo off
setlocal
cd /d "%~dp0..\..\"
py -3.13 tools\serve_frontend.py
pause
