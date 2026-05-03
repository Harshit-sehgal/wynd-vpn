#!/usr/bin/env python3
import socket
import struct

print("Testing server forwarding...")

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(('127.0.0.1', 53))

# Connect to 8.8.8.8:53 (DNS)
req = b'\x01' + socket.inet_aton('8.8.8.8') + struct.pack('!H', 53)
s.sendall(struct.pack('!H', len(req)) + req)

resp = s.recv(2)
print(f"Connect response: {resp}")

if resp and resp[1] == 0:
    print("Connected! Sending DNS query...")
    # DNS query for google.com
    query = b'\x12\x34\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00\x06google\x03com\x00\x00\x01\x00\x01'
    s.sendall(query)
    data = s.recv(512)
    print(f"Got response: {len(data)} bytes")
    
    # Check if we got actual DNS response
    if len(data) > 12:
        print("DNS query successful!")
else:
    print("Connection failed")

s.close()