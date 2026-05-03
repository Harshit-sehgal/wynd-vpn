#!/usr/bin/env python3
"""
WYND Simple HTTP Proxy Server
Forwards HTTP/HTTPS traffic through the TUN interface
"""

import socket
import struct
import threading
import signal
import sys

PORT = 53
TUN_IP = "10.0.0.1"

class WYNDProxyServer:
    def __init__(self):
        self.running = True
        self.tun_sock = None
        
    def setup_tun(self):
        """Create UDP socket to simulate TUN for simplicity"""
        # Use raw socket approach - bind to TUN IP
        try:
            self.tun_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.tun_sock.bind((TUN_IP, 0))
            print(f"TUN emulator bound to {TUN_IP}")
        except Exception as e:
            print(f"TUN setup: {e}")
            # Fallback - use direct internet from server
            self.tun_sock = None
            print("Using direct internet from server")
    
    def handle_client(self, client_sock, client_addr):
        """Handle HTTP proxy request"""
        try:
            # Read HTTP request
            request = b""
            while True:
                chunk = client_sock.recv(4096)
                request += chunk
                if b"\r\n\r\n" in chunk or len(chunk) == 0:
                    break
            
            if not request:
                client_sock.close()
                return
            
            # Parse HTTP request
            try:
                request_str = request.decode('utf-8', errors='ignore')
                lines = request_str.split('\r\n')
                if lines:
                    first_line = lines[0].split()
                    if len(first_line) >= 2:
                        method = first_line[0]
                        path = first_line[1]
                        
                        # Extract Host header
                        host = None
                        port = 80
                        for line in lines[1:]:
                            if line.lower().startswith('host:'):
                                host_port = line.split(':')[1].strip()
                                if ':' in host_port:
                                    parts = host_port.split(':')
                                    host = parts[0]
                                    port = int(parts[1])
                                else:
                                    host = host_port
                                break
                        
                        if host:
                            print(f"[{client_addr}] {method} {host}:{port}")
                            
                            # Forward to actual server
                            remote_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                            remote_sock.connect((host, port))
                            remote_sock.sendall(request)
                            
                            # Get response and send back
                            while True:
                                resp = remote_sock.recv(8192)
                                if not resp:
                                    break
                                client_sock.sendall(resp)
                                
                            remote_sock.close()
            except Exception as e:
                print(f"Request parse error: {e}")
                
        except Exception as e:
            print(f"Client error: {e}")
        finally:
            client_sock.close()
    
    def start(self):
        self.setup_tun()
        
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(('0.0.0.0', PORT))
        server.listen(10)
        
        print(f"\n{'='*50}")
        print(f"WYND HTTP Proxy on port {PORT}")
        print(f"{'='*50}")
        print(f"Server: 0.0.0.0:{PORT}")
        print(f"TUN: {TUN_IP}")
        print("\nAccepting connections...\n")
        
        while self.running:
            try:
                client_sock, client_addr = server.accept()
                thread = threading.Thread(target=self.handle_client, args=(client_sock, client_addr))
                thread.daemon = True
                thread.start()
            except Exception as e:
                if self.running:
                    print(f"Accept error: {e}")

if __name__ == "__main__":
    proxy = WYNDProxyServer()
    
    def signal_handler(sig, frame):
        print("\nShutting down...")
        proxy.running = False
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    proxy.start()