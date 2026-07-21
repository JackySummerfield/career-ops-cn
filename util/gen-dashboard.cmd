@echo off
REM Generate Career Dashboard — double-click to run
cd /d "%~dp0.."
python util\gen_dashboard.py --user %1 --vscode
if "%1"=="" (
    echo.
    echo Usage: gen-dashboard.cmd USERNAME
    echo Example: gen-dashboard.cmd JackyTao
    pause
)
