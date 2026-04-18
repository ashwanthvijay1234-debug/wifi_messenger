#!/usr/bin/env python3
"""
Local Network Messaging Application with E2EE Support
Kali Linux Style UI for Windows CMD/PowerShell and Linux terminals

Features:
- UDP Broadcasting for peer discovery and messaging
- Open Mode (plain text) and E2EE Mode (encrypted with shared passphrase)
- ANSI color-coded UI with ASCII Wi-Fi logo
- Cross-platform compatible (Windows/Linux/Mac)
- JSON-based protocol for robust communication

Dependencies:
    pip install cryptography windows-curses (for Windows)
"""

import socket
import threading
import time
import os
import sys
import hashlib
import json
import logging
from datetime import datetime
from typing import Optional, List, Tuple, Dict, Any

# Try to import cryptography library
try:
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.backends import default_backend
    from cryptography.fernet import Fernet, InvalidToken
    import base64
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False

# ============================================================================
# CONFIGURATION
# ============================================================================

UDP_PORT = 50050
BROADCAST_ADDRESS = '255.255.255.255'
BUFFER_SIZE = 8192  # Increased for JSON and encryption overhead
DISCOVERY_INTERVAL = 5  # seconds between presence broadcasts
PEER_TIMEOUT = 15  # seconds before a peer is considered offline

# Setup basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler("netmsg.log")]
)
logger = logging.getLogger(__name__)

# ANSI Color Codes
class Colors:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    BLINK = '\033[5m'
    
    # Foreground colors
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'      # Neon green
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    
    # Bright foreground colors
    BRIGHT_RED = '\033[91m'
    BRIGHT_GREEN = '\033[92m'
    BRIGHT_YELLOW = '\033[93m'
    BRIGHT_CYAN = '\033[96m'
    
    # Background colors
    BG_BLACK = '\033[40m'
    BG_BLUE = '\033[44m'

# ============================================================================
# ASCII ART LOGO
# ============================================================================

WIFI_LOGO = """
{cyan}
      __   __
     /  \\_/  \\
    |  {green}●{cyan}   {green}●{cyan}  |
    |   ~~~   |
     \\  \\___/  /
      \\_______/
        | |
        | |
      {yellow}[NET_MSG]{cyan}
      
    {bright_green}█▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀█
    █  LOCAL NETWORK MESSENGER  █
    █▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄█
{reset}
"""

BANNER = """
{dim}┌─────────────────────────────────────────────────────────────┐
│  {bright_cyan}MODE:{reset} {mode}  {dim}|  {bright_cyan}USER:{reset} {username}  {dim}|  {bright_cyan}ENCRYPTED:{reset} {encrypted}
└─────────────────────────────────────────────────────────────┘{reset}
"""

# ============================================================================
# CRYPTOGRAPHY HELPER CLASS
# ============================================================================

class CryptoHelper:
    """Handles encryption and decryption using Fernet symmetric encryption."""
    
    def __init__(self, passphrase: str):
        """Initialize crypto helper with a passphrase to derive the key."""
        self.passphrase = passphrase.encode()
        self.salt = b'netmsg_salt_v2'  # Versioned salt
        self.key = self._derive_key()
        self.fernet = Fernet(self.key)
    
    def _derive_key(self) -> bytes:
        """Derive a 32-byte key from the passphrase using PBKDF2HMAC."""
        if not CRYPTO_AVAILABLE:
            raise RuntimeError("cryptography library not installed")
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self.salt,
            iterations=100000,
            backend=default_backend()
        )
        key = base64.urlsafe_b64encode(kdf.derive(self.passphrase))
        return key
    
    def encrypt(self, message: str) -> str:
        """Encrypt a message and return base64-encoded string."""
        try:
            encrypted = self.fernet.encrypt(message.encode())
            return encrypted.decode()
        except Exception as e:
            logger.error(f"Encryption error: {e}")
            return message
    
    def decrypt(self, encrypted_message: str) -> Optional[str]:
        """Decrypt a base64-encoded message."""
        try:
            decrypted = self.fernet.decrypt(encrypted_message.encode())
            return decrypted.decode()
        except InvalidToken:
            logger.warning("Decryption failed: Invalid token (wrong key?)")
            return None
        except Exception as e:
            logger.error(f"Decryption error: {e}")
            return None

# ============================================================================
# PEER MANAGEMENT
# ============================================================================

class Peer:
    """Represents a peer on the network."""
    
    def __init__(self, username: str, address: Tuple[str, int]):
        self.username = username
        self.address = address
        self.last_seen = time.time()
    
    def update_last_seen(self):
        self.last_seen = time.time()
    
    def is_alive(self) -> bool:
        return (time.time() - self.last_seen) < PEER_TIMEOUT

class PeerManager:
    """Manages the list of known peers on the network."""
    
    def __init__(self):
        self.peers: Dict[str, Peer] = {}
        self.lock = threading.Lock()
    
    def add_or_update_peer(self, username: str, address: Tuple[str, int]):
        """Add a new peer or update an existing one."""
        with self.lock:
            key = f"{address[0]}:{address[1]}"
            if key in self.peers:
                self.peers[key].update_last_seen()
                if self.peers[key].username != username:
                    self.peers[key].username = username
            else:
                self.peers[key] = Peer(username, address)
                logger.info(f"New peer discovered: {username} at {address}")
    
    def remove_peer(self, address: Tuple[str, int]):
        """Explicitly remove a peer."""
        with self.lock:
            key = f"{address[0]}:{address[1]}"
            if key in self.peers:
                peer = self.peers.pop(key)
                logger.info(f"Peer left: {peer.username} at {address}")
    
    def get_active_peers(self) -> List[Peer]:
        """Get list of currently active peers."""
        with self.lock:
            current_time = time.time()
            return [p for p in self.peers.values() if (current_time - p.last_seen) < PEER_TIMEOUT]
    
    def remove_stale_peers(self):
        """Remove peers that haven't been seen recently."""
        with self.lock:
            current_time = time.time()
            stale_keys = [k for k, p in self.peers.items() if (current_time - p.last_seen) >= PEER_TIMEOUT]
            for key in stale_keys:
                peer = self.peers.pop(key)
                logger.info(f"Peer timed out: {peer.username} at {peer.address}")
    
    def get_peer_count(self) -> int:
        """Get count of active peers."""
        return len(self.get_active_peers())

# ============================================================================
# NETWORK HANDLER
# ============================================================================

class NetworkHandler:
    """Handles UDP broadcasting and message receiving with JSON protocol."""
    
    def __init__(self, username: str, mode: str, crypto_helper: Optional[CryptoHelper] = None):
        self.username = username
        self.mode = mode  # 'open' or 'e2ee'
        self.crypto_helper = crypto_helper
        self.peer_manager = PeerManager()
        self.socket = None
        self.running = False
        self.messages: List[Dict[str, Any]] = []  # timestamp, sender, content
        self.messages_lock = threading.Lock()
        self.system_messages: List[Dict[str, Any]] = []  # timestamp, content
        self.system_messages_lock = threading.Lock()
    
    def start(self):
        """Start the network handler threads."""
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            self.socket.bind(('0.0.0.0', UDP_PORT))
        except OSError as e:
            logger.critical(f"Failed to bind to port {UDP_PORT}: {e}")
            print(f"{Colors.RED}Failed to bind to port {UDP_PORT}: {e}{Colors.RESET}")
            sys.exit(1)
        
        self.socket.settimeout(1.0)
        self.running = True
        
        self.receiver_thread = threading.Thread(target=self._receive_loop, daemon=True)
        self.receiver_thread.start()
        
        self.broadcast_thread = threading.Thread(target=self._broadcast_presence_loop, daemon=True)
        self.broadcast_thread.start()
        
        self.send_presence("join")
        self.add_system_message(f"Network started on port {UDP_PORT}")
        self.add_system_message(f"Mode: {self.mode.upper()}")
    
    def stop(self):
        """Stop the network handler gracefully."""
        if self.running:
            self.send_presence("leave")
            self.running = False
            time.sleep(0.5)  # Allow "leave" message to be sent
            if self.socket:
                self.socket.close()
            logger.info("Network stopped")
    
    def _receive_loop(self):
        """Continuously listen for incoming JSON messages."""
        while self.running:
            try:
                data, addr = self.socket.recvfrom(BUFFER_SIZE)
                raw_message = data.decode('utf-8', errors='ignore')
                
                try:
                    payload = json.loads(raw_message)
                    self._process_payload(payload, addr)
                except json.JSONDecodeError:
                    # Attempt decryption if in E2EE mode and JSON decode fails
                    if self.mode == 'e2ee' and self.crypto_helper:
                        decrypted = self.crypto_helper.decrypt(raw_message)
                        if decrypted:
                            try:
                                payload = json.loads(decrypted)
                                self._process_payload(payload, addr)
                            except json.JSONDecodeError:
                                logger.warning(f"Failed to decode decrypted JSON from {addr}")
                    else:
                        logger.debug(f"Received non-JSON message from {addr}")
            except socket.timeout:
                # Periodic cleanup while waiting
                self.peer_manager.remove_stale_peers()
                continue
            except Exception as e:
                if self.running:
                    logger.error(f"Receive error: {e}")
                break
    
    def _process_payload(self, payload: Dict[str, Any], addr: Tuple[str, int]):
        """Process a decoded message payload."""
        msg_type = payload.get("type")
        sender = payload.get("user")
        content = payload.get("content")
        
        if not msg_type or not sender:
            return

        if msg_type == "presence":
            action = content
            if action == "join":
                self.peer_manager.add_or_update_peer(sender, addr)
                self.add_system_message(f"👋 {sender} joined the network")
            elif action == "leave":
                self.peer_manager.remove_peer(addr)
                self.add_system_message(f"👋 {sender} left the network")
            elif action == "online":
                self.peer_manager.add_or_update_peer(sender, addr)
        
        elif msg_type == "chat":
            self.peer_manager.add_or_update_peer(sender, addr)
            # Decrypt content if it was encrypted (handled during initial receive if E2EE)
            # But if we received it as open, and we are in E2EE, we might still want to see it?
            # For simplicity, we assume consistent modes.
            self.add_message(sender, content)

    def send_presence(self, action: str):
        """Send a presence announcement."""
        payload = {
            "type": "presence",
            "user": self.username,
            "content": action,
            "ts": time.time()
        }
        self._send_payload(payload)

    def _broadcast_presence_loop(self):
        """Periodically broadcast user presence."""
        while self.running:
            try:
                self.send_presence("online")
            except Exception as e:
                logger.error(f"Broadcast error: {e}")
            
            time.sleep(DISCOVERY_INTERVAL)
    
    def send_chat_message(self, text: str):
        """Send a chat message."""
        if not text.strip():
            return
        
        payload = {
            "type": "chat",
            "user": self.username,
            "content": text,
            "ts": time.time()
        }
        
        if self._send_payload(payload):
            self.add_message(self.username, text)

    def _send_payload(self, payload: Dict[str, Any]) -> bool:
        """Encode and send a payload, encrypting if necessary."""
        try:
            data = json.dumps(payload)
            if self.mode == 'e2ee' and self.crypto_helper:
                data = self.crypto_helper.encrypt(data)
            
            self.socket.sendto(data.encode(), (BROADCAST_ADDRESS, UDP_PORT))
            return True
        except Exception as e:
            logger.error(f"Send error: {e}")
            self.add_system_message(f"Send error: {e}")
            return False

    def add_message(self, sender: str, content: str):
        """Add a message to history."""
        with self.messages_lock:
            self.messages.append({
                "ts": time.time(),
                "sender": sender,
                "content": content
            })
            if len(self.messages) > 100:
                self.messages.pop(0)
    
    def add_system_message(self, content: str):
        """Add a system message to history."""
        with self.system_messages_lock:
            self.system_messages.append({
                "ts": time.time(),
                "content": content
            })
            if len(self.system_messages) > 20:
                self.system_messages.pop(0)
    
    def get_all_entries(self) -> List[Dict[str, Any]]:
        """Return combined and sorted chat and system messages."""
        combined = []
        with self.messages_lock:
            for m in self.messages:
                combined.append({**m, "type": "chat"})
        with self.system_messages_lock:
            for m in self.system_messages:
                combined.append({**m, "type": "sys"})
        
        combined.sort(key=lambda x: x["ts"])
        return combined

# ============================================================================
# UI HANDLER
# ============================================================================

class UIHandler:
    """Handles terminal UI rendering."""
    
    def __init__(self, network_handler: NetworkHandler, username: str, mode: str):
        self.network = network_handler
        self.username = username
        self.mode = mode
        self.input_buffer = ""
        self.running = True
        self.last_render_time = 0
        self.render_interval = 0.05
    
    def clear_screen(self):
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def render(self):
        current_time = time.time()
        if current_time - self.last_render_time < self.render_interval:
            return
        self.last_render_time = current_time
        
        self.clear_screen()
        cols, rows = 80, 24
        try:
            cols, rows = os.get_terminal_size()
        except OSError:
            pass
            
        # Layout calculation
        header_height = 16
        footer_height = 4
        chat_height = max(1, rows - header_height - footer_height)
        
        # Header
        print(WIFI_LOGO.format(
            cyan=Colors.CYAN, green=Colors.GREEN, yellow=Colors.YELLOW,
            bright_green=Colors.BRIGHT_GREEN, reset=Colors.RESET
        ))
        
        encrypted_status = f"{Colors.GREEN}YES{Colors.RESET}" if self.mode == 'e2ee' else f"{Colors.YELLOW}NO{Colors.RESET}"
        print(BANNER.format(
            dim=Colors.DIM, bright_cyan=Colors.BRIGHT_CYAN, reset=Colors.RESET,
            mode=f"{Colors.BRIGHT_CYAN}{self.mode.upper()}{Colors.RESET}",
            username=f"{Colors.BRIGHT_GREEN}{self.username}{Colors.RESET}",
            encrypted=encrypted_status
        ))
        
        peers = self.network.peer_manager.get_active_peers()
        peer_names = ", ".join([p.username for p in peers]) if peers else "Searching..."
        print(f"{Colors.DIM}📡 Active: {Colors.BRIGHT_CYAN}{len(peers)}{Colors.RESET} | {Colors.DIM}{peer_names}{Colors.RESET}")
        print(f"{Colors.DIM}{'─' * min(cols, 60)}{Colors.RESET}")
        
        # Chat
        all_entries = self.network.get_all_entries()
        display_entries = all_entries[-chat_height:]
        
        for entry in display_entries:
            time_str = datetime.fromtimestamp(entry["ts"]).strftime('%H:%M:%S')
            if entry["type"] == "sys":
                print(f"{Colors.DIM}[{time_str}] {entry['content']}{Colors.RESET}")
            else:
                color = Colors.BRIGHT_GREEN if entry["sender"] == self.username else Colors.BRIGHT_CYAN
                print(f"{color}[{time_str}] <{entry['sender']}> {entry['content']}{Colors.RESET}")
        
        for _ in range(chat_height - len(display_entries)):
            print()
            
        # Footer
        print(f"{Colors.DIM}{'─' * min(cols, 60)}{Colors.RESET}")
        print(f"{Colors.BRIGHT_GREEN}┌─[{self.username}@netmsg]{Colors.RESET}")
        cursor = f"{Colors.BLINK}█{Colors.RESET}" if self.running else ""
        print(f"{Colors.BRIGHT_GREEN}│{Colors.RESET} {self.input_buffer}{cursor}")
        print(f"{Colors.BRIGHT_GREEN}└──>{Colors.RESET} ", end='', flush=True)

    def handle_input(self, char: str):
        if char in ('\r', '\n'):
            if self.input_buffer.strip():
                self.network.send_chat_message(self.input_buffer)
                self.input_buffer = ""
        elif char in ('\x08', '\x7f'):
            self.input_buffer = self.input_buffer[:-1]
        elif char == '\x03':
            self.running = False
            return False
        elif len(char) == 1 and char.isprintable():
            self.input_buffer += char
        return True

# ============================================================================
# INPUT HANDLER
# ============================================================================

class InputHandler:
    def __init__(self, ui_handler: UIHandler):
        self.ui = ui_handler
        self.running = True
        
    def start(self):
        threading.Thread(target=self._input_loop, daemon=True).start()
        
    def _input_loop(self):
        if os.name == 'nt':
            import msvcrt
            while self.running and self.ui.running:
                try:
                    if msvcrt.kbhit():
                        char = msvcrt.getwch()
                        if char in ('\xe0', '\x00'):
                            # Special/Function keys - consume next character
                            if msvcrt.kbhit():
                                msvcrt.getwch()
                            continue
                        self.ui.handle_input(char)
                except Exception as e:
                    logger.debug(f"Windows input error: {e}")
                time.sleep(0.02)
        else:
            import termios, tty, select
            fd = sys.stdin.fileno()
            try:
                old_settings = termios.tcgetattr(fd)
            except termios.error:
                # Not a terminal (e.g. running in some IDEs or non-interactive environments)
                return

            try:
                tty.setcbreak(fd)
                while self.running and self.ui.running:
                    try:
                        if select.select([sys.stdin], [], [], 0.1)[0]:
                            char = sys.stdin.read(1)
                            if char:
                                self.ui.handle_input(char)
                    except (IOError, select.error) as e:
                        logger.debug(f"Unix input select error: {e}")
                        time.sleep(0.1)
            finally:
                try:
                    termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
                except termios.error:
                    pass

    def stop(self):
        self.running = False

# ============================================================================
# MAIN
# ============================================================================

def main():
    if not CRYPTO_AVAILABLE:
        print(f"{Colors.YELLOW}Warning: cryptography not installed. E2EE disabled.{Colors.RESET}")
        time.sleep(1)

    print(WIFI_LOGO.format(
        cyan=Colors.CYAN, green=Colors.GREEN, yellow=Colors.YELLOW,
        bright_green=Colors.BRIGHT_GREEN, reset=Colors.RESET
    ))
    
    print(f"{Colors.BRIGHT_CYAN}=== SETUP ==={Colors.RESET}")
    username = input(f"{Colors.BRIGHT_CYAN}Username: {Colors.RESET}").strip() or "Anonymous"
    username = ''.join(c for c in username if c.isalnum() or c in '_-')[:15]
    
    print(f"\n1. Open Mode\n2. E2EE Mode")
    choice = input("Choice [1]: ").strip() or "1"
    
    mode = 'open'
    crypto = None
    if choice == '2' and CRYPTO_AVAILABLE:
        mode = 'e2ee'
        passphrase = input("Passphrase: ")
        if passphrase:
            crypto = CryptoHelper(passphrase)
        else:
            mode = 'open'
            print("No passphrase. Falling back to Open Mode.")

    network = NetworkHandler(username, mode, crypto)
    ui = UIHandler(network, username, mode)
    input_h = InputHandler(ui)
    
    network.start()
    input_h.start()
    
    try:
        while ui.running:
            ui.render()
            time.sleep(0.05)
    except KeyboardInterrupt:
        pass
    finally:
        ui.running = False
        input_h.stop()
        network.stop()
        print(f"\n{Colors.BRIGHT_CYAN}Goodbye!{Colors.RESET}\n")

if __name__ == "__main__":
    main()
