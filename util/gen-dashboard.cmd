@echo off
REM Generate Markdown and HTML career dashboards — double-click to run
if "%1"=="" (
    echo.
    echo Usage: gen-dashboard.cmd USERNAME
    echo Example: gen-dashboard.cmd demo_user
    pause
    exit /b 1
)
cd /d "%~dp0.."
python util\gen_dashboard.py --user %1
if errorlevel 1 exit /b 1
python util\gen_dashboard.py --user %1 --format html --vscode
