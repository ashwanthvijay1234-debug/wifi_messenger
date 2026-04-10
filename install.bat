@echo off
setlocal EnableDelayedExpansion

:: ==========================================
::               CONFIGURATION
:: ==========================================
set "APP_URL=https://raw.githubusercontent.com/ashwanthvijay1234-debug/wifi_walkie/main/wifi_walkie.py"
set "APP_NAME=wifi_walkie.py"
set "WIDTH=80"

:: ==========================================
::         HELPER FUNCTIONS FOR UI
:: ==========================================

:: Draw a wide box header
:DrawHeader
echo.
echo ┌──────────────────────────────────────────────────────────────────────────┐
echo │                                                                          │
echo │                      📻 WI-FI WALKIE-TALKIE INSTALLER                    │
echo │                          Powered by OpenClaw Style                       │
echo │                                                                          │
echo └──────────────────────────────────────────────────────────────────────────┘
echo.
goto :eof

:: Print a colored step message
:PrintStep
set "MSG=%~1"
set "COLOR=%~2"
if "%COLOR%"=="" set "COLOR=07"
color %COLOR%
echo.
echo ■ %MSG%
timeout /t 1 /nobreak >nul
goto :eof

:: Print a quote
:PrintQuote
set "Q_TEXT=%~1"
set "Q_AUTH=%~2"
echo.
echo   💬 "%Q_TEXT%"
echo      - %Q_AUTH%
echo.
timeout /t 2 /nobreak >nul
goto :eof

:: ==========================================
::        MAIN INSTALLATION LOGIC
:: ==========================================

cls
call :DrawHeader
color 0B

:: Step 1: Check Python
call :PrintStep "1/5 🔍 Checking for Python installation..." "0B"
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ ERROR: Python is not installed or not in PATH.
    echo    Please install Python from python.org first.
    pause
    exit /b 1
)
echo ✅ Python found!

:: Step 2: First Quote
call :PrintQuote "Software is eating the world." "Marc Andreessen"

:: Step 3: Install Cryptography
call :PrintStep "2/5 🔧 Upgrading pip & installing cryptography..." "0B"
python -m pip install --upgrade pip --quiet
pip install cryptography --quiet
if %errorlevel% neq 0 (
    echo ⚠️  Warning: Could not auto-install cryptography. You may need to run 'pip install cryptography' manually.
) else (
    echo ✅ Cryptography library installed successfully!
)

:: Step 4: Second Quote
call :PrintQuote "First, solve the problem. Then, write the code." "John Johnson"

:: Step 5: Download App
call :PrintStep "3/5 📥 Downloading Wi-Fi Walkie-Talkie application..." "0B"
curl -sS -o "%APP_NAME%" "%APP_URL%"
if exist "%APP_NAME%" (
    echo ✅ Application downloaded successfully!
) else (
    echo ❌ ERROR: Failed to download the application.
    echo    Please check your internet connection.
    pause
    exit /b 1
)

:: Step 6: Third Quote
call :PrintQuote "Simplicity is the soul of efficiency." "Austin Freeman"

:: Step 7: Create Requirements
call :PrintStep "4/5 📝 Creating requirements.txt..." "0B"
echo cryptography>requirements.txt
echo ✅ Requirements file created.

:: Step 8: Final Quote
call :PrintQuote "Make it work, make it right, make it fast." "Kent Beck"

:: Final Screen
cls
color 0A
echo.
echo ┌──────────────────────────────────────────────────────────────────────────┐
echo │                                                                          │
echo │                      🎉 INSTALLATION COMPLETE! 🎉                       │
echo │                                                                          │
echo │                     You are ready to talk on Wi-Fi!                      │
echo │                                                                          │
echo └──────────────────────────────────────────────────────────────────────────┘
echo.
echo    🚀 Launching Wi-Fi Walkie-Talkie now...
echo.
timeout /t 2 /nobreak >nul

:: Launch the app
python "%APP_NAME%"

:: If the app closes, pause
pause
