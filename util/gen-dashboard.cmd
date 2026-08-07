@echo off
REM Generate Markdown and HTML career dashboards for an external private data repository
if "%1"=="" (
    echo.
    echo Usage: gen-dashboard.cmd DATA_ROOT
    echo Example: gen-dashboard.cmd C:\Users\candidate\private-career-data
    pause
    exit /b 1
)
cd /d "%~dp0.."
python util\gen_dashboard.py --data-root "%~1"
if errorlevel 1 exit /b 1
python util\gen_dashboard.py --data-root "%~1" --format html --vscode
