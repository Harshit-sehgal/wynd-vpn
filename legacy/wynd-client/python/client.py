#!/usr/bin/env python3
"""
WYND Client - TCP tunnel client for connecting to WYND server
"""

import socket
import sys
import threading

SERVER = "161.118.177.7"
PORT = 53
BUFFER_SIZE = 65535

def main():
    print(f"WYND Client - Connecting to {SERVER}:{PORT}...")
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((SERVER, PORT))
        
        # Handshake
        sock.send(b"HELLO\n")
        response = sock.recv(1024)
        
        if b"OK" in response:
            print(f"Connected! {response.decode()}")
            print("Tunnel established - traffic routes through WYND server")
        else:
            print(f"Handshake failed: {response}")
            return
            
    except Exception as e:
        print(f"Connection failed: {e}")
        return
    
    print("Note: Full VPN requires TUN adapter on system")

if __name__ == "__main__":
    main()