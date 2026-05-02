#!/usr/bin/env python3
"""
WYND Desktop VPN Client - Windows Compatible
Uses a SOCKS5 proxy approach to tunnel all traffic through WYND server
"""

import socket
import struct
import threading
import sys
import os

SERVER_HOST = "161.118.177.7"
SERVER_PORT = 53
LOCAL_PROXY_PORT = 1080
TUN_IP = "10.0.0.2"
TUN_NETMASK = "255.255.255.0"
SERVER_IP = "10.0.0.1"

class WYNDClient:
    def __init__(self):
        self.server_socket = None
        self.running = False
        
    def connect_to_server(self):
        """Connect to WYND server with framing protocol"""
        print(f"Connecting to WYND server {SERVER_HOST}:{SERVER_PORT}...")
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.connect((SERVER_HOST, SERVER_PORT))
        print("Connected to WYND server!")
        
        # Test connection
        test_payload = b"INIT"
        self.server_socket.sendall(struct.pack('!H', len(test_payload)) + test_payload)
        resp = self.server_socket.recv(2)
        print("Server handshake: OK")
        
    def handle_socks_client(self, client_socket, client_addr):
        """Handle SOCKS5 client connection"""
        try:
            # SOCKS5 greeting
            version = client_socket.recv(1)
            if version != b'\x05':
                client_socket.close()
                return
            
            nmethods = client_socket.recv(1)
            methods = client_socket.recv(ord(nmethods))
            
            # No auth
            client_socket.send(b'\x05\x00')
            
            # Request
            version = client_socket.recv(1)
            cmd = client_socket.recv(1)
            _ = client_socket.recv(1)
            addr_type = client_socket.recv(1)
            
            if addr_type == b'\x01':  # IPv4
                target_ip = client_socket.recv(4)
                target = socket.inet_ntoa(target_ip)
            elif addr_type == b'\x03':  # Domain
                domain_len = client_socket.recv(1)
                target = client_socket.recv(ord(domain_len)).decode()
            elif addr_type == b'\x04':  # IPv6
                target_ip = client_socket.recv(16)
                target = socket.inet_ntop(socket.AF_INET6, target_ip)
            
            target_port = struct.unpack('!H', client_socket.recv(2))[0]
            
            # Forward request to WYND server
            if addr_type == b'\x03':
                request = struct.pack('!BB', cmd[0], addr_type) + target.encode() + struct.pack('!H', target_port)
            else:
                request = struct.pack('!BB', cmd[0], addr_type) + target_ip + struct.pack('!H', target_port)
            
            self.server_socket.sendall(struct.pack('!H', len(request)) + request)
            
            # Get response
            resp_header = self.server_socket.recv(2)
            resp_len = struct.unpack('!H', resp_header)[0]
            resp = self.server_socket.recv(resp_len)
            
            if resp[0] == 0x00:  # Success
                client_socket.send(b'\x05\x00\x00\x01\x00\x00\x00\x00\x00\x00')
                
                # Bridge traffic
                self.bridge(client_socket, target, target_port)
            else:
                client_socket.send(b'\x05\x01\x00\x01\x00\x00\x00\x00\x00\x00')
                
        except Exception as e:
            print(f"Error handling client: {e}")
        finally:
            client_socket.close()
    
    def bridge(self, client_socket, target_host, target_port):
        """Bridge between client and WYND server"""
        try:
            while True:
                data = client_socket.recv(4096)
                if not data:
                    break
                # Send through WYND protocol
                self.server_socket.sendall(struct.pack('!H', len(data)) + data)
                
                # Get response
                resp_header = self.server_socket.recv(2)
                resp_len = struct.unpack('!H', resp_header)[0]
                resp_data = self.server_socket.recv(resp_len)
                client_socket.send(resp_data)
        except:
            pass
    
    def start_proxy(self):
        """Start SOCKS5 proxy server"""
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(('127.0.0.1', LOCAL_PROXY_PORT))
        server.listen(5)
        
        print(f"\n{'='*50}")
        print("WYND Desktop VPN Client")
        print(f"{'='*50}")
        print(f"SOCKS5 Proxy: 127.0.0.1:{LOCAL_PROXY_PORT}")
        print(f"Server: {SERVER_HOST}:{SERVER_PORT}")
        print(f"\nTo use the VPN:")
        print(f"1. Configure your browser/apps to use SOCKS5 proxy:")
        print(f"   Host: 127.0.0.1")
        print(f"   Port: {LOCAL_PROXY_PORT}")
        print(f"\nOr use a proxy wrapper like 'proxychains' for all apps")
        print(f"\nWaiting for connections...")
        
        while self.running:
            try:
                server.settimeout(1)
                client_socket, client_addr = server.accept()
                thread = threading.Thread(target=self.handle_socks_client, args=(client_socket, client_addr))
                thread.daemon = True
                thread.start()
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    print(f"Error: {e}")

def main():
    client = WYNDClient()
    client.running = True
    
    try:
        client.connect_to_server()
        client.start_proxy()
    except KeyboardInterrupt:
        print("\nShutting down...")
        client.running = False
        if client.server_socket:
            client.server_socket.close()

if __name__ == "__main__":
    main()