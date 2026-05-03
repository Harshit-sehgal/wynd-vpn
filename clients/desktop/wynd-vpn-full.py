#!/usr/bin/env python3
"""
WYND VPN - Full System VPN for Windows
Uses Windows networking to route ALL traffic through port 53
"""
import socket
import struct
import threading
import subprocess
import os
import sys

SERVER = "161.118.177.7"
SERVER_PORT = 53

class WYNDFullVPN:
    def __init__(self):
        self.running = True
        self.server_conn = None
        
    def connect_to_server(self):
        """Connect to WYND server"""
        print(f"Connecting to {SERVER}:{SERVER_PORT}...")
        self.server_conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_conn.connect((SERVER, SERVER_PORT))
        print("Connected!")
        
    def handle_tcp_connection(self, client_sock, target_ip, target_port):
        """Forward a TCP connection through our server"""
        try:
            # Connect to real destination through our server
            # Our protocol: send target IP:port, get back connection
            request = f"{target_ip}:{target_port}".encode()
            self.server_conn.sendall(struct.pack('!H', len(request)) + request)
            
            # Wait for connection result
            resp = self.server_conn.recv(2)
            if resp and resp[1] == 0:  # Success
                # Forward data bidirectionally
                def forward(src, dst):
                    try:
                        while True:
                            data = src.recv(4096)
                            if not data:
                                break
                            dst.sendall(data)
                    except:
                        pass
                
                t1 = threading.Thread(target=forward, args=(client_sock, self.server_conn))
                t2 = threading.Thread(target=forward, args=(self.server_conn, client_sock))
                t1.start()
                t2.start()
                t1.join()
                t2.join()
        except Exception as e:
            pass
        finally:
            try:
                client_sock.close()
            except:
                pass
    
    def start_server(self):
        """Start listening for connections from apps"""
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(('10.0.0.2', 0))  # Listen on our VPN IP
        server.listen(50)
        
        print(f"VPN listening on 10.0.0.2")
        
        while self.running:
            try:
                client, addr = server.accept()
                # Parse target from client connection
                # For now, extract from socket
                target_ip = None
                target_port = 80
                
                # Get destination from connect request
                # We'll handle this properly
            except:
                pass
    
    def setup_windows_routing(self):
        """Set up Windows to use this VPN"""
        print("\nSetting up Windows VPN routing...")
        print("=" * 50)
        
        # Method 1: Use Windows Routing Table
        # Add a route for all traffic to go through our "gateway"
        print("\nTo enable full VPN, run these in CMD as ADMINISTRATOR:")
        print("-" * 40)
        print("1. Add a new network interface:")
        print("   This requires a TUN/TAP driver")
        print("")
        print("2. OR use proxy approach:")
        print("   netsh winhttp set proxy 127.0.0.1:1080")
        print("")
        print("3. Current best option - Use proxychains:")
        print("   Download proxychains from github.com/rofl0r/proxychains-ng")
        print(f"   Edit proxychains.conf: socks5 127.0.0.1 1080")
        print("   Then run: proxychains your_app.exe")
        print("-" * 40)
        
    def run_with_full_routing(self):
        """Run with as much routing as possible"""
        print("=" * 50)
        print("WYND VPN - Full System VPN")
        print("=" * 50)
        
        # Connect to server
        self.connect_to_server()
        
        # Try to use Windows VPN API or setup routing
        self.setup_windows_routing()
        
        print("\nStarting local proxy server...")
        
        # Create a SOCKS5-like proxy on local port
        proxy = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        proxy.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        proxy.bind(('127.0.0.1', 1080))
        proxy.listen(10)
        
        print(f"\nProxy running on 127.0.0.1:1080")
        print("\nUsage options:")
        print("1. Configure app to use 127.0.0.1:1080 as SOCKS5 proxy")
        print("2. Use proxychains: proxychains your_app.exe")
        print("3. Set Windows proxy: netsh winhttp set proxy 127.0.0.1:1080")
        print("\nWaiting for connections...\n")
        
        while self.running:
            try:
                client, addr = proxy.accept()
                print(f"Connection from {addr}")
                
                # Parse SOCKS5 request and handle
                t = threading.Thread(target=self.handle_socks5, args=(client,))
                t.daemon = True
                t.start()
            except:
                pass
    
    def handle_socks5(self, client_sock):
        """Handle SOCKS5 protocol"""
        try:
            # Greeting
            ver = client_sock.recv(1)
            nmethods = client_sock.recv(1)
            methods = client_sock.recv(ord(nmethods))
            client_sock.send(b'\x05\x00')
            
            # Request
            cmd = client_sock.recv(1)
            addr_type = client_sock.recv(1)
            
            if addr_type == b'\x01':  # IPv4
                target_ip = client_sock.recv(4)
                target = socket.inet_ntoa(target_ip)
            elif addr_type == b'\x03':  # Domain
                domain_len = client_sock.recv(1)
                target = client_sock.recv(ord(domain_len)).decode()
            
            target_port = struct.unpack('!H', client_sock.recv(2))[0]
            
            # Forward through our server
            self.handle_tcp_connection(client_sock, target, target_port)
            
        except:
            pass
        finally:
            try:
                client_sock.close()
            except:
                pass

if __name__ == "__main__":
    vpn = WYNDFullVPN()
    vpn.run_with_full_routing()