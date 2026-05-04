#!/usr/bin/env python3
"""
WYND HTTP Proxy - Simple browser VPN
Forwards all HTTP/HTTPS traffic through WYND server
"""

import socket
import struct
import threading
import sys

SERVER_HOST = "161.118.177.7"
SERVER_PORT = 53
LOCAL_HTTP_PORT = 8080
LOCAL_SOCKS_PORT = 1080

class WYNDProxy:
    def __init__(self):
        self.server_conn = None
        
    def connect(self):
        print(f"Connecting to WYND server {SERVER_HOST}:{SERVER_PORT}...")
        self.server_conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_conn.settimeout(30)
        self.server_conn.connect((SERVER_HOST, SERVER_PORT))
        
        # Handshake
        self.server_conn.sendall(struct.pack('!H', 4) + b"INIT")
        resp = self.server_conn.recv(2)
        print("Connected to WYND VPN!")
        
    def handle_http(self, client_sock, method):
        """Handle HTTP CONNECT request"""
        try:
            # Parse the request
            line = client_sock.recv(1024).decode('utf-8', errors='ignore')
            parts = line.split()
            
            if len(parts) >= 2:
                host_port = parts[1].split(':')
                target_host = host_port[0]
                target_port = int(host_port[1]) if len(host_port) > 1 else 80
                
                # Resolve hostname to IP
                resolved_ip = socket.gethostbyname(target_host)
                print(f"Resolved {target_host} -> {resolved_ip}")
                
                # Send IP-based format: [1][IP1][IP2][IP3][IP4][port_hi][port_lo]
                ip_bytes = bytes(map(int, resolved_ip.split('.')))
                request = b'\x01' + ip_bytes + struct.pack('!H', target_port)
                self.server_conn.sendall(struct.pack('!H', len(request)) + request)
                
                # Get response
                resp = self.server_conn.recv(1)
                if resp == b'\x00':
                    # Success
                    client_sock.send(b"HTTP/1.1 200 Connection Established\r\n\r\n")
                    
                    # Bridge
                    while True:
                        data = client_sock.recv(4096)
                        if not data:
                            print("No data from browser, breaking")
                            break
                        print(f"Sending {len(data)} bytes to server")
                        self.server_conn.sendall(struct.pack('!H', len(data)) + data)
                        
                        print("Waiting for response...")
                        resp_data = self.server_conn.recv(2)
                        if not resp_data:
                            print("No response from server")
                            break
                        resp_len = struct.unpack('!H', resp_data)[0]
                        print(f"Response length: {resp_len}")
                        if resp_len > 0:
                            resp = self.server_conn.recv(resp_len)
                            client_sock.send(resp)
                            print(f"Sent {len(resp)} bytes to browser")
        except Exception as e:
            print(f"Error: {e}")
        finally:
            client_sock.close()
    
    def start(self):
        self.connect()
        
        # Start HTTP proxy
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(('127.0.0.1', LOCAL_HTTP_PORT))
        server.listen(5)
        
        print(f"\n{'='*50}")
        print("WYND HTTP Proxy")
        print(f"{'='*50}")
        print(f"HTTP Proxy: http://127.0.0.1:{LOCAL_HTTP_PORT}")
        print(f"SOCKS5: 127.0.0.1:{LOCAL_SOCKS_PORT}")
        print(f"\nConfigure your browser to use HTTP proxy:")
        print(f"  Host: 127.0.0.1")
        print(f"  Port: {LOCAL_HTTP_PORT}")
        print("\nWaiting for connections...\n")
        
        while True:
            client, addr = server.accept()
            # Handle as HTTP CONNECT
            thread = threading.Thread(target=self.handle_http, args=(client, "CONNECT"))
            thread.daemon = True
            thread.start()

if __name__ == "__main__":
    proxy = WYNDProxy()
    try:
        proxy.start()
    except KeyboardInterrupt:
        print("\nStopping...")