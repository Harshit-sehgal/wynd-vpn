#!/usr/bin/env python3
"""Simple WYND tunnel client - connects to server and keeps connection alive"""

import socket
import struct
import threading
import time

SERVER_HOST = "161.118.177.7"
SERVER_PORT = 53
LOCAL_PORT = 1080

def handle_client(client_sock, server_sock):
    """Bridge traffic between client and server"""
    try:
        while True:
            data = client_sock.recv(4096)
            if not data:
                break
            server_sock.sendall(struct.pack('!H', len(data)) + data)
            
            resp_header = server_sock.recv(2)
            if not resp_header:
                break
            resp_len = struct.unpack('!H', resp_header)[0]
            if resp_len > 0:
                resp = server_sock.recv(resp_len)
                client_sock.send(resp)
    except:
        pass
    finally:
        client_sock.close()

def main():
    print("WYND Tunnel Client")
    print(f"Connecting to {SERVER_HOST}:{SERVER_PORT}...")
    
    # Connect to server
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.connect((SERVER_HOST, SERVER_PORT))
    
    # Handshake
    server_sock.sendall(struct.pack('!H', 4) + b"PING")
    resp = server_sock.recv(2)
    print(f"Server connected! Response: {resp}")
    
    # Start local proxy
    proxy = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    proxy.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    proxy.bind(('127.0.0.1', LOCAL_PORT))
    proxy.listen(5)
    
    print(f"Proxy listening on 127.0.0.1:{LOCAL_PORT}")
    print("\nTo use with apps, configure SOCKS5 proxy to this address")
    print("Or use proxychains: proxychains your_app.exe")
    print("\nPress Ctrl+C to stop\n")
    
    while True:
        try:
            client, addr = proxy.accept()
            print(f"Client connected from {addr}")
            thread = threading.Thread(target=handle_client, args=(client, server_sock))
            thread.daemon = True
            thread.start()
        except KeyboardInterrupt:
            break
        except:
            pass
    
    server_sock.close()
    print("Stopped")

if __name__ == "__main__":
    main()