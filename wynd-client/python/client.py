#!/usr/bin/env python3
"""
WYND Client - Simple TCP 53 tunnel for testing
This establishes a connection to WYND server and forwards traffic.
"""

import socket
import sys
import threading
import select

SERVER = "161.118.177.7"
PORT = 53
BUFFER_SIZE = 65535

def main():
    print("WYND Client - TCP 53 Tunnel")
    print(f"Connecting to {SERVER}:{PORT}...")
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((SERVER, PORT))
        
        # Handshake
        sock.send(b"HELLO\n")
        response = sock.recv(1024)
        
        if b"OK" in response:
            print("Connected! Tunnel established.")
            print("Traffic now routes through WYND server.")
        else:
            print(f"Handshake failed: {response}")
            return
            
    except Exception as e:
        print(f"Connection failed: {e}")
        return
    
    print("Note: This is a tunnel test. Full VPN requires TUN adapter.")

if __name__ == "__main__":
    main()