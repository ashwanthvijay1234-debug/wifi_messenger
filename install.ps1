# Wi-Fi Walkie-Talkie One-Line Installer (PowerShell)
# A fun, quote-filled installation experience!
# Also available as a one-liner: irm bit.ly/4dXwrfl | iex

$Host.UI.RawUI.WindowTitle = "📻 Wi-Fi Walkie-Talkie Installer"
Clear-Host

# Color scheme
$WarningColor = [ConsoleColor]::Yellow
$SuccessColor = [ConsoleColor]::Green
$InfoColor = [ConsoleColor]::Cyan
$ErrorColor = [ConsoleColor]::Red

# ASCII Art Header
Write-Host ""
Write-Host ""
Write-Host "       ╔═══════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "       ║     📻  Wi-Fi Walkie-Talkie Installer  📻     ║" -ForegroundColor Cyan
Write-Host "       ║         Friendly Local Chat App           ║" -ForegroundColor Cyan
Write-Host "       ╚═══════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""
Write-Host ""
Write-Host "   💡 Pro Tip: You can also install with one command:" -ForegroundColor Yellow
Write-Host "      irm bit.ly/4dXwrfl | iex" -ForegroundColor White
Write-Host ""

# Tech quotes array
$quotes = @(
    '"The advance of technology is based on making it fit in so that you don't really even notice it, so it's part of everyday life." - Bill Gates',
    '"Technology is best when it brings people together." - Matt Mullenweg',
    '"It''s not a bug, it''s a feature!" - Unknown',
    '"The most damaging phrase in the language is: ''We''ve always done it this way.'' - Grace Hopper',
    '"Simplicity is the soul of efficiency." - Austin Freeman',
    '"Talk is cheap. Show me the code." - Linus Torvalds',
    '"The computer was born to solve problems that did not exist before." - Bill Gates',
    '"Programming isn''t about what you know; it''s about what you can figure out." - Chris Pine'
)

# Function to show random quote
function Show-Quote {
    Write-Host ""
    $randomQuote = Get-Random -InputObject $quotes
    Write-Host " 💡 $randomQuote" -ForegroundColor Yellow
    Write-Host ""
    Start-Sleep -Seconds 2
}

# Step 1: Check for Python
Write-Host "[1/5] 🔍 Checking for Python installation..." -ForegroundColor Cyan
try {
    $pythonVersion = python --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host " ✅ Python found! $pythonVersion" -ForegroundColor Green
        Show-Quote
    } else {
        throw "Python not found"
    }
} catch {
    Write-Host ""
    Write-Host " ❌ Python not found! Please install Python from https://python.org" -ForegroundColor Red
    Write-Host ""
    Write-Host " 💡 Tip: Make sure to check 'Add Python to PATH' during installation!" -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

# Step 2: Check for pip
Write-Host "[2/5] 🔧 Checking for pip package manager..." -ForegroundColor Cyan
try {
    $pipVersion = python -m pip --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host " ✅ pip is ready!" -ForegroundColor Green
    } else {
        throw "pip not found"
    }
} catch {
    Write-Host " ❌ pip not found! Installing ensurepip..." -ForegroundColor Yellow
    python -m ensurepip --upgrade
}
Show-Quote

# Step 3: Upgrade pip
Write-Host "[3/5] 📦 Upgrading pip for best performance..." -ForegroundColor Cyan
python -m pip install --upgrade pip --quiet 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host " ✅ Pip upgraded successfully!" -ForegroundColor Green
} else {
    Write-Host " ⚠️  Could not upgrade pip, but continuing anyway..." -ForegroundColor Yellow
}
Show-Quote

# Step 4: Install cryptography
Write-Host "[4/5] 🔐 Installing encryption library (cryptography)..." -ForegroundColor Cyan
Write-Host "    This enables secure Secret Mode conversations!" -ForegroundColor Gray
python -m pip install cryptography --quiet
if ($LASTEXITCODE -eq 0) {
    Write-Host " ✅ Cryptography library installed!" -ForegroundColor Green
} else {
    Write-Host " ❌ Failed to install cryptography." -ForegroundColor Red
    Write-Host "    Please run: pip install cryptography" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}
Show-Quote

# Step 5: Create requirements.txt
Write-Host "[5/5] 📝 Creating requirements file..." -ForegroundColor Cyan
if (-not (Test-Path "requirements.txt")) {
    Set-Content -Path "requirements.txt" -Value "cryptography>=42.0.0"
    Write-Host " ✅ Requirements file created!" -ForegroundColor Green
} else {
    Write-Host " ✅ Requirements file already exists!" -ForegroundColor Green
}
Show-Quote

# Final success message
Clear-Host
Write-Host ""
Write-Host ""
Write-Host "       ╔═══════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "       ║          🎉 Installation Complete! 🎉        ║" -ForegroundColor Cyan
Write-Host "       ╚═══════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""
Write-Host ""
Write-Host "   ✨ Wi-Fi Walkie-Talkie is ready to use!" -ForegroundColor Green
Write-Host ""
Write-Host "   📋 What's installed:" -ForegroundColor Cyan
Write-Host "      • cryptography library (for Secret Mode encryption)"
Write-Host "      • All dependencies configured"
Write-Host ""
Write-Host "   🚀 How to run:" -ForegroundColor Cyan
Write-Host "      python wifi_walkie.py"
Write-Host ""
Write-Host "   💡 Quick Tips:" -ForegroundColor Yellow
Write-Host "      • Make sure you're on the same Wi-Fi as your friends"
Write-Host "      • Public Mode = Open chat for everyone"
Write-Host "      • Secret Mode = Encrypted chat with a shared password"
Write-Host ""
Write-Host '   "The future belongs to those who believe in the beauty of their dreams." - Eleanor Roosevelt' -ForegroundColor Magenta
Write-Host ""
Write-Host ""

# Ask if user wants to run the app now
Write-Host ""
$runNow = Read-Host "Would you like to start Wi-Fi Walkie-Talkie now? (Y/N)"
if ($runNow -eq "Y" -or $runNow -eq "y") {
    Write-Host ""
    Write-Host " 🚀 Starting Wi-Fi Walkie-Talkie..." -ForegroundColor Green
    Write-Host ""
    python wifi_walkie.py
} else {
    Write-Host ""
    Write-Host " 👋 See you later! Run 'python wifi_walkie.py' anytime to start chatting!" -ForegroundColor Cyan
    Write-Host ""
}
