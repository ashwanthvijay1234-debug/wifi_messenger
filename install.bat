@echo off
:: Enable UTF-8 encoding
chcp 65001 >nul
setlocal EnableDelayedExpansion

:: DEFINITIVE TARGET: Use a dedicated folder in the user's home directory
set "RUN_DIR=%USERPROFILE%\WiFiWalkie"
if not exist "!RUN_DIR!" mkdir "!RUN_DIR!"
cd /d "!RUN_DIR!"

set "APP_URL=https://raw.githubusercontent.com/ashwanthvijay1234-debug/wifi_walkie/main/netmsg.py"
set "CLASSIC_URL=https://raw.githubusercontent.com/ashwanthvijay1234-debug/wifi_walkie/main/wifi_walkie.py"

:DrawHeader
cls
echo.
echo    ╭────────────────────────────────────────────────────╮
echo    │                                                    │
echo    │            WI-FI WALKIE-TALKIE INSTALLER           │
echo    │                                                 
echo    │                                                    │
echo    ╰────────────────────────────────────────────────────╯
echo.
echo    Current Directory: !RUN_DIR!
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
:: Use explicit full paths for curl output to be 100% sure
curl -sS -L -o "!RUN_DIR!\netmsg.py" "%APP_URL%"
curl -sS -L -o "!RUN_DIR!\wifi_walkie.py" "%CLASSIC_URL%"

if not exist "!RUN_DIR!\netmsg.py" (
    echo   [ X ] ERROR: Failed to download netmsg.py to !RUN_DIR!
    echo         Please check your internet connection.
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

:: Explicitly change directory one last time before launch
cd /d "!RUN_DIR!"

if "%choice%"=="1" (
    if exist "!RUN_DIR!\netmsg.py" (
        echo   [ ^> ] Launching NetMsg...
        python "!RUN_DIR!\netmsg.py"
    ) else (
        echo   [ X ] Error: netmsg.py not found in !RUN_DIR!
    )
) else (
    if exist "!RUN_DIR!\wifi_walkie.py" (
        echo   [ ^> ] Launching Wi-Fi Walkie Classic...
        python "!RUN_DIR!\wifi_walkie.py"
    ) else (
        echo   [ X ] Error: wifi_walkie.py not found in !RUN_DIR!
    )
)

pause
