#!/usr/bin/env python3
"""
WYND VPN Client for Windows - Full System VPN
This creates a VPN by routing all traffic through WYND server
"""
import socket
import struct
import threading
import subprocess
import sys
import time
import os

SERVER = "161.118.177.7"
SERVER_PORT = 53
PROXY_PORT = 1080
VPN_IP = "10.0.0.2"
VPN_GATEWAY = "10.0.0.1"

class WYNDFullVPN:
    def __init__(self):
        self.server_connections = []
        
    def connect_to_server(self):
        """Establish connection to WYND server"""
        print("=" * 50)
        print("WYND VPN Client")
        print("=" * 50)
        print(f"Connecting to {SERVER}:{SERVER_PORT}...")
        
        # Test connection
        test_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        test_sock.connect((SERVER, SERVER_PORT))
        test_sock.sendall(struct.pack('!H', 4) + b"PING")
        resp = test_sock.recv(10)
        test_sock.close()
        
        print(f"Connected to WYND server!")
        return True
        
    def setup_windows_vpn_routing(self):
        """Set up Windows routing to use VPN"""
        print("\nSetting up Windows VPN routing...")
        
        try:
            # Step 1: Add a route to send VPN traffic directly (not through proxy)
            # This creates a "split tunnel" - but we'll handle all traffic
            
            # Step 2: For now, we'll use the proxy method
            # The proper way is to use "netsh" to set up a proxy
            
            print("Creating local SOCKS5 proxy on port", PROXY_PORT)
            
            # Step 3: Use netsh to redirect HTTP/HTTPS through our proxy
            # This is a Windows-native way to proxy traffic
            
            # First, let's set up the proxy server
            return True
            
        except Exception as e:
            print(f"Routing setup note: {e}")
            return True
    
    def start_socks_proxy(self):
        """Start the SOCKS5 proxy server"""
        proxy = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        proxy.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            proxy.bind(('127.0.0.1', PROXY_PORT))
        except:
            # Try alternative port
            PROXY_PORT = 1081
            proxy.bind(('127.0.0.1', PROXY_PORT))
            
        proxy.listen(10)
        print(f"SOCKS5 proxy listening on 127.0.0.1:{PROXY_PORT}")
        
        return proxy
    
    def handle_socks_client(self, client_sock, client_addr):
        """Handle a SOCKS client connection"""
        try:
            # SOCKS5 greeting
            version = client_sock.recv(1)
            if version != b'\x05':
                client_sock.close()
                return
            
            nmethods = client_sock.recv(1)
            methods = client_sock.recv(ord(nmethods))
            
            # Accept no authentication
            client_sock.send(b'\x05\x00')
            
            # Get the request
            cmd = client_sock.recv(1)
            _ = client_sock.recv(1)  # reserved
            addr_type = client_sock.recv(1)
            
            # Parse target
            if addr_type == b'\x01':  # IPv4
                target_ip = client_sock.recv(4)
                target = socket.inet_ntoa(target_ip)
            elif addr_type == b'\x03':  # Domain
                domain_len = client_sock.recv(1)
                target = client_sock.recv(ord(domain_len)).decode()
            elif addr_type == b'\x04':  # IPv6
                target_ip = client_sock.recv(16)
                target = socket.inet_ntop(socket.AF_INET6, target_ip)
                
            target_port = struct.unpack('!H', client_sock.recv(2))[0]
            
            # Connect to WYND server through our custom protocol
            # We'll tunnel the connection through the WYND server
            
            # Create connection to WYND server
            wynd_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            wynd_sock.connect((SERVER, SERVER_PORT))
            
            # Send CONNECT request through WYND protocol
            if addr_type == b'\x03':
                request = target.encode()
            else:
                request = target_ip
                
            # Forward to WYND server
            wynd_sock.sendall(struct.pack('!H', len(request)) + request)
            
            # Get response
            resp_header = wynd_sock.recv(2)
            resp_len = struct.unpack('!H', resp_header)[0]
            resp = wynd_sock.recv(resp_len)
            
            if resp and resp[0] == 0:
                # Success
                client_sock.send(b'\x05\x00\x00\x01\x00\x00\x00\x00\x00\x00')
                
                # Bridge traffic
                self.bridge_connections(client_sock, wynd_sock)
            else:
                client_sock.send(b'\x05\x01\x00\x01\x00\x00\x00\x00\x00\x00')
                
        except Exception as e:
            print(f"Client error: {e}")
        finally:
            try:
                client_sock.close()
            except:
                pass
    
    def bridge_connections(self, client_sock, server_sock):
        """Bridge data between client and server"""
        def forward(src, dst):
            try:
                while True:
                    data = src.recv(4096)
                    if not data:
                        break
                    dst.sendall(data)
            except:
                pass
        
        t1 = threading.Thread(target=forward, args=(client_sock, server_sock))
        t2 = threading.Thread(target=forward, args=(server_sock, client_sock))
        t1.start()
        t2.start()
        t1.join()
        t2.join()
    
    def run(self):
        """Main run function"""
        if not self.connect_to_server():
            print("Failed to connect to server")
            return
        
        # Start proxy
        proxy = self.start_socks_proxy()
        
        print("")
        print("=" * 50)
        print("VPN SETUP INSTRUCTIONS")
        print("=" * 50)
        print("Your WYND VPN is running!")
        print(f"SOCKS5 Proxy: 127.0.0.1:{PROXY_PORT}")
        print("")
        print("To route ALL traffic through the VPN:")
        print("")
        print("METHOD 1 - Use proxychains (Recommended):")
        print("1. Download proxychains from: github.com/rofl0r/proxychains-ng")
        print(f"2. Add: socks5 127.0.0.1 {PROXY_PORT}")
        print("3. Run: proxychains your_app.exe")
        print("")
        print("METHOD 2 - Windows Proxy Settings:")
        print(f"1. Settings -> Network -> Proxy")
        print(f"2. Manual proxy: 127.0.0.1 port {PROXY_PORT}")
        print("")
        print("METHOD 3 - Full system (run as admin):")
        print(f"   netsh winhttp set proxy 127.0.0.1:{PROXY_PORT}")
        print("")
        print("=" * 50)
        print(f"Waiting for connections on port {PROXY_PORT}...")
        
        try:
            while True:
                client, addr = proxy.accept()
                print(f"Client connected: {addr}")
                thread = threading.Thread(target=self.handle_socks_client, args=(client, addr))
                thread.daemon = True
                thread.start()
        except KeyboardInterrupt:
            print("\nStopping VPN...")

if __name__ == "__main__":
    vpn = WYNDFullVPN()
    vpn.run()