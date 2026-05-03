#!/usr/bin/env python3
"""
WYND SOCKS5 Proxy Server
Runs on port 53, forwards traffic through TUN interface
"""

import socket
import struct
import threading
import signal
import sys
import os

PORT = 53
TUN_IP = "10.0.0.1"

class WYNDSOCKS5:
    def __init__(self):
        self.running = True
        
    def setup_tun(self):
        """Set up TUN interface"""
        os.system("ip tuntap add mode tun dev tun0 2>/dev/null")
        os.system("ip addr add 10.0.0.1/24 dev tun0 2>/dev/null")
        os.system("ip link set tun0 up 2>/dev/null")
        os.system("iptables -t nat -A POSTROUTING -s 10.0.0.0/24 -j MASQUERADE 2>/dev/null")
        os.system("iptables -A FORWARD -i tun0 -j ACCEPT 2>/dev/null")
        print("TUN interface configured: 10.0.0.1/24")
    
    def handle_client(self, client_sock, client_addr):
        """Handle SOCKS5 connection"""
        try:
            # SOCKS5 greeting
            ver = client_sock.recv(1)
            if ver != b'\x05':
                client_sock.close()
                return
            
            nmethods = client_sock.recv(1)
            methods = client_sock.recv(ord(nmethods))
            
            # No auth
            client_sock.send(b'\x05\x00')
            
            # SOCKS request
            ver = client_sock.recv(1)
            cmd = client_sock.recv(1)
            _ = client_sock.recv(1)  # reserved
            addr_type = client_sock.recv(1)
            
            if addr_type == b'\x01':  # IPv4
                target = socket.inet_ntoa(client_sock.recv(4))
            elif addr_type == b'\x03':  # Domain
                domain_len = client_sock.recv(1)
                target = client_sock.recv(ord(domain_len)).decode()
            else:
                client_sock.close()
                return
                
            port = struct.unpack('!H', client_sock.recv(2))[0]
            
            print(f"[{client_addr}] {cmd} {target}:{port}")
            
            # Connect to target
            try:
                remote_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                remote_sock.connect((target, port))
                
                # Success response
                client_sock.send(b'\x05\x00\x00\x01\x00\x00\x00\x00\x00\x00')
                
                # Bridge data
                while True:
                    data = client_sock.recv(4096)
                    if not data:
                        break
                    remote_sock.sendall(data)
                    
                    response = remote_sock.recv(4096)
                    if response:
                        client_sock.sendall(response)
                        
            except Exception as e:
                # Connection failed
                client_sock.send(b'\x05\x04\x00\x01\x00\x00\x00\x00\x00\x00')
                
        except Exception as e:
            pass
        finally:
            client_sock.close()
    
    def start(self):
        self.setup_tun()
        
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(('0.0.0.0', PORT))
        server.listen(10)
        
        print(f"\n{'='*50}")
        print(f"WYND SOCKS5 Proxy on port {PORT}")
        print(f"{'='*50}")
        print(f"Proxy: 0.0.0.0:{PORT}")
        print("\nConfigure client to use SOCKS5 proxy:")
        print(f"  Host: <server-ip>")
        print(f"  Port: {PORT}")
        print("\nWaiting for connections...\n")
        
        while self.running:
            try:
                client_sock, client_addr = server.accept()
                thread = threading.Thread(target=self.handle_client, args=(client_sock, client_addr))
                thread.daemon = True
                thread.start()
            except Exception as e:
                if self.running:
                    print(f"Error: {e}")

if __name__ == "__main__":
    proxy = WYNDSOCKS5()
    
    def signal_handler(sig, frame):
        print("\nShutting down...")
        proxy.running = False
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    proxy.start()