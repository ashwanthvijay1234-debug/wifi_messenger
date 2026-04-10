@echo off
setlocal EnableDelayedExpansion

:: Wi-Fi Walkie-Talkie One-Line Installer
:: A fun, quote-filled installation experience!
:: Also available as a one-liner: curl -sS bit.ly/4dXwrfl | python

color 0B
cls

:: ASCII Art Header
echo.
echo.
echo       ╔═══════════════════════════════════════════╗
echo       ║     📻  Wi-Fi Walkie-Talkie Installer  📻     ║
echo       ║         Friendly Local Chat App           ║
echo       ╚═══════════════════════════════════════════╝
echo.
echo.
echo   💡 Pro Tip: You can also install with one command:
echo      curl -sS bit.ly/4dXwrfl ^| python
echo.

:: Array of tech quotes
set "quotes[0]=^"The advance of technology is based on making it fit in so that you don't really even notice it, so it's part of everyday life.^" - Bill Gates"
set "quotes[1]=^"Technology is best when it brings people together.^" - Matt Mullenweg"
set "quotes[2]=^"It's not a bug, it's a feature!^" - Unknown"
set "quotes[3]=^"The most damaging phrase in the language is: 'We've always done it this way.'^" - Grace Hopper"
set "quotes[4]=^"Simplicity is the soul of efficiency.^" - Austin Freeman"
set "quotes[5]=^"Talk is cheap. Show me the code.^" - Linus Torvalds"
set "quotes[6]=^"The computer was born to solve problems that did not exist before.^" - Bill Gates"
set "quotes[7]=^"Programming isn't about what you know; it's about what you can figure out.^" - Chris Pine"

:: Function to show random quote
:show_quote
set /a "quote_num=!random! %% 8"
echo.
echo 💡 !quotes[%quote_num%]!
echo.
timeout /t 2 /nobreak >nul
goto :eof

:: Check for Python
echo [1/5] 🔍 Checking for Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo ❌ Python not found! Please install Python from https://python.org
    echo.
    echo 💡 Tip: Make sure to check "Add Python to PATH" during installation!
    echo.
    pause
    exit /b 1
)
echo ✅ Python found! 
call :show_quote

:: Check for pip
echo [2/5] 🔧 Checking for pip package manager...
python -m pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ pip not found! Installing ensurepip...
    python -m ensurepip --upgrade
) else (
    echo ✅ pip is ready!
)
call :show_quote

:: Upgrade pip (for best compatibility)
echo [3/5] 📦 Upgrading pip for best performance...
python -m pip install --upgrade pip --quiet
if %errorlevel% equ 0 (
    echo ✅ Pip upgraded successfully!
) else (
    echo ⚠️  Could not upgrade pip, but continuing anyway...
)
call :show_quote

:: Install cryptography library
echo [4/5] 🔐 Installing encryption library (cryptography)...
echo    This enables secure Secret Mode conversations!
python -m pip install cryptography --quiet
if %errorlevel% equ 0 (
    echo ✅ Cryptography library installed!
) else (
    echo ❌ Failed to install cryptography. Please run: pip install cryptography
    pause
    exit /b 1
)
call :show_quote

:: Create requirements.txt if it doesn't exist
if not exist requirements.txt (
    echo [5/5] 📝 Creating requirements file...
    echo cryptography>=42.0.0 > requirements.txt
    echo ✅ Requirements file created!
) else (
    echo [5/5] ✅ Requirements file already exists!
)
call :show_quote

:: Final success message
cls
echo.
echo.
echo       ╔═══════════════════════════════════════════╗
echo       ║          🎉 Installation Complete! 🎉        ║
echo       ╚═══════════════════════════════════════════╝
echo.
echo.
echo   ✨ Wi-Fi Walkie-Talkie is ready to use!
echo.
echo   📋 What's installed:
echo      • cryptography library (for Secret Mode encryption)
echo      • All dependencies configured
echo.
echo   🚀 How to run:
echo      python wifi_walkie.py
echo.
echo   💡 Quick Tips:
echo      • Make sure you're on the same Wi-Fi as your friends
echo      • Public Mode = Open chat for everyone
echo      • Secret Mode = Encrypted chat with a shared password
echo.
echo   ^"The future belongs to those who believe in the beauty of their dreams.^" - Eleanor Roosevelt
echo.
echo.
pause

:: Optional: Ask if user wants to run the app now
echo.
set /p "run_now=Would you like to start Wi-Fi Walkie-Talkie now? (Y/N): "
if /i "%run_now%"=="Y" (
    echo.
    echo 🚀 Starting Wi-Fi Walkie-Talkie...
    echo.
    python wifi_walkie.py
) else (
    echo.
    echo 👋 See you later! Run 'python wifi_walkie.py' anytime to start chatting!
    echo.
)

endlocal
