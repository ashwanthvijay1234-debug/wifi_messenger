import socket
import threading
import time
import os
import sys
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
PEER_TIMEOUT = 15 

# --- Colors & Styles (ANSI) ---
class Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    
    # Backgrounds
    BG_HEADER = "\033[44m"       
    BG_CHAT = "\033[48;5;234m"   
    BG_INPUT = "\033[48;5;236m"  
    BG_MY_MSG = "\033[48;5;22m"  
    BG_OTHER_MSG = "\033[48;5;24m" 
    TEXT_CYAN = "\033[96m"   # Added this
    TEXT_GREEN = "\033[92m"  # Added this just in case
    
    # Text
    TEXT_HEADER = "\033[97m"     
    TEXT_MY_NAME = "\033[92m"    
    TEXT_OTHER_NAME = "\033[96m" 
    TEXT_CYAN = "\033[96m"       # <--- FIXED: Added missing attribute
    TEXT_ERROR = "\033[91m"      
    TEXT_SYSTEM = "\033[93m"     
    TEXT_TIME = "\033[90m"       
    TEXT_GREEN = "\033[92m"      # <--- Added for the success message

    HIDE_CURSOR = "\033[?25l"
    SHOW_CURSOR = "\033[?25h"

LOGO = """
  __      __  ________  _______  __    __  _______ 
 |  \    /  ||        ||        ||  |  |  ||       |
 |   \  /   |  _____| |   _   ||   | |  ||    ___|
 |        \  |  |_____  |  | |  ||    |_|  ||   |___ 
 |   |\   | |   _____| |  |_|  ||        __||    ___|
 |   | \  | |  |_____| |       ||    __|   ||   |___ 
 |___|  \__||________| |_______||__|  |__||_______|
                                                   
      📻 The Friendly Local Network Messenger
"""

class WiFIMessenger:
    def __init__(self):
        self.username = ""
        self.mode = "public"
        self.secret_key = None
        self.socket = None
        self.peers = {}
        self.messages = []
        self.running = True
        self.width = 80
        
        if os.name == 'nt':
            import msvcrt
            # Improved Windows key handling to prevent decoding crashes
            def get_key_win():
                char = msvcrt.getch()
                try:
                    return char.decode('utf-8')
                except:
                    return ""
            self.get_key = get_key_win
        else:
            import tty, termios
            self.fd = sys.stdin.fileno()
            self.get_key = self.get_key_unix

    def get_key_unix(self):
        import tty, termios
        old_settings = termios.tcgetattr(self.fd)
        try:
            tty.setraw(self.fd)
            return sys.stdin.read(1)
        finally:
            termios.tcsetattr(self.fd, termios.TCSADRAIN, old_settings)

    def setup_crypto(self, password):
        if not CRYPTO_AVAILABLE:
            return False
        salt = b'WiF-Walkie-Salt!'
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
        except:
            return None

    def init_socket(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.socket.settimeout(0.5)
        try:
            self.socket.bind(("0.0.0.0", UDP_PORT))
        except OSError:
            self.running = False

    def send_message(self, msg_type, content):
        if not self.socket: return
        data = {
            "type": msg_type,
            "user": self.username,
            "content": content,
            "time": datetime.now().strftime("%H:%M")
        }
        raw_json = json.dumps(data)
        if self.mode == 'secret':
            payload = self.encrypt_msg(raw_json).encode('utf-8')
        else:
            payload = raw_json.encode('utf-8')
        try:
            self.socket.sendto(payload, (BROADCAST_IP, UDP_PORT))
        except:
            pass

    def receive_loop(self):
        local_ip = self.get_local_ip()
        while self.running:
            try:
                data, addr = self.socket.recvfrom(BUFFER_SIZE)
                ip = addr[0]
                if ip == local_ip: continue
                
                self.peers[ip] = time.time()
                decoded = data.decode('utf-8')
                
                if self.mode == 'secret':
                    decrypted = self.decrypt_msg(decoded)
                    if decrypted:
                        payload = json.loads(decrypted)
                    else:
                        continue
                else:
                    payload = json.loads(decoded)
                
                msg_type = payload.get("type")
                user = payload.get("user", "Unknown")
                content = payload.get("content", "")
                timestamp = payload.get("time", "")

                if msg_type == 'msg':
                    self.add_message(user, content, timestamp, is_me=False)
                elif msg_type == 'join':
                    self.add_system(f"👋 {user} joined!")
                elif msg_type == 'leave':
                    self.add_system(f"👋 {user} left.")
            except:
                continue

    def get_local_ip(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(('8.8.8.8', 80))
            return s.getsockname()[0]
        except:
            return "127.0.0.1"
        finally:
            s.close()

    def add_message(self, user, content, timestamp, is_me=False):
        self.messages.append({"time": timestamp, "user": user, "content": content, "is_me": is_me})
        if len(self.messages) > 100: self.messages.pop(0)

    def add_system(self, text):
        self.messages.append({"time": datetime.now().strftime("%H:%M"), "content": text, "is_system": True})
        if len(self.messages) > 100: self.messages.pop(0)

    def draw_ui(self, input_buffer=""):
        if not self.running: return
        try:
            cols, rows = os.get_terminal_size()
        except:
            cols, rows = 80, 24
            
        sys.stdout.write("\033[H\033[J" + Colors.HIDE_CURSOR)
        mid_w = int(cols * 0.95)
        pad = " " * int((cols - mid_w) / 2)
        
        # Header
        sys.stdout.write(f"{Colors.BG_HEADER}{Colors.TEXT_HEADER}{' ' * cols}\n")
        for line in LOGO.split('\n'):
            if line.strip(): sys.stdout.write(f"{pad}{line.center(mid_w)}\n")
        sys.stdout.write(f"{pad}{'─' * mid_w}\n")
        sys.stdout.write(f"{pad} Mode: {self.mode.upper()} | User: {self.username}\n")
        sys.stdout.write(f"{' ' * cols}{Colors.RESET}\n")

        # Chat
        chat_h = rows - 12
        visible = self.messages[-chat_h:]
        sys.stdout.write(Colors.BG_CHAT)
        for msg in visible:
            if msg.get("is_system"):
                sys.stdout.write(f"{Colors.TEXT_SYSTEM}{pad}{msg['content'].center(mid_w)}{Colors.RESET}{Colors.BG_CHAT}\n")
            else:
                c_name = Colors.TEXT_MY_NAME if msg['is_me'] else Colors.TEXT_OTHER_NAME
                sys.stdout.write(f"{pad}[{msg['time']}] {c_name}{msg['user']}{Colors.RESET}{Colors.BG_CHAT}: {msg['content']}\n")
        
        # Fill empty space
        for _ in range(chat_h - len(visible)): sys.stdout.write("\n")

        # Footer
        sys.stdout.write(f"{Colors.BG_INPUT}{' ' * cols}\n")
        sys.stdout.write(f"{pad}📝 {self.username} > {input_buffer}\n")
        active = sum(1 for t in self.peers.values() if time.time() - t < PEER_TIMEOUT)
        sys.stdout.write(f"{Colors.DIM}{pad}{('📶 Online: ' + str(active)).rjust(mid_w)}{Colors.RESET}\n")
        sys.stdout.flush()

    def input_loop(self):
        buffer = ""
        self.send_message("join", "")
        
        def pinger():
            while self.running:
                self.send_message("ping", "")
                time.sleep(5)
        threading.Thread(target=pinger, daemon=True).start()

        while self.running:
            self.draw_ui(buffer)
            key = self.get_key()
            if key in ('\r', '\n'):
                if buffer.strip():
                    self.send_message("msg", buffer)
                    self.add_message(self.username, buffer, datetime.now().strftime("%H:%M"), True)
                    buffer = ""
            elif key in ('\x08', '\x7f'):
                buffer = buffer[:-1]
            elif key == '\x03':
                break
            elif len(key) == 1 and key.isprintable():
                buffer += key

    def run(self):
        os.system('cls' if os.name == 'nt' else 'clear')
        print(Colors.BOLD + LOGO + Colors.RESET)
        
        while not self.username:
            self.username = input(f"{Colors.TEXT_CYAN}Nickname: {Colors.RESET}").strip()
            
        print("\n1. Public  2. Secret")
        if input("Choice: ").strip() == '2':
            self.mode = 'secret'
            pwd = input("Secret word: ")
            self.setup_crypto(pwd)
        
        self.init_socket()
        if not self.running:
            print(f"{Colors.TEXT_ERROR}Error: Could not initialize socket. Is another instance running?{Colors.RESET}")
            return

        threading.Thread(target=self.receive_loop, daemon=True).start()
        try:
            self.input_loop()
        except (KeyboardInterrupt, SystemExit):
            self.running = False
        finally:
            try:
                self.send_message("leave", "")
            except:
                pass
            sys.stdout.write(Colors.SHOW_CURSOR + Colors.RESET)
            print(f"\n{Colors.TEXT_CYAN}Goodbye!{Colors.RESET}\n")

if __name__ == "__main__":
    WiFIMessenger().run()
