# 📻 Wi-Fi Walkie-Talkie

A **friendly, cozy** local-network messaging app that makes chatting over Wi-Fi feel like using a retro walkie-talkie! No scary hacker aesthetics—just warm colors, cute animations, and simple fun.

## ✨ Features

- **🌍 Public Mode**: Chat openly with everyone on the same Wi-Fi network (like a town square!)
- **🔒 Secret Mode**: End-to-end encrypted chats with a shared secret word
- **💬 Real-time Messaging**: Messages appear instantly with cute notifications
- **🎨 Friendly UI**: Soft pastel colors, rounded ASCII art, and approachable design
- **👥 Peer Detection**: Automatically see who else is online
- **🔄 Auto-cleanup**: Peers who leave are automatically removed after 15 seconds

## 🚀 Installation

### Option 1: One-Line Fun Installer (Recommended!) ✨

**The Super Short One-Liner:**

For Windows PowerShell:
```powershell
irm bit.ly/4dXwrfl | iex
```

For Windows CMD / Linux / Mac:
```bash
curl -sS bit.ly/4dXwrfl | python
```

This magical one-liner will:
- ✅ Check for Python installation
- 🔧 Verify pip package manager
- 📦 Upgrade pip for best compatibility
- 🔐 Install the cryptography library
- 📥 Download the Wi-Fi Walkie-Talkie app
- 📝 Create requirements.txt
- 💡 Show inspiring tech quotes along the way!

> 🔍 **Security Note**: This short URL redirects to our official [GitHub Gist installer script](https://gist.github.com/ashwanthvijay1234-debug/b3fb8fb03575d0fe6dd0f6ab9f8fc3d2). You can inspect the code there before running!

### Option 2: Local Install Scripts

**For Windows CMD:**
```cmd
install.bat
```

**For Windows PowerShell:**
```powershell
.\install.ps1
```

### Option 3: Manual Installation

```bash
# Clone or download the project
cd wifi-walkie-talkie

# Install dependencies
pip install -r requirements.txt

# Or install directly
pip install cryptography
```

## 🚀 Quick Start

### Step 1: Run the App

*(If you used the installer, dependencies are already installed!)*

```bash
python wifi_walkie.py
```

### Step 2: Chat!

1. Enter your nickname (something fun!)
2. Choose your mode:
   - **Public Mode (1)**: Everyone on Wi-Fi can see messages
   - **Secret Mode (2)**: Share a secret word with friends for encrypted chat
3. Start chatting! 💬

## 🎮 How It Works

### Network Communication
- Uses **UDP Broadcasting** on port 50050
- Automatically discovers peers on the same Wi-Fi network
- Broadcasts presence every 5 seconds
- Peers timeout after 15 seconds of silence

### Encryption (Secret Mode)
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
wifi_walkie.py      # Main application (single file!)
requirements.txt    # Dependencies
README.md          # This file
```

### Key Classes
- `Colors`: ANSI color codes for friendly styling
- `CryptoHelper`: Encryption/decryption utilities
- `NetworkHandler`: UDP broadcasting and peer management
- `WalkieTalkieUI`: User interface and input handling

### Customization Ideas
- Change the ASCII logo in `WIFI_LOGO`
- Adjust colors in the `Colors` class
- Modify `PEER_TIMEOUT` in `NetworkHandler` for faster/slower peer detection
- Add custom emojis or status indicators

## 📄 License

Free to use, modify, and share! Built with ❤️ to make technology more approachable.

## 🙏 Credits

Created to prove that command-line tools can be **friendly, fun, and welcoming** to everyone—not just tech experts!

---

**Happy chatting! 💕📻**
