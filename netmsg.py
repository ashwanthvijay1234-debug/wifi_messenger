#!/usr/bin/env python3
"""
Local Network Messaging Application with E2EE Support
Kali Linux Style UI for Windows CMD/PowerShell and Linux terminals

Features:
- UDP Broadcasting for peer discovery and messaging
- Open Mode (plain text) and E2EE Mode (encrypted with shared passphrase)
- ANSI color-coded UI with ASCII Wi-Fi logo
- Cross-platform compatible (Windows/Linux/Mac)

Dependencies:
    pip install cryptography windows-curses (for Windows)
"""

import socket
import threading
import time
import os
import sys
import hashlib
from datetime import datetime
from typing import Optional, List, Tuple

# Try to import cryptography library
try:
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.backends import default_backend
    from cryptography.fernet import Fernet
    import base64
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False

# ============================================================================
# CONFIGURATION
# ============================================================================

UDP_PORT = 50050
BROADCAST_ADDRESS = '<broadcast>'
BUFFER_SIZE = 4096
DISCOVERY_INTERVAL = 5  # seconds between presence broadcasts
PEER_TIMEOUT = 15  # seconds before a peer is considered offline

# ANSI Color Codes
class Colors:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    
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
        self.salt = b'netmsg_salt_v1'  # Fixed salt for simplicity (in production, use random)
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
            print(f"{Colors.RED}Encryption error: {e}{Colors.RESET}")
            return message
    
    def decrypt(self, encrypted_message: str) -> str:
        """Decrypt a base64-encoded message."""
        try:
            decrypted = self.fernet.decrypt(encrypted_message.encode())
            return decrypted.decode()
        except Exception:
            # Return as-is if decryption fails (might be unencrypted or wrong key)
            return encrypted_message

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
        self.peers: dict[str, Peer] = {}
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
    
    def get_active_peers(self) -> List[Peer]:
        """Get list of currently active peers."""
        with self.lock:
            return [p for p in self.peers.values() if p.is_alive()]
    
    def remove_stale_peers(self):
        """Remove peers that haven't been seen recently."""
        with self.lock:
            stale_keys = [k for k, p in self.peers.items() if not p.is_alive()]
            for key in stale_keys:
                del self.peers[key]
    
    def get_peer_count(self) -> int:
        """Get count of active peers."""
        return len(self.get_active_peers())

# ============================================================================
# NETWORK HANDLER
# ============================================================================

class NetworkHandler:
    """Handles UDP broadcasting and message receiving."""
    
    def __init__(self, username: str, mode: str, crypto_helper: Optional[CryptoHelper] = None):
        self.username = username
        self.mode = mode  # 'open' or 'e2ee'
        self.crypto_helper = crypto_helper
        self.peer_manager = PeerManager()
        self.socket = None
        self.running = False
        self.messages: List[Tuple[float, str, str]] = []  # (timestamp, sender, message)
        self.messages_lock = threading.Lock()
        self.system_messages: List[Tuple[float, str]] = []  # (timestamp, message)
    
    def start(self):
        """Start the network handler threads."""
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        # Bind to all interfaces
        try:
            self.socket.bind(('0.0.0.0', UDP_PORT))
        except OSError as e:
            print(f"{Colors.RED}Failed to bind to port {UDP_PORT}: {e}{Colors.RESET}")
            print(f"{Colors.YELLOW}Make sure no other instance is running on this port.{Colors.RESET}")
            sys.exit(1)
        
        self.socket.settimeout(1.0)  # Timeout for recvfrom
        self.running = True
        
        # Start receiver thread
        self.receiver_thread = threading.Thread(target=self._receive_loop, daemon=True)
        self.receiver_thread.start()
        
        # Start presence broadcaster thread
        self.broadcast_thread = threading.Thread(target=self._broadcast_presence_loop, daemon=True)
        self.broadcast_thread.start()
        
        # Add system message
        self.add_system_message(f"Network started on port {UDP_PORT}")
        self.add_system_message(f"Mode: {self.mode.upper()}")
    
    def stop(self):
        """Stop the network handler."""
        self.running = False
        if self.socket:
            self.socket.close()
        self.add_system_message("Network stopped")
    
    def _receive_loop(self):
        """Continuously listen for incoming messages."""
        while self.running:
            try:
                data, addr = self.socket.recvfrom(BUFFER_SIZE)
                message = data.decode('utf-8', errors='ignore')
                self._process_incoming_message(message, addr)
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    self.add_system_message(f"{Colors.RED}Receive error: {e}{Colors.RESET}")
                break
        
        # Clean up stale peers periodically
        self.peer_manager.remove_stale_peers()
    
    def _process_incoming_message(self, message: str, addr: Tuple[str, int]):
        """Process an incoming message."""
        if not message.startswith(('MSG:', 'PRESENCE:')):
            return
        
        parts = message.split(':', 2)
        if len(parts) < 3:
            return
        
        msg_type = parts[0]
        sender = parts[1]
        content = parts[2]
        
        if msg_type == 'PRESENCE:':
            # Peer presence announcement
            self.peer_manager.add_or_update_peer(sender, addr)
            # Don't show every presence as a message to reduce noise
        elif msg_type == 'MSG:':
            # Actual chat message
            self.peer_manager.add_or_update_peer(sender, addr)
            
            # Decrypt if in E2EE mode
            if self.mode == 'e2ee' and self.crypto_helper:
                try:
                    content = self.crypto_helper.decrypt(content)
                except Exception:
                    content = f"[Unable to decrypt: {content[:20]}...]"
            
            self.add_message(sender, content)
    
    def _broadcast_presence_loop(self):
        """Periodically broadcast user presence."""
        while self.running:
            try:
                presence_msg = f"PRESENCE:{self.username}:online"
                self.socket.sendto(presence_msg.encode(), (BROADCAST_ADDRESS, UDP_PORT))
            except Exception as e:
                if self.running:
                    self.add_system_message(f"{Colors.RED}Broadcast error: {e}{Colors.RESET}")
            
            time.sleep(DISCOVERY_INTERVAL)
    
    def send_message(self, message: str):
        """Send a message to all peers on the network."""
        if not message.strip():
            return
        
        # Encrypt if in E2EE mode
        if self.mode == 'e2ee' and self.crypto_helper:
            message = self.crypto_helper.encrypt(message)
        
        msg = f"MSG:{self.username}:{message}"
        try:
            self.socket.sendto(msg.encode(), (BROADCAST_ADDRESS, UDP_PORT))
            # Also add to own message list
            self.add_message(self.username, message if self.mode == 'open' else "[Encrypted]")
        except Exception as e:
            self.add_system_message(f"{Colors.RED}Send error: {e}{Colors.RESET}")
    
    def add_message(self, sender: str, content: str):
        """Add a message to the message history."""
        with self.messages_lock:
            timestamp = time.time()
            self.messages.append((timestamp, sender, content))
            # Keep only last 100 messages
            if len(self.messages) > 100:
                self.messages.pop(0)
    
    def add_system_message(self, content: str):
        """Add a system message to the history."""
        timestamp = time.time()
        self.system_messages.append((timestamp, content))
        # Keep only last 20 system messages
        if len(self.system_messages) > 20:
            self.system_messages.pop(0)
    
    def get_messages(self) -> List[Tuple[float, str, str]]:
        """Get all messages."""
        with self.messages_lock:
            return list(self.messages)
    
    def get_system_messages(self) -> List[Tuple[float, str]]:
        """Get all system messages."""
        return list(self.system_messages)

# ============================================================================
# UI HANDLER
# ============================================================================

class UIHandler:
    """Handles the terminal UI rendering."""
    
    def __init__(self, network_handler: NetworkHandler, username: str, mode: str):
        self.network = network_handler
        self.username = username
        self.mode = mode
        self.input_buffer = ""
        self.running = True
        self.last_render_time = 0
        self.render_interval = 0.1  # Minimum time between renders
    
    def clear_screen(self):
        """Clear the terminal screen."""
        # Use cls for Windows, clear for Unix
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def get_terminal_size(self) -> Tuple[int, int]:
        """Get terminal dimensions."""
        try:
            columns, rows = os.get_terminal_size()
        except OSError:
            columns, rows = 80, 24
        return columns, rows
    
    def render(self):
        """Render the complete UI."""
        current_time = time.time()
        if current_time - self.last_render_time < self.render_interval:
            return
        self.last_render_time = current_time
        
        self.clear_screen()
        
        cols, rows = self.get_terminal_size()
        
        # Calculate layout
        header_height = 15  # Logo + banner
        footer_height = 3   # Input area
        chat_height = rows - header_height - footer_height
        
        # Render header (logo)
        self._render_header(cols, header_height)
        
        # Render chat area
        self._render_chat_area(cols, chat_height, header_height)
        
        # Render footer (input)
        self._render_footer(cols, footer_height, rows - footer_height)
    
    def _render_header(self, cols: int, height: int):
        """Render the header with logo and status."""
        # Print logo
        logo = WIFI_LOGO.format(
            cyan=Colors.CYAN,
            green=Colors.GREEN,
            yellow=Colors.YELLOW,
            bright_green=Colors.BRIGHT_GREEN,
            reset=Colors.RESET
        )
        print(logo)
        
        # Print status banner
        encrypted_status = f"{Colors.GREEN}YES{Colors.RESET}" if self.mode == 'e2ee' else f"{Colors.YELLOW}NO{Colors.RESET}"
        peer_count = self.network.peer_manager.get_peer_count()
        
        banner = BANNER.format(
            dim=Colors.DIM,
            bright_cyan=Colors.BRIGHT_CYAN,
            reset=Colors.RESET,
            mode=f"{Colors.BRIGHT_CYAN}{self.mode.upper()}{Colors.RESET}",
            username=f"{Colors.BRIGHT_GREEN}{self.username}{Colors.RESET}",
            encrypted=encrypted_status
        )
        print(banner)
        
        # Print peer info
        peers = self.network.get_active_peers()
        if peers:
            peer_names = ", ".join([p.username for p in peers])
            print(f"{Colors.DIM}Active peers ({len(peers)}): {Colors.BRIGHT_CYAN}{peer_names}{Colors.RESET}")
        else:
            print(f"{Colors.DIM}No active peers detected yet...{Colors.RESET}")
        
        print(f"{Colors.DIM}{'─' * min(cols, 60)}{Colors.RESET}")
    
    def _render_chat_area(self, cols: int, height: int, start_row: int):
        """Render the chat message area."""
        messages = self.network.get_messages()
        system_messages = self.network.get_system_messages()
        
        # Combine and sort all messages by timestamp
        all_entries = []
        for ts, sender, content in messages:
            all_entries.append((ts, 'msg', sender, content))
        for ts, content in system_messages:
            all_entries.append((ts, 'sys', None, content))
        
        all_entries.sort(key=lambda x: x[0])
        
        # Get the most recent messages that fit
        display_messages = all_entries[-height:] if len(all_entries) > height else all_entries
        
        for entry in display_messages:
            ts, msg_type, sender, content = entry
            time_str = datetime.fromtimestamp(ts).strftime('%H:%M:%S')
            
            if msg_type == 'sys':
                # System message
                print(f"{Colors.DIM}[{time_str}] {content}{Colors.RESET}")
            else:
                # Chat message
                if sender == self.username:
                    # Own message - green
                    print(f"{Colors.GREEN}[{time_str}] <{sender}> {content}{Colors.RESET}")
                else:
                    # Others' messages - cyan
                    print(f"{Colors.CYAN}[{time_str}] <{sender}> {content}{Colors.RESET}")
        
        # Fill remaining space if needed
        remaining = height - len(display_messages)
        for _ in range(remaining):
            print()
    
    def _render_footer(self, cols: int, height: int, start_row: int):
        """Render the input footer."""
        print(f"{Colors.DIM}{'─' * min(cols, 60)}{Colors.RESET}")
        
        # Input prompt
        prompt = f"{Colors.BRIGHT_GREEN}┌─[{self.username}@netmsg]{Colors.RESET}"
        print(prompt)
        
        # Input field
        input_line = f"{Colors.BRIGHT_GREEN}│{Colors.RESET} {Colors.WHITE}{self.input_buffer}{Colors.RESET}"
        # Add cursor
        if self.running:
            input_line += f"{Colors.BLINK}█{Colors.RESET}"
        print(input_line)
        
        # Bottom border
        print(f"{Colors.BRIGHT_GREEN}└──>{Colors.RESET} ", end='')
    
    def handle_input(self, char: str):
        """Handle a single character input."""
        if char == '\r' or char == '\n':
            # Enter pressed - send message
            if self.input_buffer.strip():
                self.network.send_message(self.input_buffer)
                self.input_buffer = ""
            return True
        elif char == '\x08' or char == '\x7f':
            # Backspace
            if self.input_buffer:
                self.input_buffer = self.input_buffer[:-1]
        elif char == '\x03':
            # Ctrl+C
            self.running = False
            return False
        elif char == '\x1b':
            # Escape sequence (arrow keys, etc.) - ignore for now
            pass
        elif len(char) == 1 and char.isprintable():
            # Regular character
            self.input_buffer += char
        
        return True

# ============================================================================
# SIMPLE INPUT HANDLER (Cross-platform)
# ============================================================================

def get_char_non_blocking():
    """Get a single character without blocking (cross-platform)."""
    if os.name == 'nt':
        # Windows
        try:
            import msvcrt
            if msvcrt.kbhit():
                char = msvcrt.getwch()
                # Handle escape sequences
                if char == '\xe0' or char == '\x00':
                    # Arrow key or special - read next char
                    msvcrt.getwch()
                    return ''
                return char
        except ImportError:
            pass
    else:
        # Unix/Linux/Mac
        import termios
        import tty
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setcbreak(fd)
            if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
                char = sys.stdin.read(1)
                return char
        except:
            pass
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    
    return None

# Alternative simple input method using threading
class InputHandler:
    """Handles user input in a non-blocking way."""
    
    def __init__(self, ui_handler: UIHandler):
        self.ui = ui_handler
        self.running = True
        self.input_thread = None
    
    def start(self):
        """Start the input handling thread."""
        self.input_thread = threading.Thread(target=self._input_loop, daemon=True)
        self.input_thread.start()
    
    def _input_loop(self):
        """Continuously handle user input."""
        if os.name == 'nt':
            # Windows implementation
            try:
                import msvcrt
                while self.running and self.ui.running:
                    if msvcrt.kbhit():
                        char = msvcrt.getwch()
                        if char == '\xe0' or char == '\x00':
                            # Special key - consume next character
                            msvcrt.getwch()
                            continue
                        self.ui.handle_input(char)
                    time.sleep(0.05)
            except ImportError:
                # Fallback for systems without msvcrt
                self._unix_input_loop()
        else:
            # Unix implementation
            self._unix_input_loop()
    
    def _unix_input_loop(self):
        """Unix-style input loop using termios."""
        import termios
        import tty
        import select
        
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        
        try:
            tty.setcbreak(fd)
            while self.running and self.ui.running:
                if select.select([sys.stdin], [], [], 0.1)[0]:
                    char = sys.stdin.read(1)
                    if char:
                        self.ui.handle_input(char)
        except Exception as e:
            print(f"{Colors.RED}Input error: {e}{Colors.RESET}")
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    
    def stop(self):
        """Stop the input handler."""
        self.running = False

# ============================================================================
# MAIN APPLICATION
# ============================================================================

def print_banner():
    """Print the application banner."""
    print(WIFI_LOGO.format(
        cyan=Colors.CYAN,
        green=Colors.GREEN,
        yellow=Colors.YELLOW,
        bright_green=Colors.BRIGHT_GREEN,
        reset=Colors.RESET
    ))

def get_user_input(prompt: str, default: str = None) -> str:
    """Get user input with optional default value."""
    if default:
        full_prompt = f"{Colors.BRIGHT_CYAN}{prompt}{Colors.RESET} [{default}]: "
    else:
        full_prompt = f"{Colors.BRIGHT_CYAN}{prompt}{Colors.RESET}: "
    
    try:
        value = input(full_prompt).strip()
        return value if value else default
    except (EOFError, KeyboardInterrupt):
        print(f"\n{Colors.RED}Input cancelled.{Colors.RESET}")
        sys.exit(0)

def main():
    """Main entry point for the application."""
    # Check for cryptography library
    if not CRYPTO_AVAILABLE:
        print(f"{Colors.YELLOW}Warning: cryptography library not installed.{Colors.RESET}")
        print(f"{Colors.YELLOW}E2EE mode will not be available.{Colors.RESET}")
        print(f"{Colors.DIM}Install with: pip install cryptography{Colors.RESET}\n")
    
    print_banner()
    
    # Get username
    print(f"{Colors.BRIGHT_CYAN}=== SETUP ==={Colors.RESET}")
    username = get_user_input("Enter your username", "Anonymous")
    if not username:
        username = "Anonymous"
    
    # Validate username
    username = ''.join(c for c in username if c.isalnum() or c in '_-')[:20]
    if not username:
        username = "Anonymous"
    
    # Choose mode
    print(f"\n{Colors.BRIGHT_CYAN}Select mode:{Colors.RESET}")
    print(f"  {Colors.GREEN}1{Colors.RESET}. Open Mode (plain text, visible to all)")
    print(f"  {Colors.CYAN}2{Colors.RESET}. E2EE Mode (encrypted, requires shared passphrase)")
    
    if CRYPTO_AVAILABLE:
        mode_choice = get_user_input("Choose mode", "1")
    else:
        print(f"{Colors.YELLOW}E2EE not available (cryptography not installed). Using Open Mode.{Colors.RESET}")
        mode_choice = "1"
    
    mode = 'open'
    crypto_helper = None
    
    if mode_choice == '2' and CRYPTO_AVAILABLE:
        mode = 'e2ee'
        print(f"\n{Colors.BRIGHT_CYAN}=== E2EE SETUP ==={Colors.RESET}")
        print(f"{Colors.DIM}All users must enter the SAME passphrase to communicate.{Colors.RESET}")
        passphrase = get_user_input("Enter shared passphrase")
        
        if not passphrase:
            print(f"{Colors.RED}Passphrase required for E2EE mode. Falling back to Open Mode.{Colors.RESET}")
            mode = 'open'
        else:
            try:
                crypto_helper = CryptoHelper(passphrase)
                print(f"{Colors.GREEN}✓ Encryption initialized successfully{Colors.RESET}")
            except Exception as e:
                print(f"{Colors.RED}Failed to initialize encryption: {e}{Colors.RESET}")
                print(f"{Colors.YELLOW}Falling back to Open Mode.{Colors.RESET}")
                mode = 'open'
    
    print(f"\n{Colors.BRIGHT_GREEN}╔════════════════════════════════════════╗{Colors.RESET}")
    print(f"{Colors.BRIGHT_GREEN}║{Colors.RESET}  {Colors.BRIGHT_CYAN}Starting NetMsg v1.0{Colors.RESET}              {Colors.BRIGHT_GREEN}║{Colors.RESET}")
    print(f"{Colors.BRIGHT_GREEN}╚════════════════════════════════════════╝{Colors.RESET}")
    print(f"\n{Colors.DIM}Press Ctrl+C to exit{Colors.RESET}\n")
    time.sleep(1.5)
    
    # Initialize network handler
    network = NetworkHandler(username, mode, crypto_helper)
    network.start()
    
    # Initialize UI handler
    ui = UIHandler(network, username, mode)
    
    # Initialize input handler
    input_handler = InputHandler(ui)
    input_handler.start()
    
    # Main loop
    try:
        while ui.running:
            ui.render()
            time.sleep(0.1)
    except KeyboardInterrupt:
        pass
    finally:
        # Cleanup
        ui.running = False
        input_handler.stop()
        network.stop()
        
        print(f"\n{Colors.BRIGHT_CYAN}Goodbye!{Colors.RESET}")
        print(f"{Colors.DIM}Messages sent: {len(network.get_messages())}{Colors.RESET}")
        print(f"{Colors.DIM}Session ended at {datetime.now().strftime('%H:%M:%S')}{Colors.RESET}\n")

if __name__ == "__main__":
    # Import select for Unix input handling
    if os.name != 'nt':
        import select
    
    main()
