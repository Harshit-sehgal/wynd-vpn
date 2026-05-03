#!/usr/bin/env python3
"""WYND VPN Client - Single file executable"""
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

# Start proxy
proxy = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
proxy.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
proxy.bind(('127.0.0.1', PROXY_PORT))
proxy.listen(5)

print(f"Proxy running on 127.0.0.1:{PROXY_PORT}")
print()
print("HOW TO USE:")
print("1. Download proxychains: github.com/rofl0r/proxychains-ng")
print("2. Add to proxychains.conf: socks5 127.0.0.1 1080")
print("3. Run: proxychains your_app.exe")
print()
print("Press Ctrl+C to stop")
print()

def bridge(client, server):
    try:
        while True:
            data = client.recv(4096)
            if not data: break
            server.sendall(struct.pack('!H', len(data)) + data)
            h = server.recv(2)
            l = struct.unpack('!H', h)[0]
            if l > 0:
                r = server.recv(l)
                client.send(r)
    except: pass
    finally: client.close()

try:
    while True:
        c, a = proxy.accept()
        print(f"Client connected: {a}")
        t = threading.Thread(target=bridge, args=(c, socket.socket(socket.AF_INET, socket.SOCK_STREAM)))
        t.daemon = True
        t.start()
except KeyboardInterrupt:
    print("\nStopping...")
    server_sock.close()