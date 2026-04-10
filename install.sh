#!/bin/bash

# --- Colors ---
CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# --- Header ---
clear
echo -e "${CYAN}"
echo "================================================================================"
echo "                   WI-FI WALKIE-TALKIE INSTALLER"
echo "                      Powered by OpenClaw"
echo "================================================================================"
echo -e "${NC}"

# --- 1. Check Python ---
echo -e "[1/5] ${CYAN}Checking for Python...${NC}"
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
    echo -e "${GREEN}✓ Python3 found!${NC}"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
    echo -e "${GREEN}✓ Python found!${NC}"
else
    echo -e "${RED}✗ Error: Python not found! Please install Python first.${NC}"
    exit 1
fi
echo

# --- Quote 1 ---
echo -e "[2/5] ${YELLOW}Loading wisdom...${NC}"
echo -e "${CYAN}\"Software is eating the world.\" - Marc Andreessen${NC}"
sleep 2
echo

# --- 2. Install Crypto ---
echo -e "[3/5] ${CYAN}Installing cryptography library...${NC}"
if command -v pip3 &> /dev/null; then
    PIP_CMD="pip3"
elif command -v pip &> /dev/null; then
    PIP_CMD="pip"
else
    echo -e "${RED}✗ Error: pip not found!${NC}"
    exit 1
fi

$PIP_CMD install cryptography --quiet
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Cryptography installed!${NC}"
else
    echo -e "${RED}✗ Warning: Could not install cryptography automatically.${NC}"
    echo -e "${YELLOW}  Please run: $PIP_CMD install cryptography${NC}"
fi
echo

# --- Quote 2 ---
echo -e "[4/5] ${YELLOW}Final preparations...${NC}"
echo -e "${CYAN}\"Make it work, make it right, make it fast.\" - Kent Beck${NC}"
sleep 2
echo

# --- Download App ---
echo -e "[5/5] ${CYAN}Downloading Wi-Fi Walkie-Talkie app...${NC}"
curl -sS -o wifi_walkie.py "https://raw.githubusercontent.com/ashwanthvijay1234-debug/wifi_walkie/main/wifi_walkie.py"

if [ ! -f "wifi_walkie.py" ]; then
    echo -e "${RED}✗ Error: Failed to download app. Check internet connection.${NC}"
    exit 1
fi
echo -e "${GREEN}✓ App downloaded successfully!${NC}"
echo

# --- Setup 'walkie' command ---
echo -e "${CYAN}Setting up 'walkie' command...${NC}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WALKIE_SCRIPT="$HOME/.local/bin/walkie"

# Create directory if it doesn't exist
mkdir -p "$HOME/.local/bin"

# Create the launcher script
cat > "$WALKIE_SCRIPT" <<EOL
#!/bin/bash
cd "$SCRIPT_DIR"
$PYTHON_CMD wifi_walkie.py
EOL

chmod +x "$WALKIE_SCRIPT"

# Add to PATH if not already there
if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
    echo -e "${YELLOW}Adding ~/.local/bin to PATH...${NC}"
    if [[ "$SHELL" == *"zsh"* ]]; then
        echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
        echo -e "${GREEN}✓ Added to ~/.zshrc${NC}"
    elif [[ "$SHELL" == *"bash"* ]]; then
        echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
        echo -e "${GREEN}✓ Added to ~/.bashrc${NC}"
    fi
    echo -e "${YELLOW}Please restart your terminal or run: source ~/.bashrc (or ~/.zshrc)${NC}"
else
    echo -e "${GREEN}✓ Path already configured!${NC}"
fi
echo

# --- Complete ---
echo "================================================================================"
echo -e "                      ${GREEN}INSTALLATION COMPLETE!${NC}"
echo "================================================================================"
echo
echo -e "You can now run the app by typing: ${CYAN}walkie${NC}"
echo -e "Or directly: ${YELLOW}python wifi_walkie.py${NC}"
echo

# Launch immediately
read -p "Launch Wi-Fi Walkie-Talkie now? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    $PYTHON_CMD wifi_walkie.py
fi