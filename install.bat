@echo off
:: Enable UTF-8 encoding
chcp 65001 >nul
setlocal EnableDelayedExpansion

:: Ensure we are in a writable directory (User's home or temp)
set "TARGET_DIR=%USERPROFILE%\WiFiWalkie"
if not exist "%TARGET_DIR%" mkdir "%TARGET_DIR%"
cd /d "%TARGET_DIR%"

set "APP_URL=https://raw.githubusercontent.com/ashwanthvijay1234-debug/wifi_walkie/main/netmsg.py"
set "CLASSIC_URL=https://raw.githubusercontent.com/ashwanthvijay1234-debug/wifi_walkie/main/wifi_walkie.py"

:DrawHeader
cls
echo.
echo    ╭────────────────────────────────────────────────────╮
echo    │                                                    │
echo    │            WI-FI WALKIE-TALKIE INSTALLER           │
echo    │                 Powered by OpenClaw                │
echo    │                                                    │
echo    ╰────────────────────────────────────────────────────╯
echo.
echo    Installing to: %TARGET_DIR%
echo.
goto :eof

:PrintStep
set "MSG=%~1"
echo   [ * ] %MSG%
timeout /t 1 /nobreak >nul
goto :eof

call :DrawHeader

:: Step 1: Check Python
call :PrintStep "Checking for Python..."
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo   [ X ] ERROR: Python is not installed or not in PATH.
    echo         Please install Python from python.org first.
    pause
    exit /b 1
)
echo   [ + ] Python found!

:: Step 2: Install Dependencies
call :PrintStep "Installing required libraries..."
python -m pip install --upgrade pip --quiet
pip install cryptography --quiet
if %errorlevel% neq 0 (
    echo   [ ! ] Warning: Could not auto-install cryptography.
) else (
    echo   [ + ] Cryptography installed!
)

:: Step 3: Download/Update Files
call :PrintStep "Downloading latest version..."
curl -sS -o "netmsg.py" "%APP_URL%"
curl -sS -o "wifi_walkie.py" "%CLASSIC_URL%"

if not exist "netmsg.py" (
    echo   [ X ] ERROR: Failed to download netmsg.py
    pause
    exit /b 1
)

:: Final Screen
cls
echo.
echo    ╭────────────────────────────────────────────────────╮
echo    │                                                    │
echo    │               INSTALLATION COMPLETE!               │
echo    │                                                    │
echo    │           You are ready to talk on Wi-Fi.          │
echo    │                                                    │
echo    ╰────────────────────────────────────────────────────╯
echo.
echo    [ 1 ] Launch NetMsg (New, Stable Protocol)
echo    [ 2 ] Launch Wi-Fi Walkie (Classic UI)
echo.
set /p choice="Choice [1]: "
if "%choice%"=="" set choice=1

if "%choice%"=="1" (
    echo   [ ^> ] Launching NetMsg...
    timeout /t 1 /nobreak >nul
    python netmsg.py
) else (
    echo   [ ^> ] Launching Wi-Fi Walkie Classic...
    timeout /t 1 /nobreak >nul
    python wifi_walkie.py
)

pause
