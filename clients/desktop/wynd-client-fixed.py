#!/usr/bin/env python3
"""WYND VPN Client - Fixed version"""
import socket
import struct
import threading
import sys

SERVER = "161.118.177.7"
PORT = 53
PROXY_PORT = 1080

print("=" * 50)
print("WYND VPN Client")
print("=" * 50)
print(f"Server: {SERVER}:{PORT}")
print(f"Local Proxy: 127.0.0.1:{PROXY_PORT}")
print()

# Connect to server
print("Connecting to server...")
server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_sock.connect((SERVER, PORT))
server_sock.sendall(struct.pack('!H', 4) + b"PING")
resp = server_sock.recv(10)
print(f"Connected! ({resp})")
print()

# Create new server connection for each client
def handle_client(client):
    try:
        # Create new connection to WYND server for this client
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.connect((SERVER, PORT))
        
        # Bridge bidirectional
        def forward(src, dst):
            try:
                while True:
                    data = src.recv(4096)
                    if not data: break
                    dst.sendall(data)
            except: pass
        
        # Start both directions
        t1 = threading.Thread(target=forward, args=(client, server))
        t2 = threading.Thread(target=forward, args=(server, client))
        t1.start()
        t2.start()
        t1.join()
        t2.join()
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()
        server.close()

# Start proxy
proxy = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
proxy.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
proxy.bind(('127.0.0.1', PROXY_PORT))
proxy.listen(5)

print(f"Proxy running on 127.0.0.1:{PROXY_PORT}")
print()
print("HOW TO USE:")
print("1. Download proxychains from github.com/rofl0r/proxychains-ng")
print("2. Add to proxychains.conf: socks5 127.0.0.1 1080")
print("3. Run: proxychains your_app.exe")
print()
print("Press Ctrl+C to stop")
print()

try:
    while True:
        c, a = proxy.accept()
        print(f"Client connected: {a}")
        t = threading.Thread(target=handle_client)
        t.daemon = True
        t.start()
except KeyboardInterrupt:
    print("\nStopping...")
    server_sock.close()