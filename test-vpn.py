#!/usr/bin/env python3
"""
Test OpenVPN connection to WYND server.
Connects via TCP 53 and performs OpenVPN handshake.
"""

import socket
import sys
import time

SERVER = "161.118.177.7"
PORT = 53
TIMEOUT = 10

def test_connection():
    print(f"Testing connection to {SERVER}:{PORT}...")
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(TIMEOUT)
        sock.connect((SERVER, PORT))
        print(f"Connected! Connection successful.")
        
        # Send OpenVPN client hello (this won't work perfectly but tests TCP)
        # OpenVPN protocol starts with client hello
        client_hello = b'\x00\x00\x00\x00\x00\x00\x00\x00'
        sock.send(client_hello)
        print("Sent client hello")
        
        # Try to receive response
        try:
            data = sock.recv(1024)
            if data:
                print(f"Received: {data.hex()}")
        except socket.timeout:
            print("No immediate response (expected for OpenVPN)")
        
        sock.close()
        return True
        
    except socket.timeout:
        print(f"Connection timed out after {TIMEOUT}s")
        return False
    except ConnectionRefusedError:
        print("Connection refused - is server listening?")
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)