import socket
import struct

SERVER_HOST = "161.118.177.7"
SERVER_PORT = 53

print("WYND Desktop Client - Quick Test")
print(f"Connecting to {SERVER_HOST}:{SERVER_PORT}...")

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((SERVER_HOST, SERVER_PORT))
print("Connected!")

for i in range(3):
    payload = f"Test {i}".encode()
    s.sendall(struct.pack('!H', len(payload)) + payload)
    resp_len = struct.unpack('!H', s.recv(2))[0]
    resp = s.recv(resp_len)
    print(f"  Packet {i}: OK")

s.close()
print("Done!")