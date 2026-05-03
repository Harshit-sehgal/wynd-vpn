#!/usr/bin/env python3
import socket
import struct

print("Testing server forwarding...")

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(('127.0.0.1', 53))

# Connect to 8.8.8.8:53 (DNS)
req = b'\x01' + socket.inet_aton('8.8.8.8') + struct.pack('!H', 53)
s.sendall(struct.pack('!H', len(req)) + req)

# Read response
resp_header = s.recv(2)
resp_len = struct.unpack('!H', resp_header)[0]
print(f"Response length: {resp_len}")

resp_data = s.recv(resp_len)
print(f"Response data: {resp_data[0] if resp_data else 'none'}")

if resp_data and resp_data[0] == 0:
    print("Connected! Sending DNS query...")
    
    # DNS query for google.com
    query = b'\x12\x34\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00\x06google\x03com\x00\x00\x01\x00\x01'
    s.sendall(query)
    
    # Read DNS response
    data = s.recv(512)
    print(f"DNS Response: {len(data)} bytes")
    
    if len(data) > 12:
        print("SUCCESS! DNS query worked!")
else:
    print("Connection failed")

s.close()