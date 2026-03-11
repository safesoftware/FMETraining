@echo off
setlocal enabledelayedexpansion

echo ============================================
echo  FME Training Automation - Launcher
echo ============================================
echo.

:: Run from script directory so relative paths work
cd /d "%~dp0"

:: -----------------------------------------------
:: 1. Find Python
:: -----------------------------------------------
set "PYTHON="

python --version >nul 2>&1
if not errorlevel 1 set "PYTHON=python"

if "!PYTHON!"=="" (
    py --version >nul 2>&1
    if not errorlevel 1 set "PYTHON=py"
)

if "!PYTHON!"=="" (
    echo ERROR: Python not found.
    echo        Install Python 3.9 or later from https://www.python.org/downloads/
    echo        Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b 1
)

:: Require Python 3.9+
!PYTHON! -c "import sys; sys.exit(0 if sys.version_info >= (3,9) else 1)" >nul 2>&1
if errorlevel 1 (
    for /f "tokens=*" %%v in ('!PYTHON! --version 2^>^&1') do (
        echo ERROR: Python 3.9 or later is required. Found: %%v
    )
    pause
    exit /b 1
)
for /f "tokens=*" %%v in ('!PYTHON! --version 2^>^&1') do echo [OK] %%v

:: -----------------------------------------------
:: 2. Check .env
:: -----------------------------------------------
if not exist ".env" (
    if exist ".env.sample" (
        echo.
        echo WARNING: No .env file found. Creating one from .env.sample...
        copy ".env.sample" ".env" >nul
        echo.
        echo ACTION REQUIRED:
        echo   Open .env and set your OPENAI_API_KEY, then re-run this script.
        echo.
        echo Opening .env in Notepad now...
        start notepad ".env"
        pause
        exit /b 1
    ) else (
        echo.
        echo ERROR: .env not found and .env.sample is also missing.
        echo        Create a .env file with at least: OPENAI_API_KEY=your_key_here
        pause
        exit /b 1
    )
)

:: Check OPENAI_API_KEY is present and not the placeholder
set "KEY_OK=0"
for /f "usebackq tokens=1,* delims==" %%a in (".env") do (
    if /i "%%a"=="OPENAI_API_KEY" (
        if not "%%b"=="" (
            if not "%%b"=="your_openai_api_key_here" (
                set "KEY_OK=1"
            )
        )
    )
)
if "!KEY_OK!"=="0" (
    echo.
    echo ERROR: OPENAI_API_KEY is missing or still set to the placeholder in .env.
    echo        Open .env and replace "your_openai_api_key_here" with your actual key.
    echo.
    echo Opening .env in Notepad now...
    start notepad ".env"
    pause
    exit /b 1
)
echo [OK] .env

:: -----------------------------------------------
:: 3. Check / install Python requirements
:: -----------------------------------------------
echo Checking Python requirements...
!PYTHON! -c "import openai, bs4, pandas, dotenv, requests, tqdm" >nul 2>&1
if errorlevel 1 (
    echo Some packages are missing. Installing from requirements.txt...
    echo.
    !PYTHON! -m pip install -r requirements.txt
    if errorlevel 1 (
        echo.
        echo ERROR: pip install failed. See the output above for details.
        pause
        exit /b 1
    )
    echo.
    echo [OK] Requirements installed.
) else (
    echo [OK] Requirements satisfied.
)

:: -----------------------------------------------
:: 4. Free port 8080 if already in use
:: -----------------------------------------------
set "PORT=8080"
for /f "tokens=5" %%p in ('netstat -ano 2^>nul ^| findstr "LISTENING" ^| findstr ":!PORT! "') do (
    echo Port !PORT! is already in use (PID %%p^). Stopping existing process...
    taskkill /PID %%p /F >nul 2>&1
)

:: -----------------------------------------------
:: 5. Launch server and open browser
:: -----------------------------------------------
echo.
echo Starting server at http://localhost:!PORT! ...
echo Press Ctrl+C to stop.
echo.

:: Open browser after a short delay so the server has time to bind
start "" "http://localhost:!PORT!/"

!PYTHON! serve.py !PORT!
