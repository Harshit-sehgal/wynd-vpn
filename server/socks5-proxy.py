#!/usr/bin/env python3
"""
WYND SOCKS5 Proxy Server
Routes traffic through the VPN tunnel to bypass restrictions
"""

import socket
import threading
import sys
import os

LISTEN_PORT = 53
BIND_IP = "0.0.0.0"

def handle_client(client_sock, client_addr):
    """Handle SOCKS5 connection"""
    try:
        # SOCKS5 greeting
        client_sock.recv(2)  # Version + nmethods
        client_sock.send(b'\x05\x00')  # No auth required

        # SOCKS5 request
        data = client_sock.recv(4)
        cmd = data[1]
        addr_type = data[3]

        if addr_type == 1:  # IPv4
            target_ip = client_sock.recv(4)
            target = socket.inet_ntoa(target_ip)
        elif addr_type == 3:  # Domain
            domain_len = client_sock.recv(1)[0]
            target = client_sock.recv(domain_len).decode()
        elif addr_type == 4:  # IPv6
            target_ip = client_sock.recv(16)
            target = socket.inet_ntop(socket.AF_INET6, target_ip)
        
        target_port = int.from_bytes(client_sock.recv(2), 'big')

        # Connect to target (through VPN)
        # For now, connect directly - traffic goes through server's network
        try:
            remote_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            remote_sock.connect((target, target_port))
            
            # Send success response
            client_sock.send(b'\x05\x00\x00\x01\x00\x00\x00\x00\x00\x00')
            
            # Forward traffic
            def forward(src, dst):
                while True:
                    try:
                        data = src.recv(4096)
                        if not data:
                            break
                        dst.sendall(data)
                    except:
                        break
            
            # Start forwarding in both directions
            t1 = threading.Thread(target=forward, args=(client_sock, remote_sock))
            t2 = threading.Thread(target=forward, args=(remote_sock, client_sock))
            t1.start()
            t2.start()
            t1.join()
            t2.join()
            
        except Exception as e:
            client_sock.send(b'\x05\x01\x00\x01\x00\x00\x00\x00\x00\x00')
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client_sock.close()

def start_server():
    """Start SOCKS5 proxy server"""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((BIND_IP, LISTEN_PORT))
    server.listen(5)
    
    print(f"WYND SOCKS5 Proxy Server")
    print(f"========================")
    print(f"Listening on: {BIND_IP}:{LISTEN_PORT}")
    print(f"")
    print(f"Configure your app to use SOCKS5 proxy:")
    print(f"  Host: 161.118.177.7")
    print(f"  Port: {LISTEN_PORT}")
    print(f"")
    print(f"Waiting for connections...")
    
    while True:
        client_sock, client_addr = server.accept()
        print(f"New connection from: {client_addr}")
        thread = threading.Thread(target=handle_client, args=(client_sock, client_addr))
        thread.daemon = True
        thread.start()

if __name__ == "__main__":
    # Check if running as root (needed for port 53)
    if os.geteuid() != 0:
        print("Warning: Not running as root. Port 53 may require sudo.")
    
    start_server()