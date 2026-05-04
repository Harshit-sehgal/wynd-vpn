#!/usr/bin/env python3
"""
WYND Windows System-Wide VPN
Tries multiple methods to route ALL Windows traffic through port 53
"""
import socket
import struct
import threading
import subprocess
import os
import sys
import time
import json

SERVER = "161.118.177.7"
SERVER_PORT = 53
SOCKS_PORT = 1080

class WYNDSystemVPN:
    def __init__(self):
        self.running = True
        
    def connect_to_server(self):
        """Connect to WYND server"""
        print(f"Connecting to {SERVER}:{SERVER_PORT}...")
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.connect((SERVER, SERVER_PORT))
        print("Connected to WYND server!")
        
    def handle_socks_client(self, client_sock, client_addr):
        """Handle SOCKS5 client"""
        try:
            # SOCKS5 greeting
            ver = client_sock.recv(1)
            if ver != b'\x05':
                return
            
            nmethods = client_sock.recv(1)
            methods = client_sock.recv(ord(nmethods))
            client_sock.send(b'\x05\x00')  # No auth
            
            # SOCKS5 request
            cmd = client_sock.recv(1)
            addr_type = client_sock.recv(1)
            
            target = ""
            if addr_type == b'\x01':  # IPv4
                ip = client_sock.recv(4)
                target = socket.inet_ntoa(ip)
            elif addr_type == b'\x03':  # Domain
                length = client_sock.recv(1)
                target = client_sock.recv(ord(length)).decode()
                
            port = struct.unpack('!H', client_sock.recv(2))[0]
            
            # Connect through our server (using custom protocol)
            # Format: CONNECT(1) + ADDR_TYPE(1) + IP/DOMAIN + PORT(2)
            if addr_type == b'\x01':
                request = b'\x01' + ip + struct.pack('!H', port)
            else:
                request = b'\x03' + target.encode() + struct.pack('!H', port)
                
            self.server.sendall(struct.pack('!H', len(request)) + request)
            
            # Get response
            resp_header = self.server.recv(2)
            resp_len = struct.unpack('!H', resp_header)[0]
            if resp_len > 0:
                resp = self.server.recv(resp_len)
            
            # Tell client success
            client_sock.send(b'\x05\x00\x00\x01\x00\x00\x00\x00\x00\x00')
            
            # Bridge connections
            def forward(src, dst):
                try:
                    while True:
                        data = src.recv(4096)
                        if not data:
                            break
                        dst.sendall(data)
                except:
                    pass
                    
            t1 = threading.Thread(target=forward, args=(client_sock, self.server))
            t2 = threading.Thread(target=forward, args=(self.server, client_sock))
            t1.start()
            t2.start()
            t1.join()
            t2.join()
            
        except Exception as e:
            print(f"Client error: {e}")
        finally:
            try:
                client_sock.close()
            except:
                pass
    
    def start_proxy(self):
        """Start SOCKS5 proxy"""
        proxy = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        proxy.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        proxy.bind(('127.0.0.1', SOCKS_PORT))
        proxy.listen(10)
        
        print(f"SOCKS5 proxy listening on 127.0.0.1:{SOCKS_PORT}")
        
        while self.running:
            try:
                proxy.settimeout(1)
                client, addr = proxy.accept()
                print(f"Connection from {addr}")
                t = threading.Thread(target=self.handle_socks_client, args=(client, addr))
                t.daemon = True
                t.start()
            except socket.timeout:
                continue
            except:
                break
    
    def setup_windows_proxy(self):
        """Configure Windows to use our proxy"""
        print("\n" + "="*50)
        print("WINDOWS CONFIGURATION")
        print("="*50)
        
        # Method 1: WinHTTP proxy
        print("\n[Method 1] WinHTTP Proxy:")
        print("  netsh winhttp set proxy 127.0.0.1:1080")
        try:
            subprocess.run(['netsh', 'winhttp', 'set', 'proxy', f'127.0.0.1:{SOCKS_PORT}'], 
                         capture_output=True, timeout=5)
            print("  -> Applied! (Affects some Windows components)")
        except:
            print("  -> Failed (needs admin)")
        
        # Method 2: IE/Edge proxy
        print("\n[Method 2] Registry for IE/Edge:")
        reg_commands = [
            'reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Internet Settings" /v ProxyEnable /t REG_DWORD /d 1 /f',
            f'reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Internet Settings" /v ProxyServer /t REG_SZ /d "127.0.0.1:{SOCKS_PORT}" /f'
        ]
        
        for cmd in reg_commands:
            try:
                subprocess.run(cmd, shell=True, capture_output=True, timeout=5)
            except:
                pass
        print("  -> Applied to registry!")
        
        # Method 3: AppContainer loopback (for Windows Store apps)
        print("\n[Method 3] For Windows Store apps:")
        print("  Note: Requires separate config")
        
        print("\n" + "="*50)
        print("USAGE INSTRUCTIONS")
        print("="*50)
        
        print(f"""
To use with apps, configure them to use:
  SOCKS5 Proxy: 127.0.0.1:{SOCKS_PORT}

APPS WITH SOCKS5 SUPPORT:
- Chrome (with SwitchyOmega extension)
- Firefox (manual proxy settings)
- Telegram
- Discord (SOCKS5 support)
- Some games with proxy support

FOR FULL SYSTEM:
1. Download proxychains from: github.com/rofl0r/proxychains-ng
2. Edit proxychains.conf: socks5 127.0.0.1 {SOCKS_PORT}
3. Run: proxychains your_app.exe

Examples:
  proxychains cmd.exe /c dir
  proxychains powershell
  proxychainsteams.exe
  proxychains discord.exe
        """)
        
    def run(self):
        print("="*50)
        print("WYND Windows System-Wide VPN")
        print("="*50)
        
        # Connect to server
        self.connect_to_server()
        
        # Configure Windows
        self.setup_windows_proxy()
        
        # Start proxy
        print("\nStarting SOCKS5 proxy server...")
        self.start_proxy()

if __name__ == "__main__":
    vpn = WYNDSystemVPN()
    try:
        vpn.run()
    except KeyboardInterrupt:
        print("\nStopping...")
        vpn.running = False