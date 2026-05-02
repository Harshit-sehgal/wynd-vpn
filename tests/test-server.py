#!/usr/bin/env python3
"""Test connection to WYND server on TCP 53"""
import socket
import sys

SERVER = "161.118.177.7"
PORT = 53

def test():
    print(f"Connecting to {SERVER}:{PORT}...")
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(10)
        s.connect((SERVER, PORT))
        print("Connected!")
        
        # Send simple test
        s.send(b"HELLO\n")
        print("Sent HELLO")
        
        data = s.recv(1024)
        print(f"Response: {data}")
        s.close()
        
    except socket.timeout:
        print("TIMEOUT - server not responding")
    except ConnectionRefusedError:
        print("REFUSED - check server is running")
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    test()