import socket
import threading
import time
import os
import sys
import random
import json
from datetime import datetime

# Try to import cryptography, handle missing gracefully
try:
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.backends import default_backend
    from cryptography.fernet import Fernet
    import base64
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False

# --- Configuration ---
UDP_PORT = 50050
BROADCAST_IP = "255.255.255.255"
BUFFER_SIZE = 2048
PEER_TIMEOUT = 15  # Seconds before a peer is considered offline

# --- Colors & Styles (ANSI) ---
class Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    
    # Backgrounds
    BG_HEADER = "\033[44m"       # Blue
    BG_CHAT = "\033[48;5;234m"   # Very Dark Gray (Almost Black)
    BG_INPUT = "\033[48;5;236m"  # Dark Gray
    BG_MY_MSG = "\033[48;5;22m"  # Dark Green
    BG_OTHER_MSG = "\033[48;5;24m" # Dark Blue
    
    # Text
    TEXT_HEADER = "\033[97m"     # Bright White
    TEXT_MY_NAME = "\033[92m"    # Green
    TEXT_OTHER_NAME = "\033[96m" # Cyan
    TEXT_ERROR = "\033[91m"      # Red
    TEXT_SYSTEM = "\033[93m"     # Yellow
    TEXT_TIME = "\033[90m"       # Gray

    # Cursor
    HIDE_CURSOR = "\033[?25l"
    SHOW_CURSOR = "\033[?25h"

# --- ASCII Art Logo (Wider & Cleaner) ---
LOGO = """
  __      __  ________  _______  __    __  _______ 
 |  \    /  ||        ||       ||  |  |  ||       |
 |   \  /   |   _____| |   _   ||   | |  ||    ___|
 |        \  |  |_____  |  | |  ||    |_|  ||   |___ 
 |   |\   | |   _____| |  |_|  ||       __||    ___|
 |   | \  | |  |_____| |       ||   __|   ||   |___ 
 |___|  \__||________| |_______||__|  |__||_______|
                                                   
      📻 The Friendly Local Network Messenger
"""

class WiFIMessenger:
    def __init__(self):
        self.username = ""
        self.mode = "public"  # 'public' or 'secret'
        self.secret_key = None
        self.socket = None
        self.peers = {}  # {ip: last_seen_time}
        self.messages = [] # List of formatted message strings
        self.running = True
        self.width = 80 # Default, updated on draw
        
        # Setup Input Handling based on OS
        if os.name == 'nt': # Windows
            import msvcrt
            self.get_key = lambda: msvcrt.getch().decode('utf-8', errors='ignore')
        else: # Linux/Mac
            import tty, termios
            self.fd = sys.stdin.fileno()
            self.old_settings = termios.tcgetattr(self.fd)
            tty.setraw(self.fd)
            self.get_key = lambda: sys.stdin.read(1)

    def setup_crypto(self, password):
        if not CRYPTO_AVAILABLE:
            print(f"{Colors.TEXT_ERROR}Error: 'cryptography' library not installed.{Colors.RESET}")
            print(f"Run: pip install cryptography")
            return False
        
        salt = b'WiF-Walkie-Salt!' # Static salt for simplicity in this demo
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        self.secret_key = Fernet(key)
        return True

    def encrypt_msg(self, text):
        if self.mode == "public" or not self.secret_key:
            return text
        return self.secret_key.encrypt(text.encode()).decode()

    def decrypt_msg(self, text):
        if self.mode == "public" or not self.secret_key:
            return text
        try:
            return self.secret_key.decrypt(text.encode()).decode()
        except Exception:
            return "<Encrypted Message - Wrong Password?>"

    def init_socket(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.socket.settimeout(1.0) # Non-blocking receive
        
        # Bind to all interfaces
        try:
            self.socket.bind(("0.0.0.0", UDP_PORT))
        except OSError as e:
            print(f"{Colors.TEXT_ERROR}Failed to bind port {UDP_PORT}. Is another instance running?{Colors.RESET}")
            self.running = False

    def send_message(self, msg_type, content):
        if not self.socket: return
        
        data = {
            "type": msg_type, # 'msg', 'join', 'leave', 'ping'
            "user": self.username,
            "content": content,
            "time": datetime.now().strftime("%H:%M")
        }
        
        packet = json.dumps(data).encode('utf-8')
        
        if msg_type == 'msg':
            packet_str = self.encrypt_msg(json.dumps(data))
            # Send encrypted string if in secret mode, else normal json
            if self.mode == 'secret':
                final_packet = packet_str.encode('utf-8')
            else:
                final_packet = packet
        else:
            final_packet = packet
            
        try:
            self.socket.sendto(final_packet, (BROADCAST_IP, UDP_PORT))
        except Exception as e:
            pass # Ignore network glitches

    def receive_loop(self):
        while self.running:
            try:
                data, addr = self.socket.recvfrom(BUFFER_SIZE)
                ip = addr[0]
                
                # Update peer presence
                self.peers[ip] = time.time()
                
                # Decode
                try:
                    decoded = data.decode('utf-8')
                    if self.mode == 'secret':
                        # In secret mode, we expect an encrypted string directly if it's a msg
                        # But join/leave might still be plain? For simplicity, let's assume all are encrypted in secret mode
                        # Actually, to keep it simple: if secret mode, we try to decrypt. If fails, ignore.
                        try:
                            decrypted_json = self.decrypt_msg(decoded)
                            payload = json.loads(decrypted_json)
                        except:
                            continue # Skip undecryptable packets
                    else:
                        payload = json.loads(decoded)
                    
                    msg_type = payload.get("type")
                    user = payload.get("user", "Unknown")
                    content = payload.get("content", "")
                    timestamp = payload.get("time", "")

                    if msg_type == 'msg':
                        self.add_message(user, content, timestamp, is_me=(ip == self.get_local_ip()))
                    elif msg_type == 'join':
                        if user != self.username:
                            self.add_system(f"👋 {user} joined the walkie-talkie!")
                    elif msg_type == 'leave':
                        if user != self.username:
                            self.add_system(f"👋 {user} left the walkie-talkie.")
                            
                except json.JSONDecodeError:
                    continue # Ignore garbage packets
                    
            except socket.timeout:
                continue
            except Exception as e:
                time.sleep(1)

    def get_local_ip(self):
        # Helper to get current IP for comparison
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(('8.8.8.8', 80))
            return s.getsockname()[0]
        except:
            return "127.0.0.1"
        finally:
            s.close()

    def add_message(self, user, content, timestamp, is_me=False):
        # Format: [Time] User: Content
        # We store raw data to render dynamically based on width
        self.messages.append({
            "time": timestamp,
            "user": user,
            "content": content,
            "is_me": is_me
        })
        # Keep only last 100 messages to save memory
        if len(self.messages) > 100:
            self.messages.pop(0)

    def add_system(self, text):
        self.messages.append({
            "time": datetime.now().strftime("%H:%M"),
            "user": "SYSTEM",
            "content": text,
            "is_me": False,
            "is_system": True
        })
        if len(self.messages) > 100:
            self.messages.pop(0)

    def draw_ui(self, input_buffer=""):
        if not self.running: return
        
        # Get terminal size
        try:
            cols, rows = os.get_terminal_size()
        except:
            cols, rows = 100, 30
            
        self.width = cols
        mid_width = int(cols * 0.90) # 90% width
        start_pad = int((cols - mid_width) / 2)
        
        # Clear Screen (Optimized)
        sys.stdout.write("\033[H\033[J")
        sys.stdout.write(Colors.HIDE_CURSOR)
        
        padding = " " * start_pad
        
        # --- HEADER ---
        sys.stdout.write(f"{Colors.BG_HEADER}{Colors.TEXT_HEADER}{Colors.BOLD}")
        sys.stdout.write(" " * cols + "\n")
        
        # Draw Logo centered
        logo_lines = LOGO.split('\n')
        for line in logo_lines[:5]: # Top part of logo
            centered = line.center(cols)
            sys.stdout.write(f"{padding}{centered}\n")
            
        sys.stdout.write(f"{padding}{'─' * mid_width}\n")
        sys.stdout.write(f"{padding} Mode: {Colors.BOLD}{self.mode.upper()}{Colors.RESET}{Colors.BG_HEADER}{Colors.TEXT_HEADER}  |  User: {Colors.BOLD}{self.username}{Colors.RESET}{Colors.BG_HEADER}\n")
        sys.stdout.write(" " * cols + "\n")
        sys.stdout.write(f"{Colors.RESET}")

        # --- CHAT AREA ---
        # Calculate available lines for chat
        header_lines = 10
        footer_lines = 4
        chat_height = rows - header_lines - footer_lines
        
        sys.stdout.write(f"{Colors.BG_CHAT}")
        
        # Render messages from bottom up
        visible_msgs = self.messages[-chat_height:]
        
        for msg in visible_msgs:
            if msg.get("is_system"):
                # System message centered
                sys_text = f"✦ {msg['content']} ✦"
                centered_sys = sys_text.center(mid_width)
                sys.stdout.write(f"{Colors.TEXT_SYSTEM}{Colors.DIM}{padding}{centered_sys}{Colors.RESET}{Colors.BG_CHAT}\n")
            else:
                # Chat bubble
                prefix = "✓" if msg['is_me'] else "💬"
                color_bg = Colors.BG_MY_MSG if msg['is_me'] else Colors.BG_OTHER_MSG
                color_name = Colors.TEXT_MY_NAME if msg['is_me'] else Colors.TEXT_OTHER_NAME
                
                # Wrap content
                max_content_width = mid_width - 15 # Reserve space for name/time
                words = msg['content'].split()
                lines = []
                current_line = ""
                for word in words:
                    if len(current_line) + len(word) + 1 < max_content_width:
                        current_line += (" " if current_line else "") + word
                    else:
                        lines.append(current_line)
                        current_line = word
                if current_line:
                    lines.append(current_line)
                
                # Draw first line with header
                header_part = f"[{msg['time']}] {color_name}{msg['user']}{Colors.RESET}: "
                first_line_content = lines[0] if lines else ""
                
                # Construct full line
                if msg['is_me']:
                    # Right align logic is tricky with wrapping, so we left align but style differently
                    full_line = f"{prefix} {header_part}{first_line_content}"
                    # Pad right to fill bubble visually if needed, or just let it flow
                    sys.stdout.write(f"{color_bg}{padding}{full_line.ljust(mid_width)}{Colors.RESET}\n")
                else:
                    full_line = f"{prefix} {header_part}{first_line_content}"
                    sys.stdout.write(f"{color_bg}{padding}{full_line.ljust(mid_width)}{Colors.RESET}\n")
                
                # Draw wrapped lines
                for line in lines[1:]:
                    indent = " " * 15
                    sys.stdout.write(f"{color_bg}{padding}{indent}{line.ljust(max_content_width)}{Colors.RESET}\n")

        sys.stdout.write(f"{Colors.RESET}")

        # --- FOOTER / INPUT ---
        sys.stdout.write(f"{Colors.BG_INPUT}{' ' * cols}\n")
        
        prompt = f"📝 {self.username} > "
        display_input = input_buffer
        
        # Truncate input if too long
        max_input_len = mid_width - len(prompt) - 2
        if len(display_input) > max_input_len:
            display_input = "..." + display_input[-max_input_len+3:]
            
        sys.stdout.write(f"{Colors.BG_INPUT}{Colors.TEXT_HEADER}{padding}{prompt}{display_input}{Colors.RESET}\n")
        
        # Peer Count
        active_peers = sum(1 for t in self.peers.values() if time.time() - t < PEER_TIMEOUT)
        status_text = f"📶 Online: {active_peers} devices"
        sys.stdout.write(f"{Colors.BG_INPUT}{Colors.DIM}{padding}{status_text.rjust(mid_width)}{Colors.RESET}\n")
        sys.stdout.write(f"{Colors.BG_INPUT}{' ' * cols}\n")
        
        sys.stdout.flush()

    def input_loop(self):
        buffer = ""
        last_draw = 0
        
        # Announce join
        time.sleep(0.5)
        self.send_message("join", "")
        
        # Start periodic pings and cleanup
        def peer_manager():
            while self.running:
                now = time.time()
                # Remove old peers
                dead_peers = [ip for ip, t in self.peers.items() if now - t > PEER_TIMEOUT]
                for ip in dead_peers:
                    del self.peers[ip]
                
                # Send ping
                self.send_message("ping", "")
                time.sleep(5)
        
        threading.Thread(target=peer_manager, daemon=True).start()

        while self.running:
            try:
                key = self.get_key()
                
                if key == '\r' or key == '\n': # Enter
                    if buffer.strip():
                        self.send_message("msg", buffer)
                        # Add my own message locally immediately
                        self.add_message(self.username, buffer, datetime.now().strftime("%H:%M"), is_me=True)
                        buffer = ""
                    self.draw_ui(buffer)
                    
                elif key == '\x08' or key == '\x7f': # Backspace
                    if buffer:
                        buffer = buffer[:-1]
                    self.draw_ui(buffer)
                    
                elif key == '\x03': # Ctrl+C
                    raise KeyboardInterrupt
                    
                elif len(key) == 1 and key.isprintable():
                    buffer += key
                    self.draw_ui(buffer)
                    
                # Auto redraw periodically to update peer count/timestamps if idle
                if time.time() - last_draw > 2:
                    self.draw_ui(buffer)
                    last_draw = time.time()
                    
            except Exception as e:
                break

        # Cleanup
        self.send_message("leave", "")
        sys.stdout.write(Colors.SHOW_CURSOR + Colors.RESET)
        print(f"\n{Colors.TEXT_SYSTEM}Goodbye! Thanks for using Wi-Fi Walkie-Talkie.{Colors.RESET}\n")

    def run(self):
        # Clear screen initially
        os.system('cls' if os.name == 'nt' else 'clear')
        
        print(f"{Colors.TEXT_HEADER}{Colors.BOLD}")
        print(LOGO)
        print(f"{Colors.RESET}")
        
        # Get Username
        while not self.username:
            u = input(f"{Colors.TEXT_CYAN}Enter your nickname: {Colors.RESET}").strip()
            if u: self.username = u
            
        # Get Mode
        print("\nSelect Mode:")
        print("1. 🌍 Public (Open Chat)")
        print("2. 🔒 Secret (Encrypted)")
        
        choice = input(f"{Colors.TEXT_CYAN}Choice [1/2]: {Colors.RESET}").strip()
        if choice == '2':
            self.mode = 'secret'
            if not CRYPTO_AVAILABLE:
                print(f"{Colors.TEXT_ERROR}Error: Cryptography library missing. Install with 'pip install cryptography'{Colors.RESET}")
                return
            pwd = input(f"{Colors.TEXT_CYAN}Enter a shared secret word: {Colors.RESET}").strip()
            if not self.setup_crypto(pwd):
                return
            print(f"{Colors.TEXT_GREEN}✅ Encrypted Channel Established.{Colors.RESET}")
        else:
            self.mode = 'public'
            
        time.sleep(1)
        
        # Init Network
        self.init_socket()
        if not self.running: return
        
        # Start Threads
        recv_thread = threading.Thread(target=self.receive_loop, daemon=True)
        recv_thread.start()
        
        # Start UI Loop
        try:
            self.input_loop()
        except KeyboardInterrupt:
            self.running = False

if __name__ == "__main__":
    try:
        app = WiFIMessenger()
        app.run()
    except Exception as e:
        print(f"{Colors.TEXT_ERROR}Critical Error: {e}{Colors.RESET}")
        sys.exit(1)
