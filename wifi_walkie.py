#!/usr/bin/env python3
"""
📻 Wi-Fi Walkie-Talkie
A friendly local-network messaging app for chatting with people on the same Wi-Fi.

Features:
- 🌍 Public Mode: Chat openly with everyone on the network
- 🔒 Secret Mode: Encrypted chats with a shared secret word
- 💬 Real-time messaging with cute animations
- 🎨 Retro-modern, friendly UI with soft colors

Created with ❤️ for making command-line tools feel approachable!
"""

import socket
import threading
import time
import os
import sys
import json
import random
from datetime import datetime
from getpass import getpass

# Try to import cryptography, provide friendly error if missing
try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    import base64
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False

# ============================================================================
# 🎨 COLOR CODES & STYLING (ANSI Escape Codes)
# ============================================================================

class Colors:
    """Friendly pastel colors for a cozy terminal experience."""
    
    # Reset
    RESET = "\033[0m"
    BOLD = "\033[1m"
    
    # Soft, friendly colors (pastel tones)
    CYAN = "\033[96m"        # Soft cyan for headers
    YELLOW = "\033[93m"      # Warm yellow for highlights
    GREEN = "\033[92m"       # Gentle green for success
    BLUE = "\033[94m"        # Calm blue for info
    MAGENTA = "\033[95m"     # Soft magenta for accents
    WHITE = "\033[97m"       # Warm white for text
    GRAY = "\033[90m"        # Soft gray for timestamps
    
    # Background colors
    BG_BLUE = "\033[44m"
    BG_CYAN = "\033[46m"
    
    # Message colors
    YOU_BG = "\033[42m"      # Green background for your messages
    OTHER_BG = "\033[46m"    # Cyan background for others' messages
    YOU_TEXT = "\033[30m"    # Black text on colored background
    OTHER_TEXT = "\033[30m"  # Black text on colored background
    
    # Status colors
    SUCCESS = "\033[92m"
    WARNING = "\033[93m"
    ERROR = "\033[91m"
    INFO = "\033[96m"


# ============================================================================
# 📡 CUTE ASCII ART LOGO
# ============================================================================

WIFI_LOGO = """
    ╭─────────────────────────────────────╮
    │         📻 Wi-Fi Walkie-Talkie      │
    │                                     │
    │      Signal Bars with Love ♥        │
    │                                     │
    │          ▄▄▄▄▄      ◠◠◠            │
    │         ███████     ◠◠              │
    │        █████████    ◠                │
    │       ███████████                   │
    │          [♥]                        │
    │                                     │
    │     Friendly Local Chat ✨          │
    ╰─────────────────────────────────────╯
"""

WELCOME_BANNER = f"""
{Colors.CYAN}{WIFI_LOGO}{Colors.RESET}
"""


# ============================================================================
# 🔐 ENCRYPTION HELPERS (Simple & Safe)
# ============================================================================

class CryptoHelper:
    """Handles encryption and decryption using a shared secret word."""
    
    def __init__(self, secret_word: str):
        """Initialize with a secret word (password)."""
        self.secret_word = secret_word
        self.key = self._derive_key(secret_word)
        self.fernet = Fernet(self.key)
    
    def _derive_key(self, password: str) -> bytes:
        """Derive a secure key from the password using PBKDF2."""
        # Use a fixed salt for simplicity (in production, share salt too)
        salt = b"wifi_walkie_talkie_salt_2024"
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key
    
    def encrypt(self, message: str) -> str:
        """Encrypt a message and return as string."""
        try:
            encrypted = self.fernet.encrypt(message.encode())
            return encrypted.decode()
        except Exception:
            return message  # Return unencrypted on error
    
    def decrypt(self, encrypted_message: str) -> str:
        """Decrypt a message and return as string."""
        try:
            decrypted = self.fernet.decrypt(encrypted_message.encode())
            return decrypted.decode()
        except Exception:
            return "[Unable to decrypt - wrong secret word?]"


# ============================================================================
# 🌐 NETWORK HANDLER
# ============================================================================

class NetworkHandler:
    """Manages UDP broadcasting for peer discovery and messaging."""
    
    # Network settings
    BROADCAST_PORT = 50050
    BROADCAST_ADDRESS = "255.255.255.255"
    BUFFER_SIZE = 4096
    PEER_TIMEOUT = 15  # Seconds before considering peer offline
    
    def __init__(self, username: str, mode: str, secret_word: str = None):
        """Initialize network handler."""
        self.username = username
        self.mode = mode  # "public" or "secret"
        self.secret_word = secret_word
        self.crypto = CryptoHelper(secret_word) if secret_word else None
        
        self.socket = None
        self.running = False
        self.peers = {}  # {ip: {"name": username, "last_seen": timestamp}}
        self.messages = []  # List of received messages
        self.message_callback = None  # Function to call when message received
        
        self.lock = threading.Lock()
    
    def start(self):
        """Start the network listener thread."""
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        # Bind to all interfaces
        try:
            self.socket.bind(("", self.BROADCAST_PORT))
        except OSError as e:
            print(f"\n{Colors.ERROR}Oops! Can't bind to port.{Colors.RESET}")
            print(f"Another instance might be running, or firewall is blocking.")
            print(f"Error: {e}")
            return False
        
        self.socket.settimeout(1.0)  # Timeout for receiving
        self.running = True
        
        # Start listener thread
        listener_thread = threading.Thread(target=self._listen_loop, daemon=True)
        listener_thread.start()
        
        # Start peer broadcast thread
        broadcast_thread = threading.Thread(target=self._broadcast_presence, daemon=True)
        broadcast_thread.start()
        
        # Send initial join message
        self._send_join_message()
        
        return True
    
    def stop(self):
        """Stop the network handler."""
        self.running = False
        if self.socket:
            try:
                # Send leave message
                self._send_leave_message()
                self.socket.close()
            except Exception:
                pass
    
    def send_message(self, text: str):
        """Broadcast a chat message to all peers."""
        if not self.running or not self.socket:
            return
        
        message_data = {
            "type": "message",
            "username": self.username,
            "text": text,
            "mode": self.mode,
            "timestamp": datetime.now().isoformat()
        }
        
        # Encrypt if in secret mode
        if self.mode == "secret" and self.crypto:
            message_data["text"] = self.crypto.encrypt(text)
        
        try:
            packet = json.dumps(message_data).encode()
            self.socket.sendto(packet, (self.BROADCAST_ADDRESS, self.BROADCAST_PORT))
        except Exception as e:
            print(f"\n{Colors.WARNING}Failed to send message.{Colors.RESET}")
    
    def _listen_loop(self):
        """Continuously listen for incoming packets."""
        while self.running:
            try:
                data, addr = self.socket.recvfrom(self.BUFFER_SIZE)
                ip = addr[0]
                
                try:
                    message_data = json.loads(data.decode())
                    self._process_packet(message_data, ip)
                except json.JSONDecodeError:
                    continue  # Ignore malformed packets
                    
            except socket.timeout:
                continue  # Normal timeout, keep listening
            except Exception as e:
                if self.running:
                    time.sleep(0.5)  # Brief pause on error
    
    def _process_packet(self, data: dict, ip: str):
        """Process an incoming packet."""
        msg_type = data.get("type", "")
        username = data.get("username", "Unknown")
        
        with self.lock:
            # Update peer list
            if msg_type in ["join", "message", "presence"]:
                self.peers[ip] = {
                    "name": username,
                    "last_seen": time.time()
                }
            
            # Handle different message types
            if msg_type == "join":
                if username != self.username:
                    self.messages.append({
                        "type": "system",
                        "text": f"👋 {username} joined the walkie-talkie!",
                        "timestamp": datetime.now()
                    })
                    if self.message_callback:
                        self.message_callback()
            
            elif msg_type == "leave":
                if username != self.username:
                    self.messages.append({
                        "type": "system",
                        "text": f"👋 {username} left the walkie-talkie.",
                        "timestamp": datetime.now()
                    })
                    if self.message_callback:
                        self.message_callback()
                # Remove from peers
                keys_to_remove = [k for k, v in self.peers.items() if v["name"] == username]
                for key in keys_to_remove:
                    del self.peers[key]
            
            elif msg_type == "message":
                if username != self.username:
                    text = data.get("text", "")
                    
                    # Decrypt if in secret mode
                    if data.get("mode") == "secret" and self.crypto:
                        text = self.crypto.decrypt(text)
                    
                    self.messages.append({
                        "type": "chat",
                        "username": username,
                        "text": text,
                        "is_mine": False,
                        "timestamp": datetime.now()
                    })
                    
                    if self.message_callback:
                        self.message_callback()
    
    def _broadcast_presence(self):
        """Periodically broadcast presence to keep peer list updated."""
        while self.running:
            try:
                presence_data = {
                    "type": "presence",
                    "username": self.username,
                    "mode": self.mode
                }
                packet = json.dumps(presence_data).encode()
                self.socket.sendto(packet, (self.BROADCAST_ADDRESS, self.BROADCAST_PORT))
                
                # Clean up old peers
                self._cleanup_peers()
                
            except Exception:
                pass
            
            time.sleep(5)  # Broadcast every 5 seconds
    
    def _cleanup_peers(self):
        """Remove peers that haven't been seen recently."""
        current_time = time.time()
        peers_to_remove = []
        
        for ip, info in self.peers.items():
            if current_time - info["last_seen"] > self.PEER_TIMEOUT:
                peers_to_remove.append(ip)
        
        for ip in peers_to_remove:
            name = self.peers[ip]["name"]
            del self.peers[ip]
            self.messages.append({
                "type": "system",
                "text": f"👋 {name} left (timeout).",
                "timestamp": datetime.now()
            })
    
    def _send_join_message(self):
        """Send a join announcement."""
        join_data = {
            "type": "join",
            "username": self.username,
            "mode": self.mode
        }
        try:
            packet = json.dumps(join_data).encode()
            self.socket.sendto(packet, (self.BROADCAST_ADDRESS, self.BROADCAST_PORT))
        except Exception:
            pass
    
    def _send_leave_message(self):
        """Send a leave announcement."""
        leave_data = {
            "type": "leave",
            "username": self.username,
            "mode": self.mode
        }
        try:
            packet = json.dumps(leave_data).encode()
            self.socket.sendto(packet, (self.BROADCAST_ADDRESS, self.BROADCAST_PORT))
        except Exception:
            pass


# ============================================================================
# 💬 USER INTERFACE
# ============================================================================

class WalkieTalkieUI:
    """Friendly user interface for the walkie-talkie."""
    
    def __init__(self, network: NetworkHandler):
        self.network = network
        self.running = True
        self.input_buffer = ""
        
        # Set up message callback
        self.network.message_callback = self._on_new_message
    
    def _on_new_message(self):
        """Called when a new message arrives."""
        # Redraw the UI
        self._draw_chat_area()
    
    def clear_screen(self):
        """Clear the terminal screen."""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def _draw_header(self):
        """Draw the header with logo and status."""
        print(WELCOME_BANNER)
        
        # Status bar
        mode_emoji = "🌍" if self.network.mode == "public" else "🔒"
        mode_text = "Public" if self.network.mode == "public" else "Secret"
        
        active_peers = len([p for p in self.network.peers.values() 
                           if time.time() - p["last_seen"] < NetworkHandler.PEER_TIMEOUT])
        
        status_bar = (
            f"{Colors.CYAN}┌{'─' * 50}┐{Colors.RESET}\n"
            f"{Colors.CYAN}│{Colors.RESET} {mode_emoji} Mode: {Colors.BOLD}{mode_text}{Colors.RESET}"
            f"  |  👤 You: {Colors.YELLOW}{self.network.username}{Colors.RESET}"
            f"  |  👥 Online: {Colors.GREEN}{active_peers + 1}{Colors.RESET}"
            f" {Colors.CYAN}│{Colors.RESET}\n"
            f"{Colors.CYAN}└{'─' * 50}┘{Colors.RESET}"
        )
        print(status_bar)
        print()
    
    def _draw_chat_area(self):
        """Draw the chat history area."""
        self.clear_screen()
        
        self._draw_header()
        
        # Chat area box top
        print(f"{Colors.GRAY}╔{'═' * 50}╗{Colors.RESET}")
        print(f"{Colors.GRAY}║{Colors.RESET}  💬 Chat History {' ' * 31}{Colors.GRAY}║{Colors.RESET}")
        print(f"{Colors.GRAY}╠{'═' * 50}╣{Colors.RESET}")
        
        # Show last 20 messages
        messages = self.network.messages[-20:]
        
        if not messages:
            print(f"{Colors.GRAY}║{Colors.RESET}")
            print(f"{Colors.GRAY}║{Colors.RESET}  {Colors.INFO}No messages yet. Say hello! 👋{Colors.RESET}")
            print(f"{Colors.GRAY}║{Colors.RESET}")
        else:
            for msg in messages:
                timestamp = msg["timestamp"].strftime("%H:%M")
                
                if msg["type"] == "system":
                    # System message (join/leave)
                    line = f"  {Colors.GRAY}[{timestamp}] {msg['text']}{Colors.RESET}"
                    # Truncate if too long
                    if len(line) > 52:
                        line = line[:49] + "..."
                    print(f"{Colors.GRAY}║{Colors.RESET}{line}{' ' * max(0, 50 - len(line) + 2)}{Colors.GRAY}║{Colors.RESET}")
                
                elif msg["type"] == "chat":
                    if msg["is_mine"]:
                        # Your message - right aligned with green bg
                        text = msg["text"]
                        if len(text) > 40:
                            text = text[:37] + "..."
                        
                        # Right-align the message
                        padding = 50 - len(text) - 8  # 8 for timestamp and checkmark
                        line = f"{' ' * padding}{Colors.GRAY}[{timestamp}]{Colors.RESET} {Colors.YOU_BG}{Colors.YOU_TEXT} {text} ✓ {Colors.RESET}"
                        print(f"{Colors.GRAY}║{Colors.RESET}{line}{' ' * max(0, 50 - len(line) + 2)}{Colors.GRAY}║{Colors.RESET}")
                    else:
                        # Others' message - left aligned with cyan bg
                        username = msg["username"]
                        text = msg["text"]
                        
                        if len(text) > 35:
                            text = text[:32] + "..."
                        
                        line = f"  {Colors.GRAY}[{timestamp}]{Colors.RESET} {Colors.OTHER_BG}{Colors.OTHER_TEXT} {username}: {text} 💬 {Colors.RESET}"
                        # Truncate if too long
                        if len(line) > 52:
                            line = line[:49] + "...💬 " + Colors.RESET
                        print(f"{Colors.GRAY}║{Colors.RESET}{line}{' ' * max(0, 50 - len(line) + 2)}{Colors.GRAY}║{Colors.RESET}")
        
        # Chat area box bottom
        print(f"{Colors.GRAY}╚{'═' * 50}╝{Colors.RESET}")
        print()
    
    def _draw_input(self):
        """Draw the input prompt."""
        prompt = f"{Colors.YELLOW}Type here > {Colors.RESET}"
        print(prompt, end="", flush=True)
    
    def run(self):
        """Main UI loop."""
        try:
            self._draw_chat_area()
            self._draw_input()
            
            while self.running:
                # Read input character by character (non-blocking on Windows)
                if os.name == 'nt':
                    # Windows
                    try:
                        import msvcrt
                        if msvcrt.kbhit():
                            char = msvcrt.getwche()
                            
                            if char == '\r' or char == '\n':  # Enter
                                if self.input_buffer.strip():
                                    self._send_message(self.input_buffer.strip())
                                    self.input_buffer = ""
                                    self._draw_chat_area()
                                self._draw_input()
                            
                            elif char == '\x08':  # Backspace
                                if self.input_buffer:
                                    self.input_buffer = self.input_buffer[:-1]
                                self._draw_chat_area()
                                self._draw_input()
                                print(self.input_buffer, end="", flush=True)
                            
                            elif ord(char) >= 32:  # Printable character
                                self.input_buffer += char
                                self._draw_chat_area()
                                self._draw_input()
                                print(self.input_buffer, end="", flush=True)
                            
                            elif ord(char) == 3:  # Ctrl+C
                                raise KeyboardInterrupt()
                                
                    except ImportError:
                        # Fallback for systems without msvcrt
                        self._run_fallback_input()
                else:
                    # Unix-like systems
                    self._run_fallback_input()
                
                time.sleep(0.05)  # Small delay to prevent CPU hogging
                
        except KeyboardInterrupt:
            self._handle_exit()
    
    def _run_fallback_input(self):
        """Fallback input method using standard input()."""
        try:
            user_input = input()
            if user_input.strip():
                self._send_message(user_input.strip())
                self.input_buffer = ""
                self._draw_chat_area()
            self._draw_input()
        except EOFError:
            self._handle_exit()
    
    def _send_message(self, text: str):
        """Send a message through the network."""
        # Add to local messages
        self.network.messages.append({
            "type": "chat",
            "username": self.network.username,
            "text": text,
            "is_mine": True,
            "timestamp": datetime.now()
        })
        
        # Broadcast to network
        self.network.send_message(text)
        
        # Refresh display
        self._draw_chat_area()
    
    def _handle_exit(self):
        """Handle graceful exit."""
        self.running = False
        
        print(f"\n{Colors.CYAN}")
        self._loading_animation("Saying goodbye", 3)
        print(f"\n\n  Thanks for using Wi-Fi Walkie-Talkie! 💕")
        print(f"  Come back soon! 👋\n")
        print(f"{Colors.RESET}")
        
        self.network.stop()
        sys.exit(0)
    
    def _loading_animation(self, text: str, dots: int = 3):
        """Show a friendly loading animation."""
        for i in range(dots):
            print(f"\r  {text}{'.' * (i + 1)}  ", end="", flush=True)
            time.sleep(0.3)
        print()


# ============================================================================
# 🚀 MAIN APPLICATION
# ============================================================================

def print_friendly_error(message: str):
    """Print a friendly error message."""
    print(f"\n{Colors.WARNING}⚠ Oops!{Colors.RESET}")
    print(f"  {message}")
    print(f"  Don't worry, you can try again! 😊\n")


def loading_dots(text: str, duration: float = 1.0):
    """Show a loading animation with dots."""
    start = time.time()
    dots = 0
    while time.time() - start < duration:
        print(f"\r  {text}{'.' * (dots % 4)}  ", end="", flush=True)
        time.sleep(0.2)
        dots += 1
    print(f"\r  {text} done! ✓  ")


def get_username() -> str:
    """Get a friendly nickname from the user."""
    print(f"\n{Colors.CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{Colors.RESET}")
    print(f"  {Colors.BOLD}👤 What should we call you?{Colors.RESET}")
    print(f"  {Colors.GRAY}(Pick something fun!){Colors.RESET}")
    print(f"{Colors.CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{Colors.RESET}\n")
    
    while True:
        try:
            username = input(f"  {Colors.YELLOW}Your nickname > {Colors.RESET}").strip()
            
            if not username:
                print_friendly_error("Please enter a nickname!")
                continue
            
            if len(username) > 20:
                print_friendly_error("Nickname is too long! Keep it under 20 characters.")
                continue
            
            # Clean up username
            username = "".join(c for c in username if c.isalnum() or c in "_- ")
            
            if not username:
                print_friendly_error("Please use letters and numbers only!")
                continue
            
            return username
            
        except KeyboardInterrupt:
            print(f"\n\n{Colors.CYAN}Goodbye! 👋{Colors.RESET}\n")
            sys.exit(0)


def get_mode() -> str:
    """Let user choose between Public and Secret mode."""
    print(f"\n{Colors.CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{Colors.RESET}")
    print(f"  {Colors.BOLD}🔐 Choose your chat mode:{Colors.RESET}")
    print(f"{Colors.CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{Colors.RESET}\n")
    
    print(f"  {Colors.GREEN}1. 🌍 Public Mode{Colors.RESET}")
    print(f"     {Colors.GRAY}Chat openly with everyone on the Wi-Fi{Colors.RESET}")
    print(f"     {Colors.GRAY}(Like a town square!){Colors.RESET}\n")
    
    print(f"  {Colors.BLUE}2. 🔒 Secret Mode{Colors.RESET}")
    print(f"     {Colors.GRAY}Encrypted chat with a shared secret word{Colors.RESET}")
    print(f"     {Colors.GRAY}(Only friends with the word can read!){Colors.RESET}\n")
    
    while True:
        try:
            choice = input(f"  {Colors.YELLOW}Choose (1 or 2) > {Colors.RESET}").strip()
            
            if choice == "1":
                return "public"
            elif choice == "2":
                return "secret"
            else:
                print_friendly_error("Please enter 1 or 2!")
                
        except KeyboardInterrupt:
            print(f"\n\n{Colors.CYAN}Goodbye! 👋{Colors.RESET}\n")
            sys.exit(0)


def get_secret_word() -> str:
    """Get the secret word for encrypted mode."""
    print(f"\n{Colors.CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{Colors.RESET}")
    print(f"  {Colors.BOLD}🔑 Create a Secret Word{Colors.RESET}")
    print(f"{Colors.CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{Colors.RESET}\n")
    
    print(f"  {Colors.GRAY}This word will be used to encrypt your messages.{Colors.RESET}")
    print(f"  {Colors.GRAY}Share it with your friends so they can decrypt!{Colors.RESET}")
    print(f"  {Colors.GRAY}(Example: 'pizza2024' or 'sunnyday'){Colors.RESET}\n")
    
    while True:
        try:
            secret = input(f"  {Colors.YELLOW}Secret word > {Colors.RESET}").strip()
            
            if not secret:
                print_friendly_error("Please enter a secret word!")
                continue
            
            if len(secret) < 4:
                print_friendly_error("Make it at least 4 characters for security!")
                continue
            
            # Confirm the secret word
            confirm = input(f"  {Colors.YELLOW}Confirm secret word > {Colors.RESET}").strip()
            
            if secret != confirm:
                print_friendly_error("The words don't match! Try again.")
                continue
            
            return secret
            
        except KeyboardInterrupt:
            print(f"\n\n{Colors.CYAN}Goodbye! 👋{Colors.RESET}\n")
            sys.exit(0)


def check_dependencies():
    """Check if required dependencies are installed."""
    if not CRYPTO_AVAILABLE:
        print(f"\n{Colors.WARNING}⚠ Missing dependency!{Colors.RESET}\n")
        print(f"  The 'cryptography' library is needed for Secret Mode.")
        print(f"  Install it with:\n")
        print(f"  {Colors.GREEN}pip install cryptography{Colors.RESET}\n")
        print(f"  Then run the app again! 😊\n")
        
        response = input("Continue with Public Mode only? (y/n): ").strip().lower()
        if response != 'y':
            sys.exit(0)
        
        return False
    
    return True


def main():
    """Main entry point for the Wi-Fi Walkie-Talkie."""
    # Clear screen and show welcome
    os.system('cls' if os.name == 'nt' else 'clear')
    print(WELCOME_BANNER)
    
    # Check dependencies
    crypto_ready = check_dependencies()
    
    # Loading animation
    loading_dots("Getting ready", 1.0)
    
    # Get user info
    username = get_username()
    mode = get_mode()
    
    secret_word = None
    if mode == "secret":
        if crypto_ready:
            secret_word = get_secret_word()
        else:
            print(f"\n{Colors.WARNING}Can't use Secret Mode without cryptography.{Colors.RESET}")
            print(f"Switching to Public Mode.\n")
            mode = "public"
    
    # Initialize network
    print(f"\n  {Colors.INFO}Connecting to Wi-Fi network...{Colors.RESET}")
    
    network = NetworkHandler(username, mode, secret_word)
    
    if not network.start():
        print_friendly_error("Couldn't connect to the network. Check your Wi-Fi!")
        sys.exit(1)
    
    loading_dots("Connected", 0.5)
    
    # Show mode confirmation
    if mode == "public":
        print(f"\n  {Colors.SUCCESS}✓ Ready! You're in {Colors.BOLD}Public Mode{Colors.RESET}{Colors.SUCCESS}.{Colors.RESET}")
        print(f"  {Colors.GRAY}Everyone on the Wi-Fi can see your messages.{Colors.RESET}")
    else:
        print(f"\n  {Colors.SUCCESS}✓ Ready! You're in {Colors.BOLD}Secret Mode{Colors.RESET}{Colors.SUCCESS}.{Colors.RESET}")
        print(f"  {Colors.GRAY}Messages are encrypted. Only friends with the secret word can read!{Colors.RESET}")
    
    time.sleep(1.5)
    
    # Start the UI
    ui = WalkieTalkieUI(network)
    ui.run()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n{Colors.ERROR}⚠ Something went wrong.{Colors.RESET}")
        print(f"  Don't worry! Here's what happened:")
        print(f"  {Colors.GRAY}{e}{Colors.RESET}")
        print(f"\n  Try checking your Wi-Fi connection and running again.")
        print(f"  If the problem persists, ask for help! 😊\n")
