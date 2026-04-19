# 📻 Wi-Fi Walkie-Talkie

A friendly, retro-styled local network messaging app for Windows, Linux, and Mac. Chat with anyone on the same Wi-Fi network without needing internet or a server!

## ✨ Features

- 🌍 **Public Mode**: Open chat visible to everyone on the network.
- 🔒 **Secret Mode**: End-to-end encrypted chats (share a password to join).
- 🎨 **Retro UI**: Friendly, colorful terminal interface with cute ASCII art.
- ⚡ **Zero Config**: No IP addresses to type. Just run and chat.
- 👋 **Peer Discovery**: Automatically see who else is online.

## 🚀 Getting Started (Windows Executable)

For the simplest experience on Windows, download and run the `netmsg.exe` file. No installation or Python required!

1.  **Download**: Get the latest `netmsg.exe` from the [releases page](https://github.com/ashwanthvijay1234-debug/wifi_walkie/releases) (Note: You may need to create a release with the .exe).
2.  **Run**: Double-click `netmsg.exe`.
3.  **Chat**: Follow the on-screen prompts for your username and chat mode.

## 🚀 One-Line Install & Launch (Python Version)

This single command installs dependencies, downloads the app, and launches it immediately!

### For Windows PowerShell (Recommended)
Copy and paste this into your terminal:

```powershell
irm https://raw.githubusercontent.com/ashwanthvijay1234-debug/wifi_walkie/main/install.bat -OutFile $env:TEMP\install.bat; & $env:TEMP\install.bat
```

### For Windows CMD / Linux / Mac:
```bash
curl -sS -L https://raw.githubusercontent.com/ashwanthvijay1234-debug/wifi_walkie/main/install.sh -o /tmp/install.sh && chmod +x /tmp/install.sh && /tmp/install.sh
```

This magical one-liner will:
- ✅ Check for Python installation
- 🔧 Verify pip package manager
- 📦 Upgrade pip for best compatibility
- 🔐 Install the cryptography library
- 📥 Download the Wi-Fi Walkie-Talkie app files (`netmsg.py`, `wifi_walkie.py`)
- 💡 Show inspiring tech quotes along the way!

> 🔍 **Security Note**: You can inspect the installer scripts (`install.bat` and `install.sh`) in this repository before running.

## 🚀 Quick Start (Python Version)

*(If you used the one-line installer, dependencies are already installed!)*

### Step 1: Run the App

```bash
python netmsg.py
```
Or, for the classic UI:
```bash
python wifi_walkie.py
```

### Step 2: Chat!

1. Enter your nickname (something fun!)
2. Choose your mode:
   - **Open Mode (1)**: Everyone on Wi-Fi can see messages
   - **E2EE Mode (2)**: Share a secret word with friends for encrypted chat
3. Start chatting! 💬

## 🎮 How It Works

### Network Communication
- Uses **UDP Broadcasting** on port 50050
- Automatically discovers peers on the same Wi-Fi network
- Broadcasts presence every 5 seconds
- Peers timeout after 15 seconds of silence

### Encryption (E2EE Mode)
- Uses **Fernet symmetric encryption** from the `cryptography` library
- Key derivation with **PBKDF2HMAC** (100,000 iterations)
- SHA-256 hashing for secure key generation
- Only users with the exact same secret word can decrypt messages

### User Interface
- **Header**: Cute Wi-Fi logo with signal bars and hearts ♥
- **Status Bar**: Shows mode, your name, and online peer count
- **Chat Area**: 
  - Your messages → Right-aligned with green background ✓
  - Others' messages → Left-aligned with cyan background 💬
  - System messages → Gray timestamps for join/leave events
- **Input**: Simple "Type here >" prompt

## 🎨 Design Philosophy

This app was created to make command-line tools feel **approachable and fun**, not intimidating:

- ❌ No scary black-and-green "hacker" terminals
- ✅ Soft pastel colors (cyan, yellow, warm white)
- ✅ Friendly error messages ("Oops!" instead of tracebacks)
- ✅ Cute loading animations (bouncing dots)
- ✅ Emojis for visual feedback (👋, 💬, ✓, ♥)
- ✅ Rounded ASCII art instead of harsh lines

## 📱 Platform Support

- **Windows**: CMD and PowerShell (uses `msvcrt` for non-blocking input)
- **Linux/macOS**: Terminal with ANSI color support
- **Cross-platform**: Works anywhere Python 3 runs!

## 🔧 Troubleshooting

### "Can't bind to port" Error
- Another instance might already be running
- Firewall may be blocking the port
- Try closing other instances or check firewall settings

### "Missing dependency" Error
```bash
pip install cryptography
```

### No peers showing up
- Make sure you're on the same Wi-Fi network
- Check if firewall is blocking UDP port 50050
- Try restarting the app on both devices

### Colors not displaying correctly
- Some terminals don't support ANSI colors
- Try using Windows Terminal, PowerShell, or a modern terminal emulator

## 📝 Example Session

```
    ╭─────────────────────────────────────╮
    │         📻 Wi-Fi Walkie-Talkie      │
    │      Signal Bars with Love ♥        │
    │          ▄▄▄▄▄      ◠◠◠            │
    │         ███████     ◠◠              │
    │        █████████    ◠                │
    │       ███████████                   │
    │          [♥]                        │
    │     Friendly Local Chat ✨          │
    ╰─────────────────────────────────────╯

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  👤 What should we call you?
  (Pick something fun!)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Your nickname > Alex

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  🔐 Choose your chat mode:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  1. 🌍 Public Mode
     Chat openly with everyone on the Wi-Fi
     (Like a town square!)

  2. 🔒 Secret Mode
     Encrypted chat with a shared secret word
     (Only friends with the word can read!)

  Choose (1 or 2) > 1

  Getting ready...  
  Connected done! ✓  

  ✓ Ready! You're in Public Mode.
  Everyone on the Wi-Fi can see your messages.

╔══════════════════════════════════════╗
║  💬 Chat History                     ║
╠══════════════════════════════════════╣
║                                      ║
║  No messages yet. Say hello! 👋      ║
║                                      ║
╚══════════════════════════════════════╝

Type here > Hey everyone! 👋
```

## 🛠️ For Developers

### File Structure
```
netmsg.py           # Main application (new, stable protocol)
wifi_walkie.py      # Classic UI application (legacy)
install.bat         # Windows installer script
install.sh          # Linux/macOS installer script
requirements.txt    # Python dependencies
README.md           # This file
```

### Key Classes (in `netmsg.py`)
- `CryptoHelper`: Encryption/decryption utilities
- `PeerManager`: UDP peer discovery and management
- `NetworkHandler`: Core network communication (UDP broadcasting)
- `UIHandler`: User interface rendering
- `InputHandler`: Cross-platform non-blocking input

### Customization Ideas
- Change the ASCII logo in `WIFI_LOGO`
- Adjust colors in the `Colors` class
- Modify `DISCOVERY_INTERVAL` or `PEER_TIMEOUT` for peer detection
- Add custom emojis or status indicators
- Implement new message types (e.g., file transfer)

## 📄 License

Free to use, modify, and share! Built with ❤️ to make technology more approachable.

## 🙏 Credits

Created to prove that command-line tools can be **friendly, fun, and welcoming** to everyone—not just tech experts!

---

**Happy chatting! 💕📻**